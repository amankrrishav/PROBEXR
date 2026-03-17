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
from sqlmodel import select, desc

from app.models.chat import ChatMessage, ChatSession
from app.models.document import Document
from app.services.llm import chat_completion
from app.services.prompt_sanitizer import sanitize_document_content, sanitize_user_prompt

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


@dataclass
class ChatContext:
    """Prepared context for chat LLM call — shared by streaming and non-streaming paths."""
    messages_payload: list[dict[str, str]]
    session_id: int


async def prepare_chat_context(
    document_id: int,
    user_id: int,
    message: str,
    session: AsyncSession,
    session_id: int | None = None,
) -> ChatContext:
    """
    Run steps 1–5 of the chat pipeline (shared by streaming & non-streaming):
      1. Ownership check
      2. Get or create chat session
      3. Persist user message
      4. Fetch bounded history
      5. Build LLM messages payload

    Returns ChatContext with messages_payload and session_id.
    Raises ValueError on ownership/session mismatch.
    """
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

    # 4. Fetch bounded history
    history_stmt = (
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(desc(ChatMessage.created_at))
        .limit(HISTORY_LIMIT)
    )
    result = await session.execute(history_stmt)
    recent_msgs = list(result.scalars().all())
    recent_msgs.reverse()

    # 5. Build LLM payload — sanitize all user-controlled content before injection
    safe_title = sanitize_document_content(doc.title or "")
    safe_content = sanitize_document_content(
        (doc.cleaned_content or "")[:DOC_CONTEXT_CHARS]
    )
    messages_payload: list[dict[str, str]] = [
        {
            "role": "system",
            "content": (
                f"You are a helpful assistant answering questions about the following document:\n\n"
                f"Title: {safe_title}\n\n"
                f"Content:\n{safe_content}"
            ),
        }
    ]
    for m in recent_msgs:
        # Re-sanitize stored user messages when replaying history into the prompt
        content = sanitize_user_prompt(m.content) if m.role == "user" else m.content
        messages_payload.append({"role": m.role, "content": content})

    assert session_id is not None
    return ChatContext(messages_payload=messages_payload, session_id=session_id)


async def process_chat_message(
    document_id: int,
    user_id: int,
    message: str,
    session: AsyncSession,
    session_id: int | None = None,
) -> ChatReply:
    """Non-streaming chat: prepare context, call LLM, persist reply."""
    ctx = await prepare_chat_context(document_id, user_id, message, session, session_id)

    # LLM call
    reply_content = await chat_completion(ctx.messages_payload, max_tokens=1000, temperature=0.5)

    # Persist and return assistant message
    assistant_msg = ChatMessage(session_id=ctx.session_id, role="assistant", content=reply_content)
    session.add(assistant_msg)
    await session.commit()
    await session.refresh(assistant_msg)

    return ChatReply(
        id=assistant_msg.id,
        session_id=ctx.session_id,
        role=assistant_msg.role,
        content=assistant_msg.content,
        created_at=assistant_msg.created_at,
    )