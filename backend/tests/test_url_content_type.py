"""
tests/test_url_content_type.py — A-14: Content-Type validation on URL ingest

Verifies that fetching a URL returning a binary content-type (PDF, image,
video) is rejected early with a clear 400, rather than wasting bandwidth
decoding binary data as HTML.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_binary_content_types_rejected(authed_client: AsyncClient):
    """URLs returning binary content-types must be rejected with 400."""
    binary_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "video/mp4",
        "application/octet-stream",
    ]

    for content_type in binary_types:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.headers = {"content-type": content_type}
        mock_response.__aenter__ = AsyncMock(return_value=mock_response)
        mock_response.__aexit__ = AsyncMock(return_value=False)

        mock_client = MagicMock()
        mock_client.stream = MagicMock(return_value=mock_response)

        with patch("app.services.ingest.get_http_client", return_value=mock_client), \
             patch("app.services.ingest._assert_safe_url", return_value=None):
            res = await authed_client.post(
                "/ingest/url",
                json={"url": "https://example.com/file"},
            )

        assert res.status_code == 400, (
            f"Expected 400 for content-type '{content_type}', got {res.status_code}"
        )
        assert "content type" in res.json()["detail"].lower(), (
            f"Error message should mention content type for '{content_type}'"
        )


@pytest.mark.asyncio
async def test_html_content_type_passes_validation(authed_client: AsyncClient):
    """URLs returning text/html must pass the content-type check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {
        "content-type": "text/html; charset=utf-8",
        "content-length": "100",
    }
    mock_response.aiter_bytes = AsyncMock(
        return_value=iter([b"<html><head><title>Test</title></head><body>Hello world.</body></html>"])
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_response)

    with patch("app.services.ingest.get_http_client", return_value=mock_client), \
         patch("app.services.ingest._assert_safe_url", return_value=None):
        res = await authed_client.post(
            "/ingest/url",
            json={"url": "https://example.com/article"},
        )

    # Must not be rejected for content-type
    assert "content type" not in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_text_plain_content_type_passes_validation(authed_client: AsyncClient):
    """URLs returning text/plain must pass the content-type check."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/plain; charset=utf-8"}
    mock_response.aiter_bytes = AsyncMock(
        return_value=iter([b"Plain text article content here." * 10])
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_response)

    with patch("app.services.ingest.get_http_client", return_value=mock_client), \
         patch("app.services.ingest._assert_safe_url", return_value=None):
        res = await authed_client.post(
            "/ingest/url",
            json={"url": "https://example.com/article.txt"},
        )

    assert "content type" not in res.json().get("detail", "").lower()


@pytest.mark.asyncio
async def test_missing_content_type_does_not_crash(authed_client: AsyncClient):
    """A response with no Content-Type header must not crash — it proceeds."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {}  # no content-type
    mock_response.aiter_bytes = AsyncMock(
        return_value=iter([b"<html><body>Content</body></html>"])
    )
    mock_response.__aenter__ = AsyncMock(return_value=mock_response)
    mock_response.__aexit__ = AsyncMock(return_value=False)

    mock_client = MagicMock()
    mock_client.stream = MagicMock(return_value=mock_response)

    with patch("app.services.ingest.get_http_client", return_value=mock_client), \
         patch("app.services.ingest._assert_safe_url", return_value=None):
        res = await authed_client.post(
            "/ingest/url",
            json={"url": "https://example.com/article"},
        )

    # No content-type = empty string = passes the check (falsy guard)
    assert "content type" not in res.json().get("detail", "").lower()
    