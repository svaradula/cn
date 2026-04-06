"""
resume_router.py — two endpoints:
  POST /api/screen-resumes      → Phase 1: parse + embed + rank
  POST /api/generate-questions  → Phase 3: tiered Q&A + candidate info
"""
import logging
import traceback
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, field_validator

from services.pdf_parser import extract_text_from_pdf
from services.vector_store_service import VectorStoreService
from services.question_generator import QuestionGenerator, DifficultyLevel
from services.candidate_extractor import extract_candidate_info


logger = logging.getLogger(__name__)
router = APIRouter()

_vs_service = VectorStoreService()
_qg_service = QuestionGenerator()

# ── Pydantic schemas ──────────────────────────────────────────────────────────

class ShortlistedResume(BaseModel):
    filename: str
    score: float

class ScreenResponse(BaseModel):
    shortlisted: List[ShortlistedResume]
    total_uploaded: int
    threshold_used: float

class QuestionRequest(BaseModel):
    filename: str
    job_description: str
    levels: List[DifficultyLevel] = ["basic"]

    @field_validator("levels", mode="before")
    @classmethod
    def default_to_basic(cls, v):
        return v if v else ["basic"]

class QAPairSchema(BaseModel):
    question: str
    answer: str

class LevelQuestions(BaseModel):
    level: str
    items: List[QAPairSchema]

class CandidateInfoSchema(BaseModel):
    name:  str
    email: str
    phone: str

class QuestionResponse(BaseModel):
    filename: str
    candidate: CandidateInfoSchema          # ← new: extracted contact details
    results: List[LevelQuestions]
    total_questions: int

# ── Endpoint 1: Screen Resumes ────────────────────────────────────────────────

@router.post("/screen-resumes", response_model=ScreenResponse)
async def screen_resumes(
    job_description: str = Form(...),
    resumes: List[UploadFile] = File(...),
    top_k: int = Form(3),
    threshold: float = Form(0.30),
):
    if not resumes:
        raise HTTPException(status_code=400, detail="At least one resume file is required.")

    parsed: dict[str, str] = {}
    parse_errors: dict[str, str] = {}

    for upload in resumes:
        raw_bytes = await upload.read()
        filename = upload.filename or "unknown"
        logger.debug("Received: %s | %s | %d bytes", filename, upload.content_type, len(raw_bytes))

        if len(raw_bytes) == 0:
            parse_errors[filename] = "File is empty (0 bytes)"
            continue

        try:
            text = extract_text_from_pdf(raw_bytes, filename=filename)
        except Exception as exc:
            logger.error("Parse failed for %s:\n%s", filename, traceback.format_exc())
            parse_errors[filename] = str(exc)
            continue

        if not text.strip():
            parse_errors[filename] = "Parser returned empty text (possibly a scanned PDF)"
            continue

        parsed[filename] = text
        logger.info("%s: parsed OK (%d chars)", filename, len(text))

    if not parsed:
        error_lines = "\n".join(f"  • {f}: {r}" for f, r in parse_errors.items())
        raise HTTPException(
            status_code=422,
            detail="None of the uploaded files could be parsed.\n\n" + error_lines,
        )

    _vs_service.build(parsed)
    results = _vs_service.query(query_text=job_description, top_k=top_k, threshold=threshold)

    return ScreenResponse(
        shortlisted=[
            ShortlistedResume(filename=r["filename"], score=round(r["score"], 4))
            for r in results
        ],
        total_uploaded=len(parsed),
        threshold_used=threshold,
    )


# ── Endpoint 2: Generate Tiered Q&A + Candidate Info ─────────────────────────

@router.post("/generate-questions", response_model=QuestionResponse)
async def generate_questions(payload: QuestionRequest):
    resume_text = _vs_service.get_resume_text(payload.filename)
    if resume_text is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Resume '{payload.filename}' not found in session cache. "
                "Please re-run /screen-resumes first."
            ),
        )

    logger.info("Generating Q&A for '%s' | levels=%s", payload.filename, payload.levels)

    # ── Run candidate extraction + question generation concurrently ───────────
    import asyncio

    candidate_task = extract_candidate_info(resume_text)
    questions_task = _qg_service.generate(
        resume_text=resume_text,
        job_description=payload.job_description,
        levels=payload.levels,
    )

    # Both run in parallel — no waiting for extraction before questions start
    candidate_info, level_results = await asyncio.gather(candidate_task, questions_task)

    logger.info(
        "Candidate: name=%s | email=%s | phone=%s",
        candidate_info.name, candidate_info.email, candidate_info.phone,
    )

    ordered_results = [
        LevelQuestions(
            level=lv,
            items=[
                QAPairSchema(question=qa["question"], answer=qa["answer"])
                for qa in level_results[lv]
            ],
        )
        for lv in payload.levels
        if lv in level_results
    ]

    total = sum(len(r.items) for r in ordered_results)

    return QuestionResponse(
        filename=payload.filename,
        candidate=CandidateInfoSchema(**candidate_info.to_dict()),
        results=ordered_results,
        total_questions=total,
    )