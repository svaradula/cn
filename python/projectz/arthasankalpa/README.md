# MF Advisor AI — India 🇮🇳

RAG-powered Mutual Fund & Budget Advisory using **OpenAI GPT-4o + Pinecone + LangChain + FastAPI + React**

---

## Stack

| Layer      | Tech                    | Cost            |
| ---------- | ----------------------- | --------------- |
| LLM        | OpenAI GPT-4o           | ~$0.018/query   |
| Embeddings | text-embedding-3-small  | $0.02/1M tokens |
| Vector DB  | Pinecone (free tier)    | FREE (≤2GB)     |
| Cache      | Redis (Docker)          | FREE            |
| Database   | PostgreSQL (Docker)     | FREE            |
| Backend    | FastAPI + LangChain     | FREE            |
| Frontend   | React + Vite + Tailwind | FREE            |

---

## Prerequisites

- Python 3.11+
- Node.js 20+
- Docker Desktop (running)
- OpenAI API key → https://platform.openai.com/api-keys
- Pinecone API key (free) → https://app.pinecone.io

---

## Setup — Step by Step

### Step 1 — Clone and configure environment

```bash
cd mf-advisor/backend

# Copy env template and fill in your keys
cp ../.env.example .env
```

Edit `.env`:

```
OPENAI_API_KEY=sk-...your-openai-key...
PINECONE_API_KEY=...your-pinecone-api-key...
```

Everything else can stay as-is for local development.

---

### Step 2 — Start Docker services (Redis + PostgreSQL)

```bash
# From the mf-advisor/ root directory
docker compose up -d

# Verify both containers are healthy
docker compose ps
```

Expected output:

```
NAME                    STATUS
mf_advisor_redis        Up (healthy)
mf_advisor_postgres     Up (healthy)
```

---

### Step 3 — Install Python dependencies

```bash
cd mf-advisor/backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

---

### Step 4 — Run data ingestion (ONE TIME)

This fetches ~8,000 fund NAVs from AMFI, filters to ~2,500 investable growth funds,
embeds them with OpenAI, and stores vectors in Pinecone.

**Cost: ~$0.02 (one-time embedding cost)**
**Time: ~3–5 minutes**

```bash
# Make sure you're in backend/ with venv activated
cd mf-advisor/backend
source venv/bin/activate

python ../scripts/ingest.py
```

Expected output:

```
STEP 1/5 → Fetching NAV data from AMFI India...
  Fetched: 8412 raw fund records
STEP 2/5 → Filtering to investable growth-plan funds...
  After filtering: 2543 fund records
STEP 3/5 → Building text chunks for embedding...
  Built 2543 text chunks
STEP 4/5 → Embedding & upserting to Pinecone...
  Estimated OpenAI cost: ~$0.0204
  Progress: 50/2543 (2.0%) — batch 1 done
  ...
STEP 5/5 → Caching fund list in Redis...
  Cached 2543 funds in Redis (TTL: 4 hours)
✅ Ingestion complete in 187.3 seconds
```

Re-run nightly to get fresh NAV data (costs ~$0.001 for delta updates).

---

### Step 5 — Start the FastAPI backend

```bash
cd mf-advisor/backend
source venv/bin/activate

uvicorn main:app --reload --port 8000
```

API will be live at:

- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health
- WebSocket: ws://localhost:8000/ws/chat

---

### Step 6 — Start the React frontend

Open a new terminal:

```bash
cd mf-advisor/frontend

npm install
npm run dev
```

App will be live at: **http://localhost:5173**

---

## API Reference

### WebSocket Chat (Streaming)

```
ws://localhost:8000/ws/chat

Send:
{
  "user_id": "user_123",
  "query": "Which ELSS funds are best?",
  "chat_history": []
}

Receive (stream):
{"type": "token",   "token": "Based on..."}
{"type": "sources", "sources": [{...}, ...]}
{"type": "done"}
```

### REST Endpoints

| Method | Path                                    | Description                     |
| ------ | --------------------------------------- | ------------------------------- |
| POST   | /api/profile                            | Create/update user risk profile |
| GET    | /api/profile/{user_id}                  | Get saved profile               |
| POST   | /api/profile/{user_id}/risk-analysis    | AI risk analysis                |
| GET    | /api/funds/search?q=...&category=equity | Semantic fund search            |
| POST   | /api/funds/compare                      | Compare 2-3 funds side by side  |
| GET    | /api/funds/recommendations/{user_id}    | Personalized recommendations    |
| POST   | /api/budget/analyze                     | Budget analysis + AI insights   |
| GET    | /health                                 | API health check                |

---

## Project Structure

```
mf-advisor/
├── backend/
│   ├── main.py                  ← FastAPI app entry point
│   ├── config.py                ← Pydantic settings (reads .env)
│   ├── requirements.txt
│   ├── api/routes/
│   │   ├── chat.py              ← WebSocket streaming endpoint
│   │   ├── funds.py             ← Fund search / compare / recommendations
│   │   ├── budget.py            ← Budget analysis endpoint
│   │   └── profile.py           ← User profile CRUD
│   ├── rag/
│   │   ├── embedder.py          ← OpenAI text-embedding-3-small wrapper
│   │   ├── retriever.py         ← Pinecone dense retrieval + reranking
│   │   └── chain.py             ← LangChain GPT-4o chains (streaming)
│   ├── ingestion/
│   │   └── amfi_loader.py       ← AMFI NAV parser → FundRecord dataclass
│   ├── models/schemas.py        ← All Pydantic request/response models
│   ├── prompts/templates.py     ← System prompts (advisor / budget / risk)
│   └── cache/redis_cache.py     ← Async Redis helpers
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx              ← Root with tab navigation
│   │   ├── components/
│   │   │   ├── AdvisorChat.jsx  ← WebSocket streaming chat UI
│   │   │   ├── Dashboard.jsx    ← Budget analysis + Recharts
│   │   │   ├── FundExplorer.jsx ← Search + compare + cards
│   │   │   └── RiskProfiler.jsx ← Multi-step onboarding form
│   │   ├── hooks/
│   │   │   ├── useChat.js       ← WebSocket state + reconnect logic
│   │   │   └── useFunds.js      ← Fund search + recommendations hooks
│   │   └── services/api.js      ← Axios REST client
│
├── scripts/
│   └── ingest.py                ← AMFI → OpenAI → Pinecone pipeline
└── docker-compose.yml           ← Redis + PostgreSQL local services
```

---

## RAG Pipeline Flow

```
User query
    │
    ▼
classify_query_mode()      ← gpt-4o-mini, 10 tokens, ~$0.00001
    │
    ▼
retrieve_funds()           ← Pinecone cosine search (top-20 candidates)
    │  metadata filter:    ← risk_appetite, investment_horizon, category
    ▼
_simple_rerank()           ← local keyword × quality score (free)
    │  top-5 docs
    ▼
build_advisor_prompt()     ← system prompt + user profile + docs injected
    │
    ▼
ChatOpenAI(gpt-4o)         ← streams tokens via AsyncIteratorCallbackHandler
    │
    ▼
WebSocket → frontend        ← token-by-token streaming display
```

---

## Production Upgrade Path

When ready to scale beyond local:

| Local Dev        | Production Swap                |
| ---------------- | ------------------------------ |
| FAISS (optional) | Pinecone Mumbai (ap-south-1)   |
| GPT-4o           | Claude claude-opus-4-5 / GPT-5 |
| Local reranker   | Cohere Rerank v3               |
| Docker Redis     | AWS ElastiCache                |
| Docker Postgres  | AWS RDS                        |
| Uvicorn          | ECS Fargate (2-10 tasks)       |
| Manual ingest    | Celery beat (nightly cron)     |

---

## Troubleshooting

**Pinecone index not found**
→ Rerun `python scripts/ingest.py` — it creates the index automatically.

**Redis connection refused**
→ Run `docker compose up -d` from the `mf-advisor/` root directory.

**OpenAI rate limit during ingestion**
→ The ingester sleeps 0.3s between batches. For free-tier OpenAI, increase to 1.0s in `ingest.py`.

**WebSocket disconnects immediately**
→ Ensure backend is running on port 8000. Check Vite proxy in `vite.config.js`.

**AMFI fetch timeout**
→ AMFI servers can be slow. The loader has a 60s timeout. Retry once.
