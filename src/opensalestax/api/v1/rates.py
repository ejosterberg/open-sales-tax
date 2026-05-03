# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""GET /v1/rates -- jurisdictional rate stack for an address."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.api.v1.schemas import JurisdictionRate, RatesResponse
from opensalestax.core.disclaimer import disclaimer
from opensalestax.core.lookup import lookup_jurisdictions_by_zip
from opensalestax.core.resolve import combined_rate_pct, resolve_rates_for_authorities
from opensalestax.db.session import get_session

router = APIRouter(tags=["rates"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
Zip5Q = Annotated[str, Query(min_length=5, max_length=5, pattern=r"^\d{5}$")]
Zip4Q = Annotated[
    str | None,
    Query(min_length=4, max_length=4, pattern=r"^\d{4}$"),
]


@router.get(
    "/rates",
    responses={400: {"description": "Malformed ZIP code rejected by the lookup layer."}},
)
async def get_rates(
    zip5: Zip5Q,
    session: SessionDep,
    zip4: Zip4Q = None,
) -> RatesResponse:
    """Return the active jurisdictional rate stack for ``zip5`` (+ optional ``zip4``).

    The combined rate is the sum of every jurisdiction's rate that
    applies to the address on today's date. Empty
    ``jurisdictions`` array means the ZIP isn't covered by any
    loaded state module's data.
    """
    try:
        authorities = await lookup_jurisdictions_by_zip(session, zip5, zip4)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    today = dt.date.today()
    resolved = await resolve_rates_for_authorities(session, authorities, today, "general")
    combined = combined_rate_pct(resolved)

    return RatesResponse(
        input={"zip5": zip5, "zip4": zip4},
        jurisdictions=[
            JurisdictionRate(
                name=r.authority.name,
                type=r.authority.authority_type,
                rate_pct=r.rate_pct,
            )
            for r in resolved
        ],
        combined_rate_pct=combined if resolved else Decimal("0"),
        disclaimer=disclaimer(),
    )
