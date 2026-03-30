from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.document import Document


class FlashcardSet(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_id: int | None = Field(default=None, foreign_key="document.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    document: Optional["Document"] = Relationship(back_populates="flashcard_sets")
    flashcards: list["Flashcard"] = Relationship(back_populates="flashcard_set", cascade_delete=True)


class Flashcard(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    set_id: int = Field(foreign_key="flashcardset.id", index=True)
    front: str = Field(max_length=2000)  # Anki card front face
    back: str = Field(max_length=2000)  # Anki card back face

    flashcard_set: Optional["FlashcardSet"] = Relationship(back_populates="flashcards")
