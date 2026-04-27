"""
embedder.py — OpenAI embedding wrapper with batching, retry, and caching.
Model: text-embedding-3-small  ($0.02 / 1M tokens — cheapest quality option)
Dimensions: 1536
"""
from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING

from langchain_openai import OpenAIEmbeddings
from tenacity import retry, stop_after_attempt, wait_exponential

from config import get_settings

if TYPE_CHECKING:
    from ingestion.amfi_loader import FundRecord

logger = logging.getLogger(__name__)
settings = get_settings()


def get_embedder() -> OpenAIEmbeddings:
    """
    Returns a configured LangChain OpenAI embedder.
    Uses text-embedding-3-small — cheapest model that still gives
    strong semantic search quality for financial text.
    """
    return OpenAIEmbeddings(
        model=settings.openai_embed_model,          # text-embedding-3-small
        dimensions=settings.openai_embed_dims,      # 1536
        openai_api_key=settings.openai_api_key,
        # Chunk large batches automatically
        chunk_size=500,                              # OpenAI max is 2048 per batch
    )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
async def embed_texts_batch(texts: list[str], embedder: OpenAIEmbeddings) -> list[list[float]]:
    """
    Embed a list of texts with retry logic.
    Runs in a thread pool so FastAPI's async loop isn't blocked.
    """
    loop = asyncio.get_event_loop()
    embeddings = await loop.run_in_executor(
        None,
        embedder.embed_documents,
        texts,
    )
    return embeddings


async def embed_query(query: str, embedder: OpenAIEmbeddings) -> list[float]:
    """Embed a single query string."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, embedder.embed_query, query)