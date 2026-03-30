"""RefreshToken model — opaque refresh tokens with family-based rotation detection."""

from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


class RefreshToken(SQLModel, table=True):
    """Server-side refresh token for JWT rotation and revocation."""

    id: int | None = Field(default=None, primary_key=True)
    token: str = Field(index=True, unique=True)
    user_id: int = Field(foreign_key="user.id", index=True)

    # Token family — all tokens in a rotation chain share the same token_family.
    # If a revoked token is reused, the entire token_family is revoked.
    token_family: str = Field(index=True)

    is_revoked: bool = Field(default=False)
    expires_at: datetime = Field(index=True)  # Indexed — token_gc WHERE expires_at < now scans this hourly
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
