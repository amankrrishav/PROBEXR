from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.document import Document


class SynthesisDocumentLink(SQLModel, table=True):
    synthesis_id: Optional[int] = Field(
        default=None, foreign_key="synthesis.id", primary_key=True
    )
    document_id: Optional[int] = Field(
        default=None, foreign_key="document.id", primary_key=True
    )


class Synthesis(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    summary: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Replaces document_ids: str
    documents: list["Document"] = Relationship(
        back_populates="syntheses", link_model=SynthesisDocumentLink
    )

