"""
chain.py — LangChain chains for the three advisor modes.

LangChain 1.x streaming uses .astream() directly on the model —
AsyncIteratorCallbackHandler was removed in 1.x. The new approach
is cleaner: iterate over AIMessageChunk objects from llm.astream().
"""
from __future__ import annotations

import json
import logging
from typing import AsyncGenerator

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from config import get_settings
from prompts.templates import (
    build_advisor_prompt,
    BUDGET_PLANNER_SYSTEM,
    RISK_ANALYZER_SYSTEM,
    QUERY_CLASSIFIER_PROMPT,
)
from rag.retriever import retrieve_funds

logger = logging.getLogger(__name__)
settings = get_settings()


def get_llm(streaming: bool = False) -> ChatOpenAI:
    """
    GPT-4o — temperature 0.2 keeps financial answers factual but readable.
    streaming=True enables .astream() for token-by-token output.
    """
    return ChatOpenAI(
        model=settings.openai_model,
        temperature=0.2,
        max_tokens=1024,
        streaming=streaming,
        openai_api_key=settings.openai_api_key,
    )


async def classify_query_mode(query: str) -> str:
    """
    Cheap gpt-4o-mini call to route the query to the right system prompt.
    Returns: 'advisor' | 'budget' | 'risk' | 'data' | 'general'
    """
    llm = ChatOpenAI(
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=10,
        openai_api_key=settings.openai_api_key,
    )
    prompt = QUERY_CLASSIFIER_PROMPT.format(query=query)
    result = await llm.ainvoke([HumanMessage(content=prompt)])
    mode = result.content.strip().lower()
    valid_modes = {"advisor", "budget", "risk", "data", "general"}
    return mode if mode in valid_modes else "advisor"


async def stream_advisor_response(
    query: str,
    user_profile: dict,
    chat_history: list[dict],
) -> AsyncGenerator[str, None]:
    """
    Core RAG chain: Retrieve -> Augment -> Stream.

    LangChain 1.x approach:
      llm.astream(messages) yields AIMessageChunk objects.
      Each chunk.content is a string token (or empty string — skip those).

    Yields:
      - text tokens one by one
      - a final sentinel '__SOURCES__[...]__END_SOURCES__' for citations
    """
    # 1. Retrieve relevant fund documents from Pinecone
    docs = retrieve_funds(query, user_profile)

    # 2. Build system prompt injecting retrieved context
    system_prompt = build_advisor_prompt(user_profile, docs, chat_history)

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query),
    ]

    # 3. Stream tokens using LangChain 1.x .astream() API
    llm = get_llm(streaming=True)
    try:
        async for chunk in llm.astream(messages):
            token = chunk.content
            if token:               # skip empty keep-alive chunks
                yield token
    except Exception as e:
        logger.error("LLM streaming error: %s", e)
        yield f"\n\n[Error generating response: {e}]"
        return

    # 4. Append fund citation metadata as a sentinel the frontend parses out
    sources = [
        {
            "scheme_code":    doc.metadata.get("scheme_code", ""),
            "scheme_name":    doc.metadata.get("scheme_name", ""),
            "nav":            doc.metadata.get("nav", 0),
            "broad_category": doc.metadata.get("broad_category", ""),
            "risk_rating":    doc.metadata.get("risk_rating", ""),
        }
        for doc in docs[:3]
    ]
    yield f"\n\n__SOURCES__{json.dumps(sources)}__END_SOURCES__"


async def get_budget_insights(
    user_financial_data: dict,
    budget_analysis: dict,
) -> str:
    """One-shot (non-streaming) budget analysis via GPT-4o."""
    system = BUDGET_PLANNER_SYSTEM.format(
        user_financial_data=json.dumps(user_financial_data, indent=2),
        context=json.dumps(budget_analysis, indent=2),
    )
    llm = get_llm(streaming=False)
    result = await llm.ainvoke([
        SystemMessage(content=system),
        HumanMessage(content=(
            "Analyze my financial situation and give me:\n"
            "1. Budget breakdown assessment (50/30/20 rule check)\n"
            "2. Tax saving opportunities (80C, 80D, NPS)\n"
            "3. Emergency fund status\n"
            "4. Recommended monthly SIP amount with fund category suggestions\n"
            "5. Top 3 actionable steps to improve my finances\n"
            "Keep it practical and specific to my numbers."
        )),
    ])
    return result.content


async def get_risk_profile(user_data: dict) -> str:
    """One-shot risk profile analysis via GPT-4o."""
    llm = get_llm(streaming=False)
    result = await llm.ainvoke([
        SystemMessage(content=RISK_ANALYZER_SYSTEM),
        HumanMessage(content=f"User data:\n{json.dumps(user_data, indent=2)}"),
    ])
    return result.content