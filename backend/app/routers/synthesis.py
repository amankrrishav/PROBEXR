import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import SynthesisRequest
from app.models.synthesis import Synthesis
from app.deps import OptionalUser, DbSession
from app.services.synthesis import synthesize_documents

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/synthesis", tags=["synthesis"])

@router.post("/", response_model=Synthesis)
async def create_synthesis(
    request: SynthesisRequest,
    user: OptionalUser,
    session: DbSession
) -> Synthesis:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for synthesis"
        )
        
    try:
        synthesis = await synthesize_documents(request.document_ids, user.id, session, request.prompt)
        return synthesis
    except Exception as e:
        logger.exception("Synthesis failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to synthesize documents: {str(e)}"
        )
