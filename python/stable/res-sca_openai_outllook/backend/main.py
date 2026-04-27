"""
Resume Screener & Interview Question Generator
FastAPI entry point
"""
from dotenv import load_dotenv
load_dotenv()

import logging
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.resume_router import router as resume_router
from routers.schedule_router import router as schedule_router

# ── Logging setup ─────────────────────────────────────────────────────────────
# Set root logger to INFO — this silences DEBUG from all third-party libraries
# (pdfminer, pdfplumber, httpx, openai, langchain, urllib3, etc.) by default.
#
# Why this matters: pdfplumber uses pdfminer internally, which emits thousands
# of DEBUG lines (nexttoken, do_keyword, exec, etc.) per PDF page when the
# root logger is set to DEBUG. Setting root to INFO suppresses all of that.
#
# Our own modules (routers.*, services.*) are then explicitly set to DEBUG
# so we still see our application-level debug messages during development.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)

# Enable DEBUG only for our own application modules
for _mod in ("routers", "services", "__main__"):
    logging.getLogger(_mod).setLevel(logging.DEBUG)

# Explicitly silence the noisiest third-party loggers
for _lib in (
    "pdfminer",       # thousands of lines per PDF page
    "pdfplumber",
    "httpx",          # every HTTP request to OpenAI/Graph API
    "httpcore",
    "openai",
    "langchain",
    "langchain_core",
    "langchain_community",
    "langchain_openai",
    "urllib3",
    "multipart",
    "faiss",
):
    logging.getLogger(_lib).setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Resume Screener API",
    description="RAG-powered resume screening and interview question generation",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resume_router,   prefix="/api", tags=["resumes"])
app.include_router(schedule_router, prefix="/api", tags=["scheduling"])

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    logger.info("Starting Resume Screener API...")
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)