"""
check_pinecone.py — Diagnostic script.

Run from backend/ directory:
  cd backend
  python scripts/check_pinecone.py
"""
import sys, asyncio
from pathlib import Path

# backend/scripts/check_pinecone.py
#   .parent        -> backend/scripts/
#   .parent.parent -> backend/          <- what we need on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

# ── 1. Test AMFI fetch ────────────────────────────────────────────────────────
async def check_amfi():
    print("\n" + "="*55)
    print("CHECK 1 — AMFI NAV fetch")
    print("="*55)
    import httpx
    # URL permanently moved to portal.amfiindia.com — follow_redirects handles both
    url = "https://portal.amfiindia.com/spages/NAVAll.txt"
    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as c:
            r = await c.get(url)
            r.raise_for_status()
        lines = [l for l in r.text.splitlines() if ";" in l]
        print(f"  HTTP status : {r.status_code}")
        print(f"  Final URL   : {r.url}")
        print(f"  Total bytes : {len(r.content):,}")
        print(f"  Data rows   : {len(lines):,}")
        print(f"  Sample row  : {lines[5] if len(lines) > 5 else 'N/A'}")
        print(f"  Result      : {'OK' if len(lines) > 100 else 'FAIL — too few rows'}")
        return len(lines)
    except Exception as e:
        print(f"  FAILED: {e}")
        return 0

# ── 2. Check Pinecone index stats ─────────────────────────────────────────────
def check_pinecone():
    print("\n" + "="*55)
    print("CHECK 2 — Pinecone index stats")
    print("="*55)
    try:
        from config import get_settings
        from pinecone import Pinecone
        s = get_settings()
        pc = Pinecone(api_key=s.pinecone_api_key)

        try:
            names = pc.list_indexes().names()
        except AttributeError:
            names = [i["name"] for i in pc.list_indexes()]

        print(f"  Your indexes : {names}")

        if s.pinecone_index_name not in names:
            print(f"  WARNING : index '{s.pinecone_index_name}' does NOT exist yet")
            print(f"            Run ingest.py to create it")
            return 0

        idx = pc.Index(s.pinecone_index_name)
        stats = idx.describe_index_stats()
        total = stats.get("total_vector_count", 0)
        namespaces = stats.get("namespaces", {})

        print(f"  Index name    : {s.pinecone_index_name}")
        print(f"  Total vectors : {total:,}")
        print(f"  Namespaces    : {namespaces}")
        print(f"  Result        : {'OK' if total > 0 else 'EMPTY — run ingest.py'}")
        return total

    except Exception as e:
        print(f"  FAILED: {e}")
        return 0

# ── 3. Test a sample query ────────────────────────────────────────────────────
def check_sample_query():
    print("\n" + "="*55)
    print("CHECK 3 — Sample semantic query")
    print("="*55)
    try:
        from rag.retriever import retrieve_funds
        results = retrieve_funds(
            query="best large cap equity mutual fund India",
            user_profile={"risk_appetite": "medium", "investment_horizon": "long"},
            top_k=3,
        )
        if results:
            print(f"  Found {len(results)} results")
            for i, doc in enumerate(results, 1):
                name = doc.metadata.get("scheme_name", "N/A")
                cat  = doc.metadata.get("broad_category", "N/A")
                nav  = doc.metadata.get("nav", 0)
                print(f"  [{i}] {name[:55]}")
                print(f"       category={cat}  nav=Rs.{nav:.2f}")
            print("  Result : OK — RAG retrieval working")
        else:
            print("  No results returned (index may be empty)")
    except Exception as e:
        print(f"  FAILED: {e}")

async def main():
    rows = await check_amfi()
    vecs = check_pinecone()
    if vecs > 0:
        check_sample_query()

    print("\n" + "="*55)
    print("SUMMARY")
    print("="*55)
    if rows == 0:
        print("  AMFI fetch failed — check internet connection")
        print("  Try opening in browser: https://portal.amfiindia.com/spages/NAVAll.txt")
    elif vecs == 0:
        print("  AMFI OK but Pinecone is EMPTY — re-run ingest.py")
        print("  Check PINECONE_API_KEY in backend/.env")
    else:
        print(f"  All checks passed!")
        print(f"  AMFI rows: {rows:,} | Pinecone vectors: {vecs:,}")
        print(f"  Start the API: uvicorn main:app --reload --port 8000")

asyncio.run(main())