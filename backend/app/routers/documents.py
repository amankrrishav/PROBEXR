"""
Document management router — list and delete user's ingested documents.
"""
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, func

from app.deps import CurrentUser, DbSession
from app.models.document import Document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
async def list_documents(
    user: CurrentUser,
    session: DbSession,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """
    List the current user's ingested documents, newest first.
    Paginated: ?page=1&per_page=20
    """
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    # Total count
    count_stmt = select(func.count()).select_from(Document).where(Document.user_id == user.id)
    total = (await session.execute(count_stmt)).scalar() or 0

    # Fetch page
    stmt = (
        select(Document)
        .where(Document.user_id == user.id)
        .order_by(Document.created_at.desc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    docs = list(result.scalars().all())

    return {
        "documents": [
            {
                "id": doc.id,
                "title": doc.title,
                "url": doc.url,
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "word_count": len(doc.cleaned_content.split()) if doc.cleaned_content else 0,
            }
            for doc in docs
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),  # ceil division
    }


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    user: CurrentUser,
    session: DbSession,
) -> None:
    """Delete a document owned by the current user."""
    doc = await session.get(Document, document_id)
    if not doc or doc.user_id != user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or unauthorized",
        )

    await session.delete(doc)
    await session.commit()
    logger.info("Document deleted", extra={"document_id": document_id, "user_id": user.id})
