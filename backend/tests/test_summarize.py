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
