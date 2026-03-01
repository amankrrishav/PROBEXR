import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import PlainTextResponse
from sqlmodel import select, func

from app.schemas.requests import FlashcardRequest
from app.models.flashcards import FlashcardSet, Flashcard
from app.deps import OptionalUser, CurrentUser, DbSession
from app.services.flashcards import generate_flashcards, export_flashcards

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/flashcards", tags=["flashcards"])


@router.get("/")
async def list_flashcard_sets(
    user: CurrentUser,
    session: DbSession,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """List the current user's flashcard sets, newest first. Paginated."""
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    count_stmt = select(func.count()).select_from(FlashcardSet).where(FlashcardSet.user_id == user.id)
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        select(FlashcardSet)
        .where(FlashcardSet.user_id == user.id)
        .order_by(FlashcardSet.created_at.desc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    sets = list(result.scalars().all())

    # Card count per set
    items = []
    for s in sets:
        card_count_stmt = select(func.count()).select_from(Flashcard).where(Flashcard.set_id == s.id)
        card_count = (await session.execute(card_count_stmt)).scalar() or 0
        items.append({
            "id": s.id,
            "document_id": s.document_id,
            "card_count": card_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "flashcard_sets": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),
    }

@router.post("/", response_model=FlashcardSet)
async def create_flashcards(
    request: FlashcardRequest,
    user: OptionalUser,
    session: DbSession
) -> FlashcardSet:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for flashcards"
        )
        
    try:
        fc_set = await generate_flashcards(request.document_id, user.id, session, request.count)
        return fc_set
    except Exception as e:
        logger.exception("Flashcard generation failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to generate flashcards: {str(e)}"
        )

@router.get("/{set_id}/export", response_class=PlainTextResponse)
async def export_flashcards_csv(
    set_id: int,
    user: OptionalUser,
    session: DbSession
) -> PlainTextResponse:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for flashcards"
        )
        
    try:
        csv_data = await export_flashcards(session, set_id, user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

    
    return PlainTextResponse(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=flashcards_{set_id}.csv"}
    )
