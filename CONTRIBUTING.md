# Contributing to ReadPulse

ReadPulse is built to stay **scalable and feature-additive** as an open-source app with a future subscription path. This doc explains structure and how to add features.

---

## Repo layout

```
readpulse/
├── backend/          # FastAPI app (async, PostgreSQL-ready)
│   ├── app/
│   │   ├── main.py       # Mount routers, lifespan (Redis/DB init)
│   │   ├── config.py     # Env and constants; add keys for new features
│   │   ├── db.py         # Async engine (asyncpg/aiosqlite), session factory
│   │   ├── deps.py       # Auth + DB dependencies (CurrentUser, OptionalUser, DbSession)
│   │   ├── middleware.py  # Logging + rate limiting (Redis / in-memory fallback)
│   │   ├── schemas/      # Request/response models
│   │   ├── routers/      # Async route modules (health, summarize, auth, chat, etc.)
│   │   └── services/     # Async business logic (summarizer, llm, auth, chat, etc.)
│   ├── alembic/          # Database migrations (env-driven URL)
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
├── frontend/         # React + Vite
│   ├── src/
│   │   ├── config.js      # Env and constants; add keys for new features
│   │   ├── App.jsx        # Compose hooks + features
│   │   ├── services/      # API client + endpoints (auth, summarize, etc.)
│   │   ├── hooks/         # useSummarizer, useTheme, useBackendHealth, useAuth, useSubscription
│   │   └── features/      # layout, summarizer, auth, subscription; add new feature folders
│   └── package.json
├── ROADMAP.md        # Phases: MVP → features → infrastructure → subscription
└── CONTRIBUTING.md   # This file
```

---

## How to add a backend feature

1. **Config** — Add env keys in `backend/app/config.py` (e.g. `ENABLE_URL_FETCH`, rate limits).
2. **Schema** — Add Pydantic models in `backend/app/schemas/` (e.g. `UrlFetchRequest`).
3. **Service** — Add async logic in `backend/app/services/` (e.g. `url_fetch.py`). Use `AsyncSession` for all DB operations (`await session.execute()`, `await session.commit()`).
4. **Router** — Add `backend/app/routers/url_fetch.py` with `async def` handlers; mount in `app/main.py`:  
   `app.include_router(url_fetch.router, prefix="/api")`.
5. **Auth/limits (optional)** — Use `deps.CurrentUser` / `deps.OptionalUser` and helpers in `app/services/subscription.py` when you add auth-only or plan-limited routes.
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
- **Env:** Backend uses SQLite by default (no PostgreSQL needed for dev). Redis is optional (falls back to in-memory). Set `GROQ_API_KEY` for LLM summaries; no key = free extractive. Frontend uses `VITE_API_URL` (default `http://127.0.0.1:8000`).

See root [README.md](README.md) and `backend/README.md`, `frontend/README.md` for details.

---

## Infrastructure notes

- **Database:** All services use `AsyncSession` (from `sqlalchemy.ext.asyncio`). PostgreSQL (`asyncpg`) for production, SQLite (`aiosqlite`) for dev. Connection pooling is configured in `config.py`.
- **Rate limiting:** Redis-backed (`INCR + EXPIRE`) with in-memory fallback. Configured in `middleware.py`, initialized in `main.py` lifespan.
- **LLM layer:** `services/llm.py` provides `generate_full()` (blocking) and `generate_stream()` (async iterator). Existing callers use `chat_completion` alias.
- **Migrations:** Alembic reads `DATABASE_URL` from environment. Run `python -m alembic upgrade head` after model changes.

---

## Subscription path (for maintainers)

- **Config:** `SUBSCRIPTION_ENABLED`, `FREE_DAILY_LIMIT`, `APP_VERSION` already exist. Add Stripe (or other) env when you integrate.
- **Backend:** Per-user fields (`plan`, `usage_today`, `usage_reset_at`) and `app/services/subscription.py` are in place. Connect real billing to flip `plan` values instead of using the demo `POST /auth/upgrade/demo-pro` endpoint.
- **Frontend:** Auth + Pro Mode demo UI exist (account dropdown, Pro modal, limit-reached banner). Later, wire these to real billing, a full pricing page, and feature gating by plan.
- **Roadmap:** See [ROADMAP.md](ROADMAP.md) for phases.

---

## Code style

- **Backend:** Python, FastAPI conventions. Async functions for all DB and LLM operations. Type hints where helpful.
- **Frontend:** React, ES modules. Config and API in one place per feature when possible.

Keeping the app **modular and config-driven** makes it easier to add features and subscription later without big rewrites.
