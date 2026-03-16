import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import TTSRequest
from app.deps import OptionalVerifiedUser, DbSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post("/")
async def create_tts(
    request: TTSRequest,
    user: OptionalVerifiedUser,
    session: DbSession
):
    """TTS is not yet implemented. Returns 503 until a real provider is integrated."""
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Text-to-Speech is coming soon. This feature is not yet available.",
    )


@router.get("/status")
async def tts_status():
    """Check if TTS is available. Currently a stub — returns unavailable."""
    return {
        "available": False,
        "message": "Text-to-Speech is coming soon. Stay tuned!",
    }