from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Any
from app.db import get_session
from app.schemas.requests import TTSRequest
from app.models.tts import AudioSummary
from app.deps import OptionalUser
from app.services.tts import generate_audio_summary

router = APIRouter(prefix="/tts", tags=["tts"])

@router.post("/", response_model=AudioSummary)
async def create_tts(
    request: TTSRequest,
    user: OptionalUser,
    session: Session = Depends(get_session)
) -> Any:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for TTS"
        )
        
    try:
        audio = await generate_audio_summary(request.document_id, user.id, request.provider, session)
        return audio
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
