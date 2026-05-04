# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""FastAPI application factory.

The package's HTTP entry point. Production deployments instantiate
the app via uvicorn's factory mode (which constructs the app on
worker startup, ensuring ``OPENSALESTAX_DATABASE_URL`` is read at
the right moment)::

    uvicorn --factory opensalestax.app:create_app --host 0.0.0.0 --port 8080

For tests and embedded use cases, call :func:`create_app` directly.
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

# Import for side-effect: triggers state-module registration.
import opensalestax.states  # noqa: F401
from opensalestax import __version__
from opensalestax.api.v1 import router as v1_router
from opensalestax.settings import get_settings


def create_app() -> FastAPI:
    """Construct and return the FastAPI app.

    Separated from module-level ``app =`` so tests can build fresh
    instances and so future configuration (CORS, custom middleware,
    auth dispatch) can branch on settings without re-import side
    effects.

    Rate limiting (per constitution sec 6 / spec sec 6): the app
    installs a slowapi limiter scoped per-IP at the configured
    requests/minute (default 60). Tests can override the limiter
    by overriding settings before calling ``create_app``.
    """
    settings = get_settings()
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    )

    app = FastAPI(
        title="OpenSalesTax",
        version=__version__,
        description=(
            "Open-source US sales tax calculation API. "
            "Free, self-hostable, contributor-driven. "
            "Calculation only -- not legal or tax advice."
        ),
        docs_url="/v1/docs",
        redoc_url="/v1/redoc",
        openapi_url="/v1/openapi.json",
    )

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_handler)

    # Permit cross-origin browser callers (the opensalestax.org
    # calculator demo, third-party SPA integrations, etc.). The
    # default '*' is appropriate for the public demo engine; private
    # deployments should narrow ``OPENSALESTAX_CORS_ALLOWED_ORIGINS``.
    origins_raw = settings.cors_allowed_origins.strip()
    if origins_raw == "*":
        allow_origins: list[str] = ["*"]
    else:
        allow_origins = [o.strip() for o in origins_raw.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "X-API-Key"],
        max_age=600,
    )

    app.include_router(v1_router)

    @app.get("/", include_in_schema=False)
    async def _root() -> RedirectResponse:
        return RedirectResponse(url="/v1/docs")

    return app


def _rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Return a friendlier JSON body when a client exceeds the rate limit."""
    del request, exc
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Slow down or use API-key mode.",
        },
    )
