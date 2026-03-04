"""
Streaming endpoint tests — summarize/stream and chat/stream SSE endpoints.
Tests auth guards, validation, and SSE protocol for the extractive path (no LLM key needed).
"""
import json

import pytest
from httpx import AsyncClient


SAMPLE_TEXT = (
    "Artificial intelligence has transformed the technology landscape dramatically. "
    "Machine learning algorithms now power recommendation systems, natural language processing, "
    "and computer vision applications across industries. Researchers continue to push "
    "the boundaries of what is possible with deep learning architectures. Companies invest "
    "billions of dollars annually in AI research and development. The impact of these "
    "technologies extends beyond the tech sector into healthcare, finance, education, and "
    "manufacturing. Despite rapid progress, significant challenges remain in areas such as "
    "model interpretability, data privacy, and ethical deployment. Experts debate the long-term "
    "implications of increasingly capable AI systems on employment and society."
)


# ---- POST /summarize/stream ----

@pytest.mark.asyncio
async def test_summarize_stream_extractive(client: AsyncClient):
    """
    Without LLM keys, streaming summarize uses extractive fallback.
    Should return valid SSE with token + done events.
    """
    res = await client.post(
        "/summarize/stream",
        json={"text": SAMPLE_TEXT},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")

    body = res.text
    lines = [l for l in body.strip().split("\n") if l.startswith("data: ")]
    assert len(lines) >= 2  # at least token + done

    # Parse events
    events = []
    for line in lines:
        data_str = line[6:]  # strip "data: "
        try:
            events.append(json.loads(data_str))
        except json.JSONDecodeError:
            pass

    # Should have at least one token event and a done event
    token_events = [e for e in events if "token" in e]
    done_events = [e for e in events if e.get("done")]
    assert len(token_events) >= 1
    assert len(done_events) == 1

    # Done event should include metadata
    done = done_events[0]
    assert "original_word_count" in done
    assert "summary_word_count" in done
    assert "compression_ratio" in done


@pytest.mark.asyncio
async def test_summarize_stream_with_length(client: AsyncClient):
    """Length parameter should be accepted in streaming endpoint."""
    res = await client.post(
        "/summarize/stream",
        json={"text": SAMPLE_TEXT, "length": "brief"},
    )
    assert res.status_code == 200
    assert "text/event-stream" in res.headers.get("content-type", "")


@pytest.mark.asyncio
async def test_summarize_stream_too_short(client: AsyncClient):
    """Too-short text should return error SSE event."""
    res = await client.post(
        "/summarize/stream",
        json={"text": "Too short."},
    )
    # May return 400 or SSE with error
    if res.status_code == 200:
        body = res.text
        assert "error" in body.lower()
    else:
        assert res.status_code == 400


@pytest.mark.asyncio
async def test_summarize_stream_takeaways_event(client: AsyncClient):
    """Streaming should include a takeaways SSE event."""
    res = await client.post(
        "/summarize/stream",
        json={"text": SAMPLE_TEXT},
    )
    assert res.status_code == 200
    body = res.text
    lines = [l for l in body.strip().split("\n") if l.startswith("data: ")]

    takeaway_events = []
    for line in lines:
        try:
            parsed = json.loads(line[6:])
            if "takeaways" in parsed:
                takeaway_events.append(parsed)
        except json.JSONDecodeError:
            pass

    assert len(takeaway_events) >= 1
    assert isinstance(takeaway_events[0]["takeaways"], list)


# ---- POST /chat/stream ----

@pytest.mark.asyncio
async def test_chat_stream_unauthenticated(client: AsyncClient):
    """Chat streaming requires authentication."""
    res = await client.post(
        "/chat/stream",
        json={"document_id": 1, "message": "Hello"},
    )
    # Returns 401 as SSE or HTTP status
    assert res.status_code == 401 or "error" in res.text.lower()


@pytest.mark.asyncio
async def test_chat_stream_document_not_found(authed_client: AsyncClient):
    """Chat streaming with non-existent document returns error."""
    res = await authed_client.post(
        "/chat/stream",
        json={"document_id": 999999, "message": "Hello"},
    )
    assert res.status_code in (404, 200)
    if res.status_code == 200:
        assert "error" in res.text.lower()
