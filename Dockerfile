# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
#
# Multi-stage Dockerfile for OpenSalesTax.
#
# Build:
#     docker build -t opensalestax:dev .
#
# Run:
#     docker run --rm -p 8080:8080 \
#       -e OPENSALESTAX_DATABASE_URL=postgresql+asyncpg://... \
#       opensalestax:dev

# ============================================================================
# Stage 1 -- builder: install Poetry, export deps to a virtualenv
# ============================================================================
FROM python:3.11-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=1.8.4 \
    POETRY_VIRTUALENVS_CREATE=false

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

WORKDIR /build

# Copy only the manifest first to maximize layer caching on dep changes
COPY pyproject.toml poetry.lock ./
RUN poetry install --no-interaction --no-ansi --no-root --without dev

# Copy the application source last (changes most often)
COPY src ./src
COPY alembic.ini ./
# README.md is referenced in pyproject.toml; poetry-core needs it to build wheel metadata.
COPY README.md ./
# Use pip instead of `poetry install --only-root`: the latter silently skips
# console-script wiring when POETRY_VIRTUALENVS_CREATE=false on Poetry 1.8.x.
RUN pip install --no-cache-dir --no-deps --no-build-isolation .

# ============================================================================
# Stage 2 -- runtime: minimal slim image with only what's needed
# ============================================================================
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

# postgresql-client provides `psql` (and `pg_dump`) used by `opensalestax data restore`.
# The package is small (~5 MB) and only pulls libpq; no server is installed.
RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Non-root user for runtime
RUN groupadd -r app && useradd -r -g app -m app

# Pre-create data dir owned by app so volume mounts inherit the right owner.
RUN mkdir -p /var/lib/opensalestax/data \
    && chown -R app:app /var/lib/opensalestax

WORKDIR /app

# Copy installed deps + source from the builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY --from=builder /build/src /app/src
COPY --from=builder /build/alembic.ini /app/alembic.ini

# .pth ensures imports work for all entrypoints (e.g. alembic env.py).
RUN echo '/app/src' > /usr/local/lib/python3.11/site-packages/opensalestax-src.pth

USER app

EXPOSE 8080

# Health check uses /v1/health which the API exposes
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request, sys; \
        sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/v1/health').status == 200 else 1)"

CMD ["uvicorn", "--factory", "opensalestax.app:create_app", \
     "--host", "0.0.0.0", "--port", "8080"]
