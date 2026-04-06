"""
vector_store_service.py — FAISS resume scoring with HuggingFace embeddings.

Embedding model: BAAI/bge-base-en-v1.5
  - Free, open-source, Apache 2.0 licence
  - Ranks #1 on MTEB retrieval benchmark
  - Runs fully locally — resumes never leave your machine
  - 430MB download on first use (cached after that)

Installation
------------
  pip install sentence-transformers

No API key required. No internet after first model download.

BGE-specific note
-----------------
BGE models are trained with a query prefix instruction that improves
retrieval quality. For the query (JD), prepend:
  "Represent this sentence for searching relevant passages: "
For documents (resume chunks), no prefix is needed.
This is specific to BGE and improves accuracy by ~3-5% on retrieval tasks.
"""
import logging
import os
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document

from services.pdf_parser import chunk_text

logger = logging.getLogger(__name__)


# ── Embedding model factory ───────────────────────────────────────────────────

def _get_embeddings():
    """
    Load BAAI/bge-base-en-v1.5 via LangChain's HuggingFaceEmbeddings wrapper.

    HuggingFaceEmbeddings uses sentence-transformers under the hood and
    runs the model locally on CPU (or GPU if available).

    Model is downloaded to ~/.cache/huggingface/hub/ on first use (~430MB).
    Subsequent calls load from cache — no internet required.

    encode_kwargs: normalize_embeddings=True
      BGE embeddings should be L2-normalised before computing cosine similarity.
      This is mentioned in the BGE model card and improves retrieval accuracy.
    """
    from langchain_community.embeddings import HuggingFaceEmbeddings

    return HuggingFaceEmbeddings(
        model_name="BAAI/bge-base-en-v1.5",
        model_kwargs={"device": "cpu"},       # swap to "cuda" if you have a GPU
        encode_kwargs={"normalize_embeddings": True},
    )


# ── BGE query prefix ──────────────────────────────────────────────────────────

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

def _prepare_query(text: str) -> str:
    """
    Prepend the BGE retrieval instruction to the query text.

    This prefix is part of how BGE was trained — it signals to the model
    that this text is a search query rather than a document to be indexed.
    Omitting it works, but including it gives measurably better retrieval.
    Only the QUERY gets this prefix. Resume chunks do NOT get it.
    """
    return BGE_QUERY_PREFIX + text


# ── Vector store service ──────────────────────────────────────────────────────

_TOP_N_CHUNKS = 3
_CHUNK_WEIGHTS = [0.50, 0.30, 0.20]
_GAP_RATIO = 0.80


class VectorStoreService:

    def __init__(self):
        self._index: Optional[FAISS] = None
        self._resume_texts: dict[str, str] = {}
        # Cache the embedding model — loading a 430MB model on every request
        # would be extremely slow. Load once, reuse across all requests.
        self._embeddings = None

    def _get_or_load_embeddings(self):
        """Lazy-load embeddings on first use."""
        if self._embeddings is None:
            logger.info("Loading BAAI/bge-base-en-v1.5 (first load ~430MB, cached after)...")
            self._embeddings = _get_embeddings()
            logger.info("Embedding model loaded and cached.")
        return self._embeddings

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self, parsed_resumes: dict[str, str]) -> None:
        """
        Chunk resumes and build FAISS index.
        Resume chunks are embedded WITHOUT the BGE query prefix.
        """
        self._resume_texts = parsed_resumes.copy()
        documents: list[Document] = []

        for filename, text in parsed_resumes.items():
            chunks = chunk_text(text, chunk_size=400, chunk_overlap=80)
            for chunk in chunks:
                documents.append(Document(
                    page_content=chunk,
                    metadata={"source": filename},
                ))
            logger.debug("%s → %d chunks", filename, len(chunks))

        embeddings = self._get_or_load_embeddings()
        self._index = FAISS.from_documents(documents, embeddings)
        logger.info("FAISS index: %d resumes → %d chunks", len(parsed_resumes), len(documents))

    # ── Query ─────────────────────────────────────────────────────────────────

    def query(
        self,
        query_text: str,
        top_k: int = 3,
        threshold: float = 0.50,
        gap_ratio: float = _GAP_RATIO,
    ) -> list[dict]:
        """
        Score resumes against the JD.
        The JD query gets the BGE prefix for better retrieval accuracy.
        """
        if self._index is None:
            raise RuntimeError("Vector store not built. Call build() first.")

        # Prepend BGE instruction to the query (JD) only
        prepared_query = _prepare_query(query_text)

        fetch_k = min(top_k * 8, 40)
        raw = self._index.similarity_search_with_relevance_scores(prepared_query, k=fetch_k)

        logger.debug("Raw chunk scores:")
        for doc, score in raw:
            logger.debug("  %.4f  %s", score, doc.metadata.get("source"))

        # Group chunks by file
        chunks_per_file: dict[str, list[float]] = {}
        for doc, score in raw:
            filename = doc.metadata.get("source", "unknown")
            chunks_per_file.setdefault(filename, []).append(float(score))

        # Weighted average of top-N chunks
        scores: dict[str, float] = {}
        for filename, chunk_scores in chunks_per_file.items():
            sorted_scores = sorted(chunk_scores, reverse=True)
            top_n = sorted_scores[:_TOP_N_CHUNKS]
            while len(top_n) < _TOP_N_CHUNKS:
                top_n.append(0.0)
            weighted = sum(s * w for s, w in zip(top_n, _CHUNK_WEIGHTS))
            scores[filename] = weighted
            logger.debug(
                "  %s → top chunks %s → weighted %.4f",
                filename, [f"{s:.3f}" for s in top_n], weighted,
            )

        # Absolute threshold
        above_threshold = {fn: sc for fn, sc in scores.items() if sc >= threshold}
        if not above_threshold:
            logger.info("No candidates above threshold %.2f. Scores: %s", threshold,
                        {fn: f"{sc:.3f}" for fn, sc in scores.items()})
            return []

        # Relative gap filter
        top_score = max(above_threshold.values())
        relative_cutoff = top_score * gap_ratio
        filtered = {fn: sc for fn, sc in above_threshold.items() if sc >= relative_cutoff}

        logger.info("Scoring summary (BGE embeddings):")
        logger.info("  Top score: %.4f | Threshold: %.2f | Gap cutoff: %.4f",
                    top_score, threshold, relative_cutoff)
        for fn, sc in sorted(scores.items(), key=lambda x: -x[1]):
            logger.info("  %.4f  %s  %s", sc, fn,
                        "✓ selected" if fn in filtered else "✗ filtered")

        results = sorted(filtered.items(), key=lambda x: -x[1])
        return [{"filename": fn, "score": round(sc, 4)} for fn, sc in results[:top_k]]

    def get_resume_text(self, filename: str) -> Optional[str]:
        return self._resume_texts.get(filename)