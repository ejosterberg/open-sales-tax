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
)
from opensalestax.auth import authenticate
from opensalestax.core.calculate import LineItem, calculate_tax
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
    try:
        result = await calculate_tax(
            session,
            zip5=body.address.zip5,
            line_items=items,
            zip4=body.address.zip4,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

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
                    )
                    for j in line.jurisdictions
                ],
                note=line.note,
            )
            for line in result.lines
        ],
        disclaimer=result.disclaimer,
    )
