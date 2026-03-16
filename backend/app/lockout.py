"""
app/lockout.py — Account lockout store.

Tracks consecutive failed login attempts per email and locks accounts
temporarily after a configurable threshold is exceeded.

Design:
  - No DB columns needed — purely in-memory or Redis-backed.
  - Same Redis client reused from startup; in-memory fallback for dev.
  - Keys are SHA-256 hashes of lowercased email — no PII in the store.
  - Window-based: after `window_seconds` the counter naturally resets.
  - `reset()` is called on successful login to clear the counter immediately.

Lockout flow in authenticate_user:
  1. is_locked(email) → True  →  raise 429 immediately (don't even query DB)
  2. password check fails       →  record_failure(email)
  3. password check succeeds    →  reset(email)
"""
import hashlib
import logging
import time
from typing import Optional, Protocol

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Protocol (interface)
# ---------------------------------------------------------------------------

class LockoutBackend(Protocol):
    async def is_locked(self, email: str) -> bool: ...
    async def record_failure(self, email: str) -> int: ...  # returns new count
    async def reset(self, email: str) -> None: ...


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _email_key(email: str) -> str:
    """Hash email → safe Redis/dict key. No PII stored."""
    return hashlib.sha256(email.strip().lower().encode()).hexdigest()[:32]


# ---------------------------------------------------------------------------
# In-memory implementation
# ---------------------------------------------------------------------------

class InMemoryLockoutStore:
    """
    Single-process in-memory lockout store.
    Suitable for development and single-instance deployments.
    State is lost on restart — acceptable for lockout (security degrades
    gracefully; rate limiter still applies).
    """

    def __init__(self, max_attempts: int = 5, window_seconds: int = 900) -> None:
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds
        # {key: (count, window_start_unix_ts)}
        self._data: dict[str, tuple[int, float]] = {}

    def _get(self, key: str) -> tuple[int, float]:
        entry = self._data.get(key)
        if entry is None:
            return 0, time.time()
        count, window_start = entry
        if time.time() - window_start > self._window_seconds:
            # Window expired — treat as fresh
            del self._data[key]
            return 0, time.time()
        return count, window_start

    async def is_locked(self, email: str) -> bool:
        count, _ = self._get(_email_key(email))
        return count >= self._max_attempts

    async def record_failure(self, email: str) -> int:
        key = _email_key(email)
        count, window_start = self._get(key)
        if count == 0:
            window_start = time.time()
        new_count = count + 1
        self._data[key] = (new_count, window_start)
        return new_count

    async def reset(self, email: str) -> None:
        self._data.pop(_email_key(email), None)


# ---------------------------------------------------------------------------
# Redis implementation
# ---------------------------------------------------------------------------

class RedisLockoutStore:
    """
    Redis-backed lockout store using INCR + EXPIRE.
    Survives restarts, shared across multiple app instances.
    """

    def __init__(
        self,
        redis_client: "redis.asyncio.Redis",  # type: ignore[name-defined]
        max_attempts: int = 5,
        window_seconds: int = 900,
    ) -> None:
        self._redis = redis_client
        self._max_attempts = max_attempts
        self._window_seconds = window_seconds

    def _key(self, email: str) -> str:
        return f"lockout:{_email_key(email)}"

    async def is_locked(self, email: str) -> bool:
        try:
            raw = await self._redis.get(self._key(email))
            if raw is None:
                return False
            return int(raw) >= self._max_attempts
        except Exception:
            logger.warning("Redis lockout is_locked error — fail open", exc_info=True)
            return False  # fail-open: don't block users if Redis is down

    async def record_failure(self, email: str) -> int:
        try:
            key = self._key(email)
            count = await self._redis.incr(key)
            if count == 1:
                # First failure in this window — set TTL
                await self._redis.expire(key, self._window_seconds)
            return int(count)
        except Exception:
            logger.warning("Redis lockout record_failure error", exc_info=True)
            return 0

    async def reset(self, email: str) -> None:
        try:
            await self._redis.delete(self._key(email))
        except Exception:
            logger.warning("Redis lockout reset error", exc_info=True)


# ---------------------------------------------------------------------------
# No-op implementation (tests)
# ---------------------------------------------------------------------------

class NoOpLockoutStore:
    """Always allows — used in tests to prevent inter-test lockout bleed."""

    async def is_locked(self, email: str) -> bool:
        return False

    async def record_failure(self, email: str) -> int:
        return 0

    async def reset(self, email: str) -> None:
        pass


# ---------------------------------------------------------------------------
# Global singleton — set during app startup
# ---------------------------------------------------------------------------

_lockout_manager: Optional[LockoutBackend] = None  # type: ignore[assignment]


def get_lockout_manager() -> LockoutBackend:
    global _lockout_manager
    if _lockout_manager is None:
        # Fallback: create a default in-memory store
        _lockout_manager = InMemoryLockoutStore()
    return _lockout_manager


def set_lockout_manager(manager: LockoutBackend) -> None:
    global _lockout_manager
    _lockout_manager = manager