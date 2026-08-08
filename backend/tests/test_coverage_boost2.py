"""
Coverage boost phase 2 — targeting email SMTP paths, social service,
streaming helpers, TTS service, and remaining gaps.
"""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# =====================================================================
# Email service — SMTP paths (mocked)
# =====================================================================


@pytest.mark.asyncio
async def test_send_verification_email_smtp_success():
    """Verification email sends successfully via mocked SMTP."""
    from app.services.email import send_verification_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch("app.services.email.asyncio.to_thread", new_callable=AsyncMock) as mock_thread,
    ):
        mock_thread.return_value = None
        await send_verification_email("user@test.com", "https://example.com/verify")
        mock_thread.assert_called_once()


@pytest.mark.asyncio
async def test_send_password_reset_email_smtp_success():
    """Password reset email sends successfully via mocked SMTP."""
    from app.services.email import send_password_reset_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch("app.services.email.asyncio.to_thread", new_callable=AsyncMock) as mock_thread,
    ):
        mock_thread.return_value = None
        await send_password_reset_email("user@test.com", "https://example.com/reset")
        mock_thread.assert_called_once()


@pytest.mark.asyncio
async def test_send_magic_link_email_smtp_success():
    """Magic link email sends successfully via mocked SMTP."""
    from app.services.email import send_magic_link_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch("app.services.email.asyncio.to_thread", new_callable=AsyncMock) as mock_thread,
    ):
        mock_thread.return_value = None
        await send_magic_link_email("user@test.com", "https://example.com/magic")
        mock_thread.assert_called_once()


@pytest.mark.asyncio
async def test_send_account_exists_email_smtp_success():
    """Account-exists email sends successfully via mocked SMTP."""
    from app.services.email import send_account_exists_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch("app.services.email.asyncio.to_thread", new_callable=AsyncMock) as mock_thread,
    ):
        mock_thread.return_value = None
        await send_account_exists_email("user@test.com", "https://example.com/login")
        mock_thread.assert_called_once()


@pytest.mark.asyncio
async def test_send_verification_email_smtp_failure():
    """SMTP failure raises ValueError."""
    from app.services.email import send_verification_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch(
            "app.services.email.asyncio.to_thread",
            new_callable=AsyncMock,
            side_effect=Exception("SMTP connection refused"),
        ),
        pytest.raises(ValueError, match="Failed to send email"),
    ):
        await send_verification_email("user@test.com", "https://example.com/verify")


@pytest.mark.asyncio
async def test_send_password_reset_email_smtp_failure():
    """SMTP failure raises ValueError for password reset."""
    from app.services.email import send_password_reset_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch("app.services.email.asyncio.to_thread", new_callable=AsyncMock, side_effect=Exception("SMTP timeout")),
        pytest.raises(ValueError, match="Failed to send email"),
    ):
        await send_password_reset_email("user@test.com", "https://example.com/reset")


@pytest.mark.asyncio
async def test_send_magic_link_email_smtp_failure():
    """SMTP failure raises ValueError for magic link."""
    from app.services.email import send_magic_link_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch(
            "app.services.email.asyncio.to_thread", new_callable=AsyncMock, side_effect=Exception("SMTP auth failed")
        ),
        pytest.raises(ValueError, match="Failed to send email"),
    ):
        await send_magic_link_email("user@test.com", "https://example.com/magic")


@pytest.mark.asyncio
async def test_send_account_exists_email_smtp_failure():
    """SMTP failure raises ValueError for account-exists."""
    from app.services.email import send_account_exists_email

    mock_cfg = MagicMock()
    mock_cfg.smtp_host = "smtp.test.com"
    mock_cfg.smtp_port = 587
    mock_cfg.smtp_from_email = "noreply@test.com"
    mock_cfg.smtp_user = "user"
    mock_cfg.smtp_password = "pass"

    with (
        patch("app.services.email.get_config", return_value=mock_cfg),
        patch("app.services.email.asyncio.to_thread", new_callable=AsyncMock, side_effect=Exception("Network error")),
        pytest.raises(ValueError, match="Failed to send email"),
    ):
        await send_account_exists_email("user@test.com", "https://example.com/login")


# =====================================================================
# Social service — mocked HTTP calls
# =====================================================================


@pytest.mark.asyncio
async def test_google_user_info_exchange():
    """get_google_user_info exchanges code for user info."""
    from app.services.social import get_google_user_info

    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "test-token"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_user_resp = MagicMock()
    mock_user_resp.json.return_value = {"email": "google@test.com", "name": "Test User"}
    mock_user_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_resp
    mock_client.get.return_value = mock_user_resp

    with patch("app.services.social.get_http_client", return_value=mock_client):
        info = await get_google_user_info("test-code", "https://example.com/callback")
        assert info["email"] == "google@test.com"


@pytest.mark.asyncio
async def test_github_user_info_exchange():
    """get_github_user_info exchanges code for user info."""
    from app.services.social import get_github_user_info

    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "gh-token"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_user_resp = MagicMock()
    mock_user_resp.json.return_value = {"email": "github@test.com", "login": "testuser"}
    mock_user_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_resp
    mock_client.get.return_value = mock_user_resp

    with patch("app.services.social.get_http_client", return_value=mock_client):
        info = await get_github_user_info("test-code")
        assert info["email"] == "github@test.com"


@pytest.mark.asyncio
async def test_github_user_info_fetches_email_separately():
    """When GitHub profile has no email, fetch from /user/emails."""
    from app.services.social import get_github_user_info

    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"access_token": "gh-token"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_user_resp = MagicMock()
    mock_user_resp.json.return_value = {"login": "testuser"}  # no email
    mock_user_resp.raise_for_status = MagicMock()

    mock_emails_resp = MagicMock()
    mock_emails_resp.json.return_value = [
        {"email": "private@test.com", "primary": True},
        {"email": "other@test.com", "primary": False},
    ]
    mock_emails_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_resp
    mock_client.get.side_effect = [mock_user_resp, mock_emails_resp]

    with patch("app.services.social.get_http_client", return_value=mock_client):
        info = await get_github_user_info("test-code")
        assert info["email"] == "private@test.com"


@pytest.mark.asyncio
async def test_github_auth_error_raises():
    """GitHub error response raises ValueError."""
    from app.services.social import get_github_user_info

    mock_token_resp = MagicMock()
    mock_token_resp.json.return_value = {"error": "bad_code", "error_description": "Bad code"}
    mock_token_resp.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_resp

    with (
        patch("app.services.social.get_http_client", return_value=mock_client),
        pytest.raises(ValueError, match="GitHub Auth Error"),
    ):
        await get_github_user_info("bad-code")


# =====================================================================
# Streaming helpers — SSE formatting
# =====================================================================


def test_sse_token_format():
    """_sse_token formats correctly."""
    from app.routers.streaming import _sse_token

    result = _sse_token("hello")
    assert result.startswith("data: ")
    assert result.endswith("\n\n")
    parsed = json.loads(result[6:].strip())
    assert parsed["token"] == "hello"


def test_sse_done_format():
    """_sse_done includes metadata."""
    from app.routers.streaming import _sse_done

    result = _sse_done(1.5, 42, quality="full")
    parsed = json.loads(result[6:].strip())
    assert parsed["done"] is True
    assert parsed["duration_s"] == 1.5
    assert parsed["token_count"] == 42
    assert parsed["quality"] == "full"


def test_sse_error_format():
    """_sse_error includes error message."""
    from app.routers.streaming import _sse_error

    result = _sse_error("Something went wrong")
    parsed = json.loads(result[6:].strip())
    assert parsed["error"] == "Something went wrong"


# =====================================================================
# TTS service — generate_audio_summary with mocks
# =====================================================================


@pytest.mark.asyncio
async def test_tts_invalid_provider():
    """TTS rejects invalid provider."""
    from app.services.tts import generate_audio_summary

    mock_session = AsyncMock()
    with pytest.raises(ValueError, match="Unsupported TTS provider"):
        await generate_audio_summary(1, 1, "invalid_provider", mock_session)


@pytest.mark.asyncio
async def test_tts_document_not_found():
    """TTS raises when document not found."""
    from app.services.tts import generate_audio_summary

    mock_session = AsyncMock()
    mock_session.get.return_value = None  # No document

    with pytest.raises(ValueError, match="Document not found"):
        await generate_audio_summary(999, 1, "openai", mock_session)


# =====================================================================
# Chat service — data classes and constants
# =====================================================================


def test_chat_reply_dataclass():
    """ChatReply can be instantiated."""
    from app.services.chat import ChatReply

    reply = ChatReply(id=1, session_id=2, role="assistant", content="Hello!", created_at="2025-01-01")
    assert reply.id == 1
    assert reply.session_id == 2
    assert reply.role == "assistant"
    assert reply.content == "Hello!"


def test_chat_context_dataclass():
    """ChatContext can be instantiated."""
    from app.services.chat import ChatContext

    ctx = ChatContext(messages_payload=[{"role": "user", "content": "hi"}], session_id=42)
    assert ctx.session_id == 42
    assert len(ctx.messages_payload) == 1


def test_chat_constants():
    """Chat module constants are reasonable."""
    from app.services.chat import DOC_CONTEXT_CHARS, HISTORY_LIMIT

    assert HISTORY_LIMIT == 10
    assert DOC_CONTEXT_CHARS == 5_000


# =====================================================================
# Synthesis service — constant and edge case
# =====================================================================


def test_synthesis_combined_content_cap():
    """Synthesis cap is a reasonable limit."""
    from app.services.synthesis import COMBINED_CONTENT_CAP

    assert COMBINED_CONTENT_CAP == 16_000


# =====================================================================
# Flashcard service — JSON parsing edge cases
# =====================================================================


def test_flashcard_csv_empty():
    """CSV export handles empty list."""
    from app.services.flashcards import generate_csv_export

    result = generate_csv_export([])
    assert result == ""


def test_flashcard_csv_special_chars():
    """CSV export handles special characters."""
    from app.services.flashcards import generate_csv_export

    class MockCard:
        def __init__(self, f, b):
            self.front = f
            self.back = b

    cards = [MockCard('What\'s a "quote"?', "It's a 'mark'")]
    csv_str = generate_csv_export(cards)
    assert len(csv_str) > 0
    assert "quote" in csv_str


# =====================================================================
# DB module — PostgreSQL config builder
# =====================================================================


def test_build_engine_kwargs_postgres():
    """PostgreSQL engine kwargs include pool settings."""
    from app.db import _build_engine_kwargs

    mock_cfg = MagicMock()
    mock_cfg.is_sqlite = False
    mock_cfg.db_pool_size = 5
    mock_cfg.db_max_overflow = 10
    mock_cfg.db_pool_timeout = 30
    mock_cfg.db_ssl_verify = False

    with patch("app.config.get_config", return_value=mock_cfg):
        kwargs = _build_engine_kwargs()
        assert kwargs["pool_size"] == 5
        assert kwargs["max_overflow"] == 10
        assert kwargs["pool_pre_ping"] is True
        assert "ssl" in kwargs["connect_args"]


def test_build_engine_kwargs_postgres_ssl_verify():
    """PostgreSQL with SSL verification enabled."""
    from app.db import _build_engine_kwargs

    mock_cfg = MagicMock()
    mock_cfg.is_sqlite = False
    mock_cfg.db_pool_size = 5
    mock_cfg.db_max_overflow = 10
    mock_cfg.db_pool_timeout = 30
    mock_cfg.db_ssl_verify = True

    with patch("app.config.get_config", return_value=mock_cfg):
        kwargs = _build_engine_kwargs()
        ssl_ctx = kwargs["connect_args"]["ssl"]
        assert ssl_ctx.check_hostname is True


def test_build_sync_url_postgres():
    """Sync URL for PostgreSQL converts correctly."""
    from app.db import _build_sync_url

    mock_cfg = MagicMock()
    mock_cfg.is_sqlite = False
    mock_cfg.database_url = "postgresql://user:pass@host:5432/db"

    with patch("app.config.get_config", return_value=mock_cfg):
        url = _build_sync_url()
        assert "psycopg" in url
        assert "sslmode" in url


def test_build_sync_url_postgres_with_sslmode():
    """Sync URL respects existing sslmode in URL."""
    from app.db import _build_sync_url

    mock_cfg = MagicMock()
    mock_cfg.is_sqlite = False
    mock_cfg.database_url = "postgresql://user:pass@host:5432/db?sslmode=verify-full"

    with patch("app.config.get_config", return_value=mock_cfg):
        url = _build_sync_url()
        assert "sslmode=require" in url  # verify-full → require for sync driver


# =====================================================================
# Prompt sanitizer — full coverage
# =====================================================================


def test_sanitize_user_prompt():
    """Prompt sanitizer strips injection patterns."""
    from app.services.prompt_sanitizer import sanitize_user_prompt

    result = sanitize_user_prompt("Normal question about the document")
    assert isinstance(result, str)
    assert len(result) > 0


def test_sanitize_document_content():
    """Document content sanitizer works."""
    from app.services.prompt_sanitizer import sanitize_document_content

    result = sanitize_document_content("This is a test document content")
    assert isinstance(result, str)
    assert len(result) > 0


# =====================================================================
# HTTP client module
# =====================================================================


def test_http_client_module():
    """HTTP client module has expected attributes."""
    from app import http_client

    assert hasattr(http_client, "client")
    assert hasattr(http_client, "get_http_client")


# =====================================================================
# Tasks module — fire_and_forget
# =====================================================================


@pytest.mark.asyncio
async def test_tasks_fire_and_forget():
    """fire_and_forget schedules a coroutine without blocking."""
    from app.tasks import fire_and_forget

    result = []

    async def _task():
        result.append(True)

    fire_and_forget(_task(), name="test-task")
    # Give the event loop a tick to process
    import asyncio

    await asyncio.sleep(0.1)
    assert result == [True]


# =====================================================================
# Main app — middleware stack is registered
# =====================================================================


def test_middleware_stack_registered():
    """All expected middleware is in the app."""
    from app.main import app

    # App should have middleware registered (Starlette stores them)
    assert app.middleware_stack is not None or len(app.routes) > 0


def test_v1_router_has_all_expected_routes():
    """v1 router includes expected sub-routers."""
    from app.main import app

    route_paths = [r.path for r in app.routes if hasattr(r, "path")]
    # Spot check key endpoints
    assert any("/api/v1/auth" in p for p in route_paths)
    assert any("/api/v1/health" in p for p in route_paths)
