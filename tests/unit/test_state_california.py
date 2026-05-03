# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the California state module (Phase 2 Section C)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.california import CALIFORNIA, California
from opensalestax.states.protocol import StateModule


def test_california_metadata() -> None:
    assert CALIFORNIA.state_abbrev == "CA"
    assert CALIFORNIA.state_name == "California"
    assert CALIFORNIA.sst_member is False  # CA is NOT in SST
    assert CALIFORNIA.has_sales_tax is True
    assert CALIFORNIA.tier == 1
    assert CALIFORNIA.self_seeded is True  # signals the loader to skip file lookup


def test_california_satisfies_protocol() -> None:
    assert isinstance(CALIFORNIA, StateModule)
    assert isinstance(California(), StateModule)


def test_california_is_registered() -> None:
    assert get_state_module("CA") is CALIFORNIA


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # contrast with MN (non-taxable in MN)
        ("groceries", False),
        ("prescription_drugs", False),
        ("prepared_food", True),
        ("digital_goods", True),
        ("general", True),
    ],
)
def test_california_taxability(category: str, expected_taxable: bool) -> None:
    rule = CALIFORNIA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_california_unknown_category_returns_none() -> None:
    assert CALIFORNIA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_california_parse_rates_yields_725_pct() -> None:
    """California's statewide rate is 7.25% effective 2017-01-01."""
    rows = list(CALIFORNIA.parse_rates(None, "v0.2-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "California"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("7.250")
    assert row.effective_from == dt.date(2017, 1, 1)
    assert row.effective_to is None


def test_california_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(CALIFORNIA.parse_rates(None, "test"))
    rows_with_path = list(CALIFORNIA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_california_parse_boundaries_returns_empty() -> None:
    """v0.2 doesn't ship CA boundaries; v0.3 priority."""
    rows = list(CALIFORNIA.parse_boundaries(None, "v0.2-statewide"))
    assert rows == []


def test_california_special_cases_empty() -> None:
    cases = list(CALIFORNIA.special_cases())
    assert cases == []


def test_california_clothing_cites_no_exemption() -> None:
    """The clothing rule explicitly notes CA has no clothing exemption."""
    rule = CALIFORNIA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "no clothing exemption" in (rule.notes or "").lower()
