# PROBEXR — Article Summarizer & Learning Hub

PROBEXR is a full-stack article summarizer and learning platform: paste text or URLs, get a short, human-like summary, chat with the document, and export flashcards.  
*Extract signal. Ignore noise.*

**Live App:** *https://probexr.vercel.app*

---

## What It Does

**Summarization**  
- Two-stage human-like summarization (extract → synthesize) via any OpenAI-compatible API  
- Extractive fallback when no API key is configured — always works, always free  
- Real-time SSE streaming for token-by-token delivery  

**Document Intelligence**  
- URL Ingestion with content-type validation  
- Contextual Article Chat for interrogating documents  
- Multi-Document Synthesis for combining insights across sources  
- Flashcard Export to CSV (Anki-compatible)  

**Analytics & Management**  
- Personal document library with search  
- Usage analytics dashboard (lazy-loaded for performance)  
- Prometheus observability metrics  

**Authentication & Security**  
- Social Login (Google, GitHub) with timing-safe OAuth state  
- Magic Links (passwordless via SMTP)  
- Enterprise-grade: Account Lockout, Email Enumeration Defense, NIST SP 800-63B passwords  
- Cross-domain CSRF protection (Origin-header + dual-submit cookie)  
- HttpOnly JWT cookies with `SameSite=None; Secure` for split deployments  

**Architecture Highlights**  
- Fully async backend (FastAPI + asyncpg/aiosqlite)  
- Lazy-initialized DB engine for serverless compatibility  
- Consistent API response envelope with built-in pagination  
- React Error Boundary to prevent full-app crashes  
- Code-split lazy loading for heavy pages  
- Composite DB indexes for query performance  
- Redis rate limiting with `Retry-After` headers and in-memory fallback  
- Provider-agnostic LLM layer (Groq, OpenAI, OpenRouter)  

**Quality**  
- 348 backend tests + 108 frontend tests — 100% pass rate  
- CI/CD pipeline via GitHub Actions (pytest, vitest, mypy, eslint)  

---

## Tech Stack

| Layer | Tech |
|-------|------|
| Frontend | React 19, Vite |
| Backend | FastAPI (async), Python |
| Database | PostgreSQL (asyncpg) / SQLite (aiosqlite) |
| Cache | Redis |
| LLM | OpenAI-compatible (Groq, OpenAI, OpenRouter) |
| Deployment | Vercel (frontend) + Render (backend) |

---

## License

See [LICENSE](LICENSE) for details.
