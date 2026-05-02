"""
AuditLog model — persistent, queryable record of security-relevant events.

Complements Prometheus counters (which are ephemeral) with a durable
audit trail stored in the primary database. Useful for:
  - Security incident investigation
  - Compliance reporting (GDPR, SOC 2)
  - User activity review

Events are append-only. Rows should never be updated or deleted
(enforced by policy, not DB constraint, to keep the schema simple).
"""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class AuditLog(SQLModel, table=True):
    """Immutable audit event record."""

    __tablename__ = "audit_log"

    id: int | None = Field(default=None, primary_key=True)

    # When the event occurred
    timestamp: datetime = Field(default_factory=_utcnow, index=True)

    # Who triggered it (nullable for unauthenticated events like failed login)
    user_id: int | None = Field(default=None, index=True)
    user_email: str | None = Field(default=None, max_length=320)

    # What happened
    event: str = Field(index=True, max_length=100)
    # e.g. "login_success", "login_failure", "logout", "password_reset",
    #      "account_locked", "token_refresh", "document_delete",
    #      "social_login", "email_verified", "profile_update"

    # Where it came from
    ip_address: str | None = Field(default=None, max_length=45)  # IPv6 max
    user_agent: str | None = Field(default=None, max_length=512)

    # Additional structured context (JSON string)
    detail: str | None = Field(default=None, max_length=2000)
