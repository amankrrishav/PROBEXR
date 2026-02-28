import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import TTSRequest
from app.models.tts import AudioSummary
from app.deps import OptionalUser, DbSession
from app.services.tts import generate_audio_summary

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post("/", response_model=AudioSummary)
async def create_tts(
    request: TTSRequest,
    user: OptionalUser,
    session: DbSession
) -> AudioSummary:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for TTS"
        )
        
    try:
        audio = await generate_audio_summary(request.document_id, user.id, request.provider, session)
        return audio
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.exception("TTS generation failed for user_id=%s", user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
