# PROBEXR — Article Summarizer & Learning Hub

PROBEXR is a full-stack article summarizer and learning platform: paste text or URLs, get a short, human-like summary, chat with the document, and export flashcards.  
*Extract signal. Ignore noise.*

**Live App:** *https://probexr.vercel.app*

**100% free and open-source.** No plans, no paywalls, no limits. **Backend:** Scalable FastAPI app with async PostgreSQL (asyncpg), Redis rate limiting, and streaming-ready LLM layer. **$0 options:** no API key = extractive summarization; or Groq/OpenRouter free tier for human-like summaries. No need to spend $5–10/month. Runs locally with SQLite + no Redis for easy development.

---

## Project overview

**Frontend (React 19 + Vite)**  
- Paste text or URL (min 30 words).  
- Calls backend `POST /api/v1/summarize` or `POST /api/v1/ingest/...`.  
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
- **Scalable structure:** `app/` with config, schemas, routers, services—contains routers for auth, chat, documents, flashcards, ingest, summarize, synthesis, tts, analytics, and streaming.  
- **Async-first:** Full async pipeline using `asyncpg` (PostgreSQL) or `aiosqlite` (SQLite dev) with `AsyncSession`. Zero blocking calls in the request path.  
- **PostgreSQL-ready:** Connection pooling (`pool_size`, `max_overflow`, `pool_timeout`) configured for production. CockroachDB compatibility is handled seamlessly. SQLite fallback for local development.  
- **Redis rate limiting:** Atomic INCR+EXPIRE pattern with per-IP limits. Graceful in-memory fallback when Redis is unavailable.  
- **LLM streaming-ready:** `generate_full()` + `generate_stream()` in the LLM layer. SSE transport for real-time token streaming.  
- **Human-like summarization:** Two-stage (extract concepts → synthesize in natural language) via any OpenAI-compatible API.  
- **Serverless/cloud-friendly:** Minimal deps (FastAPI, httpx, pydantic, uvicorn). No PyTorch, no local LLM. Deploy on Railway, Render, Fly, or serverless (e.g. Mangum for AWS Lambda).  
- **$0 modes:** No API key → extractive summarization (sentence selection). Groq or OpenRouter free tier → human-like LLM summaries. No credit card or monthly spend required.
- **Provider-agnostic:** Set one of `GROQ_API_KEY`, `OPENAI_API_KEY`, or `OPENROUTER_API_KEY`; provider and default model are auto-detected.  
- **Enterprise-grade Auth:** Email/password + Social (Google/GitHub) with dynamic redirect URI support. Designed with advanced security: **Account Lockout** (Redis-backed anti-bruteforce), **Email Enumeration Defense**, strict **NIST SP 800-63B password policies**, and **one-time use Magic Links**. Secure by default with CSRF middleware and OAuth state validation.
- **CI/CD pipeline:** Automated GitHub Actions pipeline for frontend (vitest, eslint) and backend (pytest, mypy) on push/PR.

---

## Architecture

```
User pastes text / URL
       ↓
React frontend (VITE_API_URL → backend)
       ↓
┌──────────────────────────────────────────────────┐
│  FastAPI (async)                                 │
│    ↓ RateLimitingMiddleware (Redis / in-memory)  │
│    ↓ Routers (auth│ingest│chat│synthesis│docs│etc)│
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
│   ├── http_client.py    # Global shared httpx.AsyncClient (connection pooling)
│   ├── middleware.py      # CSRF + Logging + rate limiting (Redis / in-memory fallback)
│   ├── schemas/          # Request/response models (e.g. TextRequest)
│   ├── routers/          # Route modules (summarize, auth, chat, ingest, flashcards, tts, synthesis, streaming, documents, analytics)
│   └── services/         # Business logic (summarizer, llm, auth, social, email, chat, etc.)
├── alembic/              # Database migrations (env-driven URL)
├── requirements.txt      # Dependencies
└── run.py                # Local: python run.py (from backend/)
```


## Current capabilities

- **Two-stage human-like summarization** (extract → synthesize)  
- **URL Ingestion** for seamless web scraping with content-type validation (rejects binaries early) and DB content storage
- **Contextual Article Chat** for interrogating documents
- **Document Management** to browse, search, and manage your summary library
- **Analytics** for tracking usage and interactions
- **Observability** with built-in Prometheus metrics (`/metrics`) and `X-Request-ID` tracing for structured log correlation
- **Flashcard Export** to CSV matching Anki formats
- **Multi-Document Synthesis** for combining insights across documents
- **SSE Streaming** for real-time token delivery
- **Auth (email/password)** with HttpOnly JWT cookies
- Clear errors (validation, timeout, rate limit, API key)
- **Frictionless Auth** (Google / GitHub / Magic Links via SMTP)
- **Profile Customization** (Full Name, Avatar URL)
- **Secure Sessions** with HttpOnly JWT cookies and CSRF protection
- **Automated CI** with GitHub Actions Pipeline
