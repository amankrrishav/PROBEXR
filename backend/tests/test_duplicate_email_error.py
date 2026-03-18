"""
tests/test_duplicate_email_error.py — A-02: DuplicateEmailError domain exception

Verifies that register_user raises a typed DuplicateEmailError (not a bare
ValueError) when the email is already registered, making future callers
able to catch it specifically.
"""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_raises_duplicate_email_error(registered_user: dict):
    """Calling register_user with an existing email raises DuplicateEmailError."""
    from app.services.auth import register_user, DuplicateEmailError
    from tests.conftest import _TestSessionLocal

    async with _TestSessionLocal() as session:
        with pytest.raises(DuplicateEmailError) as exc_info:
            await register_user(session, registered_user["email"], "SomePassword123!")

    assert registered_user["email"] in str(exc_info.value)


@pytest.mark.asyncio
async def test_duplicate_email_error_is_value_error_subclass(registered_user: dict):
    """DuplicateEmailError must subclass ValueError for backward compatibility."""
    from app.services.auth import DuplicateEmailError

    exc = DuplicateEmailError("test@example.com")
    assert isinstance(exc, ValueError)
    assert "test@example.com" in str(exc)


def test_duplicate_email_error_stores_email():
    """DuplicateEmailError must expose the email attribute."""
    from app.services.auth import DuplicateEmailError

    exc = DuplicateEmailError("user@example.com")
    assert exc.email == "user@example.com"


def test_duplicate_email_error_importable_from_router():
    """DuplicateEmailError must be importable from the auth router module."""
    from app.routers.auth import DuplicateEmailError
    assert DuplicateEmailError is not None