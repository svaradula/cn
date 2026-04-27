"""
candidate_extractor.py — Extract candidate contact details from resume text.

Extraction strategy: two-pass
  Pass 1 — Regex         : instant, free, handles 90% of resumes.
  Pass 2 — LLM with Pydantic structured output:
           Uses LangChain's .with_structured_output() which binds a Pydantic
           model directly to the LLM call. The LLM is forced to return JSON
           conforming to the schema — no manual json.loads(), no guessing key
           names, no fragile string parsing.

Why .with_structured_output() instead of raw json.loads()
----------------------------------------------------------
The old approach (ainvoke → raw string → json.loads) fails when:
  - The model adds a preamble ("Here is the JSON: ...")
  - It wraps output in markdown fences (```json ... ```)
  - It changes key names ("phone_number" instead of "phone")
  - It returns a partial or malformed JSON object

.with_structured_output() solves all of these by:
  1. Injecting the Pydantic schema into the LLM's function-calling API
     (OpenAI function calling / tool use under the hood)
  2. Receiving a structured response object, not a string
  3. Returning a validated Pydantic model instance directly
  4. Raising a validation error immediately if the schema is violated,
     rather than silently returning bad data
"""
import logging
import os
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


# ── Pydantic schema — used for BOTH validation and LLM structured output ──────

class CandidateInfo(BaseModel):
    """
    Contact details extracted from a resume.

    This model serves double duty:
      1. As the structured output schema passed to the LLM via
         ChatOpenAI.with_structured_output(CandidateInfo) — the LLM is
         constrained to return exactly these fields with these types.
      2. As the validated data container returned to the caller — all
         field validators run automatically on the LLM's response.
    """
    name: Optional[str] = Field(
        default=None,
        description="Candidate's full name as written on the resume. "
                    "Return null if not clearly identifiable.",
    )
    email: Optional[str] = Field(
        default=None,
        description="Candidate's email address. Return null if not present.",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Candidate's phone number including country code if present. "
                    "Return null if not present.",
    )

    # ── Field validators ──────────────────────────────────────────────────────

    @field_validator("email", mode="before")
    @classmethod
    def normalise_email(cls, v):
        """Lowercase and strip whitespace from email."""
        if v and isinstance(v, str):
            v = v.strip().lower()
            # Reject obviously invalid values the LLM might hallucinate
            if "@" not in v or len(v) < 5:
                return None
        return v or None

    @field_validator("phone", mode="before")
    @classmethod
    def normalise_phone(cls, v):
        """Strip extraneous characters, keep digits + + ( ) - spaces."""
        if v and isinstance(v, str):
            v = re.sub(r"[^\d\s\+\(\)\-]", "", v).strip()
            # Reject too-short strings (e.g. just "N/A" or a year)
            digits = re.sub(r"\D", "", v)
            if len(digits) < 7:
                return None
        return v or None

    @field_validator("name", mode="before")
    @classmethod
    def normalise_name(cls, v):
        """Strip leading/trailing whitespace; reject single-word or all-caps strings."""
        if v and isinstance(v, str):
            v = v.strip()
            # Reject section headers that sometimes get mistaken for names
            if len(v.split()) < 2 or v.upper() == v:
                return None
        return v or None

    # ── Helpers ───────────────────────────────────────────────────────────────

    def is_complete(self) -> bool:
        return all([self.name, self.email, self.phone])

    def to_dict(self) -> dict:
        return {
            "name":  self.name  or "Not found",
            "email": self.email or "Not found",
            "phone": self.phone or "Not found",
        }


# ── Pass 1: Regex ─────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}", re.IGNORECASE)

_PHONE_RE = re.compile(
    r"(?:\+?[\d]{1,3}[\s\-.]?)?(?:\(?\d{3,5}\)?[\s\-.]?)[\d]{3,4}[\s\-.]?\d{4}"
)

_NAME_LINE_RE = re.compile(
    r"^([A-Z][a-zA-Z\-'\.]{1,20})(\s+[A-Z][a-zA-Z\-'\.]{1,20}){1,4}$"
)


def _extract_via_regex(text: str) -> CandidateInfo:
    """Fast regex pass — returns a CandidateInfo with whatever could be found."""
    email = phone = name = None

    match = _EMAIL_RE.search(text)
    if match:
        email = match.group(0)

    match = _PHONE_RE.search(text)
    if match:
        phone = match.group(0).strip()

    lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
    for line in lines[:20]:
        if any(kw in line.lower() for kw in
               ["@", "http", "linkedin", "github", "objective", "summary",
                "experience", "education", "skills", "profile", "resume", "cv"]):
            continue
        if _NAME_LINE_RE.match(line):
            name = line.strip()
            break

    # Pydantic validators run here automatically during construction
    return CandidateInfo(name=name, email=email, phone=phone)


# ── Pass 2: LLM with structured output ───────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a resume parser specialist. "
    "Extract the candidate's contact information from the resume text provided. "
    "Be precise — only extract information that is explicitly present. "
    "Do not infer or guess any values."
)


async def _extract_via_llm(text: str) -> CandidateInfo:
    """
    LLM extraction using LangChain's .with_structured_output().

    How it works
    ------------
    ChatOpenAI.with_structured_output(CandidateInfo) does three things:
      1. Converts the Pydantic model's JSON schema into an OpenAI tool definition
         and passes it via the function_call API.
      2. Instructs the model to call that tool with a valid JSON payload.
      3. Parses the model's structured response and returns a validated
         CandidateInfo instance — no string parsing needed.

    If the model returns a field that fails a validator (e.g. a phone number
    with fewer than 7 digits), Pydantic raises a ValidationError immediately
    so bad data never propagates silently.
    """
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate

    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        openai_api_key=os.environ["OPENAI_API_KEY"],
    )

    # Bind the Pydantic model as the required structured output schema.
    # Under the hood this uses OpenAI's function/tool calling API —
    # the model MUST respond with JSON conforming to CandidateInfo's schema.
    structured_llm = llm.with_structured_output(CandidateInfo)

    prompt = ChatPromptTemplate.from_messages([
        ("system", _SYSTEM_PROMPT),
        ("human",  "Extract contact details from this resume (first 3000 chars):\n\n{text}"),
    ])

    chain = prompt | structured_llm   # returns CandidateInfo directly, not a string

    # ainvoke returns a validated CandidateInfo instance
    result: CandidateInfo = await chain.ainvoke({"text": text[:3000]})
    logger.debug(
        "LLM structured output: name=%s | email=%s | phone=%s",
        result.name, result.email, result.phone,
    )
    return result


# ── Public API ────────────────────────────────────────────────────────────────

async def extract_candidate_info(resume_text: str) -> CandidateInfo:
    """
    Extract name, email, phone from resume text.

    Flow
    ----
    1. Regex pass — fast and free.
    2. If anything is missing, LLM structured output fills the gaps.
    3. Results are merged — regex wins where it found something,
       LLM fills only the missing fields.

    Returns
    -------
    CandidateInfo  — validated Pydantic model (fields are None if not found)
    """
    logger.debug("Pass 1: regex extraction...")
    info = _extract_via_regex(resume_text)
    logger.debug(
        "Regex result: name=%s | email=%s | phone=%s",
        info.name, info.email, info.phone,
    )

    if info.is_complete():
        logger.info("All fields found via regex — skipping LLM")
        return info

    logger.info(
        "Regex incomplete (name=%s, email=%s, phone=%s) — Pass 2: LLM structured output",
        bool(info.name), bool(info.email), bool(info.phone),
    )

    try:
        llm_info = await _extract_via_llm(resume_text)
        # Merge: prefer regex result, fill gaps with LLM
        merged = CandidateInfo(
            name=info.name   or llm_info.name,
            email=info.email or llm_info.email,
            phone=info.phone or llm_info.phone,
        )
        logger.info("Final merged result: %s", merged.to_dict())
        return merged
    except Exception as exc:
        logger.warning("LLM extraction failed (%s) — returning partial regex result", exc)
        return info