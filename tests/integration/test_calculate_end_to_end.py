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

    # Per-jurisdiction tax breakdown reconciles to the line total
    by_type = {j.type: j for j in line.jurisdictions}
    assert by_type["state"].tax == Decimal("6.0000")
    assert by_type["county"].tax == Decimal("0.5000")
    assert by_type["city"].tax == Decimal("1.0000")
    assert sum((j.tax for j in line.jurisdictions), Decimal("0")) == line.tax


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


@pytest.mark.asyncio
async def test_rate_modifier_replaces_state_rate(async_session: AsyncSession) -> None:
    """A TaxabilityRule.rate_modifier overrides the state-level rate.

    Replicates the IL/MO/AR/KS/MS/TN/UT/OK/VA/NC reduced-grocery-rate
    pattern: state portion is replaced with `rate_modifier`; local
    rates pass through unchanged. Encodes the engine guarantee that
    accounting callers depend on.
    """
    # Seed a state + county + city stack with a 6% state rate but a
    # rate_modifier of 1% on groceries (mirrors IL).
    state = State(abbrev="QQ", name="Quibble", has_sales_tax=True, sst_member=False)
    async_session.add(state)
    await async_session.flush()

    version = DataVersion(state_id=state.id, source="test", version_label="QQ-test-rate-modifier")
    async_session.add(version)
    await async_session.flush()

    state_auth = TaxAuthority(state_id=state.id, name="Quibble", authority_type="state")
    county_auth = TaxAuthority(state_id=state.id, name="Test County", authority_type="county")
    city_auth = TaxAuthority(state_id=state.id, name="Test City", authority_type="city")
    async_session.add_all([state_auth, county_auth, city_auth])
    await async_session.flush()

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
    async_session.add_all(
        [
            Boundary(authority_id=state_auth.id, zip5="11111", data_version_id=version.id),
            Boundary(authority_id=county_auth.id, zip5="11111", data_version_id=version.id),
            Boundary(authority_id=city_auth.id, zip5="11111", data_version_id=version.id),
        ]
    )

    # Reduced-grocery-rate rule: state rate becomes 1.0%; locals unchanged.
    async_session.add(
        TaxabilityRule(
            state_id=state.id,
            item_category="groceries",
            is_taxable=True,
            rate_modifier=Decimal("1.000"),
            effective_from=dt.date(1900, 1, 1),
            notes="Quibble taxes groceries at 1% state (locals at full rate).",
        )
    )
    await async_session.commit()

    result = await calculate_tax(
        async_session,
        zip5="11111",
        line_items=[
            LineItem(amount=Decimal("100.00"), category="general"),
            LineItem(amount=Decimal("100.00"), category="groceries"),
        ],
        effective_date=today,
    )

    general = next(line for line in result.lines if line.category == "general")
    groceries = next(line for line in result.lines if line.category == "groceries")

    # General: full 6% + 0.5% + 1% = 7.5% on $100 = $7.5000
    assert general.rate_pct == Decimal("7.500")
    assert general.tax == Decimal("7.5000")

    # Groceries: state portion overridden to 1% (not 6%), locals unchanged
    # 1% + 0.5% + 1% = 2.5% on $100 = $2.5000
    assert groceries.rate_pct == Decimal("2.500")
    assert groceries.tax == Decimal("2.5000")

    # Per-jurisdiction breakdown: state row should report 1%, not 6%
    by_type = {j.type: j for j in groceries.jurisdictions}
    assert by_type["state"].rate_pct == Decimal("1.000")
    assert by_type["state"].tax == Decimal("1.0000")
    assert by_type["county"].rate_pct == Decimal("0.500")
    assert by_type["county"].tax == Decimal("0.5000")
    assert by_type["city"].rate_pct == Decimal("1.000")
    assert by_type["city"].tax == Decimal("1.0000")
    # Per-jurisdiction reconciliation invariant still holds
    assert sum((j.tax for j in groceries.jurisdictions), Decimal("0")) == groceries.tax


@pytest.mark.asyncio
async def test_rate_modifier_zero_zeroes_state_portion(async_session: AsyncSession) -> None:
    """rate_modifier=0 means state portion is 0%; locals still apply.

    Mirrors the AR/KS/OK 2024-2026 grocery-tax-elimination pattern:
    state rate is 0% on the affected category, but local rates still
    apply at full local rate.
    """
    state = State(abbrev="QR", name="Quibble2", has_sales_tax=True, sst_member=False)
    async_session.add(state)
    await async_session.flush()
    version = DataVersion(
        state_id=state.id, source="test", version_label="QR-test-rate-modifier-zero"
    )
    async_session.add(version)
    await async_session.flush()

    state_auth = TaxAuthority(state_id=state.id, name="Quibble2", authority_type="state")
    county_auth = TaxAuthority(state_id=state.id, name="Test County 2", authority_type="county")
    async_session.add_all([state_auth, county_auth])
    await async_session.flush()

    today = dt.date.today()
    async_session.add_all(
        [
            Rate(
                authority_id=state_auth.id,
                rate_pct=Decimal("4.500"),
                effective_from=dt.date(2020, 1, 1),
                data_version_id=version.id,
            ),
            Rate(
                authority_id=county_auth.id,
                rate_pct=Decimal("2.000"),
                effective_from=dt.date(2020, 1, 1),
                data_version_id=version.id,
            ),
        ]
    )
    async_session.add_all(
        [
            Boundary(authority_id=state_auth.id, zip5="22222", data_version_id=version.id),
            Boundary(authority_id=county_auth.id, zip5="22222", data_version_id=version.id),
        ]
    )
    async_session.add(
        TaxabilityRule(
            state_id=state.id,
            item_category="groceries",
            is_taxable=True,
            rate_modifier=Decimal("0.000"),
            effective_from=dt.date(1900, 1, 1),
            notes="State portion eliminated; locals still apply.",
        )
    )
    await async_session.commit()

    result = await calculate_tax(
        async_session,
        zip5="22222",
        line_items=[LineItem(amount=Decimal("100.00"), category="groceries")],
        effective_date=today,
    )

    groceries = result.lines[0]
    # State portion 0%, county 2% = 2% effective
    assert groceries.rate_pct == Decimal("2.000")
    assert groceries.tax == Decimal("2.0000")
    by_type = {j.type: j for j in groceries.jurisdictions}
    assert by_type["state"].rate_pct == Decimal("0.000")
    assert by_type["state"].tax == Decimal("0")
    assert by_type["county"].rate_pct == Decimal("2.000")
    assert by_type["county"].tax == Decimal("2.0000")


async def _seed_threshold_state(
    async_session: AsyncSession,
    abbrev: str,
    name: str,
    zip5: str,
    state_rate: Decimal,
    threshold: Decimal,
    semantic: str,
    notes: str | None = None,
) -> None:
    """Seed a single-authority state with a clothing threshold rule."""
    state = State(abbrev=abbrev, name=name, has_sales_tax=True, sst_member=False)
    async_session.add(state)
    await async_session.flush()
    version = DataVersion(
        state_id=state.id, source="test", version_label=f"{abbrev}-test-threshold"
    )
    async_session.add(version)
    await async_session.flush()
    state_auth = TaxAuthority(state_id=state.id, name=name, authority_type="state")
    async_session.add(state_auth)
    await async_session.flush()
    async_session.add(
        Rate(
            authority_id=state_auth.id,
            rate_pct=state_rate,
            effective_from=dt.date(2020, 1, 1),
            data_version_id=version.id,
        )
    )
    async_session.add(Boundary(authority_id=state_auth.id, zip5=zip5, data_version_id=version.id))
    async_session.add(
        TaxabilityRule(
            state_id=state.id,
            item_category="clothing",
            is_taxable=True,
            taxable_threshold_amount=threshold,
            threshold_semantic=semantic,
            effective_from=dt.date(1900, 1, 1),
            notes=notes,
        )
    )
    await async_session.commit()


@pytest.mark.asyncio
async def test_threshold_below_exempt_zeros_under_cap(async_session: AsyncSession) -> None:
    """``below_exempt`` semantic mirrors NY's $110 clothing exemption.

    Items priced strictly under $110 are fully exempt; items at or
    above $110 are fully taxable at the standard rate.
    """
    await _seed_threshold_state(
        async_session,
        abbrev="QS",
        name="Quibble3",
        zip5="33333",
        state_rate=Decimal("4.000"),
        threshold=Decimal("110.00"),
        semantic="below_exempt",
        notes="Quibble3: clothing under $110 is exempt.",
    )

    today = dt.date.today()
    # $50 t-shirt -- under threshold, fully exempt.
    cheap = (
        await calculate_tax(
            async_session,
            zip5="33333",
            line_items=[LineItem(amount=Decimal("50.00"), category="clothing")],
            effective_date=today,
        )
    ).lines[0]
    assert cheap.tax == Decimal("0")
    assert cheap.note is not None
    assert "exempt" in cheap.note.lower()

    # $200 jacket -- at or above threshold, fully taxable.
    pricey = (
        await calculate_tax(
            async_session,
            zip5="33333",
            line_items=[LineItem(amount=Decimal("200.00"), category="clothing")],
            effective_date=today,
        )
    ).lines[0]
    assert pricey.tax == Decimal("8.0000")  # 4% of $200
    assert pricey.rate_pct == Decimal("4.000")


@pytest.mark.asyncio
async def test_threshold_above_excess_taxes_only_excess(async_session: AsyncSession) -> None:
    """``above_excess`` semantic mirrors MA's $175 / RI's $250 clothing exemption.

    Items at or below the threshold are fully exempt. Items above
    the threshold are taxed only on the **excess** above it.
    """
    await _seed_threshold_state(
        async_session,
        abbrev="QT",
        name="Quibble4",
        zip5="44444",
        state_rate=Decimal("6.250"),  # MA-like
        threshold=Decimal("175.00"),
        semantic="above_excess",
        notes="Quibble4: first $175 of clothing is exempt.",
    )

    today = dt.date.today()
    # $150 sweater -- under cap, fully exempt.
    under = (
        await calculate_tax(
            async_session,
            zip5="44444",
            line_items=[LineItem(amount=Decimal("150.00"), category="clothing")],
            effective_date=today,
        )
    ).lines[0]
    assert under.tax == Decimal("0")
    assert under.note is not None

    # $300 suit -- $125 excess taxable; $125 * 6.25% = $7.8125.
    over = (
        await calculate_tax(
            async_session,
            zip5="44444",
            line_items=[LineItem(amount=Decimal("300.00"), category="clothing")],
            effective_date=today,
        )
    ).lines[0]
    assert over.tax == Decimal("7.8125")
    assert over.amount == Decimal("300.00")
    assert over.note is not None
    assert "excess" in over.note.lower() or "first" in over.note.lower()
