# PROBEXR Backend

Scalable async FastAPI backend for human-like summarization, contextual chat, flashcard generation, and multi-document synthesis. Production-ready with PostgreSQL, Redis rate limiting, and enterprise-grade authentication.

## Highlights

- Fully async pipeline (zero blocking calls in request path)
- Provider-agnostic LLM layer (Groq, OpenAI, OpenRouter) with cost tracking
- Enterprise auth: Social Login, Magic Links, API Keys, Account Lockout, NIST passwords
- GDPR compliance: data export, account deletion with 30-day soft-delete grace period
- Cross-domain CSRF protection with timing-safe OAuth state
- Lazy-initialized DB engine for serverless compatibility
- Global error handling mapped to standardized API response envelopes with pagination
- Redis-backed cache-aside layer and ETag-based conditional responses
- Non-blocking background email processing with dead-letter queue handling
- Soft deletes and composite indexes for fast, safe queries
- Robust observability with Prometheus metrics, Grafana dashboards, and LLM cost counters
- Load Testing and E2E testing ready
- 450 backend tests — 100% pass rate, 78% coverage (75% CI enforced)

