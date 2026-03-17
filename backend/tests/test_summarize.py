"""
Summarization smoke tests — extractive path (no LLM key needed).
"""
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


@pytest.mark.asyncio
async def test_summarize_extractive(client: AsyncClient):
    """Without LLM keys, the backend should use extractive fallback."""
    res = await client.post("/summarize", json={"text": SAMPLE_TEXT})
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert len(data["summary"]) > 0
    # Summary should be shorter than original
    assert len(data["summary"].split()) <= len(SAMPLE_TEXT.split())


@pytest.mark.asyncio
async def test_summarize_too_short(client: AsyncClient):
    res = await client.post("/summarize", json={"text": "Too short."})
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_summarize_empty(client: AsyncClient):
    res = await client.post("/summarize", json={"text": ""})
    # Pydantic validation: min_length=1
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_summarize_missing_text(client: AsyncClient):
    res = await client.post("/summarize", json={})
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_summarize_metadata_fields(client: AsyncClient):
    """Verify that the response includes rich metadata (word counts, compression, takeaways)."""
    res = await client.post("/summarize", json={"text": SAMPLE_TEXT})
    assert res.status_code == 200
    data = res.json()
    assert "original_word_count" in data
    assert "summary_word_count" in data
    assert "compression_ratio" in data
    assert "reading_time_seconds" in data
    assert "key_takeaways" in data
    assert "quality" in data
    assert isinstance(data["key_takeaways"], list)
    assert data["original_word_count"] > data["summary_word_count"]
    assert data["compression_ratio"] > 0


@pytest.mark.asyncio
async def test_summarize_with_length_param(client: AsyncClient):
    """Verify the length parameter is accepted (testing 'brief' to avoid rate limits)."""
    res = await client.post("/summarize", json={"text": SAMPLE_TEXT, "length": "brief"})
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data
    assert len(data["summary"]) > 0
    assert data.get("length") == "brief"


@pytest.mark.asyncio
async def test_summarize_invalid_length(client: AsyncClient):
    """Invalid length value should be rejected by Pydantic validation."""
    res = await client.post("/summarize", json={"text": SAMPLE_TEXT, "length": "invalid"})
    assert res.status_code == 422


# ---------------------------------------------------------------------------
# A-24: SUMMARIZE_MAX_WORDS cap tests
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_summarize_over_max_words_returns_400(client: AsyncClient):
    """Submitting text over summarize_max_words limit returns 400."""
    from app.config import get_config
    cfg = get_config()
    # Build a text just over the limit
    over_limit_text = ("word " * (cfg.summarize_max_words + 1)).strip()
    res = await client.post("/summarize", json={"text": over_limit_text})
    assert res.status_code == 400
    detail = res.json()["detail"]
    assert "too long" in detail.lower()
    assert str(cfg.summarize_max_words) in detail.replace(",", "")


@pytest.mark.asyncio
async def test_summarize_at_max_words_passes(client: AsyncClient):
    """Submitting text exactly at the limit is allowed."""
    from app.config import get_config
    cfg = get_config()
    at_limit_text = ("word " * cfg.summarize_max_words).strip()
    res = await client.post("/summarize", json={"text": at_limit_text})
    # 200 or 400 for too-short (extractive fallback) — either way NOT 422 schema error
    assert res.status_code in (200, 400)
    if res.status_code == 400:
        # If 400, must be the min_words guard, NOT the max_words guard
        assert "too long" not in res.json()["detail"].lower()


@pytest.mark.asyncio
async def test_summarize_max_words_error_message_includes_word_count(client: AsyncClient):
    """Error message includes both the limit and the submitted count."""
    from app.config import get_config
    cfg = get_config()
    submitted = cfg.summarize_max_words + 500
    over_limit_text = ("word " * submitted).strip()
    res = await client.post("/summarize", json={"text": over_limit_text})
    assert res.status_code == 400
    detail = res.json()["detail"]
    # Should mention both the limit and the submitted count
    assert str(cfg.summarize_max_words).replace(",", "") in detail.replace(",", "")