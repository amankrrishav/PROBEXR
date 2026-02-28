"""
ReadPulse backend — scalable, serverless-ready.
Add new routers in app/routers and mount here.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_config
from app.routers import health, summarize, auth, ingest, synthesis, chat, flashcards, tts
from app.db import engine
from app.middleware import LoggingMiddleware, RateLimitingMiddleware, setup_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    cfg = get_config()

    # --- Startup assertions ---
    # 1. SECRET_KEY must not be default in production
    if cfg.environment == "production" and cfg.SECRET_KEY == "dev-secret-change-this":
        raise RuntimeError(
            "FATAL: SECRET_KEY is set to the default value in production. "
            "Set a strong, unique SECRET_KEY environment variable before deploying."
        )

    # 2. Valid database URL
    if not cfg.database_url:
        raise RuntimeError("FATAL: DATABASE_URL is not configured.")

    # 3. LLM provider availability (warning, not fatal — extractive fallback exists)
    if not cfg.has_llm_provider:
        logger.warning(
            "No LLM provider configured (GROQ_API_KEY / OPENAI_API_KEY / OPENROUTER_API_KEY). "
            "Summarization will use extractive fallback only."
        )

    logger.info(
        "ReadPulse starting: env=%s, provider=%s, db=%s",
        cfg.environment,
        cfg.summarize_provider or "extractive",
        "configured",
    )

    yield
    engine.dispose()

app = FastAPI(
    title="ReadPulse",
    description="Human-like article summarization API",
    version="1.0.0",
    lifespan=lifespan,
)

cfg = get_config()
origins = [o.strip() for o in cfg.cors_origins.split(",") if o.strip()]

app.add_middleware(LoggingMiddleware)
app.add_middleware(RateLimitingMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- Routers -----
app.include_router(health.router)
app.include_router(summarize.router)
app.include_router(auth.router)
app.include_router(ingest.router, prefix="/api")
app.include_router(synthesis.router, prefix="/api")
app.include_router(chat.router, prefix="/api")
app.include_router(flashcards.router, prefix="/api")
app.include_router(tts.router, prefix="/api")