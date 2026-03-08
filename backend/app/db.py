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
    }

async_engine = create_async_engine(cfg.async_database_url, **_engine_kwargs)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    async_engine, expire_on_commit=False
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session


# --- Sync engine for Alembic migrations only ---
from sqlalchemy import create_engine as _sa_create_engine  # noqa: E402

_sync_url = cfg.database_url
# Ensure Alembic uses the raw (sync) URL or modernized psycopg v3 URL
if _sync_url.startswith("postgres://"):
    _sync_url = _sync_url.replace("postgres://", "postgresql+psycopg://", 1)
elif _sync_url.startswith("postgresql://"):
    _sync_url = _sync_url.replace("postgresql://", "postgresql+psycopg://", 1)
elif "+asyncpg" in _sync_url:
    _sync_url = _sync_url.replace("+asyncpg", "+psycopg")
elif "+aiosqlite" in _sync_url:
    _sync_url = _sync_url.replace("+aiosqlite", "")

# Sync fix for CockroachDB cloud
if "cockroachlabs.cloud" in _sync_url:
    if "sslmode=verify-full" in _sync_url:
        _sync_url = _sync_url.replace("sslmode=verify-full", "sslmode=require")
    elif "sslmode" not in _sync_url:
        _sync_url += ("&" if "?" in _sync_url else "?") + "sslmode=require"

_sync_engine_kwargs: dict[str, Any] = {}
if cfg.is_sqlite:
    _sync_engine_kwargs = {"connect_args": {"check_same_thread": False}}

sync_engine = _sa_create_engine(_sync_url, **_sync_engine_kwargs)