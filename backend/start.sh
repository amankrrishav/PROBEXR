#!/usr/bin/env bash
set -euo pipefail

echo "==> Running Alembic migrations..."
if alembic upgrade head; then
    echo "==> Migrations complete."
else
    echo "⚠️  Alembic migrations failed (exit $?). Starting server anyway."
    echo "    Check DATABASE_URL and database availability."
fi

echo "==> Starting Gunicorn..."
exec gunicorn app.main:app \
    -w "${WEB_CONCURRENCY:-2}" \
    -k uvicorn.workers.UvicornWorker \
    --bind "0.0.0.0:${PORT:-10000}" \
    --timeout 120 \
    --graceful-timeout 30 \
    --header "server:"
