from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.flashcards import FlashcardSet
    from app.models.synthesis import Synthesis
    from app.models.chat import ChatSession
    from app.models.tts import AudioSummary

from app.models.synthesis import SynthesisDocumentLink


class Document(SQLModel, table=True):
    __table_args__ = (UniqueConstraint("user_id", "url", name="uq_document_user_url"),)
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    url: str = Field(max_length=2048)  # Ingest service caps at 2048; model enforces at schema level
    title: str = Field(default="")
    cleaned_content: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    user: Optional["User"] = Relationship(back_populates="documents")
    flashcard_sets: list["FlashcardSet"] = Relationship(back_populates="document", cascade_delete=True)
    syntheses: list["Synthesis"] = Relationship(back_populates="documents", link_model=SynthesisDocumentLink)
    chat_sessions: list["ChatSession"] = Relationship(back_populates="document", cascade_delete=True)
    audio_summaries: list["AudioSummary"] = Relationship(back_populates="document", cascade_delete=True)