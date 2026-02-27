from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from app.db import get_session
from app.schemas.requests import SynthesisRequest
from app.models.synthesis import Synthesis
from app.deps import OptionalUser, DbSession
from app.services.synthesis import synthesize_documents

router = APIRouter(prefix="/synthesis", tags=["synthesis"])

@router.post("/", response_model=Synthesis)
async def create_synthesis(
    request: SynthesisRequest,
    user: OptionalUser,
    session: DbSession
) -> Any:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for synthesis"
        )
    if user.plan != "pro":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Multi-Document Synthesis is a Pro feature"
        )
        
    try:
        synthesis = await synthesize_documents(request.document_ids, user.id, session, request.prompt)
        return synthesis
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to synthesize documents: {str(e)}"
        )
