"""
Resume Screener & Interview Question Generator
FastAPI entry point
"""

from dotenv import load_dotenv
load_dotenv()  # reads .env from the current working directory into os.environ
 
 
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.resume_router import router as resume_router

app = FastAPI(
    title="Resume Screener API",
    description="RAG-powered resume screening and interview question generation",
    version="1.0.0",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# In production, lock this down to your actual frontend origin.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(resume_router, prefix="/api", tags=["resumes"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
