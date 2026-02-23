"""
Lightweight subscription and usage tracking.

Current behavior:
- Single plan: "free" (default) and "pro" (future, manually assigned).
- Free users get full-quality summaries up to FREE_DAILY_LIMIT per day.
- After the limit, summaries are still allowed but generated at reduced quality.

This module is intentionally provider-agnostic so a real billing provider
can be plugged in later without touching routers.
"""
from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Literal, Tuple

from sqlmodel import Session

from app.config import get_config
from app.models.user import User

Quality = Literal["full", "reduced"]


def _get_logger() -> logging.Logger:
    logger = logging.getLogger("subscription")
    if logger.handlers:
        return logger

    logger.setLevel(logging.INFO)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch_formatter = logging.Formatter(
        "[%(asctime)s] [subscription] %(levelname)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    ch.setFormatter(ch_formatter)
    logger.addHandler(ch)

    # File handler (best-effort; fine if it fails on some platforms)
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logs_dir = os.path.join(base_dir, "logs")
        os.makedirs(logs_dir, exist_ok=True)
        fh = logging.FileHandler(os.path.join(logs_dir, "subscription.log"))
        fh.setLevel(logging.INFO)
        fh.setFormatter(ch_formatter)
        logger.addHandler(fh)
    except Exception:
        # Logging to file is best-effort; console logs are enough for most deployments.
        pass

    return logger


logger = _get_logger()


def _today_utc() -> datetime:
    # Normalize to midnight UTC for daily limits
    now = datetime.now(timezone.utc)
    return datetime(year=now.year, month=now.month, day=now.day, tzinfo=timezone.utc)


def reset_usage_if_needed(user: User) -> None:
    """
    Reset usage_today if usage_reset_at is before today (UTC).
    """
    today = _today_utc()
    if user.usage_reset_at is None or user.usage_reset_at < today:
        user.usage_today = 0
        user.usage_reset_at = today


def evaluate_summary_quality(user: User | None, session: Session) -> Tuple[Quality, int, int]:
    """
    Determine the quality for the next summary and update usage counters.

    Returns: (quality, usage_today, limit)
    """
    cfg = get_config()
    limit = cfg.free_daily_limit

    # Anonymous: treat as always full quality for now; frontend already gates on auth.
    if user is None:
        return "full", 0, limit

    reset_usage_if_needed(user)

    # Pro users: always full quality, no local limit.
    if user.plan == "pro":
        session.add(user)
        session.commit()
        logger.info("user_id=%s plan=pro quality=full usage_today=%s limit=unlimited", user.id, user.usage_today)
        return "full", user.usage_today, limit

    # Free users: full quality up to limit, then reduced.
    if user.usage_today < limit:
        user.usage_today += 1
        quality: Quality = "full"
    else:
        quality = "reduced"
        # Optionally still increment for analytics
        user.usage_today += 1

    session.add(user)
    session.commit()

    logger.info(
        "user_id=%s plan=%s quality=%s usage_today=%s limit=%s",
        user.id,
        user.plan,
        quality,
        user.usage_today,
        limit,
    )

    return quality, user.usage_today, limit


def is_pro(user: User | None) -> bool:
    return bool(user and user.plan == "pro")

