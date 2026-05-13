"""
PROBEXR backend — scalable, serverless-ready.
Add new routers in app/routers and mount here.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from app import http_client
from app.config import get_config
from app.db import get_engine
from app.errors import ErrorCode, code_for_status
from app.lockout import (
    InMemoryLockoutStore,
    RedisLockoutStore,
    set_lockout_manager,
)
from app.middleware import (
    CSRFMiddleware,
    InMemoryRateLimiter,
    LoggingMiddleware,
    RateLimitingMiddleware,
    RedisRateLimiter,
    SecurityHeadersMiddleware,
    set_rate_limiter,
    setup_logging,
)
from app.routers import (
    analytics,
    api_keys,
    auth,
    chat,
    documents,
    flashcards,
    health,
    ingest,
    streaming,
    summarize,
    synthesis,
    tts,
)
from app.services.cache import set_cache_redis
from app.services.token_gc import start_token_gc, stop_token_gc

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app_inst: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    cfg = get_config()

    # --- Sentry error tracking ---
    if cfg.sentry_dsn:
        try:
            import sentry_sdk

            sentry_sdk.init(
                dsn=cfg.sentry_dsn,
                environment=cfg.environment,
                release=cfg.app_version,
                traces_sample_rate=0.1,  # 10% of requests for performance monitoring
                send_default_pii=False,  # Never send PII to Sentry
            )
            logger.info("Sentry initialized: env=%s", cfg.environment)
        except Exception as e:
            logger.warning("Sentry initialization failed: %s", e)

    # --- Startup assertions ---
    # 1. SECRET_KEY must not be default in production
    if cfg.environment == "production" and cfg.SECRET_KEY == "dev-secret-change-this":
        raise RuntimeError(
            "FATAL: SECRET_KEY is set to the default value in production. "
            "Set a strong, unique SECRET_KEY environment variable before deploying."
        )
    # 1b. SECRET_KEY must have sufficient entropy (min 32 chars)
    if cfg.environment == "production" and len(cfg.SECRET_KEY) < 32:
        raise RuntimeError(
            "FATAL: SECRET_KEY is too short. Use at least 32 characters. "
            'Generate one with: python -c "import secrets; print(secrets.token_hex(32))"'
        )

    # 2. CORS wildcard guard — a wildcard in production allows any origin on
    #    credentialed requests, defeating the same-origin security model entirely.
    if cfg.environment == "production" and cfg.cors_origins.strip() == "*":
        raise RuntimeError(
            "FATAL: CORS_ORIGINS is set to '*' in production. "
            "Set it to a comma-separated list of allowed origins, e.g. "
            "https://yourdomain.com"
        )

    # 3. Valid database URL
    if not cfg.database_url:
        raise RuntimeError("FATAL: DATABASE_URL is not configured.")

    # 3. SQLite in production warning
    if cfg.is_sqlite and cfg.environment == "production":
        logger.warning("SQLite is not recommended for production. Set DATABASE_URL to a PostgreSQL connection string.")

    # 4. LLM provider availability (warning, not fatal — extractive fallback exists)
    if not cfg.has_llm_provider:
        logger.warning(
            "No LLM provider configured (GROQ_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY). "
            "Summarization will use extractive fallback only."
        )

    # 5. Database connection info
    db_mode = (
        "SQLite (aiosqlite)"
        if cfg.is_sqlite
        else f"PostgreSQL (asyncpg, pool={cfg.db_pool_size}+{cfg.db_max_overflow})"
    )
    logger.info("Database: %s", db_mode)

    # 6. Redis rate limiter initialization
    redis_client = None
    try:
        import redis.asyncio as aioredis

        redis_client = aioredis.from_url(
            cfg.redis_url,
            decode_responses=True,
            socket_connect_timeout=3,
        )
        await redis_client.ping()
        set_rate_limiter(RedisRateLimiter(redis_client))
        set_lockout_manager(
            RedisLockoutStore(
                redis_client,
                max_attempts=cfg.lockout_max_attempts,
                window_seconds=cfg.lockout_window_seconds,
            )
        )
        set_cache_redis(redis_client)
        logger.info("Redis connected: %s", cfg.redis_url.split("@")[-1] if "@" in cfg.redis_url else cfg.redis_url)
    except Exception as e:
        if cfg.environment == "production":
            logger.warning("Redis unavailable in production: %s. Falling back to in-memory rate limiter.", str(e))
        else:
            logger.info(
                "Redis not available (%s). Using in-memory rate limiter (OK for development).",
                type(e).__name__,
            )
        set_rate_limiter(InMemoryRateLimiter())
        set_lockout_manager(
            InMemoryLockoutStore(
                max_attempts=cfg.lockout_max_attempts,
                window_seconds=cfg.lockout_window_seconds,
            )
        )
        redis_client = None

    logger.info(
        "PROBEXR starting: env=%s, provider=%s, db=%s",
        cfg.environment,
        cfg.summarize_provider or "extractive",
        "configured",
    )

    # 7. Auto-create tables for SQLite (dev) — production uses Alembic migrations
    engine = get_engine()

    if cfg.is_sqlite:
        import app.models  # noqa: F401 — ensure all models are registered

        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        logger.info("SQLite tables auto-created from models.")

    # 8. Initialize global HTTP client
    http_client.client = httpx.AsyncClient()

    # 9. Start refresh token garbage collection
    start_token_gc(engine)

    yield

    # --- Shutdown ---
    await engine.dispose()
    if redis_client:
        await redis_client.aclose()
        logger.info("Redis connection closed.")
    if http_client.client:
        await http_client.client.aclose()
        logger.info("Global HTTP client closed.")
    stop_token_gc()


app = FastAPI(
    title="PROBEXR",
    description="Human-like article summarization API",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Return validation errors in the standard {detail, code} envelope."""
    cfg = get_config()
    origins = [o.strip().rstrip("/") for o in cfg.cors_origins.split(",") if o.strip()]
    origin = request.headers.get("origin")
    headers: dict[str, str] = {}
    if origin and (origin in origins or "*" in origins):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    # Build a human-readable detail string from pydantic error list
    errors = exc.errors()
    messages: list[str] = []
    for err in errors:
        loc = " -> ".join(str(p) for p in err.get("loc", []))
        msg = err.get("msg", "invalid")
        messages.append(f"{loc}: {msg}" if loc else msg)
    detail = "; ".join(messages) if messages else "Validation error"

    return JSONResponse(
        status_code=422,
        content={"detail": detail, "code": ErrorCode.VALIDATION_ERROR},
        headers=headers,
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    # Ensure CORS headers for cross-domain auth failures
    cfg = get_config()
    origins = [o.strip().rstrip("/") for o in cfg.cors_origins.split(",") if o.strip()]
    origin = request.headers.get("origin")
    headers: dict[str, str] = {}
    if origin and (origin in origins or "*" in origins):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": code_for_status(exc.status_code)},
        headers=headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Global exception caught: %s", str(exc))
    cfg = get_config()
    origins = [o.strip().rstrip("/") for o in cfg.cors_origins.split(",") if o.strip()]
    origin = request.headers.get("origin")
    headers: dict[str, str] = {}
    if origin and (origin in origins or "*" in origins):
        headers["Access-Control-Allow-Origin"] = origin
        headers["Access-Control-Allow-Credentials"] = "true"

    # Never leak internal error details to clients in production
    content: dict[str, str] = {
        "detail": "Internal Server Error",
        "code": ErrorCode.INTERNAL_ERROR,
    }
    if cfg.environment != "production":
        content["error"] = str(exc)

    return JSONResponse(
        status_code=500,
        content=content,
        headers=headers,
    )


cfg = get_config()
origins = [o.strip().rstrip("/") for o in cfg.cors_origins.split(",") if o.strip()]

# Middleware execution order (Starlette reverses add-order):
#   Request  → CORSMiddleware → SecurityHeadersMiddleware
#           → RateLimitingMiddleware → CSRFMiddleware → LoggingMiddleware → Route handler
#   Response ← CORSMiddleware ← SecurityHeadersMiddleware
#           ← RateLimitingMiddleware ← CSRFMiddleware ← LoggingMiddleware ← Route handler
app.add_middleware(LoggingMiddleware)
app.add_middleware(CSRFMiddleware)
app.add_middleware(RateLimitingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*", "X-CSRF-Token"],
)

# ----- Routers -----
from fastapi import APIRouter

v1_router = APIRouter(prefix="/api/v1")

v1_router.include_router(health.router, tags=["Health"])
v1_router.include_router(summarize.router, tags=["Summarization"])
v1_router.include_router(auth.router, tags=["Authentication"])
v1_router.include_router(ingest.router, tags=["Ingestion"])
v1_router.include_router(synthesis.router, tags=["Synthesis"])
v1_router.include_router(chat.router, tags=["Chat"])
v1_router.include_router(flashcards.router, tags=["Flashcards"])
v1_router.include_router(tts.router, tags=["TTS"])
v1_router.include_router(documents.router, tags=["Documents"])
v1_router.include_router(analytics.router, tags=["Analytics"])
v1_router.include_router(streaming.router, tags=["Streaming"])
v1_router.include_router(api_keys.router, tags=["API Keys"])

# Observability
from app.metrics import metrics_endpoint

v1_router.add_api_route("/metrics", metrics_endpoint, tags=["Observability"], include_in_schema=False)

app.include_router(v1_router)


# Root health endpoint — Render's health check hits GET / and expects 200.
@app.get("/", include_in_schema=False)
def root_health() -> dict[str, str]:
    return {"status": "ok"}
