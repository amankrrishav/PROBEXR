# PROBEXR Backend

Scalable async FastAPI backend for human-like summarization, TTS, chat, and flashcards. PostgreSQL-ready with Redis rate limiting. Includes premium **Enterprise-grade Auth UX** (Google, GitHub, JWTs, NIST Passwords, Account Lockout, Enumerable Defense, One-time Magic Links via SMTP).

## Cost: $0 options (no need to spend $5–10/month)

- **No API key:** Backend uses **extractive** summarization (sentence selection). **$0**, works everywhere. 
- **Groq (free tier):** [console.groq.com/keys](https://console.groq.com/keys) — set `GROQ_API_KEY` for high-quality human-like summaries.
- **OAuth (free):** Google and GitHub OAuth are free to set up for personal/dev projects.


## Production Deployment

1. **Connect your repo:** Deploy the `/backend` subdirectory on your preferred PaaS.
2. **Env Vars:** Set `DATABASE_URL` (PostgreSQL), `REDIS_URL` (managed Redis), `SECRET_KEY`, `CORS_ORIGINS`, and `FRONTEND_URL` (your frontend domain).
3. **Start Command:** `python -m alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT`

> **⚠️ Cross-domain deployment notes:**
> - `CORS_ORIGINS` and `FRONTEND_URL` must **not** have trailing slashes (e.g. `https://example.com` not `https://example.com/`).
> - Auth cookies use `SameSite=None; Secure; path=/` in production for cross-domain support.
> - CSRF uses Origin-header validation for cross-domain requests (dual-submit cookie is a same-domain fallback).

## Structure

- **app/config.py** — Dynamic env-based config with robust URL purification.
- **app/routers/** — Scalable API structure under `/api/v1` prefix. Includes `auth.py` (Social Login/Magic Link), `documents.py`, and `analytics.py`.
- **app/services/** — Includes `social.py` for OAuth2 client logic.
- **app/metrics.py** — Prometheus metrics tracking HTTP request durations and auth events.
- **app/middleware.py** — Cross-domain CSRF (Origin-header check + dual-submit cookie fallback), rate limiting, and structured logging with `X-Request-ID` propagation.
- **alembic/** — Migrations targeting both SQLite (dev) and PostgreSQL (prod).

## Env

| Env | Purpose |
|-----|--------|
| `FRONTEND_URL` | **CRITICAL:** Your frontend domain for OAuth redirects (no trailing slash). |
| `CORS_ORIGINS` | Comma-separated allowed origins (no trailing slashes). |
| `SECRET_KEY` | JWT signing key. |
| `GOOGLE_CLIENT_ID` | Your Google OAuth Client ID. |
| `GITHUB_CLIENT_ID` | Your GitHub OAuth Client ID. |
| `SMTP_HOST`       | SMTP server (e.g., smtp.sendgrid.net) for Magic Links. |
| `SMTP_PORT`       | SMTP port (usually 587 or 465). |
| `SMTP_USER`       | SMTP username (e.g., apikey). |
| `SMTP_PASSWORD`   | SMTP password. |
| `SMTP_FROM_EMAIL` | Sender address (e.g., noreply@yourdomain.com). |
| `DATABASE_URL` | `sqlite:///` or `postgresql://`. |
| `REDIS_URL` | For rate limiting (optional). |
