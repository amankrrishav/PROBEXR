from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Column, DateTime
from sqlmodel import Field, Index, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from app.models.chat import ChatSession
    from app.models.flashcards import FlashcardSet
    from app.models.synthesis import Synthesis
    from app.models.tts import AudioSummary
    from app.models.user import User

from app.models.synthesis import SynthesisDocumentLink


def _utcnow() -> datetime:
    """Return a timezone-naive UTC timestamp for DB storage."""
    return datetime.now(UTC).replace(tzinfo=None)


class Document(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_document_user_url"),
        Index("ix_document_user_created", "user_id", "created_at"),
    )
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    url: str = Field(max_length=2048)  # Ingest service caps at 2048; model enforces at schema level
    title: str = Field(default="")
    cleaned_content: str = Field(default="")
    created_at: datetime = Field(default_factory=_utcnow)

    # Audit: auto-set on every UPDATE via SQLAlchemy server-side onupdate
    updated_at: datetime | None = Field(
        default=None,
        sa_column=Column(DateTime, nullable=True, onupdate=_utcnow),
    )

    # Soft-delete: when set, the document is considered deleted
    deleted_at: datetime | None = Field(default=None)

    user: Optional["User"] = Relationship(back_populates="documents")
    flashcard_sets: list["FlashcardSet"] = Relationship(back_populates="document", cascade_delete=True)
    syntheses: list["Synthesis"] = Relationship(back_populates="documents", link_model=SynthesisDocumentLink)
    chat_sessions: list["ChatSession"] = Relationship(back_populates="document", cascade_delete=True)
    audio_summaries: list["AudioSummary"] = Relationship(back_populates="document", cascade_delete=True)
