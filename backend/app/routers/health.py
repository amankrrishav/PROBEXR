import logging
from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, Any]:
    """Liveness probe — always returns 200.

    Kubernetes-style: if the process is alive and can serve HTTP, it's live.
    Does NOT check downstream dependencies (that's /ready).
    Frontend can also use this for mode/version info.
    """
    cfg = get_config()
    mode = cfg.summarize_provider if cfg.has_llm_provider else "extractive"
    return {
        "status": f"{cfg.app_name} running",
        "version": cfg.app_version,
        "mode": mode or "extractive",
        "capabilities": ["summarize"],
        "note": "extractive = free, no API key. Set GROQ_API_KEY (free) for better summaries.",
    }


@router.get("/ready")
async def readiness() -> JSONResponse:
    """Readiness probe — checks DB and Redis connectivity.

    Kubernetes-style: returns 200 only when all critical dependencies
    are reachable. Returns 503 with details when something is down.
    """
    checks: dict[str, Any] = {}
    all_ready = True

    # ── Database ────────────────────────────────────────────────
    try:
        from sqlalchemy import text

        from app.db import get_engine

        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        checks["database"] = {"status": "ok"}
    except Exception as exc:
        checks["database"] = {"status": "error", "detail": str(exc)}
        all_ready = False

    # ── Redis ───────────────────────────────────────────────────
    try:
        import redis.asyncio as aioredis

        cfg = get_config()
        r = aioredis.from_url(cfg.redis_url, decode_responses=True, socket_connect_timeout=2)
        await r.ping()  # type: ignore[misc]
        await r.aclose()
        checks["redis"] = {"status": "ok"}
    except Exception as exc:
        # Redis is optional (in-memory fallback exists), mark as degraded
        checks["redis"] = {"status": "degraded", "detail": str(exc)}

    # ── LLM Provider ────────────────────────────────────────────
    cfg = get_config()
    if cfg.has_llm_provider:
        checks["llm"] = {
            "status": "ok",
            "provider": cfg.summarize_provider,
            "model": cfg.summarize_model,
        }
    else:
        checks["llm"] = {"status": "degraded", "detail": "No LLM provider configured (extractive fallback)"}

    status_code = 200 if all_ready else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "ready": all_ready,
            "checks": checks,
        },
    )


# Keep the legacy GET / endpoint working (mapped via router prefix by main.py)
@router.get("/")
def legacy_health() -> dict[str, Any]:
    """Backward-compatible root health endpoint."""
    return health()
