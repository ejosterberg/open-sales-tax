# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""GET /v1/health -- liveness + readiness signal."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax import __version__
from opensalestax.api.v1.schemas import HealthResponse
from opensalestax.db.session import get_session

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(session: AsyncSession = Depends(get_session)) -> HealthResponse:
    """Return service health.

    Reports the package version and a quick DB connectivity check.
    Status is ``"ok"`` when everything responds; ``"degraded"`` if
    the DB ping fails (the API still responds so monitors can
    distinguish "service down" from "DB down").
    """
    db_ok = await _ping_database(session)
    return HealthResponse(
        status="ok" if db_ok else "degraded",
        version=__version__,
        database_connected=db_ok,
    )


async def _ping_database(session: AsyncSession) -> bool:
    """Return True if the database accepts a trivial query."""
    try:
        result = await session.execute(text("SELECT 1"))
        return result.scalar() == 1
    except Exception:  # pragma: no cover -- defensive; intentionally broad
        return False
