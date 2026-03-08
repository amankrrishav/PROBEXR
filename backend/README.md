# ReadPulse Backend

Scalable async FastAPI backend for human-like summarization, TTS, chat, and flashcards. PostgreSQL-ready with Redis rate limiting.

## Cost: $0 options (no need to spend $5–10/month)

- **No API key:** Backend uses **extractive** summarization (sentence selection). **$0**, works everywhere. Quality is lower than LLM but usable.
- **Groq (free tier):** [console.groq.com/keys](https://console.groq.com/keys) — free, no credit card. Set `GROQ_API_KEY` for human-like summaries, chat, and synthesis at **$0**.
- **OpenRouter (free models):** Set `OPENROUTER_API_KEY` and use a free model (e.g. `meta-llama/llama-3.1-8b-instruct:free`). **$0** for limited use.

You can run the backend **right now with $0** — no key = extractive; add a free Groq key for better quality.

## Run (first time)

1. **Create a venv and install deps** (macOS/Homebrew Python needs a venv):

   ```bash
   cd backend
   python3 -m venv .venv
   source .venv/bin/activate   # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env with your settings (defaults work for local dev)
   ```

3. **Optional: set an API key** (for human-like summaries; otherwise extractive is used):

   - **Groq (free):** [console.groq.com/keys](https://console.groq.com/keys) → create key, then:
     ```bash
     export GROQ_API_KEY=your_key_here
     ```
   - Or OpenRouter free models: `OPENROUTER_API_KEY` + `OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free`.

   If you set **no key**, the backend still runs and uses extractive summarization ($0).

4. **Optional: PostgreSQL / CockroachDB** (defaults to SQLite for dev):

   ```bash
   # In .env:
   DATABASE_URL=postgresql://user:pass@localhost:5432/readpulse
   ```
   **Note:** In production (Render + CockroachDB), the app uses `cockroachdb+psycopg` for migrations and `postgresql+asyncpg` for the app.

5. **Optional: Redis** (defaults to in-memory rate limiter for dev):

   ```bash
   # In .env:
   REDIS_URL=redis://localhost:6379/0
   ```

6. **Run migrations and start:**

   ```bash
   python -m alembic upgrade head
   uvicorn app.main:app --reload
   ```
   Or: `python run.py`

   Backend: [http://127.0.0.1:8000](http://127.0.0.1:8000). Health: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (shows `mode: extractive` or `groq` etc.).

7. **Run tests:**
   ```bash
   pytest
   ```

## Run (later)

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

## Structure

- **app/main.py** — FastAPI app, lifespan (Redis/DB init), CORS, router mounting.
- **app/config.py** — Env-based config (DB, Redis, LLM, pool settings).
- **app/db.py** — Async engine (`asyncpg` for PostgreSQL, `aiosqlite` for SQLite), `AsyncSession` factory.
- **app/deps.py** — Dependencies (`DbSession`, `CurrentUser`, `OptionalUser`).
- **app/middleware.py** — Structured JSON logging + rate limiting (Redis with in-memory fallback).
- **app/schemas/** — Pydantic request/response models. Includes schemas for `ChatRequest`, `FlashcardRequest`, `TTSRequest`, `SynthesizeRequest`, etc.
- **app/routers/** — Async route modules (`health`, `summarize`, `auth`, `chat`, `flashcards`, `tts`, `synthesis`, `ingest`). Mounted in `main.py`.
- **app/services/** — Async business logic (summarizer, llm, extractive, auth, subscription) keeping the routers thin.
- **alembic/** — Database migrations (env-driven URL, supports both SQLite and PostgreSQL).

## Add a feature

1. Config: add env keys in `app/config.py`.
2. Schema: add in `app/schemas/` (e.g. `requests.py` or new file).
3. Service: add in `app/services/` (e.g. `url_fetch.py`). Use `AsyncSession` for DB ops.
4. Router: add in `app/routers/` (e.g. `url_fetch.py`) and in `main.py`: `app.include_router(url_fetch.router, prefix="/api")`.

## Env

See `.env.example` for all available variables. Key ones:

| Env | Purpose |
|-----|--------|
| `DATABASE_URL` | Database (`sqlite:///./readpulse.db` for dev, `postgresql://...` for prod) |
| `REDIS_URL` | Redis for rate limiting (optional in dev, falls back to in-memory) |
| `SECRET_KEY` | JWT secret (**must change in production**) |
| `GROQ_API_KEY` | Groq LLM (free tier available) |
| `OPENAI_API_KEY` | OpenAI LLM |
| `OPENROUTER_API_KEY` | OpenRouter LLM (free models available) |
| `DB_POOL_SIZE` | PostgreSQL pool size (default 5) |
| `RATE_LIMIT_PER_MINUTE` | General rate limit (default 60) |
| `RATE_LIMIT_LLM_PER_MINUTE` | LLM route rate limit (default 10) |

See root [README.md](../README.md) for full env table and deployment guide.
