"""
Document management router — list and delete user's ingested documents.

ETag support: GET /documents/ returns an ETag header based on the response
content hash. Clients sending If-None-Match with the same ETag receive a
304 Not Modified, saving bandwidth and improving perceived performance.
"""

import hashlib
import json
import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse
from sqlmodel import func, select

from app.deps import DbSession, VerifiedUser
from app.models.document import Document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("/")
async def list_documents(
    request: Request,
    user: VerifiedUser,
    session: DbSession,
    page: int = 1,
    per_page: int = 20,
) -> JSONResponse:
    """
    List the current user's ingested documents, newest first.
    Paginated: ?page=1&per_page=20

    Supports ETag / If-None-Match for conditional requests.
    """
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    # Total count
    count_stmt = (
        select(func.count())
        .select_from(Document)
        .where(Document.user_id == user.id, Document.deleted_at.is_(None))  # type: ignore[union-attr]
    )
    total = (await session.execute(count_stmt)).scalar() or 0

    # Fetch page
    stmt = (
        select(Document)
        .where(Document.user_id == user.id, Document.deleted_at.is_(None))  # type: ignore[union-attr]
        .order_by(Document.created_at.desc())  # type: ignore[attr-defined]
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    docs = list(result.scalars().all())

    body: dict[str, Any] = {
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

    # ETag: hash the JSON response content
    body_bytes = json.dumps(body, sort_keys=True, default=str).encode()
    etag = f'"{hashlib.sha256(body_bytes).hexdigest()[:16]}"'

    # 304 Not Modified: if client sent a matching If-None-Match header
    if_none_match = request.headers.get("if-none-match")
    if if_none_match and if_none_match == etag:
        return JSONResponse(status_code=304, content=None, headers={"ETag": etag})

    return JSONResponse(content=body, headers={"ETag": etag})


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: int,
    user: VerifiedUser,
    session: DbSession,
) -> None:
    """Delete a document owned by the current user."""
    doc = await session.get(Document, document_id)
    if not doc or doc.user_id != user.id or doc.deleted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found or unauthorized",
        )

    # Soft-delete: mark as deleted instead of removing from DB
    from datetime import UTC, datetime

    doc.deleted_at = datetime.now(UTC).replace(tzinfo=None)
    session.add(doc)
    await session.commit()
    logger.info("Document soft-deleted", extra={"document_id": document_id, "user_id": user.id})
