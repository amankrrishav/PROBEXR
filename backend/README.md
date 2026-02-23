# ReadPulse Backend

Scalable FastAPI backend for human-like summarization. Serverless/cloud-ready.

## Cost: $0 options (no need to spend $5–10/month)

- **No API key:** Backend uses **extractive** summarization (sentence selection). **$0**, works everywhere. Quality is lower than LLM but usable.
- **Groq (free tier):** [console.groq.com/keys](https://console.groq.com/keys) — free, no credit card. Set `GROQ_API_KEY` for human-like summaries at **$0**.
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

2. **Optional: set an API key** (for human-like summaries; otherwise extractive is used):

   - **Groq (free):** [console.groq.com/keys](https://console.groq.com/keys) → create key, then:
     ```bash
     export GROQ_API_KEY=your_key_here
     ```
   - Or OpenRouter free models: `OPENROUTER_API_KEY` + `OPENROUTER_MODEL=meta-llama/llama-3.1-8b-instruct:free`.

   If you set **no key**, the backend still runs and uses extractive summarization ($0).

3. **Start the server:**

   ```bash
   uvicorn app.main:app --reload
   ```
   Or: `python run.py`

   Backend: [http://127.0.0.1:8000](http://127.0.0.1:8000). Health: [http://127.0.0.1:8000/](http://127.0.0.1:8000/) (shows `mode: extractive` or `groq` etc.).

## Run (later)

```bash
cd backend
source .venv/bin/activate
export GROQ_API_KEY=your_key   # if not in .env
uvicorn app.main:app --reload
```

## Structure

- **app/config.py** — Env-based config. Add new keys when adding features (summarization, auth, subscription, etc.).
- **app/schemas/** — Pydantic request/response models (summarize, auth, user).
- **app/routers/** — Route modules (`health`, `summarize`, `auth`). Add a new file and mount in `main.py`.
- **app/services/** — Business logic (summarizer, llm, extractive, auth, subscription). Add new services as needed.

## Add a feature

1. Config: add env keys in `app/config.py`.
2. Schema: add in `app/schemas/` (e.g. `requests.py` or new file).
3. Service: add in `app/services/` (e.g. `url_fetch.py`).
4. Router: add in `app/routers/` (e.g. `url_fetch.py`) and in `main.py`: `app.include_router(url_fetch.router, prefix="/api")`.

## Env

At least one of: `GROQ_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`.  
Optional: `SUMMARIZE_PROVIDER`, `SUMMARIZE_MODEL`, `SUMMARIZE_TIMEOUT`, `CORS_ORIGINS`, `SUMMARIZE_MIN_WORDS`, etc. See root README.
