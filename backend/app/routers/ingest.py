from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db import get_session
from app.schemas.requests import URLRequest
from app.models.document import Document
from app.deps import OptionalUser
from app.services.ingest import fetch_and_clean_url

router = APIRouter(prefix="/ingest", tags=["ingest"])

@router.post("/url", response_model=Document)
async def ingest_url(
    request: URLRequest,
    user: OptionalUser,
    session: Session = Depends(get_session)
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
