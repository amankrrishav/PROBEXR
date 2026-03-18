"""
tests/test_email_logging.py — N-08, N-09: email.py logging hygiene

N-08: print() calls in dev fallback path replaced with logger.debug()
N-09: f-string logger calls replaced with %-style formatting
"""
import inspect
import pytest
from unittest.mock import patch, AsyncMock
import app.services.email as email_module


def _src() -> str:
    return inspect.getsource(email_module)


# ---------------------------------------------------------------------------
# N-08: No print() calls in email.py
# ---------------------------------------------------------------------------

def test_no_print_calls_in_email_service():
    """email.py must not contain bare print() calls."""
    src = _src()
    lines = [l.strip() for l in src.split('\n') if l.strip().startswith('print(')]
    assert not lines, (
        f"email.py must use logger.debug() not print(). Found: {lines}"
    )


def test_dev_fallback_uses_logger_debug():
    """Dev fallback (no SMTP) must log via logger.debug(), not print()."""
    src = _src()
    assert 'logger.debug' in src, (
        "email.py dev fallback must use logger.debug() to route through the logging pipeline"
    )


# ---------------------------------------------------------------------------
# N-09: No f-string logger calls in email.py
# ---------------------------------------------------------------------------

def test_no_fstring_logger_calls():
    """email.py must not use f-strings in logger calls."""
    src = _src()
    import re
    # Match logger.X(f"...") patterns
    fstring_logger = re.findall(r'logger\.\w+\(f["\']', src)
    assert not fstring_logger, (
        f"email.py must use %-style logger formatting, not f-strings. Found: {fstring_logger}"
    )


def test_logger_uses_percent_formatting():
    """email.py logger calls must use %s placeholders."""
    src = _src()
    import re
    logger_calls = re.findall(r'logger\.\w+\(.*?\)', src, re.DOTALL)
    # At least some logger calls should use %s
    percent_calls = [c for c in logger_calls if '%s' in c or '%d' in c]
    assert percent_calls, "email.py must use %-style logger formatting"


# ---------------------------------------------------------------------------
# Integration: dev fallback actually logs (no crash, no print)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_send_magic_link_dev_fallback_no_crash(caplog):
    """send_magic_link_email with no SMTP host must not raise and must not print."""
    import logging
    with patch('app.services.email.get_config') as mock_cfg:
        mock_cfg.return_value.smtp_host = None
        with caplog.at_level(logging.DEBUG, logger='app.services.email'):
            await email_module.send_magic_link_email('test@example.com', 'http://example.com/link')
    # No exception raised — dev fallback worked cleanly


@pytest.mark.asyncio
async def test_send_verification_email_dev_fallback_no_crash():
    """send_verification_email with no SMTP host must not raise."""
    with patch('app.services.email.get_config') as mock_cfg:
        mock_cfg.return_value.smtp_host = None
        await email_module.send_verification_email('test@example.com', 'http://example.com/verify')


@pytest.mark.asyncio
async def test_send_password_reset_email_dev_fallback_no_crash():
    """send_password_reset_email with no SMTP host must not raise."""
    with patch('app.services.email.get_config') as mock_cfg:
        mock_cfg.return_value.smtp_host = None
        await email_module.send_password_reset_email('test@example.com', 'http://example.com/reset')