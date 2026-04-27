r"""
ingest.py - Data ingestion pipeline with financial metric enrichment.

Run from backend\ directory (with venv activated):
  Windows  : python scripts\ingest.py
  Mac/Linux: python scripts/ingest.py

Pipeline:
  1. Fetch ~8,000 NAVs from AMFI (free)
  2. Filter to ~2,500 investable growth funds
  3. Enrich with 1Y/3Y/5Y CAGR + Sharpe ratio from mfapi.in (free)
  4. Build rich text chunks and embed via OpenAI
  5. Upsert to Pinecone
  6. Cache in Redis

Enrichment adds ~5-8 minutes but makes recommendations dramatically better.
Skip with --no-enrich flag for a quick re-index.
"""
from __future__ import annotations

import asyncio
import logging
import sys
import time
import uuid
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

print(f"[path] BACKEND_DIR = {BACKEND_DIR}")
print(f"[path] config.py   = {(BACKEND_DIR / 'config.py').exists()}")

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env", override=True)

_MISSING = []
for _mod, _pkg in [
    ("dotenv",            "python-dotenv"),
    ("pydantic_settings", "pydantic-settings"),
    ("openai",            "openai"),
    ("pinecone",          "pinecone"),
    ("httpx",             "httpx"),
]:
    try:
        __import__(_mod)
    except ImportError:
        _MISSING.append(_pkg)

if _MISSING:
    print(f"\n[ERROR] Missing packages: {', '.join(_MISSING)}")
    print("Run: pip install -r requirements.txt")
    sys.exit(1)

from config import get_settings
from ingestion.amfi_loader import fetch_amfi_nav, filter_investable_funds
from ingestion.enricher import enrich_batch
from cache.redis_cache import set_all_funds_cache

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
    encoding="utf-8" if sys.platform == "win32" else None,
)
logger = logging.getLogger("ingest")
settings = get_settings()

EMBED_BATCH  = 50
UPSERT_BATCH = 100
NO_ENRICH    = "--no-enrich" in sys.argv


def embed_batch(client, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=settings.openai_embed_model,
        input=texts,
    )
    return [item.embedding for item in response.data]


async def run_ingestion() -> None:
    start = time.time()
    logger.info("=" * 60)
    logger.info("MF Advisor - Data Ingestion Pipeline")
    logger.info("=" * 60)
    logger.info("Enrich mode   : %s", "OFF (--no-enrich)" if NO_ENRICH else "ON (mfapi.in)")
    logger.info("Embed model   : %s", settings.openai_embed_model)
    logger.info("Pinecone index: %s", settings.pinecone_index_name)

    # Step 1: Fetch AMFI
    logger.info("\nSTEP 1/6 -> Fetching NAV data from AMFI India...")
    records = await fetch_amfi_nav(settings.amfi_nav_url)
    logger.info("  Fetched  : %d raw records", len(records))

    # Step 2: Filter
    logger.info("STEP 2/6 -> Filtering to investable growth funds...")
    records = filter_investable_funds(records)
    logger.info("  Filtered : %d records", len(records))
    if not records:
        logger.error("No records after filtering - aborting")
        return

    # Step 3: Enrich with historical data
    if NO_ENRICH:
        logger.info("STEP 3/6 -> Skipping enrichment (--no-enrich)")
    else:
        logger.info("STEP 3/6 -> Enriching with historical returns from mfapi.in...")
        logger.info("  This takes 5-10 min but makes recommendations much better.")
        logger.info("  Skip next time with: python scripts/ingest.py --no-enrich")
        records = await enrich_batch(records, max_concurrent=20)
        enriched = sum(1 for r in records if r.returns_1y is not None)
        logger.info("  Funds with 1Y returns: %d / %d", enriched, len(records))

    # Step 4: Build chunks
    logger.info("STEP 4/6 -> Building text chunks...")
    documents = [
        {"text": r.to_chunk_text(), "metadata": r.to_metadata()}
        for r in records
    ]
    logger.info("  Chunks built : %d", len(documents))
    logger.info("  Sample chunk preview:")
    preview = documents[0]["text"][:400].encode("ascii", "replace").decode("ascii")
    print(preview)
    print("---")

    # Step 5: Embed + Upsert
    logger.info("STEP 5/6 -> Embedding & upserting to Pinecone...")
    logger.info("  Est. cost: ~$%.4f", len(documents) * 400 / 1_000_000 * 0.02)

    from openai import OpenAI
    from pinecone import Pinecone, ServerlessSpec

    oai = OpenAI(api_key=settings.openai_api_key)
    pc  = Pinecone(api_key=settings.pinecone_api_key)

    try:
        existing = pc.list_indexes().names()
    except AttributeError:
        existing = [i["name"] for i in pc.list_indexes()]

    if settings.pinecone_index_name not in existing:
        logger.info("  Creating index '%s'...", settings.pinecone_index_name)
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.openai_embed_dims,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        time.sleep(10)

    idx = pc.Index(settings.pinecone_index_name)

    all_vectors    = []
    total_embedded = 0

    for i in range(0, len(documents), EMBED_BATCH):
        batch_docs  = documents[i : i + EMBED_BATCH]
        batch_texts = [d["text"] for d in batch_docs]
        batch_metas = [d["metadata"] for d in batch_docs]

        try:
            embeddings = embed_batch(oai, batch_texts)
        except Exception as e:
            logger.error("  Embed batch %d FAILED: %s", i // EMBED_BATCH, e)
            await asyncio.sleep(2)
            continue

        for text, meta, emb in zip(batch_texts, batch_metas, embeddings):
            all_vectors.append({
                "id":       str(uuid.uuid4()),
                "values":   emb,
                "metadata": {**meta, "text": text[:800]},
            })

        total_embedded += len(batch_docs)
        pct = total_embedded / len(documents) * 100
        logger.info("  Embedded %d/%d (%.0f%%)", total_embedded, len(documents), pct)
        await asyncio.sleep(0.3)

    total_upserted = 0
    for i in range(0, len(all_vectors), UPSERT_BATCH):
        batch = all_vectors[i : i + UPSERT_BATCH]
        try:
            idx.upsert(vectors=batch, namespace=settings.pinecone_namespace)
            total_upserted += len(batch)
        except Exception as e:
            logger.error("  Upsert batch %d FAILED: %s", i // UPSERT_BATCH, e)
        await asyncio.sleep(0.1)

    logger.info("  Upserted %d vectors total", total_upserted)
    await asyncio.sleep(5)
    confirmed = idx.describe_index_stats().get("total_vector_count", 0)
    logger.info("  Confirmed in Pinecone: %d", confirmed)

    # Step 6: Cache in Redis
    logger.info("STEP 6/6 -> Caching in Redis...")
    try:
        cache_data = [
            {
                "scheme_code":    r.scheme_code,
                "scheme_name":    r.scheme_name,
                "nav":            r.nav,
                "date":           r.date,
                "broad_category": r.broad_category,
                "sub_category":   r.sub_category,
                "risk_rating":    r.risk_rating,
                "amc_name":       r.amc_name,
                "returns_1y":     r.returns_1y,
                "returns_3y":     r.returns_3y,
                "returns_5y":     r.returns_5y,
                "sharpe_ratio":   r.sharpe_ratio,
                "expense_ratio":  r.expense_ratio,
                "aum_crores":     r.aum_crores,
                "rating_stars":   r.rating_stars,
            }
            for r in records
        ]
        await set_all_funds_cache(cache_data)
        logger.info("  Cached %d funds in Redis", len(cache_data))
    except Exception as e:
        logger.warning("  Redis cache skipped: %s", e)

    elapsed = time.time() - start
    logger.info("\n" + "=" * 60)
    logger.info("Ingestion complete in %.1f seconds (%.1f min)", elapsed, elapsed / 60)
    logger.info("  Records    : %d", len(records))
    logger.info("  Vectors    : %d", total_upserted)
    logger.info("  Confirmed  : %d", confirmed)
    logger.info("=" * 60)
    if confirmed > 0:
        logger.info("Start API: uvicorn main:app --reload --port 8000")
    else:
        logger.error("0 vectors confirmed - check errors above")


if __name__ == "__main__":
    asyncio.run(run_ingestion())