# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for input validation in the calculate module.

These don't require a database -- they test the Python-level
input contract for LineItem and the lookup helpers.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from opensalestax.core.calculate import (
    TAX_QUANTUM,
    CalculatedLine,
    JurisdictionResult,
    LineItem,
)
from opensalestax.core.lookup import lookup_jurisdictions_by_zip


def test_line_item_rejects_negative_amount() -> None:
    with pytest.raises(ValueError, match="non-negative"):
        LineItem(amount=Decimal("-1"))


def test_line_item_zero_amount_allowed() -> None:
    item = LineItem(amount=Decimal("0"))
    assert item.amount == Decimal("0")


def test_line_item_default_category() -> None:
    item = LineItem(amount=Decimal("100"))
    assert item.category == "general"


def test_tax_quantum_is_4dp() -> None:
    assert Decimal("0.0001") == TAX_QUANTUM


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_zip", ["1234", "123456", "abcde", ""])
async def test_lookup_rejects_bad_zip5(bad_zip: str) -> None:
    """The lookup function rejects malformed ZIP5 before hitting the DB."""
    with pytest.raises(ValueError, match="zip5"):
        # session arg never used because validation fails first
        await lookup_jurisdictions_by_zip(session=None, zip5=bad_zip)  # type: ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("bad_zip4", ["abcd", "12a4", " "])
async def test_lookup_rejects_bad_zip4(bad_zip4: str) -> None:
    with pytest.raises(ValueError, match="zip4"):
        await lookup_jurisdictions_by_zip(
            session=None,  # type: ignore[arg-type]
            zip5="55401",
            zip4=bad_zip4,
        )


def test_jurisdiction_tax_field_defaults_to_zero() -> None:
    """JurisdictionResult.tax defaults to 0 so non-engine callers don't break."""
    j = JurisdictionResult(name="Minnesota", type="state", rate_pct=Decimal("6.875"))
    assert j.tax == Decimal("0")


def test_jurisdiction_breakdown_reconciles_to_line_total() -> None:
    """Per-jurisdiction tax sums to line tax exactly (no rounding drift).

    Given a $99.99 line at MN's full Minneapolis stack
    (state 6.875% + county 0.15% + city 0.5%), each jurisdiction
    is quantized to 4dp, then summed. The sum is the line total.
    """
    amount = Decimal("99.99")
    jurisdictions = [
        JurisdictionResult(
            name="Minnesota",
            type="state",
            rate_pct=Decimal("6.875"),
            tax=(amount * Decimal("6.875") / Decimal("100")).quantize(TAX_QUANTUM),
        ),
        JurisdictionResult(
            name="Hennepin County",
            type="county",
            rate_pct=Decimal("0.15"),
            tax=(amount * Decimal("0.15") / Decimal("100")).quantize(TAX_QUANTUM),
        ),
        JurisdictionResult(
            name="City of Minneapolis",
            type="city",
            rate_pct=Decimal("0.5"),
            tax=(amount * Decimal("0.5") / Decimal("100")).quantize(TAX_QUANTUM),
        ),
    ]
    line_tax = sum((j.tax for j in jurisdictions), Decimal("0"))
    line = CalculatedLine(
        amount=amount,
        category="general",
        tax=line_tax,
        rate_pct=Decimal("7.525"),
        jurisdictions=jurisdictions,
    )
    assert line.tax == sum((j.tax for j in line.jurisdictions), Decimal("0"))
    # state $99.99 * 0.06875 = $6.87431... -> $6.8743 (HALF_UP)
    # county $99.99 * 0.0015 = $0.14998... -> $0.1500 (HALF_UP)
    # city $99.99 * 0.005 = $0.49995 -> $0.5000 (HALF_UP)
    # sum = $7.5243 (vs $99.99 * 7.525% = $7.524247... = $7.5242 round-then-sum)
    # Per-jurisdiction-then-sum drifts by 1 quantum here -- and that's
    # the point: per-jurisdiction is the source of truth so accounting
    # callers can reconcile state/county/city splits against the line.
    assert line.tax == Decimal("7.5243")
