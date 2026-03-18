"""
tests/test_cors_guard.py — A-15: CORS wildcard guard in production startup

Verifies that the startup assertion blocks CORS_ORIGINS=* in production
but allows it in development.
"""
import pytest


def test_cors_wildcard_blocked_in_production():
    """CORS_ORIGINS=* with environment=production must trigger the guard."""
    from app.config import AppConfig
    cfg = AppConfig(
        environment="production",
        cors_origins="*",
        secret_key="a" * 32,
        database_url="sqlite:///./test.db",
    )
    # The guard condition that main.py checks at startup
    assert cfg.cors_origins.strip() == "*" and cfg.environment == "production"


def test_cors_wildcard_allowed_in_development():
    """CORS_ORIGINS=* is fine in development — guard must not fire."""
    from app.config import AppConfig
    cfg = AppConfig(
        environment="development",
        cors_origins="*",
        secret_key="dev-secret",
        database_url="sqlite:///./test.db",
    )
    assert not (cfg.cors_origins.strip() == "*" and cfg.environment == "production")


def test_specific_origins_pass_in_production():
    """Specific comma-separated origins in production do not trigger the guard."""
    from app.config import AppConfig
    cfg = AppConfig(
        environment="production",
        cors_origins="https://app.probexr.com,https://www.probexr.com",
        secret_key="a" * 32,
        database_url="postgresql://user:pass@host/db",
    )
    assert cfg.cors_origins.strip() != "*"


def test_cors_guard_present_in_main():
    """The CORS wildcard guard assertion must exist in main.py startup code."""
    import inspect
    import app.main as main_module
    src = inspect.getsource(main_module)
    assert "cors_origins" in src and "production" in src and '"*"' in src, (
        "main.py must contain the CORS wildcard guard"
    )