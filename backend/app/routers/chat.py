from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session
from typing import Any
from app.db import get_session
from app.schemas.requests import ChatRequest
from app.models.chat import ChatMessage
from app.deps import OptionalUser
from app.services.chat import process_chat_message

router = APIRouter(prefix="/chat", tags=["chat"])

@router.post("/", response_model=ChatMessage)
async def chat_endpoint(
    request: ChatRequest,
    user: OptionalUser,
    session: Session = Depends(get_session)
) -> Any:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for chat"
        )
        
    try:
        reply = await process_chat_message(
            document_id=request.document_id,
            user_id=user.id,
            message=request.message,
            session=session,
            session_id=request.session_id
        )
        return reply
    except ValueError as ve:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(ve)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Chat failed: {str(e)}"
        )
