"""
test_upsert.py — Minimal end-to-end test: embed 1 doc → upsert → verify.

Run from backend/:
  python scripts/test_upsert.py

This bypasses LangChain completely and uses the raw SDKs directly
to isolate exactly which step fails.
"""
import sys, asyncio
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

from config import get_settings
settings = get_settings()


async def main():
    print("\n" + "="*55)
    print("Minimal embed + upsert test")
    print("="*55)

    # ── Step A: Test OpenAI embedding ─────────────────────────────────────────
    print("\n[A] Testing OpenAI embedding (1 document)...")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.openai_api_key)
        resp = client.embeddings.create(
            model=settings.openai_embed_model,
            input=["Mirae Asset Large Cap Fund - Growth - best large cap equity fund India"],
        )
        vec = resp.data[0].embedding
        print(f"    Embedding dimensions : {len(vec)}")
        print(f"    First 5 values       : {[round(v, 4) for v in vec[:5]]}")
        print(f"    Result               : OK")
    except Exception as e:
        print(f"    FAILED: {e}")
        print("    Check OPENAI_API_KEY in backend/.env")
        return

    # ── Step B: Upsert directly via Pinecone SDK (no LangChain) ──────────────
    print("\n[B] Upserting 1 test vector directly via Pinecone SDK...")
    try:
        from pinecone import Pinecone
        pc = Pinecone(api_key=settings.pinecone_api_key)
        idx = pc.Index(settings.pinecone_index_name)

        idx.upsert(
            vectors=[{
                "id": "test-vector-001",
                "values": vec,
                "metadata": {
                    "scheme_name": "TEST - Mirae Asset Large Cap Fund",
                    "broad_category": "equity",
                    "risk_rating": "moderate",
                    "doc_type": "fund",
                    "nav": 99.99,
                    "text": "Test fund for diagnostic purposes",
                },
            }],
            namespace=settings.pinecone_namespace,
        )
        print(f"    Upserted to index    : {settings.pinecone_index_name}")
        print(f"    Namespace            : {settings.pinecone_namespace}")
        print(f"    Result               : OK")
    except Exception as e:
        print(f"    FAILED: {e}")
        print("    Check PINECONE_API_KEY in backend/.env")
        return

    # ── Step C: Verify it's there ─────────────────────────────────────────────
    print("\n[C] Verifying vector count after upsert...")
    import time
    time.sleep(3)   # Pinecone serverless needs ~2-3s to reflect new vectors
    try:
        stats = idx.describe_index_stats()
        total = stats.get("total_vector_count", 0)
        ns    = stats.get("namespaces", {})
        print(f"    Total vectors : {total}")
        print(f"    Namespaces    : {ns}")
        if total > 0:
            print(f"    Result        : OK — vectors confirmed in index")
        else:
            print(f"    Result        : Still 0 — serverless index may need more time")
            print(f"                    Wait 30s then re-run check_pinecone.py")
    except Exception as e:
        print(f"    FAILED: {e}")
        return

    # ── Step D: Delete test vector ────────────────────────────────────────────
    print("\n[D] Cleaning up test vector...")
    try:
        idx.delete(ids=["test-vector-001"], namespace=settings.pinecone_namespace)
        print(f"    Deleted test-vector-001")
    except Exception as e:
        print(f"    Cleanup failed (not critical): {e}")

    print("\n" + "="*55)
    print("All steps passed — running full ingest.py should work.")
    print("Run: python scripts/ingest.py")
    print("="*55)


asyncio.run(main())