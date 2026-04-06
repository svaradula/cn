"""
pdf_parser.py — Extract plain text from PDF (and DOCX) bytes.

Primary parser : pdfplumber  (accurate layout-aware extraction)
Fallback parser: PyMuPDF (fitz) — faster but sometimes loses formatting

For DOCX support install `python-docx`.
"""
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _parse_pdf_pdfplumber(raw_bytes: bytes) -> str:
    import pdfplumber
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def _parse_pdf_pymupdf(raw_bytes: bytes) -> str:
    import fitz  # PyMuPDF
    doc = fitz.open(stream=raw_bytes, filetype="pdf")
    pages = [page.get_text("text") for page in doc]
    return "\n\n".join(pages)


def _parse_docx(raw_bytes: bytes) -> str:
    from docx import Document
    doc = Document(io.BytesIO(raw_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


# ── Public API ────────────────────────────────────────────────────────────────

def extract_text_from_pdf(raw_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Dispatch on file extension (or try PDF first then DOCX).
    """
    ext = (filename or "").lower().rsplit(".", 1)[-1]

    if ext in ("docx", "doc"):
        logger.debug("Parsing DOCX: %s", filename)
        return _parse_docx(raw_bytes)

    logger.debug("Parsing PDF: %s", filename)
    try:
        text = _parse_pdf_pdfplumber(raw_bytes)
        if text.strip():
            return text
        logger.warning("%s: pdfplumber returned empty text, trying PyMuPDF", filename)
    except Exception as exc:
        logger.warning("%s: pdfplumber failed (%s), trying PyMuPDF", filename, exc)

    try:
        text = _parse_pdf_pymupdf(raw_bytes)
        return text
    except Exception as exc:
        raise ValueError(f"Both PDF parsers failed for '{filename}': {exc}") from exc


# ── Text chunking (used by vector_store_service) ──────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[str]:
    """
    Split text into overlapping chunks for embedding.

    Uses LangChain's RecursiveCharacterTextSplitter — tries to split on
    paragraphs first, then sentences, then words, keeping chunks semantically
    coherent.
    """
    # ── Fixed import (LangChain v0.2+ package split) ──────────────────────────
    # langchain_text_splitters  replaces  langchain.text_splitter
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    return splitter.split_text(text)