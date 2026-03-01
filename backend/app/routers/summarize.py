from fastapi import APIRouter, HTTPException

from app.deps import OptionalUser, DbSession
from app.schemas import TextRequest
from app.services.summarizer import process_summarize

router = APIRouter(prefix="", tags=["summarize"])


from typing import Any

@router.post("/summarize")
async def summarize_endpoint(
    request: TextRequest,
    user: OptionalUser,
    session: DbSession,
) -> dict[str, Any]:
    try:
        return await process_summarize(request.text, user, session)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
