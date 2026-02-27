from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db import get_session
from app.schemas.requests import URLRequest, TextIngestRequest
from app.models.document import Document
from app.deps import OptionalUser, DbSession
from app.services.ingest import fetch_and_clean_url

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/url", response_model=Document)
async def ingest_url(
    request: URLRequest,
    user: OptionalUser,
    session: DbSession
) -> Any:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to ingest URLs"
        )
    try:
        doc = await fetch_and_clean_url(request.url, user.id, session)
        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to ingest URL: {str(e)}"
        )

@router.post("/text", response_model=Document)
async def ingest_text(
    request: TextIngestRequest,
    user: OptionalUser,
    session: DbSession
) -> Any:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required to save documents"
        )
    try:
        doc = Document(
            user_id=user.id,
            url="pasted_text",
            title=request.title[:200],
            raw_content=request.text,
            cleaned_content=request.text
        )
        session.add(doc)
        session.commit()
        session.refresh(doc)
        return doc
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to save text document: {str(e)}"
        )
