# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Minnesota state module."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.states import get_state_module
from opensalestax.states.minnesota import MINNESOTA, Minnesota
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_minnesota_metadata() -> None:
    assert MINNESOTA.state_abbrev == "MN"
    assert MINNESOTA.state_name == "Minnesota"
    assert MINNESOTA.sst_member is True
    assert MINNESOTA.has_sales_tax is True
    assert MINNESOTA.tier == 1


def test_minnesota_satisfies_protocol() -> None:
    assert isinstance(MINNESOTA, StateModule)


def test_minnesota_is_registered() -> None:
    assert get_state_module("MN") is MINNESOTA
    assert get_state_module("mn") is MINNESOTA  # case-insensitive


# ---------------------------------------------------------------------------
# Taxability matrix (constitutional contrast with WI)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", False),  # the headline MN/WI contrast
        ("groceries", False),
        ("prescription_drugs", False),
        ("prepared_food", True),
        ("digital_goods", True),
        ("general", True),
    ],
)
def test_minnesota_taxability(category: str, expected_taxable: bool) -> None:
    rule = MINNESOTA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # always documents the source


def test_minnesota_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert MINNESOTA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_minnesota_clothing_rule_cites_statute() -> None:
    """Constitutional check: every taxability rule explains why."""
    rule = MINNESOTA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "297A.67" in (rule.notes or "")  # MN clothing exemption statute


# ---------------------------------------------------------------------------
# Rate parsing against real MN SST file
# ---------------------------------------------------------------------------
def test_parse_rates_yields_state_base() -> None:
    """The MN module extracts the 6.875% state base rate from a real SST file."""
    fixture = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    rows = list(MINNESOTA.parse_rates(fixture, "MN-SST-2026Q2FEB18"))

    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    state_row = state_rows[0]
    assert state_row.authority_name == "Minnesota"
    assert state_row.rate_pct == Decimal("6.87500")  # 6.875%
    assert state_row.parent_authority_name is None  # state has no parent


def test_parse_rates_classifies_local_jurisdictions() -> None:
    """Local additions (type 01) are classified as cities."""
    fixture = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    rows = list(MINNESOTA.parse_rates(fixture, "MN-SST-2026Q2FEB18"))

    city_rows = [r for r in rows if r.authority_type == "city"]
    assert city_rows  # MN has many local additions
    sample = city_rows[0]
    assert sample.parent_authority_name == "Minnesota"
    # Most MN local additions are 0.5%
    assert sample.rate_pct > Decimal("0")


def test_parse_rates_handles_special_districts() -> None:
    """Type-63 rows (transit / special districts) are emitted as 'district'."""
    fixture = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    rows = list(MINNESOTA.parse_rates(fixture, "MN-SST-2026Q2FEB18"))

    district_rows = [r for r in rows if r.authority_type == "district"]
    assert district_rows  # MN's metro-transit district is in this file


def test_parse_rates_total_count_matches_known_codes() -> None:
    """Every recognized type code appears in the output."""
    fixture = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    rows = list(MINNESOTA.parse_rates(fixture, "MN-SST-2026Q2FEB18"))
    types_seen = {r.authority_type for r in rows}
    assert types_seen == {"state", "county", "city", "district"}


# ---------------------------------------------------------------------------
# Boundary parsing
# ---------------------------------------------------------------------------
def test_parse_boundaries_emits_state_and_county_rows() -> None:
    """Each MN ZIP yields BOTH a state and a county BoundaryRow.

    The state row is essential: without it the engine's lookup
    join finds only the county authority and silently drops MN's
    6.875% statewide rate.
    """
    fixture = state_fixture_dir("MN") / "MNB2026Q2FEB18-sample.csv"
    rows = list(MINNESOTA.parse_boundaries(fixture, "MN-SST-2026Q2FEB18"))

    assert rows
    types = {row.authority_type for row in rows}
    assert "state" in types
    assert "county" in types
    state_rows = [r for r in rows if r.authority_type == "state"]
    county_rows = [r for r in rows if r.authority_type == "county"]
    assert all(r.authority_name == "Minnesota" for r in state_rows)
    # State boundaries are deduped per-ZIP
    assert len({r.zip5 for r in state_rows}) == len(state_rows)
    for row in rows:
        assert len(row.zip5) == 5
        assert row.zip5.isdigit()
    # Every county-bound ZIP also has a state-bound row
    assert {r.zip5 for r in county_rows} <= {r.zip5 for r in state_rows}


# ---------------------------------------------------------------------------
# Special cases (none in Phase 1)
# ---------------------------------------------------------------------------
def test_minnesota_special_cases_empty_in_phase_1() -> None:
    cases = list(MINNESOTA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Protocol-only contract: the class itself is a StateModule
# ---------------------------------------------------------------------------
def test_minnesota_class_satisfies_protocol() -> None:
    """A fresh instance also satisfies the Protocol (not just the registered one)."""
    instance = Minnesota()
    assert isinstance(instance, StateModule)
