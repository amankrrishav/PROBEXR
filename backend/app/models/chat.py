from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class ChatSession(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_id: Optional[int] = Field(default=None, foreign_key="document.id", index=True)
    context: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatMessage(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    session_id: int = Field(foreign_key="chatsession.id", index=True)
    role: str = Field(index=True)  # "user" or "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
