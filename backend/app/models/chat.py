from datetime import UTC, datetime
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.document import Document


class ChatSession(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_id: int | None = Field(default=None, foreign_key="document.id", index=True)
    context: str = Field(default="")
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    document: Optional["Document"] = Relationship(back_populates="chat_sessions")
    messages: list["ChatMessage"] = Relationship(back_populates="chat_session", cascade_delete=True)


class ChatMessage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", index=True)
    role: str = Field(index=True)  # "user" or "assistant"
    content: str = Field(max_length=32000)  # LLM responses capped; user messages bounded by ChatRequest.message (2000)
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    chat_session: Optional["ChatSession"] = Relationship(back_populates="messages")
