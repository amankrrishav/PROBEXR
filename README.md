# PROBEXR — Article Summarizer & Learning Hub

PROBEXR is a full-stack article summarizer and learning platform: paste text or URLs, get a short, human-like summary, chat with the document, and export flashcards.  
*Extract signal. Ignore noise.*

**Live App:** [https://probefy.netlify.app/](https://probefy.netlify.app/)  
**Live API (Core Hub):** [https://probexr.onrender.com/](https://probexr.onrender.com/)

**100% free and open-source.** No plans, no paywalls, no limits.**Backend:** Scalable FastAPI app with async PostgreSQL/CockroachDB (asyncpg), Redis rate limiting, and streaming-ready LLM layer. **$0 options:** no API key = extractive summarization; or Groq/OpenRouter free tier for human-like summaries. No need to spend $5–10/month. Runs locally with SQLite + no Redis for easy development.

---

## Project overview

**Frontend (React + Vite)**  
- Paste text or URL (min 30 words).  
- Calls backend `POST /summarize` or `POST /api/ingest/url`.  
- Displays summary with typewriter effect and "Show full".  
- **Premium Auth UX:** 
  - **Social Login:** Sign in instantly via Google or GitHub.
  - **Magic Links:** Secure, passwordless entry via email link.
  - **Profile Management:** Update your name and avatar directly in-app.
- **Advanced Features:** 
  - **Chat:** Ask contextual questions about the analyzed text.
  - **Flashcards:** Generate and export flashcard CSVs (Anki-compatible).
  - **Multi-Document Synthesis:** Synthesize multiple documents into a single briefing.
  - **Read Aloud (TTS):** Coming soon — listen to summaries.

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
- **Auth:** Email/password + Social (Google/GitHub) with dynamic redirect URI support. JWT (HttpOnly cookies), Argon2 password hashing.

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
│    ↓ Routers (auth│social│ingest│chat│synthesis)   │
│    ↓ Services (async, AsyncSession)              │
│    ↓ LLM Layer (generate_full / generate_stream) │
│    ↓ Database (asyncpg / aiosqlite)              │
└─────────────────────────────────────────────────┘
       ↓
{ "summary": "..." } → UI Reveals Chat, Flashcards, and Profile Settings
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
│   ├── routers/          # Route modules (summarize, auth, chat, ingest, flashcards, tts, synthesis, streaming, social)
│   └── services/         # Business logic (summarizer, llm, auth, social, chat, etc.)
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
  - **OAuth:** Set `GOOGLE_CLIENT_ID` and `GITHUB_CLIENT_ID` for `http://localhost:5173`.
  - **Optional:** Install PostgreSQL and set `DATABASE_URL=postgresql://user:pass@localhost:5432/probexr` (defaults to SQLite for dev)  
  - **Optional:** Install Redis and set `REDIS_URL=redis://localhost:6379/0` (defaults to in-memory rate limiter for dev)  
  - Run migrations: `python -m alembic upgrade head`  
  - `uvicorn app.main:app --reload` or `python run.py`  

**Frontend**  
- From `frontend/`: `npm install` then `npm run dev`.  
- Uses `http://localhost:8000` by default; set `VITE_API_URL` for production.

---

## Deploy (Production)

- **Backend (Render):** Deploy `backend/` as a Web Service. Set `DATABASE_URL` (CockroachDB), `REDIS_URL` (Aiven), and `FRONTEND_URL`.
- **Frontend (Netlify):** Use `netlify.toml` (included). Set `VITE_API_URL` to your Render endpoint.
- **OAuth:** Update redirect URIs in Google/GitHub consoles to point to your Netlify domain.

---

## Backend env (summary)

| Env | Purpose |
|-----|--------|
| `DATABASE_URL` | Database connection (`sqlite:///./probexr.db` or `postgresql://...`) |
| `REDIS_URL` | Redis connection for rate limiting (optional) |
| `SECRET_KEY` | JWT secret (**must change in production**) |
| `GROQ_API_KEY` | Groq (free tier) for high-intelligence summaries |
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
| `FRONTEND_URL` | Used for dynamic OAuth redirect URIs (e.g. `https://you.netlify.app`) |
| `GOOGLE_CLIENT_ID` | Production/Local Google Client ID |
| `GITHUB_CLIENT_ID` | Production/Local GitHub Client ID |

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
- **Frictionless Auth** (Google / GitHub / Magic Links)
- **Profile Customization** (Full Name, Avatar URL)
- **Secure Sessions** with HttpOnly JWT cookies
