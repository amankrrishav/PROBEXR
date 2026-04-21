"""
app/services/audit.py — Audit logging service.

Provides fire-and-forget audit event recording. Events are written
to the audit_log table asynchronously so they never block the
request path. If the write fails, the error is logged but the
request continues normally.

Usage in routes:
    from app.services.audit import record_audit_event
    record_audit_event("login_success", request=request, user=user)
"""

import json
import logging
from typing import Any

from fastapi import Request

from app.models.user import User

logger = logging.getLogger(__name__)


def record_audit_event(
    event: str,
    *,
    request: Request | None = None,
    user: User | None = None,
    user_email: str | None = None,
    detail: dict[str, Any] | None = None,
) -> None:
    """Record an audit event in the background.

    This is fire-and-forget: failures are logged but never propagated.
    The event is persisted to the audit_log table via a background task.

    Args:
        event: Event name (e.g. "login_success", "document_delete").
        request: The FastAPI request (for IP and User-Agent extraction).
        user: The authenticated user, if available.
        user_email: Email override (for pre-auth events like login_failure).
        detail: Optional dict of extra context (stored as JSON).
    """
    from app.tasks import fire_and_forget

    # Extract request metadata
    ip_address: str | None = None
    user_agent: str | None = None
    if request is not None:
        ip_address = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        if not ip_address:
            ip_address = str(request.client.host) if request.client else None
        user_agent = (request.headers.get("user-agent") or "")[:512]

    # Resolve email
    email = user_email or (user.email if user else None)
    uid = user.id if user else None
    detail_str = json.dumps(detail, default=str)[:2000] if detail else None

    async def _write() -> None:
        try:
            from app.db import get_session_factory
            from app.models.audit_log import AuditLog

            factory = get_session_factory()
            async with factory() as session:
                entry = AuditLog(
                    user_id=uid,
                    user_email=email,
                    event=event,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    detail=detail_str,
                )
                session.add(entry)
                await session.commit()
        except Exception:
            logger.warning(
                "Failed to write audit event: event=%s user=%s",
                event,
                email,
                exc_info=True,
            )

    fire_and_forget(_write(), name=f"audit:{event}:{email or 'anon'}")
