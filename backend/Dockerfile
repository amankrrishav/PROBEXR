# =============================================================================
# PROBEXR backend — multi-stage Dockerfile
# Build:  docker build -t probexr-backend .
# Run:    docker run --env-file .env -p 8000:8000 probexr-backend
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — builder
# Installs all Python dependencies into a virtual environment.
# We use the full slim image here so pip can compile C extensions if needed.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS builder

WORKDIR /build

# Install build tools needed by some C-extension packages (cffi, asyncpg…)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create a virtualenv so the runtime stage can simply copy it
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install pinned, hashed requirements first (better layer caching)
COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip install --require-hashes -r requirements.txt

# ---------------------------------------------------------------------------
# Stage 2 — runtime
# Lean image: no compiler, no build headers, minimal attack surface.
# ---------------------------------------------------------------------------
FROM python:3.12-slim AS runtime

WORKDIR /app

# Runtime system deps only (libpq for asyncpg/psycopg at runtime)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the pre-built virtualenv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create a non-root user before copying code
RUN groupadd --gid 1001 appgroup \
    && useradd --uid 1001 --gid appgroup --no-create-home --shell /sbin/nologin appuser

# Copy application source (never .env — secrets come in via environment variables)
COPY app/       ./app/
COPY alembic/   ./alembic/
COPY alembic.ini .
COPY run.py     .
# requirements.txt is baked into the image; no need to ship it to /app

# Hand ownership of the working directory to the non-root user
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Readiness / liveness probe — hits the public health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/v1/ || exit 1

# exec form → uvicorn receives SIGTERM directly (clean shutdown)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]