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
# Stage 1 -- builder: install Poetry, install deps into an app virtualenv
# ============================================================================
# Poetry lives in its OWN virtualenv (/opt/poetry) and installs the app
# into a SEPARATE target virtualenv (/opt/venv). Only /opt/venv is copied
# into the runtime image, so Poetry and its tooling dependencies (dulwich,
# virtualenv, filelock, keyring, ...) never ship to production. Before
# 2026-11-12 Poetry was pip-installed into the system site-packages that
# the runtime stage copied wholesale, which put 41 of the image's 43
# known advisories into production without the app ever importing them.
FROM python:3.11-slim-bookworm AS builder

ENV PIP_NO_CACHE_DIR=1     PIP_DISABLE_PIP_VERSION_CHECK=1     POETRY_VERSION=1.8.4     POETRY_VIRTUALENVS_CREATE=false     VIRTUAL_ENV=/opt/venv     PATH=/opt/venv/bin:$PATH

RUN python -m venv /opt/poetry  && /opt/poetry/bin/pip install --no-cache-dir "poetry==${POETRY_VERSION}"  && python -m venv /opt/venv

WORKDIR /build

# Copy only the manifest first to maximize layer caching on dep changes.
# With VIRTUAL_ENV set and virtualenv creation off, Poetry installs into
# /opt/venv rather than into its own environment.
COPY pyproject.toml poetry.lock ./
RUN /opt/poetry/bin/poetry install --no-interaction --no-ansi --no-root --without dev

# Copy the application source last (changes most often)
COPY src ./src
COPY alembic.ini ./
RUN /opt/poetry/bin/poetry install --no-interaction --no-ansi --only-root


# ============================================================================
# Stage 2 -- runtime: minimal slim image with only what's needed
# ============================================================================
FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONPATH=/app/src

# Non-root user for runtime
RUN groupadd -r app && useradd -r -g app -m app

WORKDIR /app

# Copy the app virtualenv + source from the builder. Same base image and
# same /opt/venv path, so the venv's interpreter links and script
# shebangs stay valid. Poetry's /opt/poetry is deliberately NOT copied.
COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /build/src /app/src
COPY --from=builder /build/alembic.ini /app/alembic.ini

# Belt + suspenders: PYTHONPATH above is the primary mechanism, but
# also "install" the project as a `.pth` so import works whether or
# not PYTHONPATH is honored by all entrypoints (e.g. alembic env.py).
RUN echo '/app/src' > /opt/venv/lib/python3.11/site-packages/opensalestax-src.pth

USER app

EXPOSE 8080

# Health check uses /v1/health which the API exposes
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import urllib.request, sys; \
        sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/v1/health').status == 200 else 1)"

CMD ["uvicorn", "--factory", "opensalestax.app:create_app", \
     "--host", "0.0.0.0", "--port", "8080"]
