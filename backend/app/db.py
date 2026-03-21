"""
Database engine and session factory.

Supports two modes driven by DATABASE_URL:
  - SQLite  (async via aiosqlite)  — development
  - PostgreSQL (async via asyncpg) — production

Connection pooling is configured for PostgreSQL only.
"""
import logging
from typing import Any, AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
# CockroachDB version strings often break SQLAlchemy's standard Postgres parser.
# We patch the dialect method directly (not via event) because _get_server_version_info
# is called *during* the first connect inside dialect.initialize() — an event listener
# would fire too late.
def _register_cockroachdb_version_fix(engine) -> None:
    """Patch the dialect's version parser so CockroachDB version strings don't crash."""
    original = engine.dialect.__class__._get_server_version_info

    def _patched_get_server_version_info(*args):
        # When set as an instance attr, Python does NOT auto-pass `self`.
        # SQLAlchemy calls self._get_server_version_info(connection),
        # so args = (connection,) here. But `original` is an unbound class
        # method expecting (self, connection), so we prepend the dialect.
        try:
            return original(engine.dialect, args[-1])
        except (AssertionError, Exception):
            return (13, 0, 0)

    engine.dialect._get_server_version_info = _patched_get_server_version_info

from app.config import get_config

logger = logging.getLogger(__name__)

cfg = get_config()

_engine_kwargs: dict[str, Any] = {}

if cfg.is_sqlite:
    # SQLite + aiosqlite: use StaticPool (single connection, no pooling)
    _engine_kwargs = {
        "connect_args": {"check_same_thread": False},
        "poolclass": StaticPool,
        "echo": False,
    }
else:
    # PostgreSQL + asyncpg: real connection pooling
    _engine_kwargs = {
        "pool_size": cfg.db_pool_size,
        "max_overflow": cfg.db_max_overflow,
        "pool_timeout": cfg.db_pool_timeout,
        "pool_pre_ping": True,
        "echo": False,
        "connect_args": {"ssl": True},
    }

logger.info("App: Initializing Async Engine (scheme=%s)", cfg.async_database_url.split("://")[0])
async_engine = create_async_engine(cfg.async_database_url, **_engine_kwargs)

# Apply the scoped CockroachDB version fix to this engine only (A-19)
_register_cockroachdb_version_fix(async_engine)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


# --- Sync engine for Alembic migrations only ---
from sqlalchemy import create_engine as _sa_create_engine  # noqa: E402

# Robust sync URL builder for Alembic/Migrations
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

_sync_engine_kwargs: dict[str, Any] = {}
if cfg.is_sqlite:
    _sync_engine_kwargs = {"connect_args": {"check_same_thread": False}}

sync_engine = _sa_create_engine(_sync_url, **_sync_engine_kwargs)