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
        _scheme_part, _rest = _db_url.split("://", 1)
        scheme = "cockroachdb+psycopg" if is_cockroach else "postgresql+psycopg"
        _db_url = f"{scheme}://{_rest}"
    
    # 2. Aggressive SSL Purification for Render CockroachDB
    # We strip sslrootcert/sslcert/sslkey because they point to paths that don't exist in the build container,
    # and we force sslmode=require which is safer and doesn't need them.
    from urllib.parse import urlparse, urlunparse, parse_qs, urlencode
    
    _u = urlparse(_db_url)
    _q = parse_qs(_u.query)
    
    # Remove junk
    for k in ["sslrootcert", "sslcert", "sslkey"]:
        _q.pop(k, None)
    
    # Force safe mode
    _q["sslmode"] = ["require"]
    
    _u = _u._replace(query=urlencode(_q, doseq=True))
    _db_url = urlunparse(_u)
    
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
    try:
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
    except Exception as e:
        print(f"ALEMBIC FATAL ERROR: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
