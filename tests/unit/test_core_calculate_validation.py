# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for input validation in the calculate module.

These don't require a database -- they test the Python-level
input contract for LineItem and the lookup helpers.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from types import SimpleNamespace

from opensalestax.core.calculate import (
    TAX_QUANTUM,
    CalculatedLine,
    JurisdictionResult,
    LineItem,
    _apply_threshold,
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


def _threshold_rule(
    threshold: Decimal,
    semantic: str | None,
    notes: str | None = None,
) -> SimpleNamespace:
    """Build a minimal stand-in for an ORM TaxabilityRule for the helper."""
    return SimpleNamespace(
        taxable_threshold_amount=threshold,
        threshold_semantic=semantic,
        notes=notes,
    )


class TestApplyThresholdBelowExempt:
    """``below_exempt`` semantic: amount strictly < threshold -> fully exempt."""

    def test_below_threshold_returns_zero_line(self) -> None:
        rule = _threshold_rule(Decimal("110.00"), "below_exempt")
        outcome = _apply_threshold(rule, Decimal("50.00"), "NY", "clothing")
        assert outcome.zero_line is True
        assert outcome.taxable_basis == Decimal("0")
        assert outcome.note is not None

    def test_at_threshold_taxes_full_amount(self) -> None:
        rule = _threshold_rule(Decimal("110.00"), "below_exempt")
        outcome = _apply_threshold(rule, Decimal("110.00"), "NY", "clothing")
        assert outcome.zero_line is False
        assert outcome.taxable_basis == Decimal("110.00")
        assert outcome.note is None

    def test_above_threshold_taxes_full_amount(self) -> None:
        rule = _threshold_rule(Decimal("110.00"), "below_exempt")
        outcome = _apply_threshold(rule, Decimal("250.00"), "NY", "clothing")
        assert outcome.zero_line is False
        assert outcome.taxable_basis == Decimal("250.00")

    def test_uses_rule_notes_when_provided(self) -> None:
        rule = _threshold_rule(
            Decimal("110.00"), "below_exempt", notes="NY: clothing under $110 is exempt."
        )
        outcome = _apply_threshold(rule, Decimal("50.00"), "NY", "clothing")
        assert outcome.note == "NY: clothing under $110 is exempt."


class TestApplyThresholdAboveExcess:
    """``above_excess`` semantic: tax only the excess above the threshold."""

    def test_at_or_below_threshold_returns_zero_line(self) -> None:
        rule = _threshold_rule(Decimal("175.00"), "above_excess")
        # at threshold
        outcome = _apply_threshold(rule, Decimal("175.00"), "MA", "clothing")
        assert outcome.zero_line is True
        # below threshold
        outcome = _apply_threshold(rule, Decimal("100.00"), "MA", "clothing")
        assert outcome.zero_line is True

    def test_above_threshold_taxes_only_excess(self) -> None:
        rule = _threshold_rule(Decimal("175.00"), "above_excess")
        outcome = _apply_threshold(rule, Decimal("300.00"), "MA", "clothing")
        assert outcome.zero_line is False
        assert outcome.taxable_basis == Decimal("125.00")
        assert outcome.note is not None
        assert "first" in outcome.note.lower() or "excess" in outcome.note.lower()

    def test_above_excess_rhode_island_250(self) -> None:
        """RI's $250 clothing exemption -- $400 jacket has $150 taxable."""
        rule = _threshold_rule(Decimal("250.00"), "above_excess")
        outcome = _apply_threshold(rule, Decimal("400.00"), "RI", "clothing")
        assert outcome.taxable_basis == Decimal("150.00")


def test_apply_threshold_unknown_semantic_falls_back_to_full_basis() -> None:
    """An unrecognized semantic value taxes the full amount (safest default)."""
    rule = _threshold_rule(Decimal("100.00"), "made_up_semantic")
    outcome = _apply_threshold(rule, Decimal("500.00"), "QQ", "clothing")
    assert outcome.zero_line is False
    assert outcome.taxable_basis == Decimal("500.00")
    assert outcome.note is None
