"""
SSE streaming endpoints for LLM-powered features.

Sits alongside existing non-streaming routes for backward compatibility.
  - POST /summarize/stream  — streaming summarization
  - POST /api/chat/stream   — streaming contextual chat

Protocol: text/event-stream
  data: {"token": "..."}   (incremental content delta)
  data: [DONE]             (stream complete)
  data: {"error": "..."}   (on failure)
"""
import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import APIRouter, Request, status
from starlette.responses import StreamingResponse

from app.deps import OptionalUser, DbSession
from app.schemas import TextRequest
from app.schemas.requests import ChatRequest
from app.config import get_config
from app.services.extractive import summarize_extractive
from app.models.document import Document
from app.models.chat import ChatMessage, ChatSession
from sqlmodel import select

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _sse_token(token: str) -> str:
    """Format a single token as an SSE data line."""
    return f"data: {json.dumps({'token': token})}\n\n"


def _sse_done(duration_s: float, token_count: int) -> str:
    """Format the final DONE event with metadata."""
    return f"data: {json.dumps({'done': True, 'duration_s': round(duration_s, 2), 'token_count': token_count})}\n\n"


def _sse_error(message: str) -> str:
    """Format an error event."""
    return f"data: {json.dumps({'error': message})}\n\n"


async def _stream_llm(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 1024,
    temperature: float = 0.4,
    request: Request,
) -> AsyncIterator[str]:
    """
    Core streaming generator. Yields SSE-formatted lines from LLM stream.
    Handles cancellation if the client disconnects.
    """
    from app.services.llm import generate_stream

    t0 = time.monotonic()
    token_count = 0

    try:
        async for delta in generate_stream(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
            # Check if client disconnected
            if await request.is_disconnected():
                logger.info("Client disconnected during stream after %d tokens", token_count)
                return

            token_count += 1
            yield _sse_token(delta)

        duration = time.monotonic() - t0
        yield _sse_done(duration, token_count)
        logger.info(
            "Stream completed",
            extra={"duration_s": round(duration, 2), "token_count": token_count},
        )
    except asyncio.CancelledError:
        duration = time.monotonic() - t0
        logger.info("Stream cancelled after %.2fs, %d tokens", duration, token_count)
        return
    except Exception as exc:
        duration = time.monotonic() - t0
        logger.exception("Stream error after %.2fs: %s", duration, exc)
        yield _sse_error(str(exc))


# ---------------------------------------------------------------------------
# POST /summarize/stream
# ---------------------------------------------------------------------------

@router.post("/summarize/stream")
async def summarize_stream(
    body: TextRequest,
    user: OptionalUser,
    session: DbSession,
    request: Request,
):
    """
    Streaming summarization endpoint.

    Two-stage pipeline (same logic as /summarize):
      1. Extraction (non-streaming) — produces structured notes.
      2. Synthesis (streamed) — turns notes into prose, streamed to client.

    Falls back to extractive summary (non-streaming) for reduced quality.
    """
    import re
    from app.services.llm import chat_completion

    cfg = get_config()
    text = re.sub(r"\[\d+\]", "", body.text)
    text = re.sub(r"\s+", " ", text).strip()
    words = text.split()

    if len(words) < cfg.min_words:
        return StreamingResponse(
            iter([_sse_error(f"Text too short. Minimum {cfg.min_words} words."), _sse_done(0, 0)]),
            media_type="text/event-stream",
            status_code=status.HTTP_400_BAD_REQUEST,
        )

    # Extractive fallback when no LLM provider
    if not cfg.has_llm_provider:
        summary = summarize_extractive(
            text,
            min_words=cfg.min_words,
            target_min=cfg.target_min_words,
            target_max=cfg.target_max_words,
        )

        async def _extractive_gen():
            yield _sse_token(summary)
            yield _sse_done(0.0, 1)

        return StreamingResponse(_extractive_gen(), media_type="text/event-stream")

    # Full quality: Stage 1 — extraction (non-streaming)
    original_word_count = len(words)
    target_words = max(cfg.target_min_words, int(original_word_count * 0.25))
    target_words = min(target_words, cfg.target_max_words)

    extraction_system = (
        "You are an expert reader. Your job is to extract the core ideas from an article—not to rewrite it.\n"
        "Output clear, concise notes: thesis, main arguments, key evidence or examples, any counterpoints, and implications or takeaways.\n"
        "Be structured (bullets or short lines). Do not paraphrase into full sentences yet."
    )
    extraction_user = f"Article:\n\n{text}"

    try:
        structured_notes = await chat_completion(
            [
                {"role": "system", "content": extraction_system},
                {"role": "user", "content": extraction_user},
            ],
            max_tokens=1024,
            temperature=0.2,
        )
    except Exception as exc:
        return StreamingResponse(
            iter([_sse_error(f"Extraction failed: {exc}"), _sse_done(0, 0)]),
            media_type="text/event-stream",
        )

    if not structured_notes.strip():
        return StreamingResponse(
            iter([_sse_error("Could not extract ideas from the text."), _sse_done(0, 0)]),
            media_type="text/event-stream",
        )

    # Stage 2 — synthesis (STREAMED)
    synthesis_system = (
        "You are a skilled explainer. Using only the notes provided, write a short summary as if you understood "
        "the topic and are explaining it to a colleague.\n"
        "Write in clear, natural prose. Preserve important facts and nuance. Do not copy phrases from the notes "
        "verbatim—use your own words. Keep a formal but readable tone."
    )
    synthesis_user = (
        f"Notes:\n{structured_notes}\n\n"
        f"Write a cohesive summary of approximately {target_words} words. One or two short paragraphs. No bullet points."
    )

    messages = [
        {"role": "system", "content": synthesis_system},
        {"role": "user", "content": synthesis_user},
    ]

    return StreamingResponse(
        _stream_llm(messages, max_tokens=600, temperature=0.4, request=request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# POST /api/chat/stream
# ---------------------------------------------------------------------------

HISTORY_LIMIT = 10
DOC_CONTEXT_CHARS = 5_000


@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    user: OptionalUser,
    session: DbSession,
    request: Request,
):
    """
    Streaming chat endpoint. Same logic as /api/chat/ but streams the LLM response.
    The full response is persisted to the DB after the stream completes.
    """
    if not user or user.id is None:
        return StreamingResponse(
            iter([_sse_error("Authentication required for chat"), _sse_done(0, 0)]),
            media_type="text/event-stream",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    # 1. Ownership check
    doc = await session.get(Document, body.document_id)
    if not doc or doc.user_id != user.id:
        return StreamingResponse(
            iter([_sse_error("Document not found or unauthorized"), _sse_done(0, 0)]),
            media_type="text/event-stream",
            status_code=status.HTTP_404_NOT_FOUND,
        )

    # 2. Get or create chat session
    session_id = body.session_id
    if session_id:
        chat_session = await session.get(ChatSession, session_id)
        if (
            not chat_session
            or chat_session.user_id != user.id
            or chat_session.document_id != body.document_id
        ):
            return StreamingResponse(
                iter([_sse_error("Chat session not found or mismatched"), _sse_done(0, 0)]),
                media_type="text/event-stream",
                status_code=status.HTTP_404_NOT_FOUND,
            )
    else:
        chat_session = ChatSession(user_id=user.id, document_id=body.document_id)
        session.add(chat_session)
        await session.commit()
        await session.refresh(chat_session)
        session_id = chat_session.id

    # 3. Persist user message
    user_msg = ChatMessage(session_id=session_id, role="user", content=body.message)
    session.add(user_msg)
    await session.commit()

    # 4. Fetch bounded history
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

    # 6. Stream LLM response, collect full text, persist on completion
    from app.services.llm import generate_stream

    t0 = time.monotonic()
    token_count = 0
    collected_tokens: list[str] = []

    async def _chat_stream_gen():
        nonlocal token_count
        try:
            async for delta in generate_stream(
                messages_payload, max_tokens=1000, temperature=0.5
            ):
                if await request.is_disconnected():
                    logger.info("Chat client disconnected after %d tokens", token_count)
                    return
                token_count += 1
                collected_tokens.append(delta)
                yield _sse_token(delta)

            # Persist the full assistant message
            full_content = "".join(collected_tokens)
            assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=full_content)
            session.add(assistant_msg)
            await session.commit()
            await session.refresh(assistant_msg)

            duration = time.monotonic() - t0
            yield f"data: {json.dumps({'done': True, 'session_id': session_id, 'message_id': assistant_msg.id, 'duration_s': round(duration, 2), 'token_count': token_count})}\n\n"
            logger.info(
                "Chat stream completed",
                extra={"duration_s": round(duration, 2), "token_count": token_count, "session_id": session_id},
            )
        except asyncio.CancelledError:
            # Try to persist partial response
            if collected_tokens:
                partial = "".join(collected_tokens)
                partial_msg = ChatMessage(session_id=session_id, role="assistant", content=partial + " [interrupted]")
                session.add(partial_msg)
                try:
                    await session.commit()
                except Exception:
                    pass
            logger.info("Chat stream cancelled after %d tokens", token_count)
            return
        except Exception as exc:
            logger.exception("Chat stream error: %s", exc)
            yield _sse_error(str(exc))

    return StreamingResponse(
        _chat_stream_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
