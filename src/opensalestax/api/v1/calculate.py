# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""POST /v1/calculate -- top-level tax calculation for line items."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.api.v1.schemas import (
    CalculatedLineResponse,
    CalculateRequest,
    CalculateResponse,
    JurisdictionRate,
    ShippingOutput,
)
from opensalestax.auth import authenticate
from opensalestax.core.calculate import LineItem, ShippingRequest, calculate_tax
from opensalestax.core.coverage import coverage_warning_for_states
from opensalestax.db.session import get_session

router = APIRouter(tags=["calculate"])

SessionDep = Annotated[AsyncSession, Depends(get_session)]
AuthDep = Annotated[object, Depends(authenticate)]


@router.post(
    "/calculate",
    responses={
        400: {"description": "Engine-level validation error (e.g. malformed ZIP)."},
        401: {"description": "Missing or invalid X-API-Key (api_key auth mode only)."},
    },
)
async def calculate(
    body: CalculateRequest,
    session: SessionDep,
    auth: AuthDep,
) -> CalculateResponse:
    """Calculate sales tax for a list of line items at a given address.

    Returns a per-line decomposition with the constitution-§13
    disclaimer. Lines for non-taxable categories return ``tax=0``
    with an explanatory ``note``. Unknown ZIPs return ``tax=0`` for
    every line, also with a ``note`` -- the call doesn't fail.
    """
    items = [LineItem(amount=li.amount, category=li.category) for li in body.line_items]
    shipping_request: ShippingRequest | None = None
    if body.shipping is not None:
        shipping_request = ShippingRequest(
            amount=body.shipping.amount,
            separately_stated=body.shipping.separately_stated,
            is_handling_charge=body.shipping.is_handling_charge,
            method=body.shipping.method,
        )
    try:
        result = await calculate_tax(
            session,
            zip5=body.address.zip5,
            line_items=items,
            zip4=body.address.zip4,
            shipping=shipping_request,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    # Surface a coverage_warning for states with known local-tax gaps
    # (CO home-rule, LA parishes, AL home-rule, HI Maui dispute).
    # ``result.data_versions`` is declared on the dataclass but isn't
    # populated by the calculate engine; derive the state set from the
    # actual line-level jurisdictions instead. The state-typed
    # authority's name is the canonical state name ("Colorado" /
    # "Louisiana" / "Alabama" / "Hawaii"), which we reverse-map to
    # USPS abbrev via the warning table's reverse mapping below.
    _STATE_NAME_TO_ABBREV = {
        "Colorado": "CO",
        "Louisiana": "LA",
        "Alabama": "AL",
        "Hawaii": "HI",
    }
    state_abbrevs = sorted(
        {
            _STATE_NAME_TO_ABBREV[j.name]
            for line in result.lines
            for j in line.jurisdictions
            if j.type == "state" and j.name in _STATE_NAME_TO_ABBREV
        }
    )
    coverage_warning = coverage_warning_for_states(state_abbrevs)

    shipping_output: ShippingOutput | None = None
    if result.shipping is not None:
        shipping_output = ShippingOutput(
            amount=result.shipping.amount,
            tax_amount=result.shipping.tax_amount,
            rate_pct=result.shipping.rate_pct,
            taxable_reason=result.shipping.taxable_reason,
        )

    return CalculateResponse(
        subtotal=result.subtotal,
        tax_total=result.tax_total,
        lines=[
            CalculatedLineResponse(
                amount=line.amount,
                category=line.category,
                tax=line.tax,
                rate_pct=line.rate_pct,
                jurisdictions=[
                    JurisdictionRate(
                        name=j.name,
                        type=j.type,
                        rate_pct=j.rate_pct,
                        tax=j.tax,
                    )
                    for j in line.jurisdictions
                ],
                note=line.note,
            )
            for line in result.lines
        ],
        disclaimer=result.disclaimer,
        coverage_warning=coverage_warning,
        shipping=shipping_output,
    )
