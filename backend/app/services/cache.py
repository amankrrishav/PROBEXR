"""
Cache-aside layer for expensive computations (summaries, etc.).

Strategy:
  1. Hash the input parameters → cache key
  2. Check Redis → return cached result if hit
  3. Compute (LLM call, etc.) → store result in Redis with TTL
  4. Fall through gracefully if Redis is unavailable

TTL: 24 hours (configurable). Summaries are deterministic enough
that caching the same text+length+mode combination is safe.

Connection reuse: Instead of creating a new Redis client per call,
this module reuses a shared client set during app startup. Falls back
to creating a short-lived client if the shared one is not available
(e.g., during tests or startup race).
"""

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default TTL: 24 hours
_DEFAULT_TTL_SECONDS = 86400

# ---------------------------------------------------------------------------
# Shared Redis client — set during app startup via set_cache_redis()
# ---------------------------------------------------------------------------

_shared_redis: Any = None


def set_cache_redis(redis_client: Any) -> None:
    """Set the shared Redis client for cache operations.

    Called during app startup after the Redis connection is verified.
    This avoids creating a new connection + ping on every cache call.
    """
    global _shared_redis
    _shared_redis = redis_client
    logger.info("Cache layer: using shared Redis client")


def _build_cache_key(prefix: str, **params: Any) -> str:
    """Build a deterministic cache key from sorted parameters."""
    # Sort params for deterministic ordering
    canonical = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:32]
    return f"cache:{prefix}:{digest}"


async def _get_redis() -> Any:
    """Get a Redis client for cache operations.

    Prefers the shared client set during startup. Falls back to creating
    a short-lived client if the shared one is unavailable (e.g. tests).
    """
    # Fast path: reuse the shared client from startup
    if _shared_redis is not None:
        try:
            await _shared_redis.ping()
            return _shared_redis, False  # (client, needs_close)
        except Exception:
            # Shared client lost connection — fall through to create a new one
            pass

    # Slow path: create a temporary client (dev/tests/startup race)
    try:
        import redis.asyncio as aioredis

        from app.config import get_config

        cfg = get_config()
        client = aioredis.from_url(
            cfg.redis_url,
            decode_responses=True,
            socket_connect_timeout=1,
        )
        await client.ping()  # type: ignore[misc]
        return client, True  # (client, needs_close)
    except Exception:
        return None, False


async def cache_get(prefix: str, **params: Any) -> dict[str, Any] | None:
    """Look up a cached result. Returns None on miss or if Redis is unavailable."""
    redis, needs_close = await _get_redis()
    if not redis:
        return None

    key = _build_cache_key(prefix, **params)
    try:
        raw = await redis.get(key)
        if raw:
            logger.debug("Cache HIT: %s", key)
            return json.loads(raw)  # type: ignore[no-any-return]
        logger.debug("Cache MISS: %s", key)
        return None
    except Exception:
        logger.warning("Cache read error for key %s", key, exc_info=True)
        return None
    finally:
        if needs_close:
            await redis.aclose()


async def cache_set(
    prefix: str,
    value: dict[str, Any],
    ttl: int = _DEFAULT_TTL_SECONDS,
    **params: Any,
) -> None:
    """Store a result in cache. Fails silently if Redis is unavailable."""
    redis, needs_close = await _get_redis()
    if not redis:
        return

    key = _build_cache_key(prefix, **params)
    try:
        await redis.setex(key, ttl, json.dumps(value, default=str))
        logger.debug("Cache SET: %s (TTL=%ds)", key, ttl)
    except Exception:
        logger.warning("Cache write error for key %s", key, exc_info=True)
    finally:
        if needs_close:
            await redis.aclose()


async def get_cached_summary(
    text: str,
    length: str = "standard",
    mode: str = "paragraph",
    tone: str = "neutral",
    keywords: list[str] | None = None,
) -> dict[str, Any] | None:
    """Check cache for a previously computed summary."""
    return await cache_get(
        "summary",
        text=text,
        length=length,
        mode=mode,
        tone=tone,
        keywords=sorted(keywords or []),
    )


async def set_cached_summary(
    text: str,
    result: dict[str, Any],
    length: str = "standard",
    mode: str = "paragraph",
    tone: str = "neutral",
    keywords: list[str] | None = None,
) -> None:
    """Store a computed summary in cache."""
    await cache_set(
        "summary",
        result,
        text=text,
        length=length,
        mode=mode,
        tone=tone,
        keywords=sorted(keywords or []),
    )
