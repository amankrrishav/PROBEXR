# PROBEXR Backend

Scalable async FastAPI backend for human-like summarization, contextual chat, flashcard generation, and multi-document synthesis. Production-ready with PostgreSQL, Redis rate limiting, and enterprise-grade authentication.

## Highlights

- Fully async pipeline (zero blocking calls in request path)
- Provider-agnostic LLM layer (Groq, OpenAI, OpenRouter)
- Enterprise auth: Social Login, Magic Links, Account Lockout, NIST passwords
- Cross-domain CSRF protection with timing-safe OAuth state
- Lazy-initialized DB engine for serverless compatibility
- Consistent API response envelope with pagination
- Prometheus observability metrics
- 348 tests — 100% pass rate
