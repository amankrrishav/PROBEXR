"""Alembic env.py — supports both sync and async engines, env-driven DATABASE_URL."""
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlmodel import SQLModel
import app.models  # noqa: F401 — registers all models on metadata

target_metadata = SQLModel.metadata

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Override sqlalchemy.url from environment if available
_db_url = os.environ.get("DATABASE_URL")
if _db_url:
    # 1. Robust Scheme Construction
    is_cockroach = "cockroachlabs.cloud" in _db_url
    if "://" in _db_url:
        _, rest = _db_url.split("://", 1)
        scheme = "cockroachdb+psycopg" if is_cockroach else "postgresql+psycopg"
        _db_url = f"{scheme}://{rest}"
    
    # 2. SSL Fallback for Render
    if "sslmode=verify-full" in _db_url:
        _db_url = _db_url.replace("sslmode=verify-full", "sslmode=require")
    elif "sslmode" not in _db_url:
        _db_url += ("&" if "?" in _db_url else "?") + "sslmode=require"
    
    print(f"Alembic: Connecting with scheme {_db_url.split(':', 1)[0]} (Cockroach={is_cockroach})")
    config.set_main_option("sqlalchemy.url", _db_url)


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
