"""
Chat service for contextual article Q&A.

Key invariants:
  - document must be owned by the requesting user (user isolation).
  - Chat history is bounded: only last 10 messages fetched per turn.
  - Document content for the system prompt is capped at 5 000 chars.
  - The returned ChatMessage row is augmented with session_id so the frontend
    can maintain session continuity across turns.
"""
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document
from app.services.llm import chat_completion

# How many recent messages to include in the LLM context window
HISTORY_LIMIT = 10
# Max chars of document content injected into the system prompt
DOC_CONTEXT_CHARS = 5_000


@dataclass
class ChatReply:
    """Thin envelope so the router can return both the message and its session."""
    id: int | None
    session_id: int
    role: str
    content: str
    created_at: object  # datetime — kept as-is for JSON serialisation


async def process_chat_message(
    document_id: int,
    user_id: int,
    message: str,
    session: AsyncSession,
    session_id: int | None = None,
) -> ChatReply:
    # 1. Ownership check
    doc = await session.get(Document, document_id)
    if not doc or doc.user_id != user_id:
        raise ValueError("Document not found or unauthorized")

    # 2. Get or create chat session
    if session_id:
        chat_session = await session.get(ChatSession, session_id)
        if (
            not chat_session
            or chat_session.user_id != user_id
            or chat_session.document_id != document_id
        ):
            raise ValueError("Chat session not found or mismatched")
    else:
        chat_session = ChatSession(user_id=user_id, document_id=document_id)
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
        session_id = chat_session.id

    # 3. Persist user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=message)
    session.add(user_msg)
    await session.commit()

    # 4. Fetch bounded history (most recent first, then reverse)
    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.desc())  # type: ignore[arg-type]
        .limit(HISTORY_LIMIT)
    )
    result = await session.execute(history_stmt)
    recent_msgs = list(result.scalars().all())
    recent_msgs.reverse()

    # 5. Build LLM payload
    messages_payload: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                f"You are a helpful assistant answering questions about the following document:\n\n"
                f"Title: {doc.title}\n\n"
                f"Content:\n{doc.cleaned_content[:DOC_CONTEXT_CHARS]}"
            ),
        }
    ]
    for m in recent_msgs:
        messages_payload.append({"role": m.role, "content": m.content})

    # 6. LLM call
    reply_content = await chat_completion(messages_payload, max_tokens=1000, temperature=0.5)

    # 7. Persist and return assistant message — include session_id for client continuity
    assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=reply_content)
    session.add(assistant_msg)
    await session.commit()
    await session.refresh(assistant_msg)

    return ChatReply(
        id=assistant_msg.id,
        session_id=session_id,  # ← critical: frontend needs this to continue the session
        role=assistant_msg.role,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at,
    )
