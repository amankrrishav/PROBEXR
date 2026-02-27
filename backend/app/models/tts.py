from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class AudioSummary(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    document_id: Optional[int] = Field(default=None, foreign_key="document.id", index=True)
    audio_url: str
    provider: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
