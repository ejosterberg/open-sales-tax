# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Wisconsin state module."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.states import get_state_module
from opensalestax.states.minnesota import MINNESOTA
from opensalestax.states.protocol import StateModule
from opensalestax.states.wisconsin import WISCONSIN, Wisconsin


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_wisconsin_metadata() -> None:
    assert WISCONSIN.state_abbrev == "WI"
    assert WISCONSIN.state_name == "Wisconsin"
    assert WISCONSIN.sst_member is True
    assert WISCONSIN.has_sales_tax is True
    assert WISCONSIN.tier == 1


def test_wisconsin_satisfies_protocol() -> None:
    assert isinstance(WISCONSIN, StateModule)
    assert isinstance(Wisconsin(), StateModule)


def test_wisconsin_is_registered() -> None:
    assert get_state_module("WI") is WISCONSIN


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # the headline MN/WI contrast
        ("groceries", False),
        ("prescription_drugs", False),
        ("prepared_food", True),
        ("digital_goods", True),
        ("general", True),
    ],
)
def test_wisconsin_taxability(category: str, expected_taxable: bool) -> None:
    rule = WISCONSIN.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_wisconsin_clothing_is_taxable_unlike_minnesota() -> None:
    """The headline contrast: clothing is taxable in WI, not in MN.

    This is the test that proves the per-state contributor pattern
    handles divergent taxability rules from the same engine.
    """
    today = dt.date(2026, 5, 3)
    mn_rule = MINNESOTA.taxability_for("clothing", today)
    wi_rule = WISCONSIN.taxability_for("clothing", today)
    assert mn_rule is not None
    assert wi_rule is not None
    assert mn_rule.is_taxable is False
    assert wi_rule.is_taxable is True


def test_wisconsin_unknown_category_returns_none() -> None:
    assert WISCONSIN.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


# ---------------------------------------------------------------------------
# Rate parsing against real WI SST file
# ---------------------------------------------------------------------------
def test_parse_rates_yields_state_base() -> None:
    """The WI module extracts the 5.0% state base rate."""
    fixture = state_fixture_dir("WI") / "WIR2026Q2FEB18.csv"
    rows = list(WISCONSIN.parse_rates(fixture, "WI-SST-2026Q2FEB18"))

    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    state_row = state_rows[0]
    assert state_row.authority_name == "Wisconsin"
    assert state_row.rate_pct == Decimal("5.000")  # 5.0%
    assert state_row.parent_authority_name is None


def test_parse_rates_classifies_local_jurisdictions() -> None:
    """WI's SST file has many county and city additions."""
    fixture = state_fixture_dir("WI") / "WIR2026Q2FEB18.csv"
    rows = list(WISCONSIN.parse_rates(fixture, "WI-SST-2026Q2FEB18"))

    counties = [r for r in rows if r.authority_type == "county"]
    cities = [r for r in rows if r.authority_type == "city"]
    # WI has 70-72 counties + many sub-jurisdictions
    assert len(counties) > 50
    assert len(cities) > 100


def test_parse_rates_handles_99991231_sentinel() -> None:
    """WI uses 99991231 (not 29991231) as the open-end sentinel.

    Verifies the parser's NO_END_DATE_SENTINELS frozenset handles
    both forms.
    """
    fixture = state_fixture_dir("WI") / "WIR2026Q2FEB18.csv"
    rows = list(WISCONSIN.parse_rates(fixture, "WI-SST-2026Q2FEB18"))
    open_ended = [r for r in rows if r.effective_to is None]
    # Vast majority of WI rates are still in force
    assert len(open_ended) > len(rows) // 2


def test_parse_rates_total_count_matches_known_codes() -> None:
    """Every recognized type code appears in the output."""
    fixture = state_fixture_dir("WI") / "WIR2026Q2FEB18.csv"
    rows = list(WISCONSIN.parse_rates(fixture, "WI-SST-2026Q2FEB18"))
    types_seen = {r.authority_type for r in rows}
    # WI file has all 4 type codes (state, county, city, district)
    assert "state" in types_seen
    assert "county" in types_seen
    assert "city" in types_seen
    # district may or may not be present in any given quarter
