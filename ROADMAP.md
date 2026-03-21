# PROBEXR Roadmap

PROBEXR is **100% free and open-source**. This doc outlines completed work and upcoming phases.

---

## Current (Completed)

- **Backend:** FastAPI (fully async), config, routers, services. Includes endpoints (`/api/v1`) for Summarize (extractive + LLM), URL Ingest, Text-to-Speech (ready for production implementation), Contextual Chat, Flashcard Export, Document Management, Analytics, and Multi-Document Synthesis. Health checks, auth (email + password, JWT with HttpOnly cookies).
- **Infrastructure:** Async database layer (PostgreSQL via `asyncpg` + SQLite via `aiosqlite`), connection pooling, Redis rate limiter with in-memory fallback, LLM streaming (`generate_full` + `generate_stream`), structured JSON observability logging, Alembic migrations (env-driven). Full local dev compatibility preserved.
- **Frontend:** React 19 + Vite, config, hooks, features. Summarizer + theme, backend health on load, request timeout, auth modal (sign up / log in), account menu. Features include the Synthesis Workspace, Sidebar navigation, personal Document Management (Library Dashboard), robust Analytics, and interactive Output Cards for chat and flashcards. SSE streaming with automatic fallback.
- **Testing:** Comprehensive backend (pytest) and frontend (vitest) test suites covering auth, flashcards, and component rendering.
- **Production Hardening:** Live deployment with SSL/TLS, CORS configuration, and managed database/Redis.
- **Session Sync:** Multi-device session support with Refresh Token rotation and reuse detection.
- **Security & Performance:** Enterprise-grade Auth (Account Lockout, Email Enumeration Defense, NIST Passwords, One-time Magic Links), cross-domain CSRF protection (Origin-header validation + dual-submit cookie fallback), OAuth state validation, `SameSite=None; Secure` cookies for split deployments, global shared HTTPX connections, robust error masking, and Content-Type validation for URL ingest.
- **CI/CD Pipeline:** Fully automated GitHub Actions checks (mypy, pytest, eslint, vitest) on PRs/pushes.
- **Email Delivery:** Universal asynchronous SMTP service for passwordless Magic Link dispatch.
- **Robustness:** CockroachDB compatibility via scoped connection events, deterministic chat history ordering, domain-specific auth exceptions, and frontend React hook optimizations.

---

## Phase Next — Growth & Retention

- [ ] **Browser Extension** — one-click "Summarize this page" for Chrome/Firefox
- [ ] **Export & Sharing** — copy as markdown, PDF export, public share links
- [ ] **Highlights & Annotations** — highlight text spans, add notes, export
- [ ] **Real TTS** — browser SpeechSynthesis API (zero cost), then server-side TTS with better voices

---

## Adding a feature (any phase)

1. **Backend:** Config → schema → service (async, `AsyncSession`) → router → mount in `main.py`. Optional: dependency in `deps.py` (auth).
2. **Frontend:** Config → `services/api.js` → hook → feature folder → wire in `App.jsx`.
3. **Docs:** Update README, ROADMAP, or CONTRIBUTING as needed.

See [CONTRIBUTING.md](CONTRIBUTING.md) for code layout and run instructions.
