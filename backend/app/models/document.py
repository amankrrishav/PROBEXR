from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Document(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    url: str
    title: str = Field(default="")
    raw_content: str = Field(default="")
    cleaned_content: str = Field(default="")
    created_at: datetime = Field(default_factory=datetime.utcnow)
