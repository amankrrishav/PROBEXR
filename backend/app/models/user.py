from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.document import Document


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str | None = Field(default=None)  # Optional for social-only users

    # Profile
    full_name: str | None = Field(default=None, max_length=200)
    avatar_url: str | None = Field(default=None, max_length=2048)

    # Auth / lifecycle
    is_active: bool = True
    is_verified: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))
    last_login_at: datetime | None = None
    signup_source: str | None = Field(default=None, index=True)

    # Social IDs
    google_id: str | None = Field(default=None, index=True, unique=True)
    github_id: str | None = Field(default=None, index=True, unique=True)

    # Usage / Plan
    plan: str = Field(default="free", index=True)
    usage_today: int = Field(default=0)
    usage_reset_at: datetime | None = None

    documents: list["Document"] = Relationship(back_populates="user", cascade_delete=True)
