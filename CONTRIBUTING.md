# Contributing to ReadPulse

ReadPulse is built to stay **scalable and feature-additive** as an open-source app with a future subscription path. This doc explains structure and how to add features.

---

## Repo layout

```
readpulse/
├── backend/          # FastAPI app (serverless/cloud-ready)
│   ├── app/
│   │   ├── main.py   # Mount routers here
│   │   ├── config.py # Env and constants; add keys for new features
│   │   ├── deps.py   # Optional auth, rate limits (placeholder today)
│   │   ├── schemas/  # Request/response models
│   │   ├── routers/  # Route modules (health, summarize; add url_fetch, auth)
│   │   └── services/ # Business logic (summarizer, llm, extractive)
│   ├── requirements.txt
│   └── run.py
├── frontend/         # React + Vite
│   ├── src/
│   │   ├── config.js      # Env and constants; add keys for new features
│   │   ├── App.jsx        # Compose hooks + features
│   │   ├── services/      # API client + endpoints
│   │   ├── hooks/         # useSummarizer, useTheme, useBackendHealth
│   │   └── features/      # layout, summarizer; add new feature folders
│   └── package.json
├── ROADMAP.md        # Phases: MVP → features → auth → subscription
└── CONTRIBUTING.md   # This file
```

---

## How to add a backend feature

1. **Config** — Add env keys in `backend/app/config.py` (e.g. `ENABLE_URL_FETCH`, rate limits).
2. **Schema** — Add Pydantic models in `backend/app/schemas/` (e.g. `UrlFetchRequest`).
3. **Service** — Add logic in `backend/app/services/` (e.g. `url_fetch.py`).
4. **Router** — Add `backend/app/routers/url_fetch.py`; mount in `app/main.py`:  
   `app.include_router(url_fetch.router, prefix="/api")`.
5. **Auth/limits (optional)** — Use `deps.get_optional_user()` or a new dependency when you add auth/plans.

---

## How to add a frontend feature

1. **Config** — Add keys in `frontend/src/config.js` (e.g. feature flags, API paths).
2. **API** — Add endpoint in `frontend/src/services/api.js` (or a new module) using `request()` from `client.js`.
3. **Hook** — Add state and logic in `frontend/src/hooks/` (e.g. `useUrlFetch.js`).
4. **Feature** — Add `frontend/src/features/your-feature/` with components and `index.js` barrel.
5. **App** — Use the hook and feature components in `App.jsx`.

---

## Running locally

- **Backend:** `cd backend && source .venv/bin/activate && uvicorn app.main:app --reload`
- **Frontend:** `cd frontend && npm install && npm run dev`
- **Env:** Backend uses `GROQ_API_KEY` (optional) for LLM; no key = free extractive. Frontend uses `VITE_API_URL` (default `http://127.0.0.1:8000`).

See root [README.md](README.md) and `backend/README.md`, `frontend/README.md` for details.

---

## Subscription path (for maintainers)

- **Config:** `SUBSCRIPTION_ENABLED`, `FREE_DAILY_LIMIT`, `APP_VERSION` already exist. Add Stripe (or other) env when you integrate.
- **Backend:** Implement `deps.get_current_user` and optional `check_usage_limit`; return 429 with message when limit exceeded. Add `GET /me` or `GET /usage` for plan/usage.
- **Frontend:** Use `config.subscription.enabled` and `showUpgradeCta`; show upgrade CTA and limit-reached UI when backend indicates it.
- **Roadmap:** See [ROADMAP.md](ROADMAP.md) for phases.

---

## Code style

- **Backend:** Python, FastAPI conventions. Type hints where helpful.
- **Frontend:** React, ES modules. Config and API in one place per feature when possible.

Keeping the app **modular and config-driven** makes it easier to add features and subscription later without big rewrites.
