"""
Database engine and session factory.

Supports two modes driven by DATABASE_URL:
  - SQLite  (async via aiosqlite)  — development
  - PostgreSQL (async via asyncpg) — production

Connection pooling is configured for PostgreSQL only.

Design: Lazy initialization — engine is created on first access, not at import
time. This allows tests to override config before engine creation and avoids
paying connection-pool costs on serverless cold starts that only hit /health.
"""
import logging
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CockroachDB version fix
# ---------------------------------------------------------------------------

def _register_cockroachdb_version_fix(engine) -> None:
    """Patch the dialect's version parser so CockroachDB version strings don't crash."""
    original = engine.dialect.__class__._get_server_version_info

    def _patched_get_server_version_info(*args):
        try:
            return original(engine.dialect, args[-1])
        except (AssertionError, Exception):
            return (13, 0, 0)

    engine.dialect._get_server_version_info = _patched_get_server_version_info


# ---------------------------------------------------------------------------
# Lazy async engine + session factory
# ---------------------------------------------------------------------------

_async_engine = None
_async_session_factory = None


def _build_engine_kwargs() -> dict[str, Any]:
    """Build engine kwargs based on current config (SQLite vs PostgreSQL)."""
    from app.config import get_config
    cfg = get_config()

    if cfg.is_sqlite:
        return {
            "connect_args": {"check_same_thread": False},
            "poolclass": StaticPool,
            "echo": False,
        }
    else:
        return {
            "pool_size": cfg.db_pool_size,
            "max_overflow": cfg.db_max_overflow,
            "pool_timeout": cfg.db_pool_timeout,
            "pool_pre_ping": True,
            "echo": False,
            "connect_args": {"ssl": True},
        }


def get_engine():
    """Get or create the async engine (lazy singleton)."""
    global _async_engine
    if _async_engine is None:
        from app.config import get_config
        cfg = get_config()
        kwargs = _build_engine_kwargs()
        logger.info("Initializing Async Engine (scheme=%s)", cfg.async_database_url.split("://")[0])
        _async_engine = create_async_engine(cfg.async_database_url, **kwargs)
        _register_cockroachdb_version_fix(_async_engine)
    return _async_engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory (lazy singleton)."""
    global _async_session_factory
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _async_session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        yield session


def reset_engine() -> None:
    """Reset engine and session factory. Used in tests to allow config changes."""
    global _async_engine, _async_session_factory
    _async_engine = None
    _async_session_factory = None


# --- Backward compatibility aliases ---
# Some code imports `async_engine` directly. This property-like access
# triggers lazy creation on first use.
class _EngineProxy:
    """Proxy that lazily creates the engine on attribute access."""
    def __getattr__(self, name):
        return getattr(get_engine(), name)

async_engine = _EngineProxy()


# --- Sync engine for Alembic migrations only ---
from sqlalchemy import create_engine as _sa_create_engine  # noqa: E402


def _build_sync_url() -> str:
    from app.config import get_config
    cfg = get_config()
    _sync_url = cfg.database_url
    if _sync_url and not cfg.is_sqlite:
        _is_cockroach = "cockroachlabs.cloud" in _sync_url
        if "://" in _sync_url:
            _, _rest = _sync_url.split("://", 1)
            _scheme = "cockroachdb+psycopg" if _is_cockroach else "postgresql+psycopg"
            _sync_url = f"{_scheme}://{_rest}"

        if "sslmode=verify-full" in _sync_url:
            _sync_url = _sync_url.replace("sslmode=verify-full", "sslmode=require")
        elif "sslmode" not in _sync_url:
            _sync_url += ("&" if "?" in _sync_url else "?") + "sslmode=require"
    return _sync_url


def get_sync_engine():
    """Build sync engine for Alembic migrations."""
    from app.config import get_config
    cfg = get_config()
    kwargs: dict[str, Any] = {}
    if cfg.is_sqlite:
        kwargs = {"connect_args": {"check_same_thread": False}}
    return _sa_create_engine(_build_sync_url(), **kwargs)


# Backward compat: some Alembic code imports sync_engine directly
sync_engine = None  # Initialized lazily via get_sync_engine()
""" "Scalable, serverless-ready FastAPI backend." """