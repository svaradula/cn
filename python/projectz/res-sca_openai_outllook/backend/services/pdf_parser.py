"""
pdf_parser.py — Extract plain text from PDF (and DOCX) bytes.

Primary parser : pdfplumber  (accurate layout-aware extraction)
Fallback parser: PyMuPDF (fitz) — faster but sometimes loses formatting
"""
import io
import logging
from typing import Optional

logger = logging.getLogger(__name__)


# ── Parser implementations ────────────────────────────────────────────────────

def _parse_pdf_pdfplumber(raw_bytes: bytes) -> str:
    """pdfplumber — primary engine, layout-aware."""
    import pdfplumber

    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(raw_bytes)) as pdf:
        logger.debug("pdfplumber: opened PDF with %d pages", len(pdf.pages))
        for i, page in enumerate(pdf.pages):
            page_text = page.extract_text(x_tolerance=2, y_tolerance=2)
            if page_text:
                text_parts.append(page_text)
            else:
                logger.debug("pdfplumber: page %d returned no text", i + 1)
    return "\n\n".join(text_parts)


def _parse_pdf_pymupdf(raw_bytes: bytes) -> str:
    """
    PyMuPDF (fitz) — fallback engine.

    Windows / PyMuPDF bug fix
    -------------------------
    fitz.open(stream=bytes, filetype="pdf") can misinterpret plain `bytes`
    as a file-path string on some Windows + PyMuPDF version combinations,
    producing errors like "Directory 'static/' does not exist".

    Root cause: PyMuPDF's C extension checks whether the stream argument
    is a mutable buffer type. Plain `bytes` is immutable and on certain
    builds the type check falls through to the filename code path.

    Two fixes applied in sequence:
      1. Cast to `bytearray` — mutable buffer, always routed correctly
         as an in-memory stream by PyMuPDF's type dispatch.
      2. Wrap in `io.BytesIO` — a file-like object, unambiguously treated
         as a stream regardless of platform or PyMuPDF version.
    """
    import fitz  # PyMuPDF

    # Fix 1: bytearray — mutable buffer avoids path misinterpretation
    try:
        doc = fitz.open(stream=bytearray(raw_bytes), filetype="pdf")
        logger.debug("PyMuPDF (bytearray): opened PDF with %d pages", len(doc))
        pages = [page.get_text("text") for page in doc]
        doc.close()
        return "\n\n".join(pages)
    except Exception as exc:
        logger.warning("PyMuPDF bytearray failed (%s), trying BytesIO...", exc)

    # Fix 2: BytesIO — file-like object, never misread as a path
    doc = fitz.open(stream=io.BytesIO(raw_bytes), filetype="pdf")
    logger.debug("PyMuPDF (BytesIO): opened PDF with %d pages", len(doc))
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return "\n\n".join(pages)


def _parse_docx(raw_bytes: bytes) -> str:
    """python-docx — for .docx files."""
    from docx import Document

    doc = Document(io.BytesIO(raw_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)


# ── Public API ────────────────────────────────────────────────────────────────

def extract_text_from_pdf(raw_bytes: bytes, filename: Optional[str] = None) -> str:
    """
    Extract plain text from a PDF or DOCX file.
    Tries pdfplumber first, falls back to PyMuPDF for PDFs.
    Raises ValueError if both engines fail.
    """
    ext = (filename or "").lower().rsplit(".", 1)[-1]

    # ── DOCX ─────────────────────────────────────────────────────────────────
    if ext in ("docx", "doc"):
        logger.debug("Dispatching to DOCX parser: %s", filename)
        try:
            return _parse_docx(raw_bytes)
        except Exception as exc:
            raise ValueError(f"DOCX parsing failed for '{filename}': {exc}") from exc

    # ── PDF (primary: pdfplumber) ─────────────────────────────────────────────
    logger.debug("Dispatching to PDF parser (pdfplumber): %s", filename)
    try:
        text = _parse_pdf_pdfplumber(raw_bytes)
        if text.strip():
            logger.debug("pdfplumber succeeded for %s", filename)
            return text
        logger.warning(
            "%s: pdfplumber returned empty text — "
            "file may be image-only or encrypted. Trying PyMuPDF...",
            filename,
        )
    except Exception as exc:
        logger.warning(
            "%s: pdfplumber raised %s: %s — trying PyMuPDF...",
            filename, type(exc).__name__, exc,
        )

    # ── PDF (fallback: PyMuPDF) ───────────────────────────────────────────────
    logger.debug("Dispatching to PDF parser (PyMuPDF): %s", filename)
    try:
        text = _parse_pdf_pymupdf(raw_bytes)
        if text.strip():
            logger.debug("PyMuPDF succeeded for %s", filename)
            return text
        raise ValueError(
            f"Both parsers returned empty text for '{filename}'. "
            "The file may be a scanned/image-only PDF with no embedded text. "
            "Try running OCR on it first (e.g. Adobe Acrobat, or tesseract)."
        )
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError(
            f"Both PDF parsers failed for '{filename}'. "
            f"PyMuPDF error: {type(exc).__name__}: {exc}"
        ) from exc


# ── Text chunking ─────────────────────────────────────────────────────────────

def chunk_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 100,
) -> list[str]:
    """
    Split text into overlapping chunks for embedding.
    Uses LangChain's RecursiveCharacterTextSplitter.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""],
    )
    chunks = splitter.split_text(text)
    logger.debug("chunk_text: %d chars → %d chunks", len(text), len(chunks))
    return chunks