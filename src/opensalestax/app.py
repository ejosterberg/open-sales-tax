# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""FastAPI application factory.

The package's HTTP entry point. Production deployments instantiate
the app via uvicorn::

    uvicorn opensalestax.app:app --host 0.0.0.0 --port 8080

For tests and embedded use cases, call :func:`create_app` directly.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import RedirectResponse

# Import for side-effect: triggers state-module registration.
import opensalestax.states  # noqa: F401
from opensalestax import __version__
from opensalestax.api.v1 import router as v1_router


def create_app() -> FastAPI:
    """Construct and return the FastAPI app.

    Separated from module-level ``app =`` so tests can build fresh
    instances and so future configuration (CORS, custom middleware,
    auth dispatch) can branch on settings without re-import side
    effects.
    """
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

    app.include_router(v1_router)

    @app.get("/", include_in_schema=False)
    async def _root() -> RedirectResponse:
        return RedirectResponse(url="/v1/docs")

    return app


# Module-level instance for ``uvicorn opensalestax.app:app``
app = create_app()
