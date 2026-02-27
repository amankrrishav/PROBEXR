from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Synthesis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_ids: str = Field(default="")  # Comma separated list of document IDs
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
