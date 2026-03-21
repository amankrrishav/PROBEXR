"""
Dependencies for routes — auth, rate limits, etc.
Route handlers should import these aliases instead of touching auth internals.
"""
from typing import Annotated, Optional

from fastapi import Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import get_session
from app.models.user import User
from app.services.auth import get_current_user, get_optional_user

# --- Base Dependency ---
DbSession = Annotated[AsyncSession, Depends(get_session)]

# --- Auth Dependencies ---
CurrentUser = Annotated[User, Depends(get_current_user)]
OptionalUser = Annotated[Optional[User], Depends(get_optional_user)]


async def _get_verified_user(user: User = Depends(get_current_user)) -> User:
    """Requires a logged-in AND email-verified user."""
    if not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified. Please check your inbox and verify your email address.",
        )
    return user


async def _get_optional_verified_user(user: Optional[User] = Depends(get_optional_user)) -> Optional[User]:
    """Returns verified user if logged in and verified, otherwise None."""
    if user is not None and not user.is_verified:
        return None
    return user


VerifiedUser = Annotated[User, Depends(_get_verified_user)]
OptionalVerifiedUser = Annotated[Optional[User], Depends(_get_optional_verified_user)]


# --- Pagination ---
class PaginationParams:
    """Reusable pagination dependency. Max 100 items per page."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0, description="Number of items to skip"),
        limit: int = Query(default=50, ge=1, le=100, description="Max items to return (1-100)"),
    ):
        self.skip = skip
        self.limit = limit


Pagination = Annotated[PaginationParams, Depends()]