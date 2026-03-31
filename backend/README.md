# PROBEXR Backend

Scalable async FastAPI backend for human-like summarization, contextual chat, flashcard generation, and multi-document synthesis. Production-ready with PostgreSQL, Redis rate limiting, and enterprise-grade authentication.

## Highlights

- Fully async pipeline (zero blocking calls in request path)
- Provider-agnostic LLM layer (Groq, OpenAI, OpenRouter)
- Enterprise auth: Social Login, Magic Links, Account Lockout, NIST passwords
- Cross-domain CSRF protection with timing-safe OAuth state
- Lazy-initialized DB engine for serverless compatibility
- Global error handling mapped to standardized API response envelopes with pagination
- Redis-backed cache-aside layer and ETag-based conditional responses
- Non-blocking background email processing with dead-letter queue handling
- Soft deletes and composite indexes for fast, safe queries
- Robust observability with Prometheus metrics and Grafana dashboards
- Load Testing and E2E testing ready
- 349 clean backend tests — 100% pass rate, enforcing strict mypy typing and ruff standards
