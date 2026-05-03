# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the state-module Protocol and its data carriers."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states.protocol import (
    BoundaryRow,
    RateRow,
    SpecialCase,
    StateModule,
    TaxabilityRule,
)


def test_rate_row_is_frozen() -> None:
    from dataclasses import FrozenInstanceError

    row = RateRow(
        authority_name="Minnesota",
        authority_type="state",
        rate_pct=Decimal("6.875"),
        effective_from=dt.date(2024, 1, 1),
    )
    with pytest.raises(FrozenInstanceError):
        row.rate_pct = Decimal("0")  # type: ignore[misc]


def test_boundary_row_optional_fields_default_to_none() -> None:
    row = BoundaryRow(
        authority_name="Minneapolis",
        authority_type="city",
        zip5="55401",
    )
    assert row.zip4_low is None
    assert row.zip4_high is None
    assert row.address_pattern is None


def test_taxability_rule_default_effective_from() -> None:
    rule = TaxabilityRule(item_category="clothing", is_taxable=False)
    assert rule.effective_from == dt.date(1900, 1, 1)


def test_special_case_defaults() -> None:
    sc = SpecialCase(name="grocery_holiday", description="Test")
    assert sc.affected_categories == ()
    assert sc.applies_from is None


def test_no_tax_state_satisfies_protocol() -> None:
    """NoTaxState is structurally a StateModule (runtime check)."""
    from opensalestax.states.no_tax import NoTaxState

    instance = NoTaxState("ZZ", "Test State")
    assert isinstance(instance, StateModule)
