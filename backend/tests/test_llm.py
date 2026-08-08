"""
Tests for LLM service (generate_full, generate_stream, and retries).
"""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.llm import chat_completion, generate_full, generate_stream


@pytest.fixture
def mock_config():
    with patch("app.services.llm.get_config") as m_config:
        cfg = MagicMock()
        cfg.get_llm_base_url.return_value = "https://mock.llm.com"
        cfg.get_llm_api_key.return_value = "sk-mock"
        cfg.summarize_model = "mock-model"
        cfg.summarize_timeout_seconds = 30
        m_config.return_value = cfg
        yield cfg

@pytest.mark.asyncio
async def test_generate_full_success(mock_config):
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello World!"}}],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5}
    }

    mock_client = MagicMock()
    mock_client.post = AsyncMock(return_value=mock_resp)

    with patch("app.services.llm.get_http_client", return_value=mock_client):
        res = await generate_full([{"role": "user", "content": "hi"}], model="mock-model")
        assert res == "Hello World!"
        mock_client.post.assert_called_once()

@pytest.mark.asyncio
async def test_generate_full_retries_on_502(mock_config):
    mock_err_resp = MagicMock()
    mock_err_resp.status_code = 502

    mock_ok_resp = MagicMock()
    mock_ok_resp.status_code = 200
    mock_ok_resp.json.return_value = {
        "choices": [{"message": {"content": "Retry Success"}}]
    }

    mock_client = MagicMock()
    mock_client.post = AsyncMock(side_effect=[mock_err_resp, mock_ok_resp])

    with (
        patch("app.services.llm.get_http_client", return_value=mock_client),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        res = await generate_full([{"role": "user", "content": "hi"}])
        assert res == "Retry Success"
        assert mock_client.post.call_count == 2

@pytest.mark.asyncio
async def test_generate_full_handles_429(mock_config):
    mock_resp = MagicMock()
    mock_resp.status_code = 429

    mock_client = MagicMock()
    # Always return 429 to trigger HTTPStatusError inside _handle_error_status
    mock_client.post = AsyncMock(return_value=mock_resp)

    with (
        patch("app.services.llm.get_http_client", return_value=mock_client),
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        with pytest.raises(httpx.HTTPStatusError) as exc:
            await generate_full([{"role": "user", "content": "hi"}])
        assert exc.value.response.status_code == 429

@pytest.mark.asyncio
async def test_generate_stream_success(mock_config):
    mock_resp = MagicMock()
    mock_resp.status_code = 200

    async def mock_aiter_lines():
        yield 'data: {"choices": [{"delta": {"content": "Hello"}}]}'
        yield 'data: {"choices": [{"delta": {"content": " World"}}]}'
        yield 'data: [DONE]'

    mock_resp.aiter_lines = mock_aiter_lines
    mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
    mock_resp.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_resp)

    with patch("app.services.llm.get_http_client", return_value=mock_client):
        chunks = []
        async for chunk in generate_stream([{"role": "user", "content": "hi"}]):
            chunks.append(chunk)

        assert chunks == ["Hello", " World"]

def test_chat_completion_alias():
    assert chat_completion is generate_full
