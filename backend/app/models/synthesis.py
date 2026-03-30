from datetime import UTC, datetime
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from app.models.document import Document


class SynthesisDocumentLink(SQLModel, table=True):
    synthesis_id: int | None = Field(default=None, foreign_key="synthesis.id", primary_key=True)
    document_id: int | None = Field(default=None, foreign_key="document.id", primary_key=True)


class Synthesis(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    summary: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(tzinfo=None))

    documents: list["Document"] = Relationship(back_populates="syntheses", link_model=SynthesisDocumentLink)
