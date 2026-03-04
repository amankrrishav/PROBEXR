from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.flashcards import FlashcardSet
    from app.models.synthesis import Synthesis
    from app.models.chat import ChatSession
    from app.models.tts import AudioSummary

from app.models.synthesis import SynthesisDocumentLink


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    url: str
    title: str = Field(default="")
    cleaned_content: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    user: Optional["User"] = Relationship(back_populates="documents")
    flashcard_sets: list["FlashcardSet"] = Relationship(back_populates="document", cascade_delete=True)
    syntheses: list["Synthesis"] = Relationship(back_populates="documents", link_model=SynthesisDocumentLink)
    chat_sessions: list["ChatSession"] = Relationship(back_populates="document", cascade_delete=True)
    audio_summaries: list["AudioSummary"] = Relationship(back_populates="document", cascade_delete=True)
