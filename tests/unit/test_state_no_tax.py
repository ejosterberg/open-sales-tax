# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the no_tax state module."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.no_tax import (
    DELAWARE,
    MONTANA,
    NEW_HAMPSHIRE,
    NO_TAX_STATES,
    OREGON,
    NoTaxState,
)

# Use Delaware as the canonical no-tax exemplar in tests that
# previously hard-coded ALASKA. Alaska moved to its own module in
# v0.49 (cities-only ARSSTC MVP) and is no longer a NoTaxState.
_EXEMPLAR = DELAWARE


def test_four_no_tax_states_exported() -> None:
    """v0.49 demoted AK from no-tax to a real state module; 4 remain."""
    assert len(NO_TAX_STATES) == 4
    assert {s.state_abbrev for s in NO_TAX_STATES} == {"DE", "MT", "NH", "OR"}


@pytest.mark.parametrize(
    "instance,abbrev,name",
    [
        (DELAWARE, "DE", "Delaware"),
        (MONTANA, "MT", "Montana"),
        (NEW_HAMPSHIRE, "NH", "New Hampshire"),
        (OREGON, "OR", "Oregon"),
    ],
)
def test_each_no_tax_state_metadata(instance: NoTaxState, abbrev: str, name: str) -> None:
    assert instance.state_abbrev == abbrev
    assert instance.state_name == name
    assert instance.has_sales_tax is False
    assert instance.sst_member is False
    assert instance.tier == 1


@pytest.mark.parametrize("abbrev", ["DE", "MT", "NH", "OR"])
def test_no_tax_states_are_registered(abbrev: str) -> None:
    mod = get_state_module(abbrev)
    assert mod is not None
    assert isinstance(mod, NoTaxState)


def test_parse_rates_returns_empty() -> None:
    rows = list(_EXEMPLAR.parse_rates(Path("ignored"), "ignored"))
    assert rows == []


def test_parse_boundaries_returns_empty() -> None:
    rows = list(_EXEMPLAR.parse_boundaries(Path("ignored"), "ignored"))
    assert rows == []


@pytest.mark.parametrize("category", ["general", "clothing", "groceries", "anything"])
def test_taxability_for_returns_non_taxable(category: str) -> None:
    rule = _EXEMPLAR.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert rule.item_category == category


def test_special_cases_returns_empty() -> None:
    cases = list(_EXEMPLAR.special_cases())
    assert cases == []


def test_alaska_no_longer_a_no_tax_state() -> None:
    """v0.49 promotes Alaska to a real state module via ARSSTC data."""
    mod = get_state_module("AK")
    assert mod is not None
    assert not isinstance(
        mod, NoTaxState
    ), "AK should now be the cities-only ARSSTC module, not NoTaxState"
    assert mod.has_sales_tax is True
