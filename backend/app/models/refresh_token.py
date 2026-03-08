"""RefreshToken model — opaque refresh tokens with family-based rotation detection."""

from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    """Server-side refresh token for JWT rotation and revocation."""

    id: Optional[int] = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    # Token family — all tokens in a rotation chain share the same token_family.
    # If a revoked token is reused, the entire token_family is revoked.
    token_family: str = Field(index=True)

    is_revoked: bool = Field(default=False)
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.utcnow())
