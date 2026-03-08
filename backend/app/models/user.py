from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.document import Document


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: Optional[str] = Field(default=None)  # Optional for social-only users

    # Profile
    full_name: Optional[str] = Field(default=None)
    avatar_url: Optional[str] = Field(default=None)

    # Auth / lifecycle
    is_active: bool = True
    is_verified: bool = Field(default=False)
    created_at: Optional[datetime] = Field(default=None)
    last_login_at: Optional[datetime] = None
    signup_source: Optional[str] = Field(default=None, index=True)

    # Social IDs
    google_id: Optional[str] = Field(default=None, index=True, unique=True)
    github_id: Optional[str] = Field(default=None, index=True, unique=True)

    # Usage / Plan
    plan: str = Field(default="free", index=True)
    usage_today: int = Field(default=0)
    usage_reset_at: Optional[datetime] = None

    documents: list["Document"] = Relationship(back_populates="user", cascade_delete=True)