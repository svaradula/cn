"""
question_generator.py — Tiered interview question generation with 65/35 JD/Resume
weighting, plus a simple recruiter-facing answer for every question.

Output format per question
--------------------------
Each LLM response is parsed into a list of:
  {
    "question": "Full question text with [JD-Focused] / [Resume-Focused] tag",
    "answer":   "Plain-English answer in ≤200 words, written for a non-technical recruiter"
  }

Prompt strategy
---------------
The LLM is instructed to output each Q&A block in a strict delimited format:

  Q1. [JD-Focused] <question text>
  A1. <answer text — max 200 words, plain English>

  Q2. [Resume-Focused] <question text>
  A2. <answer text>
  ...

Using numbered Q/A prefixes (Q1./A1.) instead of freeform labels makes
regex parsing unambiguous even when answer text spans multiple sentences.
"""
import asyncio
import logging
import os
import re
from typing import Literal

from langchain_core.prompts import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

DifficultyLevel = Literal["basic", "intermediate", "advanced"]

# ── 65/35 weighting + answer instructions (shared across all levels) ──────────

WEIGHTING_AND_ANSWER_BLOCK = """
STRICT SOURCE WEIGHTING — follow this for every set of 5 questions:
  • 65% JD-Focused  (3 questions): derived from core responsibilities, required
    tech stack, and must-have skills in the Job Description.
  • 35% Resume-Focused (2 questions): derived from the candidate's specific
    projects, tools used, and claims in their resume.

Tag every question:
  [JD-Focused]     — for the 3 JD-derived questions
  [Resume-Focused] — for the 2 Resume-derived questions

ANSWER INSTRUCTIONS:
After every question write a concise answer that a NON-TECHNICAL recruiter
can understand and use during the interview to evaluate the candidate's response.
Rules for answers:
  - Maximum 200 words per answer.
  - Use plain, simple English — avoid jargon where possible.
  - If a technical term is unavoidable, briefly explain it in parentheses.
  - Structure: (1) what a GOOD answer looks like, (2) one or two key points
    the recruiter should listen for, (3) a red flag to watch out for.
  - Do NOT write "The candidate should say..." — write it directly and naturally.

OUTPUT FORMAT — follow this exactly, no deviations:

Q1. [JD-Focused] <question text>
A1. <answer — max 200 words>

Q2. [JD-Focused] <question text>
A2. <answer — max 200 words>

Q3. [JD-Focused] <question text>
A3. <answer — max 200 words>

Q4. [Resume-Focused] <question text>
A4. <answer — max 200 words>

Q5. [Resume-Focused] <question text>
A5. <answer — max 200 words>

No preamble, no section headers, no extra commentary — only the Q/A blocks above.
"""

# ── Per-level system prompts ──────────────────────────────────────────────────

SYSTEM_PROMPTS: dict[DifficultyLevel, str] = {

    "basic": f"""You are a senior technical interviewer generating BASIC-level screening questions.

BASIC questions test:
  - Definitions and terminology ("What is X?", "What does Y stand for?")
  - Syntax and basic usage of the required technologies
  - Conceptual understanding — no implementation depth required
  - Entry-level recognition of tools and practices

Do NOT ask about architecture, trade-offs, optimisation, or design patterns.
A junior developer (0-2 years experience) should be able to answer these.

{WEIGHTING_AND_ANSWER_BLOCK}
""",

    "intermediate": f"""You are a senior technical interviewer generating INTERMEDIATE-level questions.

INTERMEDIATE questions test:
  - Scenario-based problem solving ("Given X situation, how would you...?")
  - Trade-off awareness ("When would you choose X over Y?")
  - Real-world debugging and troubleshooting
  - Integration of multiple technologies
  - Project-level decision making

Do NOT ask basic definitions. Do NOT ask about enterprise-scale architecture.
Target candidates with 2-5 years of relevant experience.

{WEIGHTING_AND_ANSWER_BLOCK}
""",

    "advanced": f"""You are a principal engineer generating ADVANCED-level interview questions.

ADVANCED questions test:
  - System architecture and distributed systems design
  - Performance optimisation and scalability at production scale
  - Security, compliance, and reliability engineering
  - Technology selection with measurable business impact
  - Deep internals knowledge and engineering leadership

Do NOT ask basic or intermediate questions.
Target candidates with 5+ years of senior/lead experience.

{WEIGHTING_AND_ANSWER_BLOCK}
""",
}

HUMAN_PROMPT = """
## Job Description
{job_description}

## Candidate Resume
{resume_text}

Generate exactly 5 {level} interview questions with recruiter-friendly answers.
Follow the Q1./A1. format strictly.
"""

# ── Data structure ────────────────────────────────────────────────────────────

class QAPair:
    """One question + its recruiter-facing answer."""
    def __init__(self, question: str, answer: str):
        self.question = question
        self.answer = answer

    def to_dict(self) -> dict:
        return {"question": self.question, "answer": self.answer}


# ── Generator ─────────────────────────────────────────────────────────────────

class QuestionGenerator:
    """
    Runs one LCEL chain per difficulty level concurrently.

    Returns
    -------
    dict[level] → list of {"question": str, "answer": str}
    """

    def __init__(self, model: str = "gpt-4o", temperature: float = 0.7):
        api_key = os.environ["OPENAI_API_KEY"]
        self._chains: dict[DifficultyLevel, object] = {}

        for level, system_prompt in SYSTEM_PROMPTS.items():
            llm = ChatOpenAI(
                model=model,
                temperature=temperature,
                openai_api_key=api_key,
                max_tokens=2048,          # increased — answers need more tokens
            )
            prompt = ChatPromptTemplate.from_messages([
                SystemMessagePromptTemplate.from_template(system_prompt),
                HumanMessagePromptTemplate.from_template(HUMAN_PROMPT),
            ])
            self._chains[level] = prompt | llm | StrOutputParser()

    async def generate(
        self,
        resume_text: str,
        job_description: str,
        levels: list[DifficultyLevel],
    ) -> dict[str, list[dict]]:
        """
        Run all requested levels concurrently via asyncio.gather.

        Returns
        -------
        {
          "basic":        [{"question": "...", "answer": "..."}, ...],
          "intermediate": [...],
          "advanced":     [...],
        }
        """
        seen: set[str] = set()
        valid_levels: list[DifficultyLevel] = []
        for lv in levels:
            lv = lv.lower()
            if lv in SYSTEM_PROMPTS and lv not in seen:
                valid_levels.append(lv)
                seen.add(lv)

        if not valid_levels:
            logger.warning("No valid levels — defaulting to basic")
            valid_levels = ["basic"]

        logger.info("Generating Q&A for levels: %s", valid_levels)

        inputs = {"job_description": job_description, "resume_text": resume_text}

        async def _invoke(level: DifficultyLevel) -> tuple[str, list[dict]]:
            raw: str = await self._chains[level].ainvoke({**inputs, "level": level})
            logger.debug("Raw LLM output for '%s':\n%s", level, raw)
            pairs = _parse_qa_pairs(raw)
            logger.info("Level '%s': parsed %d Q&A pairs", level, len(pairs))
            return level, [p.to_dict() for p in pairs]

        results = await asyncio.gather(*[_invoke(lv) for lv in valid_levels])
        return dict(results)


# ── Parser ────────────────────────────────────────────────────────────────────

def _parse_qa_pairs(raw: str) -> list[QAPair]:
    """
    Parse the LLM's Q1./A1. formatted output into QAPair objects.

    Handles:
      Q1. [JD-Focused] What is dependency injection?
      A1. Dependency injection is a pattern where...

    Also handles edge cases:
      - Extra blank lines between blocks
      - LLM occasionally writing "Question 1." or "1." instead of "Q1."
      - Answer text spanning multiple lines
    """
    # Normalise line endings
    text = raw.strip().replace("\r\n", "\n").replace("\r", "\n")

    # Split into Q/A blocks — each block starts at a Qn. line
    # Pattern matches: Q1. / Q 1. / Question 1. / 1. (as question marker)
    block_pattern = re.compile(
        r"(?:^|\n)\s*(?:Q\s*(\d+)|Question\s+(\d+)|(\d+))\.\s*(\[(?:JD|Resume)-Focused\])?\s*(.+?)(?=\n\s*(?:Q\s*\d+|Question\s+\d+|\d+)\.|$)",
        re.DOTALL | re.IGNORECASE,
    )

    # Simpler two-pass approach: split on "Qn." markers, then find "An." within each block
    qa_pairs: list[QAPair] = []

    # Split the whole text into question blocks by looking for Q\d+. or \d+. markers
    # Then within each block look for A\d+.
    q_splits = re.split(r"\n?(?=(?:Q\s*\d+\.|Question\s+\d+\.|\b\d+\.))", text)

    for block in q_splits:
        block = block.strip()
        if not block:
            continue

        # Try to split this block into question part and answer part
        # Match: Q<n>. [tag] <question text>\nA<n>. <answer text>
        qa_match = re.match(
            r"(?:Q\s*\d+|Question\s+\d+|\d+)\.\s*"   # question number
            r"((?:\[(?:JD|Resume)-Focused\]\s*)?)"    # optional tag
            r"(.+?)\n"                                 # question text (stops at newline)
            r"\s*(?:A\s*\d+|Answer\s+\d+|\d+)\.\s*"  # answer number
            r"(.+)$",                                  # answer text (rest of block)
            block,
            re.DOTALL | re.IGNORECASE,
        )

        if qa_match:
            tag = qa_match.group(1).strip()
            question_text = qa_match.group(2).strip()
            answer_text = qa_match.group(3).strip()

            # Re-attach the source tag to the question string (UI uses it for colour coding)
            full_question = f"{tag} {question_text}".strip() if tag else question_text

            # Truncate answer hard at 200 words as a safety net
            answer_words = answer_text.split()
            if len(answer_words) > 200:
                answer_text = " ".join(answer_words[:200]) + "…"

            if len(full_question) > 15 and len(answer_text) > 10:
                qa_pairs.append(QAPair(question=full_question, answer=answer_text))
        else:
            # Fallback: block has a question but no parseable answer separator
            # Strip the number prefix and store with empty answer
            cleaned = re.sub(r"^(?:Q\s*\d+|Question\s+\d+|\d+)\.\s*", "", block).strip()
            if len(cleaned) > 15:
                logger.debug("Could not parse answer for block: %s", cleaned[:80])
                qa_pairs.append(QAPair(
                    question=cleaned,
                    answer="Answer not available — please refer to a technical colleague for evaluation.",
                ))

    # Final fallback: if parsing completely failed, return raw text as single item
    if not qa_pairs:
        logger.warning("QA parser returned 0 pairs — returning raw output as fallback")
        qa_pairs = [QAPair(question=raw.strip(), answer="")]

    return qa_pairs