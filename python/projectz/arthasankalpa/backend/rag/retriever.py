"""
retriever.py — Pinecone vector retrieval with metadata filtering.

Strategy:
  1. Dense semantic search via Pinecone (cosine similarity)
  2. Metadata pre-filter based on user risk profile / category
  3. Simple score-based reranking (no Cohere — free local approach)
  
For production: swap step 3 with Cohere Rerank or a local cross-encoder.
"""
from __future__ import annotations

import logging
from typing import Optional

from langchain_pinecone import PineconeVectorStore
from langchain_core.documents import Document
from pinecone import Pinecone, ServerlessSpec

from config import get_settings
from rag.embedder import get_embedder

logger = logging.getLogger(__name__)
settings = get_settings()

# Module-level singletons — initialized once at startup
_pinecone_store: Optional[PineconeVectorStore] = None


def init_pinecone() -> PineconeVectorStore:
    """
    Connect to Pinecone and return the vector store.
    Creates the index if it does not exist (free tier: 2GB, 5 indexes).
    """
    global _pinecone_store
    if _pinecone_store is not None:
        return _pinecone_store

    pc = Pinecone(api_key=settings.pinecone_api_key)

    # list_indexes() returns an IndexList object in pinecone>=5.x.
    # .names() is available in v5+; iterate .indexes for v3/v4 fallback.
    try:
        existing = pc.list_indexes().names()   # pinecone v5–v7
    except AttributeError:
        existing = [idx["name"] for idx in pc.list_indexes()]  # pinecone v3/v4

    if settings.pinecone_index_name not in existing:
        logger.info("Creating Pinecone index: %s", settings.pinecone_index_name)
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=settings.openai_embed_dims,   # 1536
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1",  # Free tier region — change to ap-south-1 for prod
            ),
        )
    else:
        logger.info("Pinecone index already exists: %s", settings.pinecone_index_name)

    embedder = get_embedder()
    _pinecone_store = PineconeVectorStore(
        index_name=settings.pinecone_index_name,
        embedding=embedder,
        namespace=settings.pinecone_namespace,
        pinecone_api_key=settings.pinecone_api_key,
    )
    logger.info("Pinecone vector store initialized")
    return _pinecone_store


def _build_pinecone_filter(user_profile: dict) -> dict:
    """
    Build Pinecone metadata filter from user's risk/category preferences.
    
    Pinecone filter syntax uses MongoDB-style operators.
    """
    risk_map = {
        "low":    ["low"],
        "medium": ["low", "moderate"],
        "high":   ["low", "moderate", "high"],
    }
    risk = user_profile.get("risk_appetite", "medium")
    allowed_risks = risk_map.get(risk, ["low", "moderate"])

    pinecone_filter: dict = {
        "risk_rating": {"$in": allowed_risks},
        "doc_type": {"$eq": "fund"},
    }

    # Optional category constraint
    preferred_cat = user_profile.get("preferred_category")
    if preferred_cat and preferred_cat != "all":
        pinecone_filter["broad_category"] = {"$eq": preferred_cat}

    # For short-horizon users: restrict to debt/hybrid/index
    horizon = user_profile.get("investment_horizon", "long")
    if horizon == "short":
        pinecone_filter["broad_category"] = {"$in": ["debt", "hybrid", "index"]}

    return pinecone_filter


def retrieve_funds(
    query: str,
    user_profile: dict,
    top_k: int = None,
) -> list[Document]:
    """
    Retrieve the most relevant fund documents for a query.
    
    Args:
        query: Natural language query from the user.
        user_profile: Dict with keys: risk_appetite, investment_horizon, preferred_category.
        top_k: Number of candidates to fetch before reranking.
    
    Returns:
        List of LangChain Documents (page_content + metadata).
    """
    top_k = top_k or settings.retrieval_top_k
    store = init_pinecone()
    pinecone_filter = _build_pinecone_filter(user_profile)

    logger.debug("Pinecone filter: %s", pinecone_filter)
    logger.debug("Retrieving top-%d docs for query: %s", top_k, query[:80])

    # similarity_search_with_score returns (Document, score) tuples
    results_with_scores = store.similarity_search_with_score(
        query=query,
        k=top_k,
        filter=pinecone_filter,
    )

    if not results_with_scores:
        # Fallback: retrieve without filter if nothing matches
        logger.warning("No results with filter — falling back to unfiltered search")
        results_with_scores = store.similarity_search_with_score(query=query, k=10)

    # Score cutoff + backfill page_content from metadata.
    # When vectors are upserted via raw Pinecone SDK (ingest.py), text
    # lives in metadata["text"] rather than LangChain page_content.
    docs = []
    for doc, score in results_with_scores:
        if score <= 0.25:
            continue
        if not doc.page_content and doc.metadata.get("text"):
            doc.page_content = doc.metadata["text"]
        docs.append(doc)

    # Rerank by composite: similarity score × fund quality signal
    rerank_top_n = settings.rerank_top_n
    docs_reranked = _simple_rerank(docs, query)[:rerank_top_n]

    logger.info("Retrieved %d docs → reranked to %d", len(docs), len(docs_reranked))
    return docs_reranked


def _simple_rerank(docs: list[Document], query: str) -> list[Document]:
    """
    Local reranking without Cohere API.
    Scores each document by:
      - Keyword overlap with query
      - Fund quality signals (stars, AUM, Sharpe ratio) from metadata
    
    In production: replace with Cohere Rerank or cross-encoder model.
    """
    query_words = set(query.lower().split())

    def score(doc: Document) -> float:
        meta = doc.metadata
        text_lower = doc.page_content.lower()

        # Keyword overlap (0-1)
        text_words = set(text_lower.split())
        overlap = len(query_words & text_words) / max(len(query_words), 1)

        # Quality signals (normalize to 0-1 range)
        stars = float(meta.get("rating_stars", 3)) / 5.0
        sharpe = min(float(meta.get("sharpe_ratio", 0.5)) / 2.0, 1.0)
        aum_score = min(float(meta.get("aum_crores", 100)) / 10000.0, 1.0)

        return (0.5 * overlap) + (0.2 * stars) + (0.2 * sharpe) + (0.1 * aum_score)

    return sorted(docs, key=score, reverse=True)


def get_store() -> PineconeVectorStore:
    """Return initialized Pinecone store (for upsert operations)."""
    return init_pinecone()