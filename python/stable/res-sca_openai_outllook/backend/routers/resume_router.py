"""
resume_router.py — two endpoints:
  POST /api/screen-resumes      → Phase 1: parse + embed + rank
  POST /api/generate-questions  → Phase 3: tiered Q&A + candidate info

Pydantic v2 fix
---------------
The original code imported DifficultyLevel from services.question_generator:
  from services.question_generator import QuestionGenerator, DifficultyLevel

When Pydantic v2 tries to build the TypeAdapter for QuestionRequest (which uses
DifficultyLevel in List[DifficultyLevel]), it looks up the type in the module
where QuestionRequest is defined — routers.resume_router. Since DifficultyLevel
was defined in a different module (services.question_generator), Pydantic v2
cannot always resolve it from the local namespace, leaving the model in a
"not fully defined" state and raising PydanticUserError at request time.

Fix: redefine DifficultyLevel as a plain Literal directly in this module,
then call QuestionRequest.model_rebuild() to force Pydantic to re-resolve
all type annotations using the now-complete local namespace.
"""
import asyncio
import logging
import traceback
from typing import List, Literal, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, field_validator

from services.pdf_parser import extract_text_from_pdf
from services.vector_store_service import VectorStoreService
from services.question_generator import QuestionGenerator
from services.candidate_extractor import extract_candidate_info

logger = logging.getLogger(__name__)
router = APIRouter()

_vs_service = VectorStoreService()
_qg_service = QuestionGenerator()

# ── DifficultyLevel defined HERE, not imported from another module ────────────
# Pydantic v2 resolves Literal types using the namespace of the module where
# the model class is defined. Importing a Literal alias from another module
# causes "class not fully defined" because Pydantic searches for the name in
# THIS module's __dict__ and cannot find it there.
DifficultyLevel = Literal["basic", "intermediate", "advanced"]

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

# model_rebuild() forces Pydantic v2 to re-evaluate all annotations using the
# current module globals — at this point DifficultyLevel IS in the local
# namespace so the rebuild succeeds and the TypeAdapter is fully defined.
QuestionRequest.model_rebuild()

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
    candidate: CandidateInfoSchema
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

    candidate_info, level_results = await asyncio.gather(
        extract_candidate_info(resume_text),
        _qg_service.generate(
            resume_text=resume_text,
            job_description=payload.job_description,
            levels=list(payload.levels),
        ),
    )

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

    return QuestionResponse(
        filename=payload.filename,
        candidate=CandidateInfoSchema(**candidate_info.to_dict()),
        results=ordered_results,
        total_questions=sum(len(r.items) for r in ordered_results),
    )

# ── Endpoint 3: Extract Candidate Info only ───────────────────────────────────

class CandidateInfoRequest(BaseModel):
    filename: str

@router.post("/extract-candidate", response_model=CandidateInfoSchema)
async def extract_candidate(payload: CandidateInfoRequest):
    """
    Lightweight endpoint — extracts name/email/phone from a cached resume
    without generating questions. Used when recruiter wants to schedule
    directly from Phase 2 without going through Phase 3.
    """
    resume_text = _vs_service.get_resume_text(payload.filename)
    if resume_text is None:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Resume '{payload.filename}' not found in session cache. "
                "Please re-run /screen-resumes first."
            ),
        )
    info = await extract_candidate_info(resume_text)
    return CandidateInfoSchema(**info.to_dict())