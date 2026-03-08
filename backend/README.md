# ReadPulse Backend

Scalable async FastAPI backend for human-like summarization, TTS, chat, and flashcards. PostgreSQL-ready with Redis rate limiting. Includes premium **Auth UX** (Google, GitHub, Magic Links).

## Cost: $0 options (no need to spend $5–10/month)

- **No API key:** Backend uses **extractive** summarization (sentence selection). **$0**, works everywhere. 
- **Groq (free tier):** [console.groq.com/keys](https://console.groq.com/keys) — set `GROQ_API_KEY` for high-quality human-like summaries.
- **OAuth (free):** Google and GitHub OAuth are free to set up for personal/dev projects.

## Run (first time)

1. **Create a venv and install deps**:
   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and set your SECRET_KEY and OAuth IDs.
   ```

3. **Database & Migrations**:
   - Local: Defaults to SQLite.
   - Run: `python -m alembic upgrade head`

4. **Start**:
   ```bash
   uvicorn app.main:app --reload
   ```

## Production Deployment (Render)

1. **Connect GitHub:** Deploy the `/backend` subdirectory.
2. **Env Vars:** Set `DATABASE_URL` (CockroachDB), `REDIS_URL` (Aiven), `SECRET_KEY`, and `FRONTEND_URL` (your Netlify domain).
3. **Start Command:** `python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## Structure

- **app/config.py** — Dynamic env-based config with robust URL purification.
- **app/routers/** — Includes `auth.py` with Social Login and Magic Link support.
- **app/services/** — Includes `social.py` for OAuth2 client logic.
- **alembic/** — Migrations targeting both SQLite (dev) and PostgreSQL (prod).

## Env

| Env | Purpose |
|-----|--------|
| `FRONTEND_URL` | **CRITICAL:** Your frontend domain for OAuth redirects. |
| `GOOGLE_CLIENT_ID` | Your Google OAuth Client ID. |
| `GITHUB_CLIENT_ID` | Your GitHub OAuth Client ID. |
| `DATABASE_URL` | `sqlite:///` or `postgresql://`. |
| `REDIS_URL` | For rate limiting (optional). |
