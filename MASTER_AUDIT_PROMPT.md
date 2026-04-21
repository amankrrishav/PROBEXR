# MASTER AUDIT PROMPT — PROBEXR

> **Version:** 1.0 | **Last Updated:** 2026-04-21
> **Scope:** Full-stack audit for PROBEXR — an article summarizer & learning platform.
> **Stack:** React 19 + Vite (frontend), FastAPI async + SQLModel (backend), PostgreSQL/SQLite (DB), Redis (cache/rate-limit), Prometheus + Grafana (observability).
> **Deployment:** Vercel (frontend) → Render/Docker (backend), split-domain architecture.

---

## HOW TO USE THIS PROMPT

Copy this entire document and paste it as your prompt to any LLM/AI agent. It will perform a comprehensive audit of the PROBEXR repository. The prompt is **self-updating** — each section asks the auditor to flag items that are present, missing, or need improvement. This means it works whether the repo has 10 features or 100.

**Run this audit:**
- Before every major release
- After adding any new feature domain (new router, new service, new frontend feature)
- Quarterly for ongoing health checks
- When onboarding new team members (as a codebase understanding exercise)
- After any security incident or dependency vulnerability disclosure

---

## INSTRUCTIONS FOR THE AUDITOR

You are performing a **comprehensive, zero-assumptions audit** of the PROBEXR repository. For every section below, you must:

1. **Inspect the actual code** — do not rely on documentation or README claims.
2. **Verdict each item** as: ✅ PASS | ⚠️ WARN | ❌ FAIL | 🔍 N/A (not applicable yet)
3. **Provide evidence** — cite the file path and line number for every finding.
4. **Score each section** on a scale of 1–10.
5. **Produce a final summary** with a prioritized action list (P0 = do now, P1 = this sprint, P2 = this quarter, P3 = backlog).

---

## SECTION 1: SECURITY AUDIT

### 1.1 Authentication & Authorization

- [ ] **Password hashing**: Verify Argon2id (or bcrypt) is used, not MD5/SHA/plaintext. Check `app/services/auth.py`.
- [ ] **JWT implementation**: Check signing algorithm (HS256 minimum, RS256 preferred for multi-service). Verify `exp`, `sub`, `iat` claims are set. Check `algorithm` config.
- [ ] **Token lifecycle**: Access token ≤ 15 min, refresh token ≤ 7 days. Verify `access_token_expire_minutes` and `refresh_token_expire_days`.
- [ ] **Refresh token rotation**: Old token revoked on rotation. Check `rotate_refresh_token()`.
- [ ] **Refresh token reuse detection**: If a revoked token is reused, entire family is revoked. Check `_revoke_family()`.
- [ ] **Cookie security**: `HttpOnly=True`, `Secure=True` (prod), `SameSite=None` (cross-domain) or `Lax` (same-domain). Check `set_auth_cookie()`, `set_refresh_cookie()`.
- [ ] **Cookie deletion parity**: `delete_auth_cookies()` uses same `samesite`/`secure` attributes as set.
- [ ] **Account lockout**: Lockout after N failed attempts within a window. Check `lockout.py`, `authenticate_user()`.
- [ ] **Email enumeration defense**: Login failure path is timing-safe (same action whether email exists or not).
- [ ] **Magic link one-time use**: `UsedToken` table enforces jti uniqueness. Check `verify_magic_link_token()`.
- [ ] **OAuth state validation**: Timing-safe comparison of state cookie vs callback param. Check `social.py`.
- [ ] **Social login account linking**: Existing email accounts are linked, not duplicated. Check `handle_social_login()`.
- [ ] **Password strength**: NIST SP 800-63B compliance (min length, no composition rules). Check registration endpoint.
- [ ] **RS256 readiness**: Config supports `jwt_private_key` / `jwt_public_key` for asymmetric JWTs.
- [ ] **Dependency auth resolution**: `get_current_user` checks `is_active`. `get_optional_user` returns None on failure, doesn't throw.

### 1.2 CSRF Protection

- [ ] **Dual-submit cookie pattern**: `csrf_token` cookie (non-HttpOnly) + `X-CSRF-Token` header. Check `CSRFMiddleware`.
- [ ] **Origin-header check**: Cross-domain requests validated against CORS allow list.
- [ ] **Timing-safe comparison**: `secrets.compare_digest()` for cookie vs header.
- [ ] **Exempt paths are minimal**: Only health, metrics, OAuth callbacks, OpenAPI docs.
- [ ] **Safe methods bypass**: GET/HEAD/OPTIONS always pass.
- [ ] **CSRF cookie refresh**: Token set/refreshed on every response.

### 1.3 CORS

- [ ] **No wildcard in production**: Startup assertion blocks `CORS_ORIGINS=*` in production.
- [ ] **Credentials allowed**: `allow_credentials=True` with explicit origins.
- [ ] **Custom headers exposed**: `X-CSRF-Token` in `allow_headers`.
- [ ] **Error responses include CORS headers**: Exception handlers add `Access-Control-Allow-Origin`.

### 1.4 Input Validation & Injection

- [ ] **Prompt injection sanitizer**: `prompt_sanitizer.py` strips instruction-override patterns from user text before LLM.
- [ ] **Document vs user prompt sanitization**: Different strictness levels for document content vs user instructions.
- [ ] **SQL injection**: Parameterized queries via SQLModel/SQLAlchemy (no raw SQL).
- [ ] **XSS in API responses**: JSON-only responses (no HTML rendering server-side). Frontend uses `react-markdown` with `rehype-sanitize`.
- [ ] **URL validation**: `ingest.py` validates content-type of ingested URLs.
- [ ] **Max input length**: `summarize_max_words` enforced server-side (hard cap).
- [ ] **Pydantic validation**: All request bodies use typed schemas (`TextRequest`, etc.).

### 1.5 Security Headers

- [ ] **Content-Security-Policy**: `default-src 'self'`, `frame-ancestors 'none'`, no `unsafe-eval`.
- [ ] **X-Content-Type-Options**: `nosniff`.
- [ ] **X-Frame-Options**: `DENY`.
- [ ] **Referrer-Policy**: `strict-origin-when-cross-origin`.
- [ ] **Permissions-Policy**: Camera, mic, geo disabled.
- [ ] **HSTS**: `max-age=31536000; includeSubDomains` in production only.
- [ ] **No server version leakage**: FastAPI/Uvicorn version not exposed in headers.

### 1.6 Secrets Management

- [ ] **SECRET_KEY**: Not default in production (startup assertion).
- [ ] **SECRET_KEY entropy**: Minimum 32 characters (startup assertion).
- [ ] **API keys**: Loaded from environment, never hardcoded. Check `config.py`.
- [ ] **No secrets in git**: `.gitignore` covers `.env`, no secrets in committed files.
- [ ] **Docker**: `.env` not copied into image. Secrets via environment variables.

### 1.7 Rate Limiting

- [ ] **Three tiers**: Auth (5/min), LLM (10/min), General (60/min).
- [ ] **IP-based**: All routes.
- [ ] **Per-user**: Authenticated requests hashed by JWT sub.
- [ ] **Per-email**: Auth routes parse request body, hash email.
- [ ] **Redis-backed with in-memory fallback**: `RedisRateLimiter` + `InMemoryRateLimiter`.
- [ ] **Rate limit headers**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`, `Retry-After`.
- [ ] **Fail-open on Redis error**: Don't block users if Redis is down.

### 1.8 Dependency Vulnerabilities

- [ ] **pip-audit**: Run `pip-audit -r requirements.txt` — zero critical/high vulnerabilities.
- [ ] **npm audit**: Run `npm audit` — zero critical/high vulnerabilities.
- [ ] **Pinned dependencies**: `requirements.txt` uses hashes (`--require-hashes`).
- [ ] **Python version**: ≥ 3.11 (supported, receives security patches).
- [ ] **Node version**: ≥ 20 LTS.
- [ ] **CI runs security scans**: `bandit`, `pip-audit` in GitHub Actions.

---

## SECTION 2: ARCHITECTURE & CODE QUALITY

### 2.1 Backend Architecture

- [ ] **Layered separation**: Routers → Services → Models/Schemas → DB. No business logic in routers.
- [ ] **Dependency injection**: `Depends()` for auth, session, pagination. Central `deps.py`.
- [ ] **Config management**: `pydantic-settings` `BaseSettings` with env file support, `lru_cache` singleton.
- [ ] **Error handling**: Structured error codes (`ErrorCode` class), consistent `{detail, code}` envelope.
- [ ] **Global exception handlers**: `HTTPException`, `RequestValidationError`, catch-all `Exception` — all return JSON.
- [ ] **No error detail leakage**: Production strips internal error messages in the catch-all handler.
- [ ] **Async throughout**: All DB operations, HTTP calls, and services are async.
- [ ] **Lazy initialization**: DB engine, config created on first access (serverless-friendly).
- [ ] **Provider-agnostic LLM**: Supports Groq, OpenAI, OpenRouter via `config.py` auto-detection.
- [ ] **Extractive fallback**: Works without any LLM provider configured.
- [ ] **Feature flags**: `tts_enabled` pattern for gating features.

### 2.2 Frontend Architecture

- [ ] **React 19**: Using latest features appropriately.
- [ ] **SPA routing**: `react-router-dom` with Vercel rewrites.
- [ ] **Code splitting**: `lazy()` + `Suspense` for heavy pages (Analytics).
- [ ] **Context providers**: `AppContext` (auth, dark mode, history), `SummarizerContext` (summarizer state).
- [ ] **Custom hooks**: `useAuth`, `useSummarizer`, `useTheme`, `useStreaming`, `useBackendHealth`, `useFeatureFlags`, `useSummaryHistory`.
- [ ] **Error boundaries**: `ErrorBoundary` wrapping main content.
- [ ] **Service layer**: `client.js` (base fetch + retry), `api.js` (endpoint functions), `auth.js`, `swr.js`.
- [ ] **Auto-refresh on 401**: Token refresh + retry in `client.js`.
- [ ] **Skeleton screens**: Loading states with `Skeleton.jsx`.
- [ ] **Keyboard shortcuts**: `⌘K` new, `⌘Enter` summarize, `⌘/` help, `⌘F` focus mode.
- [ ] **Service Worker**: `sw.js` for offline support.
- [ ] **Custom cursor**: Desktop-only `CustomCursor.jsx`.

### 2.3 Database Design

- [ ] **Models**: User, Document, ChatSession, FlashcardSet, Synthesis, AudioSummary, RefreshToken, UsedToken, FailedEmail.
- [ ] **Indexes**: Composite index on `(user_id, created_at)`, individual indexes on foreign keys, unique constraints on email/social IDs.
- [ ] **Soft deletes**: `deleted_at` on Document — queries must filter `deleted_at IS NULL`.
- [ ] **Audit columns**: `created_at`, `updated_at` (SQLAlchemy `onupdate`).
- [ ] **Cascade deletes**: User → Documents → FlashcardSets/ChatSessions/AudioSummaries.
- [ ] **Unique constraints**: `uq_document_user_url` prevents duplicate URL ingestion per user.
- [ ] **Timezone handling**: Naive UTC datetimes stored, converted at boundaries.
- [ ] **Migrations**: Alembic configured (Dockerfile copies `alembic/`). Sync engine available for migration runner.
- [ ] **Connection pooling**: PostgreSQL uses `pool_size`, `max_overflow`, `pool_timeout`, `pool_pre_ping`.
- [ ] **SSL for DB**: SSL context created with configurable `db_ssl_verify`.

### 2.4 API Design

- [ ] **Versioned**: All routes under `/api/v1/`.
- [ ] **Consistent response envelope**: `{detail, code}` for errors, structured data for success.
- [ ] **Pagination**: Reusable `PaginationParams` dependency with `skip` + `limit` (max 100).
- [ ] **ETag support**: Check if conditional responses are implemented.
- [ ] **OpenAPI docs**: FastAPI auto-generates at `/docs` and `/openapi.json`.
- [ ] **SSE streaming**: `/summarize/stream`, `/chat/stream` for real-time token delivery.
- [ ] **Health endpoints**: `/` (root for Render), `/api/v1/health` (detailed).

### 2.5 Code Quality

- [ ] **Type annotations**: Strict mypy (`disallow_untyped_defs`, `disallow_incomplete_defs`).
- [ ] **Linting**: Ruff with comprehensive rule set (E, W, F, I, B, C4, UP, S, T20, SIM).
- [ ] **Formatting**: Ruff formatter (double quotes, space indent).
- [ ] **Pre-commit hooks**: trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files, check-merge-conflict, ruff, mypy, bandit.
- [ ] **No print statements**: `T20` rule catches print() in production code.
- [ ] **Docstrings**: All services, middleware, and models have docstrings.
- [ ] **Frontend linting**: ESLint with react, react-hooks, react-refresh plugins.

---

## SECTION 3: PERFORMANCE & SCALABILITY

### 3.1 Backend Performance

- [ ] **Async I/O**: No sync blocking calls in async handlers (check for `time.sleep()`, sync `requests`, sync file I/O).
- [ ] **Connection pooling**: PostgreSQL pool configured with appropriate sizes.
- [ ] **Redis connection reuse**: Single Redis client created at startup, reused.
- [ ] **Cache-aside pattern**: Summaries cached in Redis with 24h TTL, keyed by content hash.
- [ ] **LLM timeout**: Configurable `summarize_timeout_seconds` (default 90s).
- [ ] **LLM retry**: Exponential backoff on 429/502/503/504, max 2 retries.
- [ ] **Map-reduce for long text**: Texts > 3000 words chunked and processed in parallel via `asyncio.gather`.
- [ ] **Background tasks**: Token GC runs periodically (`token_gc.py`). Email sending is non-blocking.
- [ ] **Request timeout**: `httpx.Timeout` with explicit connect + read timeouts.
- [ ] **Global HTTP client**: Single `httpx.AsyncClient` shared across requests.

### 3.2 Frontend Performance

- [ ] **Code splitting**: Analytics dashboard lazy-loaded.
- [ ] **Bundle size**: Check `dist/` output — no unnecessary large dependencies.
- [ ] **Request timeout**: `requestTimeoutMs` config (default 120s).
- [ ] **Abort controller**: Streaming requests can be cancelled.
- [ ] **SWR caching**: Data fetching with stale-while-revalidate.
- [ ] **Skeleton screens**: Immediate visual feedback during loading.
- [ ] **No unnecessary re-renders**: `useCallback`, `useMemo` used appropriately.

### 3.3 Scalability Readiness

- [ ] **Stateless backend**: No in-process state that prevents horizontal scaling (except in-memory rate limiter fallback — documented).
- [ ] **Redis required for multi-instance**: Rate limiter, lockout, and cache all use Redis in production.
- [ ] **Docker multi-stage**: Builder + runtime stages, minimal attack surface.
- [ ] **Gunicorn + UvicornWorker**: 4 workers for async request handling.
- [ ] **Health check**: Docker HEALTHCHECK and `/` endpoint.
- [ ] **Graceful shutdown**: `exec` form CMD, proper cleanup in lifespan context manager.

---

## SECTION 4: TESTING

### 4.1 Backend Tests

- [ ] **Test count**: Verify README claim of 349+ tests.
- [ ] **Coverage**: ≥ 80% (CI enforced via `--cov-fail-under=80`).
- [ ] **Test domains covered**:
  - Auth (login, register, social, magic link, lockout, CSRF, token rotation)
  - Summarization (extractive, LLM, map-reduce, streaming, cache)
  - Documents (CRUD, pagination, soft delete)
  - Chat (ordering, streaming)
  - Flashcards, TTS, Analytics
  - Middleware (CORS, CSRF, rate limiting, security headers, request ID)
  - Infrastructure (health, metrics, config, DB)
  - Security (prompt sanitizer, import hygiene)
  - Load testing (Locust)
  - E2E (critical flows)
- [ ] **Fixtures**: `conftest.py` provides shared test fixtures.
- [ ] **Async tests**: `asyncio_mode = "auto"` in pytest config.
- [ ] **No flaky tests**: Tests don't depend on external services or timing.
- [ ] **Test isolation**: `clear_config()`, `reset_engine()` prevent state leakage between tests.
- [ ] **Lockout isolation**: `NoOpLockoutStore` used in tests to prevent inter-test lockout bleed.

### 4.2 Frontend Tests

- [ ] **Test count**: Verify README claim of 108+ tests.
- [ ] **Test framework**: Vitest + React Testing Library + jsdom.
- [ ] **Test domains covered**:
  - Auth (AuthModal, AccountSettings)
  - Summarizer (Editor, OutputCard, SynthesisWorkspace)
  - Layout (Sidebar)
  - Analytics (Dashboard)
  - Components (ErrorBoundary, KeyboardShortcuts)
  - Hooks (useAuth, useSummarizer)
- [ ] **Test setup**: `src/test/setup.js` provides global test configuration.
- [ ] **User event simulation**: `@testing-library/user-event` for realistic interactions.

### 4.3 CI/CD Pipeline

- [ ] **Triggers**: Push to main, PRs to main.
- [ ] **Concurrency**: Cancel in-progress runs for same branch.
- [ ] **Backend steps**: Python setup → pip install → ruff check + format → mypy → bandit → pip-audit → pytest with coverage.
- [ ] **Frontend steps**: Node setup → npm ci → eslint → vitest.
- [ ] **Cache**: pip cache and npm cache for faster CI runs.
- [ ] **Environment**: SQLite in CI for speed, proper env vars set.

---

## SECTION 5: OBSERVABILITY & MONITORING

### 5.1 Logging

- [ ] **Structured JSON logging**: `pythonjsonlogger` with `JsonFormatter`.
- [ ] **Request correlation**: `X-Request-ID` header (generated or propagated).
- [ ] **Log levels**: INFO for normal operations, WARNING for degraded states, ERROR for failures.
- [ ] **No PII in logs**: Email hashed, no passwords or tokens logged.
- [ ] **No double logging**: Uvicorn access logs disabled to prevent duplication.

### 5.2 Metrics

- [ ] **Prometheus metrics endpoint**: `/api/v1/metrics` (excluded from schema).
- [ ] **HTTP metrics**: `http_request_duration_seconds` (histogram), `http_requests_total` (counter).
- [ ] **LLM metrics**: `llm_latency_seconds` (histogram), `llm_calls_total` (counter with model/method/status/result labels).
- [ ] **Auth metrics**: `auth_events_total` (counter with event label).
- [ ] **Histogram buckets**: HTTP (10ms–10s), LLM (1s–60s) — appropriate for workload.

### 5.3 Alerting

- [ ] **Alert rules defined**: `monitoring/alerts.yml` with PromQL expressions.
- [ ] **Alerts covered**:
  - HighErrorRate (5xx > 5% for 5m) — critical
  - High4xxRate (4xx > 25% for 10m) — warning
  - LLMLatencyHigh (p95 > 30s for 5m) — critical
  - LLMErrorRateHigh (error > 10% for 5m) — warning
  - AuthFailureSpike (> 50 failures in 10m) — warning
  - AuthLockoutSpike (> 10 lockouts in 10m) — critical
  - HighRequestLatency (p95 > 5s for 5m) — warning
  - NoTraffic (0 requests for 15m) — warning
- [ ] **Runbook references**: Critical alerts include remediation guidance.
- [ ] **Grafana dashboard**: `monitoring/grafana-dashboard.json` exists.

---

## SECTION 6: DEVOPS & DEPLOYMENT

### 6.1 Docker

- [ ] **Multi-stage build**: Builder (compile) → Runtime (lean).
- [ ] **Non-root user**: `appuser:appgroup` with UID 1001.
- [ ] **No `.env` in image**: Secrets via environment variables.
- [ ] **Pinned base image**: `python:3.12-slim`.
- [ ] **Hashed requirements**: `pip install --require-hashes`.
- [ ] **HEALTHCHECK**: Curl-based check every 30s.
- [ ] **Exec form CMD**: Gunicorn receives SIGTERM directly.
- [ ] **Minimal system deps**: Only `libpq5` + `curl` in runtime.

### 6.2 Vercel (Frontend)

- [ ] **Framework**: Vite.
- [ ] **Build command**: `npm run build`.
- [ ] **Output directory**: `dist`.
- [ ] **SPA rewrites**: `/(.*) → /index.html`.
- [ ] **Environment variables**: `VITE_API_URL` configured for production backend.

### 6.3 Pre-commit

- [ ] **Hooks configured**: trailing-whitespace, end-of-file-fixer, check-yaml, check-added-large-files (500KB), check-merge-conflict, ruff (check + format), mypy, bandit.
- [ ] **All hooks run**: No skipped or disabled hooks.

---

## SECTION 7: DOCUMENTATION

- [ ] **README**: Accurate description, tech stack table, feature list.
- [ ] **README claims match code**: Verify test counts, feature claims, architecture descriptions.
- [ ] **CONTRIBUTING.md**: Contribution guidelines exist.
- [ ] **ROADMAP.md**: Future plans documented.
- [ ] **API documentation**: FastAPI auto-generated OpenAPI spec.
- [ ] **Code comments**: Complex middleware, security decisions, and architecture choices documented inline.
- [ ] **Config documentation**: All environment variables have descriptive names and defaults in `config.py`.

---

## SECTION 8: FUTURE-PROOFING CHECKLIST

These items may not exist yet. **Flag them as recommendations** if missing.

### 8.1 Security Enhancements

- [ ] **API key authentication**: For programmatic access (SDK/CLI users).
- [ ] **Role-based access control (RBAC)**: Admin, Pro, Free user tiers with enforced permissions.
- [ ] **Webhook signature verification**: If webhooks are added.
- [ ] **Content Security Policy reporting**: CSP `report-uri` or `report-to` directive.
- [ ] **Subresource Integrity (SRI)**: For any CDN-loaded scripts/styles.
- [ ] **WAF integration**: Rate limiting at edge (Cloudflare, AWS WAF).
- [ ] **DMARC/SPF/DKIM**: Email authentication for SMTP sends.
- [ ] **Secrets rotation**: Automated rotation for JWT signing keys, API keys.
- [ ] **Audit log**: Persistent log of all auth events, data access, admin actions.

### 8.2 Architecture Enhancements

- [ ] **Database migrations**: Alembic migration files tracked in version control.
- [ ] **API versioning strategy**: Plan for `/api/v2/` when breaking changes are needed.
- [ ] **Event-driven architecture**: Pub/sub for cross-service communication if microservices are adopted.
- [ ] **File upload support**: If document upload (PDF, DOCX) is planned.
- [ ] **Websocket support**: For real-time collaborative features.
- [ ] **Multi-tenancy**: Organization/team support if B2B is planned.
- [ ] **Internationalization (i18n)**: Frontend translation infrastructure.
- [ ] **Accessibility (a11y)**: WCAG 2.1 AA compliance audit.

### 8.3 Operational Enhancements

- [ ] **Staging environment**: Separate staging deployment for pre-release testing.
- [ ] **Blue-green / canary deploys**: Zero-downtime deployment strategy.
- [ ] **Database backups**: Automated backup schedule with point-in-time recovery.
- [ ] **Log aggregation**: Centralized logging (DataDog, Grafana Loki, ELK).
- [ ] **Error tracking**: Sentry or equivalent for production error monitoring.
- [ ] **Uptime monitoring**: External uptime check (e.g., Better Uptime, UptimeRobot).
- [ ] **Cost monitoring**: LLM API spend tracking and alerts.
- [ ] **Load testing baseline**: Establish performance baselines with Locust results.
- [ ] **Disaster recovery plan**: RTO/RPO targets and documented recovery procedures.
- [ ] **Dependency update policy**: Dependabot or Renovate for automated dependency updates.
- [ ] **License compliance**: SBOM (Software Bill of Materials) generation.

### 8.4 Testing Enhancements

- [ ] **Contract tests**: API contract tests between frontend and backend.
- [ ] **Visual regression tests**: Screenshot comparison for frontend UI.
- [ ] **Chaos engineering**: Failure injection testing (Redis down, DB slow, LLM timeout).
- [ ] **Performance regression tests**: Benchmark critical paths in CI.
- [ ] **Security regression tests**: Automated pen-testing in CI (OWASP ZAP).

---

## SECTION 9: COMPLIANCE & LEGAL

- [ ] **Privacy policy**: Data retention, processing, and deletion policies.
- [ ] **Terms of service**: User agreement for the platform.
- [ ] **GDPR compliance**: Right to erasure, data export, consent management.
- [ ] **Data retention policy**: How long are documents, summaries, and chat sessions stored?
- [ ] **Third-party data processing**: LLM providers receive user content — is this disclosed?
- [ ] **Cookie consent**: Required if operating in EU jurisdictions.
- [ ] **LICENSE file**: Repository license declared.

---

## OUTPUT FORMAT

Produce your audit report in this structure:

```markdown
# PROBEXR Audit Report — [DATE]

## Executive Summary
- Overall Score: X/100
- Critical Issues: N
- Warnings: N
- Passes: N

## Section Scores
| Section | Score | Critical | Warnings |
|---------|-------|----------|----------|
| Security | X/10 | N | N |
| Architecture | X/10 | N | N |
| Performance | X/10 | N | N |
| Testing | X/10 | N | N |
| Observability | X/10 | N | N |
| DevOps | X/10 | N | N |
| Documentation | X/10 | N | N |
| Future-Proofing | X/10 | N | N |
| Compliance | X/10 | N | N |

## Detailed Findings
[Per-section findings with ✅/⚠️/❌ verdicts]

## Prioritized Action List
### P0 — Fix Immediately
### P1 — This Sprint
### P2 — This Quarter
### P3 — Backlog
```

---

*This prompt is designed to be exhaustive and evergreen. As the codebase evolves, new items should be added to the relevant sections. The structure ensures nothing is missed, whether auditing today or in 2030.*
