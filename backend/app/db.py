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
# Scoped via an engine event listener rather than a global class mutation (A-19).
def _register_cockroachdb_version_fix(engine) -> None:
    """Attach a connect event that overrides the server version check for this
    engine only — does NOT mutate PGDialect globally.

    Must attach to sync_engine because SQLAlchemy does not support async
    engine events directly.
    """
    from sqlalchemy import event

    # AsyncEngine exposes sync_engine for synchronous event listeners
    sync_engine = getattr(engine, "sync_engine", engine)

    @event.listens_for(sync_engine, "connect")
    def _set_version(dbapi_conn, connection_record):
        # Patch the dialect instance on this engine only
        if hasattr(engine.dialect, "_get_server_version_info"):
            engine.dialect._get_server_version_info = lambda self, conn: (13, 0, 0)

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