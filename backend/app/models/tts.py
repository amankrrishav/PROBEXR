from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.document import Document


class AudioSummary(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_id: int | None = Field(default=None, foreign_key="document.id", index=True)
    audio_url: str
    provider: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    document: Optional["Document"] = Relationship(back_populates="audio_summaries")
