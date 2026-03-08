# ReadPulse — Article Summarizer & Learning Hub

ReadPulse is a full-stack article summarizer and learning platform: paste text or URLs, get a short, human-like summary, chat with the document, and export flashcards.  
*Extract signal. Ignore noise.*

**Live App:** [https://probefy.netlify.app/](https://probefy.netlify.app/)  
**Live API (Core Hub):** [https://readpulse.onrender.com/](https://readpulse.onrender.com/)

**100% free and open-source.** No plans, no paywalls, no limits.

**Backend:** Scalable FastAPI app with async PostgreSQL/CockroachDB (asyncpg), Redis rate limiting, and streaming-ready LLM layer. **$0 options:** no API key = extractive summarization; or Groq/OpenRouter free tier for human-like summaries. No need to spend $5–10/month. Runs locally with SQLite + no Redis for easy development.

---

## Project overview

**Frontend (React + Vite)**  
- Paste text or URL (min 30 words).  
- Calls backend `POST /summarize` or `POST /api/ingest/url`.  
- Displays summary with typewriter effect and "Show full".  
- **Advanced Features:** 
  - **Chat:** Ask contextual questions about the analyzed text.
  - **Flashcards:** Generate and export flashcard CSVs (Anki-compatible).
  - **Multi-Document Synthesis:** Synthesize multiple documents into a single briefing.
  - **Read Aloud (TTS):** Coming soon — listen to summaries.
- Auth: sign up / log in modal, account dropdown.

**Backend (FastAPI)**  
- **Scalable structure:** `app/` with config, schemas, routers, services—contains routers for auth, chat, flashcards, ingest, summarize, synthesis, and tts.  
- **Async-first:** Full async pipeline using `asyncpg` (PostgreSQL) or `aiosqlite` (SQLite dev) with `AsyncSession`. Zero blocking calls in the request path.  
- **PostgreSQL-ready:** Connection pooling (`pool_size`, `max_overflow`, `pool_timeout`) configured for production. SQLite fallback for local development.  
- **Redis rate limiting:** Atomic INCR+EXPIRE pattern with per-IP limits. Graceful in-memory fallback when Redis is unavailable.  
- **LLM streaming-ready:** `generate_full()` + `generate_stream()` in the LLM layer. SSE transport for real-time token streaming.  
- **Human-like summarization:** Two-stage (extract concepts → synthesize in natural language) via any OpenAI-compatible API.  
- **Serverless/cloud-friendly:** Minimal deps (FastAPI, httpx, pydantic, uvicorn). No PyTorch, no local LLM. Deploy on Railway, Render, Fly, or serverless (e.g. Mangum for AWS Lambda).  
- **$0 modes:** No API key → extractive summarization (sentence selection). Groq or OpenRouter free tier → human-like LLM summaries. No credit card or monthly spend required.
- **Provider-agnostic:** Set one of `GROQ_API_KEY`, `OPENAI_API_KEY`, or `OPENROUTER_API_KEY`; provider and default model are auto-detected.  
- **Auth:** Email/password accounts with JWT (HttpOnly cookies), Argon2 password hashing, required and optional auth dependencies.

---

## Architecture

```
User pastes text / URL
       ↓
React frontend (VITE_API_URL → backend)
       ↓
┌─────────────────────────────────────────────────┐
│  FastAPI (async)                                │
│    ↓ RateLimitingMiddleware (Redis / in-memory)  │
│    ↓ Routers (auth│ingest│chat│tts│flashcards)   │
│    ↓ Services (async, AsyncSession)              │
│    ↓ LLM Layer (generate_full / generate_stream) │
│    ↓ Database (asyncpg / aiosqlite)              │
└─────────────────────────────────────────────────┘
       ↓
{ "summary": "..." } → UI Reveals Chat, Flashcards, and TTS Buttons
```

---

## Backend structure (scalable)

```
backend/
├── app/
│   ├── main.py           # FastAPI app, lifespan (Redis/DB init), CORS, router mounting
│   ├── config.py         # Env-based config (DB, Redis, LLM, pool settings)
│   ├── db.py             # Async engine (asyncpg/aiosqlite), session factory
│   ├── deps.py           # Auth + DB session dependencies (AsyncSession)
│   ├── middleware.py      # Logging + rate limiting (Redis / in-memory fallback)
│   ├── schemas/          # Request/response models (e.g. TextRequest)
│   ├── routers/          # Route modules (summarize, auth, chat, ingest, flashcards, tts, synthesis, streaming)
│   └── services/         # Business logic (summarizer, llm, auth, chat, etc.)
├── alembic/              # Database migrations (env-driven URL)
├── requirements.txt      # Dependencies
├── .env.example          # Environment variables template
└── run.py                # Local: python run.py (from backend/)
```

**Adding a feature:**  
1. Add config in `app/config.py` if needed.  
2. Add schemas in `app/schemas/`.  
3. Add a service in `app/services/`.  
4. Add a router in `app/routers/` and mount it in `app/main.py`.

---

## Run locally

**Backend**  
- From `backend/`:  
  - Create venv: `python3 -m venv .venv` then `source .venv/bin/activate`  
  - `pip install -r requirements.txt`  
  - Copy `.env.example` to `.env` and configure (defaults work for local dev)  
  - **Optional:** Set a free API key for human-like summaries (Groq: [console.groq.com](https://console.groq.com) → `export GROQ_API_KEY=your_key`). If you set **no key**, the backend still runs using extractive summarization ($0).  
  - **Optional:** Install PostgreSQL and set `DATABASE_URL=postgresql://user:pass@localhost:5432/readpulse` (defaults to SQLite for dev)  
  - **Optional:** Install Redis and set `REDIS_URL=redis://localhost:6379/0` (defaults to in-memory rate limiter for dev)  
  - Run migrations: `python -m alembic upgrade head`  
  - `uvicorn app.main:app --reload` or `python run.py`  

**Frontend**  
- From `frontend/`: `npm install` then `npm run dev`.  
- Uses `http://localhost:8000` by default; set `VITE_API_URL` for production.

---

## Backend env (summary)

| Env | Purpose |
|-----|--------|
| `DATABASE_URL` | Database connection (`sqlite:///./readpulse.db` for dev, `postgresql://...` for prod) |
| `REDIS_URL` | Redis connection for rate limiting (optional in dev) |
| `SECRET_KEY` | JWT secret (**must change in production**) |
| `GROQ_API_KEY` | Groq (free tier); default model `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | OpenAI; default model `gpt-4o-mini` |
| `OPENROUTER_API_KEY` | OpenRouter; default model `meta-llama/llama-3.1-8b-instruct:free` |
| `SUMMARIZE_PROVIDER` | Force provider: `groq` \| `openai` \| `openrouter` |
| `SUMMARIZE_MODEL` | Override model name |
| `SUMMARIZE_TIMEOUT` | LLM request timeout (seconds, default 90) |
| `CORS_ORIGINS` | Comma-separated origins or `*` |
| `DB_POOL_SIZE` | PostgreSQL connection pool size (default 5) |
| `DB_MAX_OVERFLOW` | Pool overflow connections (default 10) |
| `RATE_LIMIT_PER_MINUTE` | General rate limit (default 60) |
| `RATE_LIMIT_LLM_PER_MINUTE` | LLM route rate limit (default 10) |

---

## Deploy (serverless / cloud)

- **Railway / Render / Fly:** Set build command to install deps and start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add env vars (`DATABASE_URL` for PostgreSQL/CockroachDB, `REDIS_URL`, `SECRET_KEY`, and optionally `GROQ_API_KEY`). Run `python -m alembic upgrade head` as a release command. Use `cockroachdb+psycopg` for migrations and `postgresql+asyncpg` for the app.
- **AWS Lambda:** Use [Mangum](https://mangum.io/) to wrap `app.main:app`; package with dependencies; set handler and env.  
- **Vercel / Netlify:** Optimized for React. Use `netlify.toml` with `base = "frontend"` and point to the `dist` directory. Ensure `_redirects` is set for SPA routing.
- **Database:** Use a managed PostgreSQL or CockroachDB (e.g. CockroachDB Serverless, Supabase, Neon). Configure `sslmode=require` for secure connections.
- **Redis:** Use managed Redis (e.g. Upstash, Railway Redis) or Aiven. Falls back to in-memory if unavailable.

---

## Current capabilities

- **Two-stage human-like summarization** (extract → synthesize)  
- **URL Ingestion** for seamless web scraping and DB content storage
- **Contextual Article Chat** for interrogating documents
- **Flashcard Export** to CSV matching Anki formats
- **Multi-Document Synthesis** for combining insights across documents
- **SSE Streaming** for real-time token delivery
- **Auth (email/password)** with HttpOnly JWT cookies
- Clear errors (validation, timeout, rate limit, API key)
