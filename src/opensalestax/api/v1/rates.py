# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""GET /v1/rates -- jurisdictional rate stack for an address."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.api.v1.schemas import JurisdictionRate, RatesResponse
from opensalestax.auth import authenticate
from opensalestax.core.coverage import coverage_warning_for_states
from opensalestax.core.disclaimer import disclaimer
from opensalestax.core.lookup import (
    lookup_jurisdictions_by_zip,
    lookup_jurisdictions_by_zip5_loose,
)
from opensalestax.core.resolve import combined_rate_pct, resolve_rates_for_authorities
from opensalestax.db.session import get_session

router = APIRouter(tags=["rates"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AuthDep = Annotated[object, Depends(authenticate)]
Zip5Q = Annotated[str, Query(min_length=5, max_length=5, pattern=r"^\d{5}$")]
Zip4Q = Annotated[
    str | None,
    Query(min_length=4, max_length=4, pattern=r"^\d{4}$"),
]


@router.get(
    "/rates",
    responses={
        400: {"description": "Malformed ZIP code rejected by the lookup layer."},
        401: {"description": "Missing or invalid X-API-Key (api_key auth mode only)."},
    },
)
async def get_rates(
    zip5: Zip5Q,
    session: SessionDep,
    auth: AuthDep,
    response: Response,
    zip4: Zip4Q = None,
) -> RatesResponse:
    """Return the active jurisdictional rate stack for ``zip5`` (+ optional ``zip4``).

    The combined rate is the sum of every jurisdiction's rate that
    applies to the address on today's date. Empty
    ``jurisdictions`` array means the ZIP isn't covered by any
    loaded state module's data.
    """
    try:
        # Mirror /v1/calculate's lookup precedence so /rates and /calculate
        # never disagree about which authorities apply: strict ZIP+4 lookup
        # when the caller supplies a +4, loose ZIP-5-only lookup otherwise.
        # Without this, ZIPs whose city authority lives only in type-4
        # records (e.g. SLC 84101 -> Salt Lake City) underreport on /rates
        # while /calculate gets it right -- a confusing inconsistency.
        if zip4 is not None:
            authorities = await lookup_jurisdictions_by_zip(session, zip5, zip4)
        else:
            authorities = await lookup_jurisdictions_by_zip5_loose(session, zip5)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    today = dt.date.today()
    resolved = await resolve_rates_for_authorities(session, authorities, today, "general")
    combined = combined_rate_pct(resolved)

    # Surface a coverage_warning for states with known local-tax gaps
    # (CO home-rule, LA parishes, AL home-rule, HI Maui dispute). Without
    # this, a CO ZIP returns a state-only 2.9% that a casual user might
    # mistake for the full combined rate.
    state_abbrevs = sorted(
        {
            r.authority.state.abbrev
            for r in resolved
            if r.authority.state is not None and r.authority.state.abbrev
        }
    )
    coverage_warning = coverage_warning_for_states(state_abbrevs)

    # Rate data refreshes quarterly when SST publishes new files.
    # 5 minutes is conservative -- mid-quarter changes that prompt a
    # `data load` on prod will still propagate within 5 min through
    # downstream caches. Cloudflare in front can cache by full URL
    # (zip5 + zip4 are query params), so this dramatically cuts
    # origin load for popular ZIPs.
    response.headers["Cache-Control"] = "public, max-age=300"

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
        coverage_warning=coverage_warning,
    )
