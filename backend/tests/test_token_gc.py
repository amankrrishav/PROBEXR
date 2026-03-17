"""
Token GC tests — CancelledError propagation, RefreshToken + UsedToken cleanup.
"""
import asyncio
from datetime import datetime, timezone, timedelta

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlmodel import select

from app.models.refresh_token import RefreshToken
from app.models.used_token import UsedToken
from app.services.token_gc import _cleanup_tokens, _gc_loop


# Re-use the test engine from conftest
from tests.conftest import _test_engine

_TestSession = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


# ---- CancelledError propagation ----

@pytest.mark.asyncio
async def test_gc_loop_propagates_cancelled_error():
    """CancelledError must propagate out of _gc_loop for clean shutdown."""
    task = asyncio.create_task(_gc_loop(_TestSession))
    # Give the loop a moment to start (it will try cleanup then sleep)
    await asyncio.sleep(0.05)
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task


# ---- UsedToken cleanup ----

@pytest.mark.asyncio
async def test_cleanup_purges_expired_used_tokens():
    """Expired UsedToken rows must be deleted by _cleanup_tokens."""
    async with _TestSession() as session:
        # Insert an already-expired UsedToken
        expired = UsedToken(
            jti="expired-jti-001",
            token_type="magic_link",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
        )
        # Insert a still-valid UsedToken
        valid = UsedToken(
            jti="valid-jti-002",
            token_type="email_verification",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
        )
        session.add(expired)
        session.add(valid)
        await session.commit()

    # Run cleanup
    count = await _cleanup_tokens(_TestSession)
    assert count >= 1

    # Verify: expired token is gone, valid token remains
    async with _TestSession() as session:
        remaining = (await session.execute(select(UsedToken))).scalars().all()
        jtis = [t.jti for t in remaining]
        assert "expired-jti-001" not in jtis
        assert "valid-jti-002" in jtis


# ---- RefreshToken cleanup still works ----

@pytest.mark.asyncio
async def test_cleanup_purges_expired_refresh_tokens():
    """Expired RefreshToken rows must still be deleted after the UsedToken addition."""
    async with _TestSession() as session:
        expired_rt = RefreshToken(
            user_id=1,
            token="expired-token-001",
            token_family="family-001",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1),
            is_revoked=False,
        )
        valid_rt = RefreshToken(
            user_id=1,
            token="valid-token-002",
            token_family="family-002",
            expires_at=datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(hours=1),
            is_revoked=False,
        )
        session.add(expired_rt)
        session.add(valid_rt)
        await session.commit()

    count = await _cleanup_tokens(_TestSession)
    assert count >= 1

    async with _TestSession() as session:
        remaining = (await session.execute(select(RefreshToken))).scalars().all()
        tokens = [t.token for t in remaining]
        assert "expired-token-001" not in tokens
        assert "valid-token-002" in tokens
