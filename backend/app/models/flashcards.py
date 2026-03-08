from datetime import datetime, timezone
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.document import Document


class FlashcardSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_id: Optional[int] = Field(default=None, foreign_key="document.id", index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    document: Optional["Document"] = Relationship(back_populates="flashcard_sets")
    flashcards: list["Flashcard"] = Relationship(back_populates="flashcard_set", cascade_delete=True)

class Flashcard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    set_id: int = Field(foreign_key="flashcardset.id", index=True)
    front: str
    back: str

    flashcard_set: Optional["FlashcardSet"] = Relationship(back_populates="flashcards")
