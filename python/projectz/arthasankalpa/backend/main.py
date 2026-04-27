"""
main.py - FastAPI application entry point.
Run: uvicorn main:app --reload --port 8000
"""
from __future__ import annotations

import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import get_settings
from rag.retriever import init_pinecone
from api.routes import chat, funds, budget, profile

# ── Logging ───────────────────────────────────────────────────────────────────
# Force UTF-8 on Windows so emoji-free log lines still render cleanly.
# We use ASCII-safe messages throughout to avoid CP1252 UnicodeEncodeError.
logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
    encoding="utf-8" if sys.platform == "win32" else None,
)
logger = logging.getLogger(__name__)
settings = get_settings()


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("[STARTUP] MF Advisor API starting — env: %s", settings.app_env)

    try:
        init_pinecone()
        logger.info("[STARTUP] Pinecone initialized OK — index: %s", settings.pinecone_index_name)
    except Exception as e:
        logger.warning("[STARTUP] Pinecone init failed (will retry on first request): %s", e)

    logger.info("[STARTUP] API ready at http://127.0.0.1:8000")
    logger.info("[STARTUP] Swagger UI  -> http://127.0.0.1:8000/docs")
    logger.info("[STARTUP] WebSocket   -> ws://127.0.0.1:8000/ws/chat")

    yield

    logger.info("[SHUTDOWN] MF Advisor API stopped")


# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="MF Advisor AI - India",
    description="RAG-powered Mutual Fund & Budget Advisory API (OpenAI + Pinecone)",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(chat.router)
app.include_router(funds.router)
app.include_router(budget.router)
app.include_router(profile.router)


# ── System endpoints ──────────────────────────────────────────────────────────
@app.get("/health", tags=["system"])
async def health():
    return {
        "status": "ok",
        "env": settings.app_env,
        "model": settings.openai_model,
        "pinecone_index": settings.pinecone_index_name,
    }


@app.get("/", tags=["system"])
async def root():
    return {
        "app": "MF Advisor AI",
        "docs": "/docs",
        "websocket": "ws://localhost:8000/ws/chat",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=settings.is_dev)