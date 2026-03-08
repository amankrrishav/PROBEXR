from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.document import Document


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str

    # Auth / lifecycle
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_login_at: Optional[datetime] = None
    signup_source: Optional[str] = Field(default=None, index=True)

    # Usage / Plan
    plan: str = Field(default="free", index=True)
    usage_today: int = Field(default=0)
    usage_reset_at: Optional[datetime] = None

    documents: list["Document"] = Relationship(back_populates="user", cascade_delete=True)