"""
vector_store_service.py — FAISS-backed resume scoring with improved relevance logic.

Scoring improvements (v3)
--------------------------
v1 — max chunk score (easily gamed by one generic matching chunk)
v2 — cosine similarity via similarity_search_with_relevance_scores (correct metric)
v3 — weighted average of top-N chunks + relative gap filter (this version)

Why max-chunk scoring fails
---------------------------
A Java resume contains "object-oriented programming", "Git", "SQL" — all present
in the JD. These 3 chunks can score 0.65+ each. Max-chunk takes 0.65 and reports
the Java resume as a strong match, even though 95% of it is irrelevant.

The fix: weighted average of top-3 chunks per file
---------------------------------------------------
  score = (chunk1 * 0.50) + (chunk2 * 0.30) + (chunk3 * 0.20)

This requires the candidate to be consistently relevant across multiple passages,
not just lucky on one. A Java resume with one generic match and four low scores
will average out much lower than a .NET resume with uniformly high scores.

Relative gap filter
-------------------
After scoring, we drop any candidate whose score is less than
(top_score * gap_ratio). Default gap_ratio=0.80 means:
  - If the best match scores 0.72, only include candidates scoring ≥ 0.576
  - If all candidates score similarly (weak JD), nobody gets dropped
  - If there is a clear best match, the weaker ones get filtered out

This is the key fix for the .NET/.Java scenario:
  .NET resume → 0.74   ← kept (top scorer)
  Java resume → 0.41   ← dropped (below 0.74 * 0.80 = 0.59)
"""
import logging
import os
from typing import Optional

from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document

from services.pdf_parser import chunk_text

logger = logging.getLogger(__name__)

# Number of top chunks per file to include in the weighted average
_TOP_N_CHUNKS = 3

# Weights for the top-N chunks (must sum to 1.0)
_CHUNK_WEIGHTS = [0.50, 0.30, 0.20]

# A candidate is dropped if their score < top_score * GAP_RATIO
_GAP_RATIO = 0.80


def _get_embeddings():
    return OpenAIEmbeddings(
        model="text-embedding-3-small",
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )


class VectorStoreService:

    def __init__(self):
        self._index: Optional[FAISS] = None
        self._resume_texts: dict[str, str] = {}

    # ── Build ─────────────────────────────────────────────────────────────────

    def build(self, parsed_resumes: dict[str, str]) -> None:
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

        self._index = FAISS.from_documents(documents, _get_embeddings())
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
        Score resumes against the JD using weighted top-N chunk averaging.

        Steps
        -----
        1. Over-fetch chunks (top_k * 8, max 40) to ensure every file has
           enough chunks represented in the result set.
        2. Group chunks by source file.
        3. For each file, sort chunks descending and compute a weighted
           average of the top _TOP_N_CHUNKS scores.
        4. Apply absolute threshold filter.
        5. Apply relative gap filter — drop candidates far below the top scorer.
        6. Return top_k sorted descending.

        Parameters
        ----------
        query_text : str    — full JD text
        top_k      : int    — max results to return
        threshold  : float  — minimum absolute score (0-1). Default 0.50.
        gap_ratio  : float  — relative cutoff vs top scorer. Default 0.80.
                              Set to 0.0 to disable gap filtering.
        """
        if self._index is None:
            raise RuntimeError("Vector store not built. Call build() first.")

        # Over-fetch so every resume gets multiple chunks in the result
        fetch_k = min(top_k * 8, 40)

        raw = self._index.similarity_search_with_relevance_scores(query_text, k=fetch_k)

        # Log all raw chunk scores for debugging
        logger.debug("Raw chunk scores:")
        for doc, score in raw:
            logger.debug("  %.4f  %s", score, doc.metadata.get("source"))

        # ── Group chunks by file ──────────────────────────────────────────────
        chunks_per_file: dict[str, list[float]] = {}
        for doc, score in raw:
            filename = doc.metadata.get("source", "unknown")
            chunks_per_file.setdefault(filename, []).append(float(score))

        # ── Weighted average of top-N chunks per file ─────────────────────────
        scores: dict[str, float] = {}
        for filename, chunk_scores in chunks_per_file.items():
            sorted_scores = sorted(chunk_scores, reverse=True)
            top_n = sorted_scores[:_TOP_N_CHUNKS]

            # Pad with zeros if fewer than _TOP_N_CHUNKS chunks were retrieved
            while len(top_n) < _TOP_N_CHUNKS:
                top_n.append(0.0)

            weighted = sum(s * w for s, w in zip(top_n, _CHUNK_WEIGHTS))
            scores[filename] = weighted
            logger.debug(
                "  %s → top chunks %s → weighted avg %.4f",
                filename,
                [f"{s:.3f}" for s in top_n],
                weighted,
            )

        # ── Absolute threshold filter ─────────────────────────────────────────
        above_threshold = {fn: sc for fn, sc in scores.items() if sc >= threshold}

        if not above_threshold:
            logger.info(
                "No candidates above threshold %.2f. "
                "Scores were: %s",
                threshold,
                {fn: f"{sc:.3f}" for fn, sc in scores.items()},
            )
            return []

        # ── Relative gap filter ───────────────────────────────────────────────
        top_score = max(above_threshold.values())
        relative_cutoff = top_score * gap_ratio

        filtered = {
            fn: sc for fn, sc in above_threshold.items()
            if sc >= relative_cutoff
        }

        logger.info("Scoring summary:")
        logger.info("  Top score         : %.4f", top_score)
        logger.info("  Absolute threshold: %.2f", threshold)
        logger.info("  Relative cutoff   : %.4f (%.2f × top score)", relative_cutoff, gap_ratio)
        for fn, sc in sorted(scores.items(), key=lambda x: -x[1]):
            status = "✓ selected" if fn in filtered else "✗ filtered out"
            logger.info("  %.4f  %s  %s", sc, fn, status)

        # ── Sort and return top_k ─────────────────────────────────────────────
        results = sorted(filtered.items(), key=lambda x: -x[1])
        return [{"filename": fn, "score": round(sc, 4)} for fn, sc in results[:top_k]]

    # ── Cache ─────────────────────────────────────────────────────────────────

    def get_resume_text(self, filename: str) -> Optional[str]:
        return self._resume_texts.get(filename)