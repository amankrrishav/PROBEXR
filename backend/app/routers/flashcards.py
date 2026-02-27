from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlmodel import Session, select
from typing import Any
from app.db import get_session
from app.schemas.requests import FlashcardRequest
from app.models.flashcards import FlashcardSet, Flashcard
from app.deps import OptionalUser, DbSession
from app.services.flashcards import generate_flashcards, generate_csv_export, export_flashcards

router = APIRouter(prefix="/flashcards", tags=["flashcards"])

@router.post("/", response_model=FlashcardSet)
async def create_flashcards(
    request: FlashcardRequest,
    user: OptionalUser,
    session: DbSession
) -> Any:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for flashcards"
        )
        
    try:
        fc_set = await generate_flashcards(request.document_id, user.id, session, request.count)
        return fc_set
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate flashcards: {str(e)}"
        )

@router.get("/{set_id}/export", response_class=PlainTextResponse)
def export_flashcards_csv(
    set_id: int,
    user: OptionalUser,
    session: DbSession
) -> Any:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for flashcards"
        )
        
    try:
        csv_data = export_flashcards(session, set_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=flashcards_{set_id}.csv"}
    )
