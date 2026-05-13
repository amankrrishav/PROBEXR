# PROBEXR

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
- Prometheus observability metrics with Grafana dashboards & alerting rules

**Authentication & Security**  
- Social Login (Google, GitHub) with timing-safe OAuth state  
- Magic Links (passwordless via SMTP)  
- API Key authentication for programmatic access  
- Enterprise-grade: Account Lockout, Email Enumeration Defense, NIST SP 800-63B passwords  
- Cross-domain CSRF protection (Origin-header + dual-submit cookie)  
- HttpOnly JWT cookies with `SameSite=None; Secure` for split deployments  
- Server header version suppression across all deployment targets  

**Compliance & Accessibility**  
- GDPR: data export (`GET /auth/export`), account deletion (`DELETE /auth/account`)  
- Cookie consent banner with accept/decline  
- WCAG 2.1 AA: aria-labels, semantic landmarks, keyboard navigation  
- Privacy Policy, Terms of Service, MIT License  

**Architecture Highlights**  
- Fully async backend (FastAPI + asyncpg/aiosqlite)  
- Redis-backed cache-aside layer and ETag-based conditional responses
- Non-blocking background email processing with dead-letter handling
- Lazy-initialized DB engine for serverless compatibility  
- Consistent API response envelope with built-in pagination, and standardized error codes
- React Error Boundary, SWR data fetching, offline support via Service Workers, and skeleton screens
- Code-split lazy loading for heavy pages  
- Composite DB indexes and soft-deletes (`deleted_at`) for query performance  
- Redis rate limiting with `Retry-After` headers and in-memory fallback  
- Provider-agnostic LLM layer (Groq, OpenAI, OpenRouter)  

**Quality**  
- 450 backend tests + 108 frontend tests (558 total) — 100% pass rate  
- 78% backend code coverage with 75% CI enforcement  
- Bundle size monitoring (600KB limit)  
- SBOM generation for license compliance  
- LLM API cost tracking via Prometheus metrics  
- CI/CD pipeline via GitHub Actions (pytest, vitest, strict mypy, ruff, eslint)  

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

## Legal

- [Privacy Policy](PRIVACY_POLICY.md) — how we handle your data, including third-party LLM processing  
- [Terms of Service](TERMS_OF_SERVICE.md) — acceptable use, disclaimers, and liability  
- [License](LICENSE) — source code license
