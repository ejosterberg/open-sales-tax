# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the no_tax state module."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.no_tax import (
    ALASKA,
    DELAWARE,
    MONTANA,
    NEW_HAMPSHIRE,
    NO_TAX_STATES,
    OREGON,
    NoTaxState,
)


def test_five_no_tax_states_exported() -> None:
    assert len(NO_TAX_STATES) == 5
    assert {s.state_abbrev for s in NO_TAX_STATES} == {"AK", "DE", "MT", "NH", "OR"}


@pytest.mark.parametrize(
    "instance,abbrev,name",
    [
        (ALASKA, "AK", "Alaska"),
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


@pytest.mark.parametrize("abbrev", ["AK", "DE", "MT", "NH", "OR"])
def test_no_tax_states_are_registered(abbrev: str) -> None:
    mod = get_state_module(abbrev)
    assert mod is not None
    assert isinstance(mod, NoTaxState)


def test_parse_rates_returns_empty() -> None:
    rows = list(ALASKA.parse_rates(Path("ignored"), "ignored"))
    assert rows == []


def test_parse_boundaries_returns_empty() -> None:
    rows = list(ALASKA.parse_boundaries(Path("ignored"), "ignored"))
    assert rows == []


@pytest.mark.parametrize("category", ["general", "clothing", "groceries", "anything"])
def test_taxability_for_returns_non_taxable(category: str) -> None:
    rule = ALASKA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert rule.item_category == category


def test_special_cases_returns_empty() -> None:
    cases = list(ALASKA.special_cases())
    assert cases == []


def test_alaska_has_arsstc_note() -> None:
    """The ARSSTC caveat is documented in the notes for visibility."""
    assert "arsstc" in ALASKA.notes.lower()
    assert "Alaska Remote Seller Sales Tax Commission" in ALASKA.notes
