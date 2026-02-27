from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class FlashcardSet(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_id: Optional[int] = Field(default=None, foreign_key="document.id", index=True)
    content: str = Field(default="") # JSON or text representing the overview
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Flashcard(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    set_id: int = Field(foreign_key="flashcardset.id", index=True)
    front: str
    back: str
