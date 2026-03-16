"""
SSE streaming endpoints for LLM-powered features.

Sits alongside existing non-streaming routes for backward compatibility.
  - POST /summarize/stream  — streaming summarization
  - POST /api/chat/stream   — streaming contextual chat

Protocol: text/event-stream
  data: {"token": "..."}   (incremental content delta)
  data: [DONE]             (stream complete)
  data: {"error": "..."}   (on failure)

v2: No more JSON_SEP filtering. The LLM now outputs ONLY clean summary text.
Metadata is computed from intelligence.py after the stream completes.
"""
import asyncio
import json
import logging
import time
from typing import AsyncIterator

from fastapi import APIRouter, Request, status
from starlette.responses import StreamingResponse

from app.deps import OptionalVerifiedUser, DbSession
from app.schemas import TextRequest
from app.schemas.requests import ChatRequest
from app.models.chat import ChatMessage
from app.services.summarizer import (
    prepare_summarize_messages,
    compute_metadata as _compute_metadata,
    LENGTH_PRESETS,
)
from app.services.summarizer.prompts import build_takeaway_prompt
from app.services.summarizer.core import _parse_takeaways
from app.services.chat import prepare_chat_context
from app.services.llm import generate_stream, generate_full

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])

# ---------------------------------------------------------------------------
# SSE helpers
# ---------------------------------------------------------------------------

def _sse_token(token: str) -> str:
    """Format a single token as an SSE data line."""
    return f"data: {json.dumps({'token': token})}\n\n"


def _sse_done(duration_s: float, token_count: int, **extra: object) -> str:
    """Format the final DONE event with metadata."""
    payload = {"done": True, "duration_s": round(duration_s, 2), "token_count": token_count}
    payload.update(extra)  # type: ignore[arg-type]
    return f"data: {json.dumps(payload)}\n\n"


def _sse_error(message: str) -> str:
    """Format an error event."""
    return f"data: {json.dumps({'error': message})}\n\n"


async def _stream_llm(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 1024,
    temperature: float = 0.3,
    request: Request,
) -> AsyncIterator[str]:
    """
    Core streaming generator. Yields SSE-formatted lines from LLM stream.
    Handles cancellation if the client disconnects.
    """
    t0 = time.monotonic()
    token_count = 0

    try:
        async for delta in generate_stream(
            messages,
            max_tokens=max_tokens,
            temperature=temperature,
        ):
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
    user: OptionalVerifiedUser,
    session: DbSession,
    request: Request,
):
    """
    Streaming summarization endpoint.
    v2: stream is pure summary text — no JSON separator filtering needed.
    """
    try:
        prep = await prepare_summarize_messages(
            body.text,
            length=body.length,
            mode=body.mode,
            tone=body.tone,
            keywords=body.keywords,
        )
    except ValueError as exc:
        return StreamingResponse(
            iter([_sse_error(str(exc)), _sse_done(0, 0)]),
            media_type="text/event-stream",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    except Exception as exc:
        return StreamingResponse(
            iter([_sse_error(f"Preparation failed: {exc}"), _sse_done(0, 0)]),
            media_type="text/event-stream",
        )

    # Extractive fallback
    if prep.is_extractive:
        ext_res = prep.extractive_result or ""
        meta = _compute_metadata(prep.original_text, ext_res)
        takeaways = prep.extractive_takeaways or []

        async def _extractive_gen() -> AsyncIterator[str]:
            yield _sse_token(ext_res)
            yield f"data: {json.dumps({'takeaways': takeaways})}\n\n"
            yield _sse_done(0.0, 1, **meta, quality="extractive", length=prep.length, mode=prep.mode)
        return StreamingResponse(_extractive_gen(), media_type="text/event-stream")

    # LLM path — clean stream, no separator filtering
    collected_tokens: list[str] = []

    async def _summarize_stream_gen():
        t0 = time.monotonic()

        # Stream the summary tokens directly to client
        async for chunk in _stream_llm(
            prep.messages,
            max_tokens=prep.max_tokens,
            temperature=prep.temperature,
            request=request,
        ):
            # Collect tokens for post-stream metadata
            if chunk.startswith('data: {"token"'):
                try:
                    token_data = json.loads(chunk[6:])
                    if "token" in token_data:
                        collected_tokens.append(token_data["token"])
                except Exception:
                    pass

            # Skip the inner _stream_llm done event (we'll emit our own)
            if chunk.startswith('data: {"done"'):
                continue

            yield chunk

        # Stream complete — compute metadata from the clean summary
        summary_text = "".join(collected_tokens).strip()
        meta = _compute_metadata(prep.original_text, summary_text)

        # Extract takeaways via a lightweight second call
        takeaways = []
        if prep.mode != "tldr" and len(summary_text.split()) > 30:
            try:
                takeaway_msgs = build_takeaway_prompt(summary_text, prep.takeaway_count)
                raw_takeaways = await generate_full(takeaway_msgs, max_tokens=400, temperature=0.2)
                takeaways = _parse_takeaways(raw_takeaways)[:prep.takeaway_count]
            except Exception:
                logger.warning("Takeaway extraction failed in stream, skipping")

        yield f"data: {json.dumps({'takeaways': takeaways})}\n\n"

        duration = time.monotonic() - t0
        yield _sse_done(duration, len(collected_tokens), **meta, quality="full", length=prep.length, mode=prep.mode)

    return StreamingResponse(
        _summarize_stream_gen(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# POST /chat/stream
# ---------------------------------------------------------------------------

@router.post("/chat/stream")
async def chat_stream(
    body: ChatRequest,
    user: OptionalVerifiedUser,
    session: DbSession,
    request: Request,
):
    """
    Streaming chat endpoint.
    """
    if not user or user.id is None:
        return StreamingResponse(
            iter([_sse_error("Authentication required for chat"), _sse_done(0, 0)]),
            media_type="text/event-stream",
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

    try:
        ctx = await prepare_chat_context(
            document_id=body.document_id,
            user_id=user.id,
            message=body.message,
            session=session,
            session_id=body.session_id,
        )
    except ValueError as exc:
        error_msg = str(exc)
        http_status = (
            status.HTTP_404_NOT_FOUND
            if "not found" in error_msg.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        return StreamingResponse(
            iter([_sse_error(error_msg), _sse_done(0, 0)]),
            media_type="text/event-stream",
            status_code=http_status,
        )

    t0 = time.monotonic()
    token_count = 0
    collected_tokens: list[str] = []

    async def _chat_stream_gen():
        nonlocal token_count
        try:
            async for delta in generate_stream(
                ctx.messages_payload, max_tokens=1000, temperature=0.5
            ):
                if await request.is_disconnected():
                    logger.info("Chat client disconnected after %d tokens", token_count)
                    return
                token_count += 1
                collected_tokens.append(delta)
                yield _sse_token(delta)

            full_content = "".join(collected_tokens)
            assistant_msg = ChatMessage(session_id=ctx.session_id, role="assistant", content=full_content)
            session.add(assistant_msg)
            await session.commit()
            await session.refresh(assistant_msg)

            duration = time.monotonic() - t0
            yield _sse_done(
                duration, token_count,
                session_id=ctx.session_id,
                message_id=assistant_msg.id,
            )
            logger.info(
                "Chat stream completed",
                extra={"duration_s": round(duration, 2), "token_count": token_count, "session_id": ctx.session_id},
            )
        except asyncio.CancelledError:
            if collected_tokens:
                partial = "".join(collected_tokens)
                partial_msg = ChatMessage(session_id=ctx.session_id, role="assistant", content=partial + " [interrupted]")
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