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

from collections.abc import Awaitable, Callable

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse, Response
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest

# Import for side-effect: triggers state-module registration.
import opensalestax.states  # noqa: F401
from opensalestax import __version__
from opensalestax.api.v1 import router as v1_router
from opensalestax.settings import get_settings

# Defense-in-depth response headers. JSON-only API; no CSP because the
# /v1/docs Swagger UI requires inline scripts that a strict CSP would
# block. HSTS + nosniff + frame-deny + locked-down referrer/permissions
# cover the realistic browser-side risks for an unauthenticated public
# engine sitting behind Cloudflare.
_SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach defense-in-depth response headers to every response."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        response = await call_next(request)
        for key, value in _SECURITY_HEADERS.items():
            response.headers.setdefault(key, value)
        return response


def _client_ip_proxy_aware(request: StarletteRequest) -> str:
    """Return the real client IP, preferring proxy-injected headers.

    Cloudflare-fronted prod sees ``request.client.host`` as the CF
    edge IP, which rotates across requests and would split each user's
    quota across many edges. ``CF-Connecting-IP`` (Cloudflare-set,
    unspoofable from outside CF) and the first hop of
    ``X-Forwarded-For`` carry the real client IP.

    Only invoked when ``OPENSALESTAX_TRUST_FORWARDED_FOR=true``.
    Trusting these headers without a proxy in front lets any caller
    pick their own rate-limit bucket, so the default is to use the
    immediate peer (``get_remote_address``).
    """
    cf = request.headers.get("CF-Connecting-IP")
    if cf:
        return cf
    xff = request.headers.get("X-Forwarded-For")
    if xff:
        first_hop = xff.split(",", 1)[0].strip()
        if first_hop:
            return first_hop
    return get_remote_address(request)


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
    key_func = _client_ip_proxy_aware if settings.trust_forwarded_for else get_remote_address
    limiter = Limiter(
        key_func=key_func,
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

    # Middleware execution order is REVERSE of add_middleware order:
    # CORS runs first on the request (handles preflight cleanly),
    # then SecurityHeaders, then SlowAPI enforces the limit. On the
    # response, SlowAPI -> SecurityHeaders -> CORS, so security
    # headers and CORS headers attach to all responses, including
    # 429s emitted by the rate-limit exception handler.
    app.add_middleware(SlowAPIMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

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
    """Return a friendlier JSON body when a client exceeds the rate limit.

    Sets a conservative ``Retry-After: 60`` so well-behaved clients (and
    our own integration tests) can back off cleanly. The actual reset
    window may be shorter under a sliding-window storage backend, but 60s
    is correct as an upper bound for a per-minute limit.
    """
    del request, exc
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Rate limit exceeded. Slow down or use API-key mode.",
        },
        headers={"Retry-After": "60"},
    )
