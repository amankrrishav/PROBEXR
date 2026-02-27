# ReadPulse — Article Summarizer & Learning Hub

ReadPulse is a full-stack article summarizer and learning platform: paste text or URLs, get a short, human-like summary, chat with the document, listen to it, and export flashcards.  
*Extract signal. Ignore noise.*

Designed as an **open-source app** with a path to **subscription / startup** later (see [ROADMAP.md](ROADMAP.md) and [CONTRIBUTING.md](CONTRIBUTING.md)).

**Backend:** Scalable FastAPI app, serverless/cloud-ready. **$0 options:** no API key = extractive summarization; or Groq/OpenRouter free tier for human-like summaries. No need to spend $5–10/month.

---

## Project overview

**Frontend (React + Vite)**  
- Paste text or URL (min 30 words).  
- Calls backend `POST /summarize` or `POST /api/ingest/url`.  
- Displays summary with typewriter effect and “Show full”.  
- **Advanced Features:** 
  - **Read Aloud (TTS):** Listen to the summarized document.
  - **Chat:** Ask contextual questions about the analyzed text.
  - **Flashcards:** Generate and export flashcard CSVs (Anki-compatible).
  - **Multi-Document Synthesis (Pro):** Synthesize multiple documents into a single briefing.
- Optional auth: sign up / log in modal, account dropdown, daily usage and plan display, and a demo Pro Mode upgrade flow.

**Backend (FastAPI)**  
- **Scalable structure:** `app/` with config, schemas, routers, services—contains routers for auth, chat, flashcards, ingest, summarize, synthesis, and tts.  
- **Human-like summarization:** Two-stage (extract concepts → synthesize in natural language) via any OpenAI-compatible API.  
- **Serverless/cloud-friendly:** Minimal deps (FastAPI, httpx, pydantic, uvicorn). No PyTorch, no local LLM. Deploy on Railway, Render, Fly, or serverless (e.g. Mangum for AWS Lambda).  
- **$0 modes:** No API key → extractive summarization (sentence selection). Groq or OpenRouter free tier → human-like LLM summaries. No credit card or monthly spend required.
- **Provider-agnostic:** Set one of `GROQ_API_KEY`, `OPENAI_API_KEY`, or `OPENROUTER_API_KEY`; provider and default model are auto-detected.  
- **Auth + subscription-ready:** Email/password accounts with JWT, per-user plan + daily usage fields, and a fake Pro Mode upgrade endpoint (`POST /auth/upgrade/demo-pro`) for testing subscription UX before real billing.

---

## Architecture

```
User pastes text / URL
       ↓
React frontend (VITE_API_URL → backend)
       ↓
POST /api/ingest/text OR /api/ingest/url
       ↓
POST /summarize
       ↓
FastAPI (app/main.py)
       ↓
Summarizer service → LLM (if key set) or extractive (no key, $0)
       ↓
{ "summary": "..." } → UI Reveals Chat, Flashcards, and TTS Buttons
```

---

## Backend structure (scalable)

```
backend/
├── app/
│   ├── main.py           # FastAPI app, CORS, router mounting
│   ├── config.py         # Env-based config (add new keys here)
│   ├── schemas/          # Request/response models (e.g. TextRequest)
│   ├── routers/          # Route modules (summarize, auth, chat, ingest, flashcards, tts, synthesis)
│   └── services/         # Business logic (summarizer, llm, auth, chat, etc.)
├── requirements.txt      # Minimal dependencies
├── run.py                # Local: python run.py (from backend/)
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
  - **Optional:** Set a free API key for human-like summaries (Groq: [console.groq.com](https://console.groq.com) → `export GROQ_API_KEY=your_key`). If you set **no key**, the backend still runs using extractive summarization ($0).  
  - `uvicorn app.main:app --reload` or `python run.py`  

**Frontend**  
- From `frontend/`: `npm install` then `npm run dev`.  
- Uses `http://localhost:8000` by default; set `VITE_API_URL` for production.

---

## Backend env (summary)

| Env | Purpose |
|-----|--------|
| `GROQ_API_KEY` | Groq (free tier); default model `llama-3.3-70b-versatile` |
| `OPENAI_API_KEY` | OpenAI; default model `gpt-4o-mini` |
| `OPENROUTER_API_KEY` | OpenRouter; default model `meta-llama/llama-3.1-8b-instruct:free` |
| `SUMMARIZE_PROVIDER` | Force provider: `groq` \| `openai` \| `openrouter` |
| `SUMMARIZE_MODEL` | Override model name |
| `SUMMARIZE_TIMEOUT` | LLM request timeout (seconds, default 90) |
| `SUMMARIZE_MIN_WORDS` | Min input words (default 30) |
| `CORS_ORIGINS` | Comma-separated origins or `*` |

---

## Deploy (serverless / cloud)

- **Railway / Render / Fly:** Set build command to install deps and start command to `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add env vars (e.g. `GROQ_API_KEY`).  
- **AWS Lambda:** Use [Mangum](https://mangum.io/) to wrap `app.main:app`; package with dependencies; set handler and env.  
- **Vercel / Netlify:** Use their Python serverless support and point to a single module that exports the ASGI app (or a serverless function that forwards to your backend URL).

---

## Current capabilities

- **Two-stage human-like summarization** (extract → synthesize)  
- **URL Ingestion** for seamless web scraping and DB content storage
- **Contextual Article Chat** for interrogating documents
- **Text-to-Speech (TTS)** audio generation
- **Flashcard Export** to CSV matching Anki formats
- **Multi-Document Synthesis** for Pro users to combine insights
- **Auth (email/password)** with persistent session cache
- Clear errors (validation, timeout, rate limit, API key)
