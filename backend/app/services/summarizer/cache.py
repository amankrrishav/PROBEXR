"""
Summarizer Cache: Redis-backed persistent storage for text summaries.
Falls back to in-memory dictionary if Redis is unavailable.
"""
import hashlib
import json
import logging
from typing import Any
try:
    from redis.asyncio import Redis
except ImportError:
    Redis = None

from app.config import get_config

logger = logging.getLogger(__name__)

class SummarizerCache:
    def __init__(self):
        cfg = get_config()
        self.enabled = False
        self._redis = None
        self._memory = {}
        self._max_memory = 200

        if Redis and cfg.redis_url:
            try:
                self._redis = Redis.from_url(cfg.redis_url, decode_responses=True)
                self.enabled = True
                logger.info("Summarizer: Redis cache initialized")
            except Exception as e:
                logger.warning("Summarizer: Redis connection failed, falling back to memory: %s", e)

    def _key(self, text: str, length: str) -> str:
        # Hash text to avoid massive keys
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        return f"summarizer:{length}:{text_hash}"

    async def get(self, text: str, length: str) -> dict[str, Any] | None:
        key = self._key(text, length)
        
        # 1. Try Redis
        if self._redis:
            try:
                cached = await self._redis.get(key)
                if cached:
                    return json.loads(cached)
            except Exception as e:
                logger.error("Summarizer: Cache get failed: %s", e)

        # 2. Try Memory
        return self._memory.get(key)

    async def set(self, text: str, length: str, result: dict[str, Any]) -> None:
        key = self._key(text, length)
        
        # 1. Set Memory
        if len(self._memory) >= self._max_memory:
            # Evict oldest
            keys = list(self._memory.keys())
            for k in keys[:50]:
                self._memory.pop(k, None)
        self._memory[key] = result

        # 2. Set Redis
        if self._redis:
            try:
                # Cache for 24 hours
                await self._redis.setex(key, 86400, json.dumps(result))
            except Exception as e:
                logger.error("Summarizer: Cache set failed: %s", e)

# Singleton
cache = SummarizerCache()
