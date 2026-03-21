# Contributing to PROBEXR

PROBEXR is **100% free and open-source**. This doc explains the project structure and how to add features.

---

## Repo layout

```
probexr/
├── backend/          # FastAPI app (async, PostgreSQL-ready)
│   ├── app/
│   │   ├── main.py       # Mount routers, lifespan (Redis/DB init)
│   │   ├── config.py     # Env and constants; add keys for new features
│   │   ├── db.py         # Async engine (asyncpg/aiosqlite), session factory
│   │   ├── deps.py       # Auth + DB dependencies (CurrentUser, OptionalUser, DbSession)
│   │   ├── middleware.py  # Cross-domain CSRF + Logging + rate limiting (Redis/in-memory)
│   │   ├── schemas/      # Request/response models
│   │   ├── routers/      # Async route modules (health, summarize, auth, chat, ingest, flashcards, tts, synthesis, streaming, documents, analytics, social)
│   │   └── services/     # Async business logic (summarizer, llm, auth, chat, email, social, etc.)
│   ├── alembic/          # Database migrations (env-driven URL)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/         # React + Vite
│   ├── src/
│   │   ├── config.js      # Env and constants
│   │   ├── App.jsx        # Compose hooks + features
│   │   ├── services/      # API client + endpoints (auth, summarize, etc.)
│   │   ├── hooks/         # useSummarizer, useTheme, useBackendHealth, useAuth
│   │   ├── contexts/      # AppContext, SummarizerContext
│   │   └── features/      # layout, summarizer, auth; add new feature folders
│   └── package.json
├── ROADMAP.md        # Phases and upcoming features
└── CONTRIBUTING.md   # This file
```

---

## How to add a backend feature

1. **Config** — Add env keys in `backend/app/config.py` (e.g. `ENABLE_URL_FETCH`, rate limits).
2. **Schema** — Add Pydantic models in `backend/app/schemas/` (e.g. `UrlFetchRequest`).
3. **Service** — Add async logic in `backend/app/services/` (e.g. `url_fetch.py`). Use `AsyncSession` for all DB operations (`await session.execute()`, `await session.commit()`).
4. **Router** — Add `backend/app/routers/url_fetch.py` with `async def` handlers; mount in `app/main.py`:  
   `app.include_router(url_fetch.router, prefix="/api/v1")`.
5. **Auth (optional)** — Use `deps.CurrentUser` (required) or `deps.OptionalUser` (optional) for auth-gated routes.
6. **Migration (if new models)** — Run `python -m alembic revision --autogenerate -m "description"` then `python -m alembic upgrade head`.

---

## How to add a frontend feature

1. **Config** — Add keys in `frontend/src/config.js` (e.g. feature flags, API paths).
2. **API** — Add endpoint in `frontend/src/services/api.js` (or a new module) using `request()` from `client.js`.
3. **Hook** — Add state and logic in `frontend/src/hooks/` (e.g. `useUrlFetch.js`).
4. **Feature** — Add `frontend/src/features/your-feature/` with components and `index.js` barrel.
5. **App** — Use the hook and feature components in `App.jsx`.

---

## Running locally

- **Backend:**
  ```bash
  cd backend
  source .venv/bin/activate
  cp .env.example .env  # first time only
  python -m alembic upgrade head
  uvicorn app.main:app --reload
  ```
- **Frontend:** `cd frontend && npm install && npm run dev`
- **Env:** Backend uses SQLite by default (no PostgreSQL needed for dev). Redis is optional (falls back to in-memory). Set `GROQ_API_KEY` for LLM summaries; no key = free extractive. Frontend uses `VITE_API_URL` (default `http://localhost:8000/api/v1`; must include `/api/v1`).

See root [README.md](README.md) and `backend/README.md`, `frontend/README.md` for details.

---

## Infrastructure notes

- **Database:** All services use `AsyncSession` (from `sqlalchemy.ext.asyncio`). Models are defined using `SQLModel`. PostgreSQL (`asyncpg`) for production, SQLite (`aiosqlite`) for dev. In production, a specialized setup for PostgreSQL-compatible dialects (like CockroachDB) is used, scoping dialect version patches to engine connection events.
- **Rate limiting & Lockouts:** Redis-backed (`INCR + EXPIRE`) with in-memory fallback for global rate limiting and Brute-force Account Lockout. Configured in `middleware.py` and `lockout.py`, initialized in `main.py` lifespan.
- **CSRF:** Two-strategy approach in `middleware.py`: (1) Origin-header check for cross-domain requests (used when frontend and backend are on different domains), (2) dual-submit cookie pattern for same-domain fallback. Auth endpoints (`/api/v1/auth/`) are exempt as they have no session to protect.
- **LLM layer:** `services/llm.py` provides `generate_full()` (blocking) and `generate_stream()` (async iterator). Existing callers use `chat_completion` alias.
- **Migrations:** Alembic reads `DATABASE_URL` from environment. Run `python -m alembic upgrade head` after model changes.
- **CI/CD Pipeline:** GitHub Actions automatically runs tests (pytest, vitest) and linters (mypy, eslint) on all pushes and PRs to `main`.

---

## Code style

- **Backend:** Python, FastAPI conventions. Async functions for all DB and LLM operations. Type hints where helpful.
- **Frontend:** React, ES modules. Config and API in one place per feature when possible.

Keeping the app **modular and config-driven** makes it easy to add features without big rewrites.
