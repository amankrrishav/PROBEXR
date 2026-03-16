"""
Analytics router — reading dashboard metrics.
"""
import logging

from fastapi import APIRouter

from app.deps import VerifiedUser, DbSession
from app.services.analytics import get_dashboard

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def dashboard(
    user: VerifiedUser,
    session: DbSession,
) -> dict:
    """Return aggregated reading analytics for the authenticated user."""
    assert user.id is not None
    return await get_dashboard(user.id, session)