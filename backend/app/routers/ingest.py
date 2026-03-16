import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import URLRequest, TextIngestRequest
from app.models.document import Document
from app.deps import OptionalVerifiedUser, DbSession
from app.services.ingest import fetch_and_clean_url, ingest_text_document

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/url", response_model=Document)
async def ingest_url(
    request: URLRequest,
    user: OptionalVerifiedUser,
    session: DbSession
) -> Document:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to ingest URLs"
        )
    try:
        doc = await fetch_and_clean_url(str(request.url), user.id, session)
        return doc
    except Exception as e:
        logger.exception("URL ingestion failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest URL: {str(e)}"
        )

@router.post("/text", response_model=Document)
async def ingest_text(
    request: TextIngestRequest,
    user: OptionalVerifiedUser,
    session: DbSession
) -> Document:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to save documents"
        )
    try:
        doc = await ingest_text_document(user.id, request.text, request.title, session)
        return doc
    except Exception as e:
        logger.exception("Text ingestion failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save text document: {str(e)}"
        )