"""
Cache-aside layer for expensive computations (summaries, etc.).

Strategy:
  1. Hash the input parameters → cache key
  2. Check Redis → return cached result if hit
  3. Compute (LLM call, etc.) → store result in Redis with TTL
  4. Fall through gracefully if Redis is unavailable

TTL: 24 hours (configurable). Summaries are deterministic enough
that caching the same text+length+mode combination is safe.
"""

import hashlib
import json
import logging
from typing import Any

logger = logging.getLogger(__name__)

# Default TTL: 24 hours
_DEFAULT_TTL_SECONDS = 86400


def _build_cache_key(prefix: str, **params: Any) -> str:
    """Build a deterministic cache key from sorted parameters."""
    # Sort params for deterministic ordering
    canonical = json.dumps(params, sort_keys=True, default=str)
    digest = hashlib.sha256(canonical.encode()).hexdigest()[:32]
    return f"cache:{prefix}:{digest}"


async def _get_redis() -> Any:
    """Try to get a Redis client. Returns None if unavailable."""
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
        return client
    except Exception:
        return None


async def cache_get(prefix: str, **params: Any) -> dict[str, Any] | None:
    """Look up a cached result. Returns None on miss or if Redis is unavailable."""
    redis = await _get_redis()
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
        await redis.aclose()


async def cache_set(
    prefix: str,
    value: dict[str, Any],
    ttl: int = _DEFAULT_TTL_SECONDS,
    **params: Any,
) -> None:
    """Store a result in cache. Fails silently if Redis is unavailable."""
    redis = await _get_redis()
    if not redis:
        return

    key = _build_cache_key(prefix, **params)
    try:
        await redis.setex(key, ttl, json.dumps(value, default=str))
        logger.debug("Cache SET: %s (TTL=%ds)", key, ttl)
    except Exception:
        logger.warning("Cache write error for key %s", key, exc_info=True)
    finally:
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
