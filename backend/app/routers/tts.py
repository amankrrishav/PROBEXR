import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import TTSRequest
from app.deps import OptionalVerifiedUser, DbSession
from app.config import get_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tts", tags=["tts"])


@router.post("/")
async def create_tts(
    request: TTSRequest,
    user: OptionalVerifiedUser,
    session: DbSession,
):
    """Generate an audio summary for a document.

    Requires TTS_ENABLED=true in environment and an authenticated user.
    Returns 503 until the feature flag is enabled.
    """
    cfg = get_config()
    if not cfg.tts_enabled:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Text-to-Speech is not yet available. "
                "Set TTS_ENABLED=true to activate when provider keys are configured."
            ),
        )

    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for TTS",
        )

    from app.services.tts import generate_audio_summary
    try:
        audio = await generate_audio_summary(
            document_id=request.document_id,
            user_id=user.id,
            provider=request.provider,
            session=session,
        )
        return audio
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.exception("TTS generation failed for user_id=%s", user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"TTS generation failed: {str(e)}",
        )


@router.get("/status")
async def tts_status():
    """Check if TTS is available."""
    cfg = get_config()
    available = cfg.tts_enabled
    return {
        "available": available,
        "message": "TTS is active." if available else "Text-to-Speech is not yet enabled.",
    }