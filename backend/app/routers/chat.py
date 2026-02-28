import logging

from fastapi import APIRouter, HTTPException, status

from app.schemas.requests import ChatRequest
from app.deps import OptionalUser, DbSession
from app.services.chat import process_chat_message, ChatReply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/")
async def chat_endpoint(
    request: ChatRequest,
    user: OptionalUser,
    session: DbSession,
) -> ChatReply:
    if not user or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required for chat",
        )

    try:
        reply = await process_chat_message(
            document_id=request.document_id,
            user_id=user.id,
            message=request.message,
            session=session,
            session_id=request.session_id,
        )
        return reply
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(ve))
    except Exception as e:
        logger.exception("Chat failed for user_id=%s", user.id)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Chat failed: {str(e)}")
