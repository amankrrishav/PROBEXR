"""
tests/test_map_reduce.py  —  A-36: Map-reduce summarization flow coverage.

The map-reduce path only triggers for text > 3000 words (_CHUNK_WORD_LIMIT).
No existing test exercises it — a bug there goes undetected until a real user
submits a long document.

Strategy
--------
- Mock llm.chat_completion to return deterministic strings (no API key needed).
- Build text that is guaranteed to exceed _CHUNK_WORD_LIMIT so the map-reduce
  branch is taken, not the single-call branch.
- Assert the correct number of LLM calls are made (map per chunk + reduce + takeaways).
- Assert the final result has the expected structure.
- Also test _chunk_text directly as a pure unit test.
"""
import asyncio
from unittest.mock import AsyncMock, patch, call
from typing import Any

import pytest

from app.services.summarizer.core import (
    summarize,
    _chunk_text,
    _map_reduce_flow,
    _CHUNK_WORD_LIMIT,
    LENGTH_PRESETS,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_long_text(word_count: int) -> str:
    """
    Build a realistic-looking text with the given word count.
    Uses varied sentences so the chunker produces multiple chunks.
    """
    sentence = (
        "Researchers have discovered that artificial intelligence systems can now "
        "perform tasks previously thought to require human expertise and judgment. "
    )
    words_per_sentence = len(sentence.split())
    sentences_needed = (word_count // words_per_sentence) + 2
    return " ".join([sentence.strip()] * sentences_needed)


# Text long enough to always trigger map-reduce (well over 3000 words)
LONG_TEXT = _make_long_text(_CHUNK_WORD_LIMIT + 500)
# Verify it's actually long enough
assert len(LONG_TEXT.split()) > _CHUNK_WORD_LIMIT, (
    f"LONG_TEXT must be >{_CHUNK_WORD_LIMIT} words, got {len(LONG_TEXT.split())}"
)

# Short text — stays under the threshold
SHORT_TEXT = _make_long_text(_CHUNK_WORD_LIMIT - 100)
assert len(SHORT_TEXT.split()) <= _CHUNK_WORD_LIMIT


# ---------------------------------------------------------------------------
# 1. _chunk_text unit tests
# ---------------------------------------------------------------------------

class TestChunkText:
    def test_short_text_single_chunk(self):
        """Text under the limit produces exactly one chunk."""
        text = "Hello world. " * 100  # ~200 words
        chunks = _chunk_text(text)
        assert len(chunks) == 1

    def test_long_text_multiple_chunks(self):
        """Text over the limit is split into multiple chunks."""
        chunks = _chunk_text(LONG_TEXT)
        assert len(chunks) >= 2

    def test_each_chunk_within_limit(self):
        """Every chunk produced is at or near the word limit."""
        chunks = _chunk_text(LONG_TEXT)
        for chunk in chunks:
            # Each chunk should not be wildly over the limit
            # (small overage possible due to carry-over sentences)
            assert len(chunk.split()) <= _CHUNK_WORD_LIMIT * 1.1

    def test_no_content_lost(self):
        """Total word count across all chunks covers the original text."""
        text = "The quick brown fox jumps over the lazy dog. " * 200
        chunks = _chunk_text(text)
        total_chunk_words = sum(len(c.split()) for c in chunks)
        original_words = len(text.split())
        # Overlap (carry-over sentences) means chunks may have slightly more words
        assert total_chunk_words >= original_words * 0.95

    def test_empty_text_returns_one_chunk(self):
        """Empty text returns a single (empty) chunk rather than crashing."""
        chunks = _chunk_text("")
        assert len(chunks) == 1

    def test_chunk_count_scales_with_text_length(self):
        """Longer text produces more chunks than shorter text."""
        medium = _make_long_text(_CHUNK_WORD_LIMIT + 200)
        large = _make_long_text(_CHUNK_WORD_LIMIT * 3)
        assert len(_chunk_text(large)) > len(_chunk_text(medium))


# ---------------------------------------------------------------------------
# 2. _map_reduce_flow unit tests (LLM mocked)
# ---------------------------------------------------------------------------

MOCK_CHUNK_SUMMARY = "This chunk discusses AI advancements and their impact on industry."
MOCK_FINAL_SUMMARY = (
    "Artificial intelligence has transformed multiple industries. "
    "Research shows significant progress in machine learning. "
    "Challenges remain in deployment and ethics. "
    "Companies continue to invest heavily in AI capabilities. "
    "The societal impact is expected to grow substantially."
)
MOCK_TAKEAWAYS = (
    "• AI adoption has accelerated across all major industries.\n"
    "• Machine learning powers modern recommendation systems.\n"
    "• Ethical deployment remains an open challenge.\n"
    "• Investment in AI research continues to grow.\n"
    "• Societal impacts will intensify over the next decade."
)


@pytest.mark.asyncio
async def test_map_reduce_flow_returns_required_keys():
    """_map_reduce_flow returns dict with summary, key_takeaways, metadata."""
    preset = LENGTH_PRESETS["standard"]
    call_count = 0

    async def mock_llm(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        # First N calls are map phase (chunk summaries), then reduce, then takeaways
        if call_count == 1:
            return MOCK_CHUNK_SUMMARY
        if call_count == 2:
            return MOCK_CHUNK_SUMMARY
        if call_count == 3:
            return MOCK_FINAL_SUMMARY
        return MOCK_TAKEAWAYS

    with patch("app.services.llm.chat_completion", side_effect=mock_llm):
        result = await _map_reduce_flow(
            LONG_TEXT, target=150, preset=preset, length="standard"
        )

    assert "summary" in result
    assert "key_takeaways" in result
    assert "metadata" in result
    assert isinstance(result["summary"], str)
    assert len(result["summary"]) > 0
    assert isinstance(result["key_takeaways"], list)


@pytest.mark.asyncio
async def test_map_reduce_flow_calls_llm_multiple_times():
    """
    Map-reduce must call LLM at least: len(chunks) times (map) + 1 (reduce).
    Takeaway call is optional but typically adds 1 more.
    """
    preset = LENGTH_PRESETS["standard"]
    chunks = _chunk_text(LONG_TEXT)
    min_expected_calls = len(chunks) + 1  # map + reduce

    llm_calls = []

    async def mock_llm(messages, **kwargs):
        llm_calls.append(messages)
        if len(llm_calls) <= len(chunks):
            return MOCK_CHUNK_SUMMARY
        if len(llm_calls) == len(chunks) + 1:
            return MOCK_FINAL_SUMMARY
        return MOCK_TAKEAWAYS

    with patch("app.services.llm.chat_completion", side_effect=mock_llm):
        await _map_reduce_flow(
            LONG_TEXT, target=150, preset=preset, length="standard"
        )

    assert len(llm_calls) >= min_expected_calls, (
        f"Expected at least {min_expected_calls} LLM calls, got {len(llm_calls)}"
    )


@pytest.mark.asyncio
async def test_map_reduce_flow_uses_reduce_prompt_for_final_call():
    """
    The reduce call must receive all chunk summaries in its prompt,
    not just the last one — verifies map outputs are actually aggregated.
    """
    preset = LENGTH_PRESETS["standard"]
    chunks = _chunk_text(LONG_TEXT)
    captured_messages = []

    async def mock_llm(messages, **kwargs):
        captured_messages.append(messages)
        if len(captured_messages) <= len(chunks):
            return f"Chunk summary {len(captured_messages)}."
        if len(captured_messages) == len(chunks) + 1:
            return MOCK_FINAL_SUMMARY
        return MOCK_TAKEAWAYS

    with patch("app.services.llm.chat_completion", side_effect=mock_llm):
        await _map_reduce_flow(
            LONG_TEXT, target=150, preset=preset, length="standard"
        )

    # The reduce call (index = len(chunks)) should contain multiple chunk summaries
    reduce_call_messages = captured_messages[len(chunks)]
    reduce_user_content = reduce_call_messages[-1]["content"]
    # All chunk summaries should appear in the reduce prompt
    for i in range(1, len(chunks) + 1):
        assert f"Chunk summary {i}." in reduce_user_content, (
            f"Chunk summary {i} missing from reduce prompt"
        )


@pytest.mark.asyncio
async def test_map_reduce_takeaway_failure_does_not_crash():
    """
    If the takeaway extraction call fails, map-reduce should still return
    a result (empty takeaways list) rather than raising.
    """
    preset = LENGTH_PRESETS["standard"]
    chunks = _chunk_text(LONG_TEXT)
    call_count = 0

    async def mock_llm(messages, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= len(chunks):
            return MOCK_CHUNK_SUMMARY
        if call_count == len(chunks) + 1:
            return MOCK_FINAL_SUMMARY
        raise ValueError("Takeaway extraction failed — simulated error")

    with patch("app.services.llm.chat_completion", side_effect=mock_llm):
        result = await _map_reduce_flow(
            LONG_TEXT, target=150, preset=preset, length="standard"
        )

    # Should complete successfully with empty takeaways
    assert result["summary"] == MOCK_FINAL_SUMMARY
    assert result["key_takeaways"] == []


# ---------------------------------------------------------------------------
# 3. Full summarize() path — map-reduce triggered (LLM mocked)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summarize_triggers_map_reduce_for_long_text():
    """
    summarize() must use _map_reduce_flow (not _single_call_flow) when
    word_count > _CHUNK_WORD_LIMIT and an LLM provider is configured.
    """
    chunks = _chunk_text(LONG_TEXT)
    call_count = 0

    async def mock_llm(messages, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= len(chunks):
            return MOCK_CHUNK_SUMMARY
        if call_count == len(chunks) + 1:
            return MOCK_FINAL_SUMMARY
        return MOCK_TAKEAWAYS

    with patch("app.services.llm.chat_completion", side_effect=mock_llm), \
         patch("app.config.AppConfig.has_llm_provider", new_callable=lambda: property(lambda self: True)):
        result = await summarize(LONG_TEXT, length="standard")

    # map + reduce = at least len(chunks) + 1 calls
    assert call_count >= len(chunks) + 1
    assert result["summary"] == MOCK_FINAL_SUMMARY
    assert result["quality"] == "full"


@pytest.mark.asyncio
async def test_summarize_uses_single_call_for_short_text():
    """
    summarize() must use _single_call_flow (not map-reduce) when
    word_count <= _CHUNK_WORD_LIMIT — single LLM call for map phase.
    """
    call_count = 0

    async def mock_llm(messages, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return MOCK_FINAL_SUMMARY
        return MOCK_TAKEAWAYS

    with patch("app.services.llm.chat_completion", side_effect=mock_llm), \
         patch("app.config.AppConfig.has_llm_provider", new_callable=lambda: property(lambda self: True)):
        result = await summarize(SHORT_TEXT, length="standard")

    # Single call flow: 1 summary call + 1 takeaway call = 2 max
    assert call_count <= 2
    assert result["summary"] == MOCK_FINAL_SUMMARY


@pytest.mark.asyncio
async def test_map_reduce_result_has_metadata():
    """Map-reduce result includes full metadata dict from compute_metadata."""
    chunks = _chunk_text(LONG_TEXT)
    call_count = 0

    async def mock_llm(messages, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count <= len(chunks):
            return MOCK_CHUNK_SUMMARY
        if call_count == len(chunks) + 1:
            return MOCK_FINAL_SUMMARY
        return MOCK_TAKEAWAYS

    with patch("app.services.llm.chat_completion", side_effect=mock_llm), \
         patch("app.config.AppConfig.has_llm_provider", new_callable=lambda: property(lambda self: True)):
        result = await summarize(LONG_TEXT, length="standard")

    assert "original_word_count" in result or "metadata" in result
    # quality must be "full" (not extractive) since LLM was mocked
    assert result.get("quality") == "full"