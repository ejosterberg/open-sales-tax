# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""End-to-end integration tests for the calculate engine.

Seeds a small in-DB jurisdiction graph (a no-tax state, plus a
hypothetical state-county-city stack) and exercises the full
lookup -> resolve -> calculate pipeline against it.

Skipped automatically when ``OPENSALESTAX_DATABASE_URL`` is not
set (see ``tests/conftest.py``).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.core import LineItem, calculate_tax
from opensalestax.db.models import (
    Boundary,
    DataVersion,
    Rate,
    State,
    TaxabilityRule,
    TaxAuthority,
)


@pytest.mark.asyncio
async def test_no_tax_state_returns_zero(async_session: AsyncSession) -> None:
    """A state with has_sales_tax=False and no boundaries returns 0 tax."""
    de = State(abbrev="DE", name="Delaware", has_sales_tax=False, sst_member=False)
    async_session.add(de)
    await async_session.commit()

    result = await calculate_tax(
        async_session,
        zip5="19901",  # Dover, DE
        line_items=[LineItem(amount=Decimal("100.00"))],
    )

    assert result.subtotal == Decimal("100.00")
    assert result.tax_total == Decimal("0")
    assert len(result.lines) == 1
    line = result.lines[0]
    assert line.tax == Decimal("0")
    assert line.rate_pct == Decimal("0")
    assert line.note  # non-empty explanation
    assert "ZIP 19901" in line.note
    assert "Calculation only" in result.disclaimer


@pytest.mark.asyncio
async def test_full_jurisdiction_stack(async_session: AsyncSession) -> None:
    """Seed a state + county + city stack and verify rates combine correctly."""
    # State row
    fictional = State(
        abbrev="ZZ",
        name="Fictionalia",
        has_sales_tax=True,
        sst_member=True,
    )
    async_session.add(fictional)
    await async_session.flush()  # populate fictional.id

    # Data version (required for boundaries)
    version = DataVersion(
        state_id=fictional.id,
        source="test",
        version_label="ZZ-test-2026Q2",
    )
    async_session.add(version)
    await async_session.flush()

    # Authorities: state, county, city
    state_auth = TaxAuthority(state_id=fictional.id, name="Fictionalia", authority_type="state")
    county_auth = TaxAuthority(state_id=fictional.id, name="Test County", authority_type="county")
    city_auth = TaxAuthority(state_id=fictional.id, name="Test City", authority_type="city")
    async_session.add_all([state_auth, county_auth, city_auth])
    await async_session.flush()

    # Rates: 6% state + 0.5% county + 1% city = 7.5% combined
    today = dt.date.today()
    async_session.add_all(
        [
            Rate(
                authority_id=state_auth.id,
                rate_pct=Decimal("6.000"),
                effective_from=dt.date(2020, 1, 1),
                data_version_id=version.id,
            ),
            Rate(
                authority_id=county_auth.id,
                rate_pct=Decimal("0.500"),
                effective_from=dt.date(2020, 1, 1),
                data_version_id=version.id,
            ),
            Rate(
                authority_id=city_auth.id,
                rate_pct=Decimal("1.000"),
                effective_from=dt.date(2020, 1, 1),
                data_version_id=version.id,
            ),
        ]
    )

    # All three authorities cover ZIP 99999 (no ZIP+4 range -> matches any)
    async_session.add_all(
        [
            Boundary(
                authority_id=state_auth.id,
                zip5="99999",
                data_version_id=version.id,
            ),
            Boundary(
                authority_id=county_auth.id,
                zip5="99999",
                data_version_id=version.id,
            ),
            Boundary(
                authority_id=city_auth.id,
                zip5="99999",
                data_version_id=version.id,
            ),
        ]
    )

    await async_session.commit()

    result = await calculate_tax(
        async_session,
        zip5="99999",
        line_items=[LineItem(amount=Decimal("100.00"))],
        effective_date=today,
    )

    assert result.subtotal == Decimal("100.00")
    # 7.5% of $100 = $7.50
    assert result.tax_total == Decimal("7.5000")
    line = result.lines[0]
    assert line.rate_pct == Decimal("7.500")
    assert len(line.jurisdictions) == 3
    types = {j.type for j in line.jurisdictions}
    assert types == {"state", "county", "city"}


@pytest.mark.asyncio
async def test_taxability_rule_zeroes_out_clothing(async_session: AsyncSession) -> None:
    """A category with is_taxable=False bypasses rate calculation."""
    # State with a single 5% rate that would otherwise apply
    fictional = State(abbrev="YY", name="Yonderland", has_sales_tax=True, sst_member=True)
    async_session.add(fictional)
    await async_session.flush()

    version = DataVersion(state_id=fictional.id, source="test", version_label="YY-test-2026Q2")
    async_session.add(version)
    await async_session.flush()

    state_auth = TaxAuthority(state_id=fictional.id, name="Yonderland", authority_type="state")
    async_session.add(state_auth)
    await async_session.flush()

    async_session.add_all(
        [
            Rate(
                authority_id=state_auth.id,
                rate_pct=Decimal("5.000"),
                effective_from=dt.date(2020, 1, 1),
                data_version_id=version.id,
            ),
            Boundary(
                authority_id=state_auth.id,
                zip5="88888",
                data_version_id=version.id,
            ),
            # Clothing is non-taxable in Yonderland
            TaxabilityRule(
                state_id=fictional.id,
                item_category="clothing",
                is_taxable=False,
                effective_from=dt.date(1900, 1, 1),
                notes="Clothing is non-taxable in Yonderland.",
            ),
        ]
    )
    await async_session.commit()

    result = await calculate_tax(
        async_session,
        zip5="88888",
        line_items=[
            LineItem(amount=Decimal("100.00"), category="general"),
            LineItem(amount=Decimal("50.00"), category="clothing"),
        ],
    )

    # General line: 5% of $100 = $5.00; clothing line: $0.00
    general = next(line for line in result.lines if line.category == "general")
    clothing = next(line for line in result.lines if line.category == "clothing")
    assert general.tax == Decimal("5.0000")
    assert clothing.tax == Decimal("0")
    assert clothing.note is not None
    assert "non-taxable" in clothing.note.lower()
    assert result.tax_total == Decimal("5.0000")


@pytest.mark.asyncio
async def test_no_jurisdictions_returns_zero(async_session: AsyncSession) -> None:
    """If no boundaries match the ZIP, the engine returns 0 with a note."""
    result = await calculate_tax(
        async_session,
        zip5="00000",  # never registered
        line_items=[LineItem(amount=Decimal("100.00"))],
    )
    assert result.tax_total == Decimal("0")
    assert result.lines[0].note is not None
    assert "00000" in result.lines[0].note


@pytest.mark.asyncio
async def test_empty_line_items_returns_empty(async_session: AsyncSession) -> None:
    result = await calculate_tax(async_session, zip5="55401", line_items=[])
    assert result.subtotal == Decimal("0")
    assert result.tax_total == Decimal("0")
    assert result.lines == []
