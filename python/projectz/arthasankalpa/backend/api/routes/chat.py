"""
chat.py - WebSocket endpoint for streaming chat.
"""
from __future__ import annotations

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from cache.redis_cache import get_user_profile
from rag.chain import classify_query_mode, stream_advisor_response

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["chat"])

DEFAULT_PROFILE = {
    "user_id": "anonymous",
    "age": 30,
    "monthly_income_inr": 50000,
    "monthly_savings_inr": 10000,
    "risk_appetite": "medium",
    "investment_horizon": "long",
    "financial_goals": [],
    "tax_bracket_pct": 20.0,
}

SENTINEL_START = "__SOURCES__"
SENTINEL_END   = "__END_SOURCES__"


@router.websocket("/chat")
async def websocket_chat(websocket: WebSocket):
    await websocket.accept()
    logger.info("WebSocket connection opened")

    try:
        while True:
            raw  = await websocket.receive_text()
            data = json.loads(raw)

            user_id      = data.get("user_id", "anonymous")
            query        = data.get("query", "").strip()
            chat_history = data.get("chat_history", [])

            if not query:
                await websocket.send_json({"type": "error", "message": "Empty query"})
                continue

            profile = await get_user_profile(user_id) or {**DEFAULT_PROFILE, "user_id": user_id}
            mode    = await classify_query_mode(query)
            logger.info("Query mode: %s | user: %s", mode, user_id)

            sources      = []
            text_buffer  = ""   # accumulate tokens to detect multi-chunk sentinel

            async for chunk in stream_advisor_response(query, profile, chat_history):
                text_buffer += chunk

                # Check if the accumulated buffer now contains the sentinel.
                # The sentinel arrives as a single yield from chain.py but may
                # start with "\n\n", so we must check with `in` not `startswith`.
                if SENTINEL_START in text_buffer:
                    # Split: everything before sentinel is real text, rest is metadata
                    before, _, after = text_buffer.partition(SENTINEL_START)

                    # Flush any remaining real text before the sentinel
                    if before.strip():
                        await websocket.send_json({"type": "token", "token": before})

                    # Parse the sources JSON
                    sources_raw = after.replace(SENTINEL_END, "").strip()
                    try:
                        sources = json.loads(sources_raw)
                        await websocket.send_json({"type": "sources", "sources": sources})
                    except Exception as e:
                        logger.warning("Failed to parse sources JSON: %s | raw: %s", e, sources_raw[:100])

                    text_buffer = ""   # reset buffer — sentinel consumed
                else:
                    # No sentinel yet — send the chunk as a token immediately
                    await websocket.send_json({"type": "token", "token": chunk})
                    text_buffer = ""   # reset — already sent

            await websocket.send_json({"type": "done", "mode": mode})

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
    except Exception as e:
        logger.exception("WebSocket error: %s", e)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass