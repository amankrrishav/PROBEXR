"""API key model — programmatic access for integrations and CI/CD pipelines."""
import secrets
from datetime import UTC, datetime

from sqlmodel import Field, SQLModel


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


class APIKey(SQLModel, table=True):
    """Persistent API key for programmatic (non-browser) access.

    Keys are stored as SHA-256 hashes — the plaintext is shown only once
    at creation time and never stored.
    """

    __tablename__ = "api_key"

    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    name: str = Field(max_length=100)  # human label, e.g. "CI pipeline"
    key_hash: str = Field(unique=True, index=True)  # SHA-256 of the raw key
    prefix: str = Field(max_length=8)  # first 8 chars for identification
    created_at: datetime = Field(default_factory=_utcnow)
    last_used_at: datetime | None = None
    is_active: bool = True

    @staticmethod
    def generate_key() -> str:
        """Generate a new API key with probexr_ prefix."""
        return f"probexr_{secrets.token_urlsafe(32)}"
