"""UsedToken — tracks consumed one-time JWTs (magic links, email verification, etc.)

Design:
  - Keyed by `jti` (JWT ID claim) — a UUID embedded in the token at creation.
  - On first use: INSERT the jti. Unique constraint prevents double-insertion.
  - On second use: jti already exists → reject.
  - A background GC job (or periodic alembic cleanup) removes expired rows.
    Until then, rows are cheap — only magic link + verification tokens land here.
"""
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class UsedToken(SQLModel, table=True):
    """Tracks consumed one-time JWT tokens to prevent replay attacks."""

    __tablename__ = "used_token"

    id: Optional[int] = Field(default=None, primary_key=True)

    # JWT ID — the `jti` claim embedded in the token at creation.
    # Unique constraint is the enforcement mechanism: second INSERT fails.
    jti: str = Field(index=True, unique=True)

    # Token type for auditing ("magic_link", "email_verification")
    token_type: str = Field(index=True)

    # When the original JWT expires — used for garbage collection
    expires_at: datetime = Field(index=True)  # Indexed — token GC WHERE expires_at < now scans this hourly

    # When this record was created
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )