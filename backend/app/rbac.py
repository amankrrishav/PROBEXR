"""
app/rbac.py — Role-Based Access Control (RBAC) tier enforcement.

Defines plan-based usage limits and provides FastAPI dependencies
that enforce them. Routes use these dependencies to gate features
behind plan tiers.

Plan tiers:
  free   — generous defaults for individual users
  pro    — higher limits for power users
  team   — highest limits for team/org accounts

Usage tracking:
  User.usage_today + User.usage_reset_at track daily LLM calls.
  The counter resets automatically when a new day is detected.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime

from fastapi import Depends, HTTPException, status

from app.models.user import User
from app.services.auth import get_current_user, get_optional_user

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Plan definitions
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PlanLimits:
    """Usage limits for a plan tier."""

    summarizations_per_day: int
    documents_max: int
    synthesis_max_docs: int
    chat_sessions_per_day: int
    flashcard_sets_per_day: int


# Configurable limits per plan — easy to adjust without code changes
PLAN_LIMITS: dict[str, PlanLimits] = {
    "free": PlanLimits(
        summarizations_per_day=25,
        documents_max=50,
        synthesis_max_docs=5,
        chat_sessions_per_day=20,
        flashcard_sets_per_day=10,
    ),
    "pro": PlanLimits(
        summarizations_per_day=200,
        documents_max=500,
        synthesis_max_docs=10,
        chat_sessions_per_day=100,
        flashcard_sets_per_day=50,
    ),
    "team": PlanLimits(
        summarizations_per_day=1000,
        documents_max=2000,
        synthesis_max_docs=10,
        chat_sessions_per_day=500,
        flashcard_sets_per_day=200,
    ),
}


def get_plan_limits(plan: str) -> PlanLimits:
    """Get limits for a plan, defaulting to free if unknown."""
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"])


# ---------------------------------------------------------------------------
# Usage tracking helpers
# ---------------------------------------------------------------------------


def _is_new_day(reset_at: datetime | None) -> bool:
    """Check if the usage counter should be reset (new UTC day)."""
    if reset_at is None:
        return True
    now = datetime.now(UTC).replace(tzinfo=None)
    return now.date() > reset_at.date()


async def _check_and_increment_usage(user: User) -> None:
    """Check daily usage limit and increment counter.

    Resets the counter if a new UTC day has started.
    Raises HTTPException 429 if the daily limit is exceeded.

    Note: The caller must commit the session after this function
    to persist the updated usage count.
    """
    limits = get_plan_limits(user.plan)

    # Reset counter on new day
    if _is_new_day(user.usage_reset_at):
        user.usage_today = 0
        user.usage_reset_at = datetime.now(UTC).replace(tzinfo=None)

    if user.usage_today >= limits.summarizations_per_day:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Daily limit reached ({limits.summarizations_per_day} "
                f"summarizations/day on the {user.plan} plan). "
                "Upgrade your plan or try again tomorrow."
            ),
        )

    user.usage_today += 1


# ---------------------------------------------------------------------------
# FastAPI dependencies — use in route signatures
# ---------------------------------------------------------------------------


async def enforce_usage_limit(
    user: User = Depends(get_current_user),
) -> User:
    """Dependency that checks and increments daily LLM usage.

    Use on routes that REQUIRE auth and consume an LLM call.
    """
    await _check_and_increment_usage(user)
    return user


async def enforce_optional_usage_limit(
    user: User | None = Depends(get_optional_user),
) -> User | None:
    """Dependency for routes that allow unauthenticated access (extractive fallback)
    but enforce usage limits when a user IS logged in.

    Flow:
      - Unauthenticated → returns None (route uses extractive fallback, no limit)
      - Authenticated + unverified → returns None (same as above)
      - Authenticated + verified → checks usage limit, increments, returns user
    """
    if user is None or not user.is_verified:
        return user
    await _check_and_increment_usage(user)
    return user
