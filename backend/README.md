# ⚙️ PROBEXR Backend

The backend for PROBEXR is a highly scalable, fully asynchronous FastAPI service. It handles everything from JWT-based authentication to real-time LLM streaming and multi-document synthesis.

## ✨ Highlights

- **Fully Async Pipeline:** Zero blocking calls in the request path, ensuring maximum throughput.
- **Provider-Agnostic LLM Layer:** Easily switch between OpenAI, Groq, and OpenRouter, complete with real-time cost tracking.
- **Enterprise-Grade Auth:** Supports Social Login (OAuth2), Magic Links, and programmatic API Keys. Includes Account Lockout and NIST-compliant password policies.
- **Data Safety:** Soft deletes (`deleted_at`), composite indexes for fast queries, and automated database migrations via Alembic.
- **Performance:** Redis-backed cache-aside layer, ETag-based conditional responses, and serverless-friendly lazy DB initialization.
- **Robust Background Processing:** Non-blocking email delivery with dead-letter queue handling.
- **Comprehensive Observability:** Built-in Prometheus metrics, Grafana dashboards, and LLM cost counters.
- **Tested & Verified:** Over 450 tests with a 100% pass rate and enforced 75%+ coverage in CI.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Redis (optional but recommended for caching and rate limiting)
- PostgreSQL (or use SQLite for local development)

### Installation

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt -r requirements-dev.txt
   ```

3. Configure environment variables:
   Create a `.env` file and set your database URL and secret keys.

4. Run database migrations:
   ```bash
   alembic upgrade head
   ```

5. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## 🧪 Testing & Linting

Run the test suite with coverage:
```bash
pytest tests/ -q --tb=short --cov=app --cov-report=term-missing --cov-fail-under=75
```

Run code quality checks:
```bash
ruff check app/ tests/
mypy app/
```
