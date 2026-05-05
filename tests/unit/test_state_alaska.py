# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Alaska state module (v0.49 promotion from NoTaxState).

Alaska has NO statewide sales tax but ~110 municipalities collect
local sales tax at rates 0%-7.5%. Pre-v0.49 every AK ZIP returned
0%. v0.49 ships a real state module seeded from the Alaska Remote
Seller Sales Tax Commission (ARSSTC) member-jurisdictions list;
v0.50 / v0.51 extended coverage to 42 verified municipalities.

These tests lock in:

1. Alaska is registered as a real state module, not a NoTaxState.
2. ``has_sales_tax`` is True (local-only, but the engine collects
   via cities) and ``self_seeded`` is True (signals the loader to
   skip the SST upstream file lookup).
3. The 0% statewide row is yielded by ``parse_rates``.
4. Every covered city in ``AK_CITIES`` produces a RateRow + the
   expected (state, city) BoundaryRow pair per ZIP.
5. Anchorage and Fairbanks are NOT in the city table (documented
   gap from the v0.49 module docstring -- both return 0% per
   in-state retail practice).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

from opensalestax.states import get_state_module
from opensalestax.states.ak_data import AK_CITIES, AK_STATE_RATE_PCT
from opensalestax.states.alaska import ALASKA, Alaska
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_alaska_metadata() -> None:
    assert ALASKA.state_abbrev == "AK"
    assert ALASKA.state_name == "Alaska"
    assert ALASKA.sst_member is False
    assert ALASKA.has_sales_tax is True
    assert ALASKA.tier == 1
    assert ALASKA.self_seeded is True


def test_alaska_satisfies_protocol() -> None:
    assert isinstance(ALASKA, StateModule)
    assert isinstance(Alaska(), StateModule)


def test_alaska_registered_under_ak() -> None:
    """``get_state_module("AK")`` returns the Alaska class, not NoTaxState."""
    mod = get_state_module("AK")
    assert mod is not None
    assert isinstance(mod, Alaska)


# ---------------------------------------------------------------------------
# parse_rates -- state row + per-city rows
# ---------------------------------------------------------------------------
def test_parse_rates_yields_state_at_zero_pct() -> None:
    rows = list(ALASKA.parse_rates(None, "v0.49-arsstc"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    assert state_rows[0].authority_name == "Alaska"
    assert state_rows[0].rate_pct == AK_STATE_RATE_PCT
    assert state_rows[0].rate_pct == Decimal("0.000")


def test_parse_rates_yields_one_row_per_city() -> None:
    rows = list(ALASKA.parse_rates(None, "ignored"))
    city_rows = [r for r in rows if r.authority_type == "city"]
    assert len(city_rows) == len(AK_CITIES)
    assert {r.authority_name for r in city_rows} == set(AK_CITIES)


def test_parse_rates_city_rates_match_ak_cities() -> None:
    rows = list(ALASKA.parse_rates(None, "ignored"))
    by_name = {r.authority_name: r for r in rows if r.authority_type == "city"}
    for city, (_borough, expected_rate, _zips) in AK_CITIES.items():
        assert by_name[city].rate_pct == expected_rate


# ---------------------------------------------------------------------------
# parse_boundaries -- state + city per covered ZIP
# ---------------------------------------------------------------------------
def test_parse_boundaries_yields_state_and_city_per_zip() -> None:
    rows = list(ALASKA.parse_boundaries(None, "ignored"))
    by_zip: dict[str, list[str]] = {}
    for row in rows:
        by_zip.setdefault(row.zip5, []).append(row.authority_type)
    # Every ZIP that appears at all must have BOTH a state and a city row.
    for zip5, types in by_zip.items():
        assert "state" in types, f"ZIP {zip5} missing state binding"
        assert "city" in types, f"ZIP {zip5} missing city binding"


def test_parse_boundaries_covers_every_ak_city_zip() -> None:
    """Each ZIP in AK_CITIES gets both state + city BoundaryRows."""
    rows = list(ALASKA.parse_boundaries(None, "ignored"))
    state_zips = {r.zip5 for r in rows if r.authority_type == "state"}
    city_zips = {r.zip5 for r in rows if r.authority_type == "city"}
    expected_zips = {z for _city, (_b, _r, zs) in AK_CITIES.items() for z in zs}
    assert state_zips == expected_zips
    assert city_zips == expected_zips


# ---------------------------------------------------------------------------
# Documented gaps
# ---------------------------------------------------------------------------
def test_anchorage_not_in_ak_cities() -> None:
    """Anchorage Municipality is intentionally excluded (in-state retail = 0%)."""
    assert "Anchorage" not in AK_CITIES


def test_fairbanks_not_in_ak_cities() -> None:
    """Fairbanks city has no city sales tax (FNSB also imposes none)."""
    assert "Fairbanks" not in AK_CITIES


# ---------------------------------------------------------------------------
# Taxability / holidays / special cases
# ---------------------------------------------------------------------------
def test_taxability_for_general_is_taxable_with_caveat() -> None:
    rule = ALASKA.taxability_for("general", dt.date(2026, 5, 5))
    assert rule is not None
    assert rule.is_taxable is True
    assert "ARSSTC" in rule.notes  # documented sourcing


def test_no_sales_tax_holidays() -> None:
    assert list(ALASKA.holidays_for(2026)) == []


def test_no_special_cases() -> None:
    assert list(ALASKA.special_cases()) == []


# ---------------------------------------------------------------------------
# self_seeded loader contract: source_file may be None
# ---------------------------------------------------------------------------
def test_parse_rates_accepts_none_source() -> None:
    """The loader passes ``source_file=None`` for self_seeded states."""
    rows = list(ALASKA.parse_rates(None, "v0.49-arsstc"))
    assert len(rows) > 0


def test_parse_boundaries_accepts_none_source() -> None:
    rows = list(ALASKA.parse_boundaries(None, "v0.49-arsstc"))
    assert len(rows) > 0


def test_parse_rates_accepts_path_source() -> None:
    """The signature also accepts a Path for typing compatibility."""
    rows = list(ALASKA.parse_rates(Path("ignored"), "v0.49-arsstc"))
    assert len(rows) > 0
