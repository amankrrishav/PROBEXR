"""
Refresh token garbage collection — periodic cleanup of expired and revoked tokens.

Usage: call `start_token_gc(engine)` during app lifespan startup.
It spawns an asyncio background task that runs every hour.
"""

import asyncio
import logging
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel import col
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.refresh_token import RefreshToken
from app.models.used_token import UsedToken

logger = logging.getLogger(__name__)

GC_INTERVAL_SECONDS = 60 * 60  # 1 hour


async def _cleanup_tokens(session_factory: async_sessionmaker[AsyncSession]) -> int:
    """Delete expired/revoked refresh tokens and expired used tokens. Returns total count deleted."""
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    async with session_factory() as session:
        # Purge expired / revoked refresh tokens
        refresh_stmt = delete(RefreshToken).where(
            (col(RefreshToken.expires_at) < now) | (col(RefreshToken.is_revoked) == True)  # noqa: E712
        )
        refresh_result = await session.execute(refresh_stmt)

        # Purge expired used tokens (magic links, email verification)
        used_stmt = delete(UsedToken).where(col(UsedToken.expires_at) < now)
        used_result = await session.execute(used_stmt)

        await session.commit()
        return (refresh_result.rowcount or 0) + (used_result.rowcount or 0)  # type: ignore[return-value]


async def _gc_loop(session_factory: async_sessionmaker[AsyncSession]) -> None:
    """Run token cleanup on a fixed interval. Swallows errors to avoid crash."""
    while True:
        try:
            count = await _cleanup_tokens(session_factory)
            if count:
                logger.info("Token GC: purged %d expired/revoked refresh tokens", count)
        except asyncio.CancelledError:
            logger.info("Token GC: task cancelled, shutting down")
            raise
        except Exception:
            logger.exception("Token GC: error during cleanup")
        await asyncio.sleep(GC_INTERVAL_SECONDS)


_gc_task: asyncio.Task | None = None


def start_token_gc(engine: AsyncEngine) -> None:
    """Start the background GC task. Safe to call multiple times (idempotent)."""
    global _gc_task
    if _gc_task is not None:
        return
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    _gc_task = asyncio.create_task(_gc_loop(session_factory))
    logger.info("Token GC background task started (interval=%ds)", GC_INTERVAL_SECONDS)


def stop_token_gc() -> None:
    """Cancel the background GC task (call during shutdown)."""
    global _gc_task
    if _gc_task is not None:
        _gc_task.cancel()
        _gc_task = None
        logger.info("Token GC background task stopped")
