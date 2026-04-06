"""
question_generator_hf.py — Tiered interview question generation using
the Hugging Face Inference API with Mistral-7B-Instruct-v0.3.

Model: mistralai/Mistral-7B-Instruct-v0.3
  - Free via HF Inference API (requires HF_TOKEN, free account)
  - 7 billion parameters — strong instruction following
  - Apache 2.0 licence, can be run locally too
  - Context window: 32,768 tokens

Two modes (controlled by env var HF_LOCAL=true)
------------------------------------------------
Mode A — HF Inference API (default, cloud, free tier):
  Uses HuggingFaceEndpoint to call Mistral on HF's servers.
  Requires HF_TOKEN in .env (free account at huggingface.co).
  Rate limit: ~10 requests/minute on free tier.

Mode B — Local (HF_LOCAL=true):
  Uses HuggingFacePipeline to run Mistral on your own hardware.
  Requires ~16GB RAM or a GPU with 8GB+ VRAM.
  pip install transformers accelerate bitsandbytes

Installation
------------
  pip install huggingface-hub langchain-huggingface
"""
import asyncio
import logging
import os
import re
from typing import Literal

from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

logger = logging.getLogger(__name__)

DifficultyLevel = Literal["basic", "intermediate", "advanced"]

# ── Prompt templates ──────────────────────────────────────────────────────────
# Mistral uses a specific chat format: [INST] ... [/INST]
# We keep the prompt inside a single PromptTemplate (not ChatPromptTemplate)
# because HuggingFaceEndpoint works better with raw string prompts.

WEIGHTING_BLOCK = """
STRICT SOURCE WEIGHTING for every set of 5 questions:
- 3 questions tagged [JD-Focused]: from JD's required tech stack and responsibilities
- 2 questions tagged [Resume-Focused]: from candidate's specific projects and experience

OUTPUT FORMAT (follow exactly):
Q1. [JD-Focused] <question>
A1. <recruiter-friendly answer, max 200 words, plain English>

Q2. [JD-Focused] <question>
A2. <answer>

Q3. [JD-Focused] <question>
A3. <answer>

Q4. [Resume-Focused] <question>
A4. <answer>

Q5. [Resume-Focused] <question>
A5. <answer>
"""

PROMPT_TEMPLATES: dict[DifficultyLevel, str] = {
    "basic": (
        "[INST] You are a technical interviewer. Generate 5 BASIC interview questions.\n"
        "Basic questions test: definitions, syntax, basic usage. No architecture or trade-offs.\n\n"
        + WEIGHTING_BLOCK +
        "\nJob Description:\n{job_description}\n\n"
        "Candidate Resume:\n{resume_text}\n\n"
        "Generate exactly 5 basic questions with recruiter-friendly answers. [/INST]"
    ),
    "intermediate": (
        "[INST] You are a technical interviewer. Generate 5 INTERMEDIATE interview questions.\n"
        "Intermediate questions test: scenarios, trade-offs, debugging, real-world decisions.\n\n"
        + WEIGHTING_BLOCK +
        "\nJob Description:\n{job_description}\n\n"
        "Candidate Resume:\n{resume_text}\n\n"
        "Generate exactly 5 intermediate questions with recruiter-friendly answers. [/INST]"
    ),
    "advanced": (
        "[INST] You are a principal engineer. Generate 5 ADVANCED interview questions.\n"
        "Advanced questions test: system design, optimisation, scale, architecture decisions.\n\n"
        + WEIGHTING_BLOCK +
        "\nJob Description:\n{job_description}\n\n"
        "Candidate Resume:\n{resume_text}\n\n"
        "Generate exactly 5 advanced questions with recruiter-friendly answers. [/INST]"
    ),
}


# ── LLM factory ───────────────────────────────────────────────────────────────

def _build_llm():
    """
    Build the LLM — either HF Inference API or local pipeline.

    HF Inference API (default)
    --------------------------
    HuggingFaceEndpoint wraps HF's serverless inference API.
    The model runs on HF's servers — you just send the prompt and get a response.
    Free tier: works, but rate-limited (~10 req/min).
    Paid tier ($0.0004/1K tokens): higher limits.

    Local pipeline (HF_LOCAL=true)
    --------------------------------
    HuggingFacePipeline downloads the model weights and runs inference locally.
    Requires significant RAM/VRAM but is completely free and private.
    """
    use_local = os.environ.get("HF_LOCAL", "false").lower() == "true"

    if use_local:
        logger.info("Using LOCAL Mistral-7B (requires ~16GB RAM)")
        from langchain_community.llms.huggingface_pipeline import HuggingFacePipeline
        from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
        import torch

        model_id = "mistralai/Mistral-7B-Instruct-v0.3"
        tokenizer = AutoTokenizer.from_pretrained(model_id)
        model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            device_map="auto",       # auto-selects GPU if available, else CPU
            load_in_4bit=True,       # 4-bit quantization: reduces RAM from 16GB → 5GB
                                     # requires: pip install bitsandbytes
        )
        pipe = pipeline("text-generation", model=model, tokenizer=tokenizer,
                        max_new_tokens=2048, temperature=0.7, do_sample=True)
        return HuggingFacePipeline(pipeline=pipe)

    else:
        logger.info("Using HF Inference API (Mistral-7B-Instruct-v0.3)")
        from langchain_huggingface import HuggingFaceEndpoint

        provider = os.environ.get("HF_PROVIDER", "auto")
        return HuggingFaceEndpoint(
            repo_id="mistralai/Mistral-7B-Instruct-v0.3",
            provider=provider,
            huggingfacehub_api_token=os.environ["HF_TOKEN"],
            max_new_tokens=2048,
            temperature=0.7,
            # Stop generation at these tokens to prevent runaway output
            stop_sequences=["</s>", "[INST]"],
        )


# ── Question generator ────────────────────────────────────────────────────────

class QuestionGenerator:
    """
    Tiered question generator using Mistral-7B via HuggingFace.

    One chain per difficulty level, run concurrently with asyncio.gather.
    Uses PromptTemplate (not ChatPromptTemplate) because HuggingFaceEndpoint
    is a text-completion LLM, not a chat LLM — it takes a raw string prompt.
    """

    def __init__(self):
        llm = _build_llm()
        self._chains: dict[DifficultyLevel, object] = {}

        for level, template in PROMPT_TEMPLATES.items():
            prompt = PromptTemplate(
                template=template,
                input_variables=["job_description", "resume_text"],
            )
            self._chains[level] = prompt | llm | StrOutputParser()

    async def generate(
        self,
        resume_text: str,
        job_description: str,
        levels: list[DifficultyLevel],
    ) -> dict[str, list[dict]]:
        seen: set = set()
        valid_levels = [lv for lv in levels if lv in PROMPT_TEMPLATES and lv not in seen and not seen.add(lv)]
        if not valid_levels:
            valid_levels = ["basic"]

        logger.info("Generating Q&A with Mistral for levels: %s", valid_levels)

        # HuggingFaceEndpoint is synchronous — wrap in asyncio executor
        # to avoid blocking the FastAPI event loop
        loop = asyncio.get_event_loop()

        async def _invoke(level: DifficultyLevel) -> tuple[str, list[dict]]:
            inputs = {"job_description": job_description[:3000],
                      "resume_text": resume_text[:2000]}
            # Run sync LLM in thread pool to not block async event loop
            raw = await loop.run_in_executor(
                None,
                lambda: self._chains[level].invoke(inputs)
            )
            logger.debug("Mistral raw output for '%s':\n%s", level, raw[:500])
            pairs = _parse_qa_pairs(raw)
            logger.info("Level '%s': %d Q&A pairs parsed", level, len(pairs))
            return level, [p for p in pairs]

        results = await asyncio.gather(*[_invoke(lv) for lv in valid_levels])
        return dict(results)


# ── Parser (same as OpenAI version) ──────────────────────────────────────────

def _parse_qa_pairs(raw: str) -> list[dict]:
    text = raw.strip().replace("\r\n", "\n").replace("\r", "\n")
    q_splits = re.split(r"\n?(?=(?:Q\s*\d+\.|Question\s+\d+\.|\b\d+\.))", text)
    pairs = []

    for block in q_splits:
        block = block.strip()
        if not block:
            continue
        qa_match = re.match(
            r"(?:Q\s*\d+|Question\s+\d+|\d+)\.\s*"
            r"((?:\[(?:JD|Resume)-Focused\]\s*)?)"
            r"(.+?)\n"
            r"\s*(?:A\s*\d+|Answer\s+\d+|\d+)\.\s*"
            r"(.+)$",
            block, re.DOTALL | re.IGNORECASE,
        )
        if qa_match:
            tag = qa_match.group(1).strip()
            question = qa_match.group(2).strip()
            answer = qa_match.group(3).strip()
            full_q = f"{tag} {question}".strip() if tag else question
            words = answer.split()
            if len(words) > 200:
                answer = " ".join(words[:200]) + "…"
            if len(full_q) > 15:
                pairs.append({"question": full_q, "answer": answer})
        else:
            cleaned = re.sub(r"^(?:Q\s*\d+|\d+)\.\s*", "", block).strip()
            if len(cleaned) > 15:
                pairs.append({
                    "question": cleaned,
                    "answer": "Refer to a technical colleague for evaluation.",
                })

    return pairs if pairs else [{"question": raw.strip(), "answer": ""}]