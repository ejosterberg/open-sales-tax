# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for input validation in the calculate module.

These don't require a database -- they test the Python-level
input contract for LineItem and the lookup helpers.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from opensalestax.core.calculate import TAX_QUANTUM, LineItem
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
