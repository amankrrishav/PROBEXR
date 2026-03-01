import logging
from typing import Any

from fastapi import APIRouter, HTTPException, status
from sqlmodel import select, func

from app.schemas.requests import ChatRequest
from app.deps import OptionalUser, CurrentUser, DbSession
from app.models.chat import ChatSession, ChatMessage
from app.models.document import Document
from app.services.chat import process_chat_message, ChatReply

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.get("/sessions")
async def list_chat_sessions(
    user: CurrentUser,
    session: DbSession,
    page: int = 1,
    per_page: int = 20,
) -> dict[str, Any]:
    """List the current user's chat sessions, newest first. Paginated."""
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    offset = (page - 1) * per_page

    count_stmt = select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user.id)
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user.id)
        .order_by(ChatSession.created_at.desc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    sessions_list = list(result.scalars().all())

    items = []
    for s in sessions_list:
        msg_count_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == s.id)
        msg_count = (await session.execute(msg_count_stmt)).scalar() or 0
        # Get document title
        doc = await session.get(Document, s.document_id)
        items.append({
            "id": s.id,
            "document_id": s.document_id,
            "document_title": doc.title if doc else None,
            "message_count": msg_count,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        })

    return {
        "sessions": items,
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),
    }


@router.get("/sessions/{session_id}/messages")
async def list_session_messages(
    session_id: int,
    user: CurrentUser,
    session: DbSession,
    page: int = 1,
    per_page: int = 50,
) -> dict[str, Any]:
    """List messages in a chat session, oldest first. Paginated."""
    # Ownership check
    chat_session = await session.get(ChatSession, session_id)
    if not chat_session or chat_session.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 50

    offset = (page - 1) * per_page

    count_stmt = select(func.count()).select_from(ChatMessage).where(ChatMessage.session_id == session_id)
    total = (await session.execute(count_stmt)).scalar() or 0

    stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())  # type: ignore[arg-type]
        .offset(offset)
        .limit(per_page)
    )
    result = await session.execute(stmt)
    messages = list(result.scalars().all())

    return {
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "content": m.content,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": max(1, -(-total // per_page)),
    }


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
