# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the New York state module (v0.26 ratchet).

New York is a non-SST state with a 4% statewide rate plus a layered
local structure unique among US states:

- Per-county rates (3.0%-4.875%, with NYC's five boroughs at 0%
  county portion because the NYC-level 4.5% city tax replaces it).
- Metropolitan Commuter Transportation District (MCTD) surcharge of
  0.375% in 12 downstate counties (NYC's five plus Long Island
  plus parts of the Hudson Valley) modeled as a ``district``
  authority.
- Per-city rates (only NYC, Yonkers, New Rochelle, Mount Vernon,
  and White Plains impose their own city sales tax).

Tests verify metadata, registration, Protocol conformance, the
combined NYC rate (8.875%) and Yonkers rate (8.875%, distinct
breakdown), and the ``below_exempt`` clothing-threshold rule.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.new_york import NEW_YORK, NewYork
from opensalestax.states.ny_data import (
    NY_CITIES,
    NY_COUNTY_RATE_PCT,
    NY_MCTD_COUNTIES,
    NY_MCTD_DISTRICT_NAME,
    NY_MCTD_RATE,
    NY_STATE_RATE_PCT,
)
from opensalestax.states.protocol import StateModule


def test_new_york_metadata() -> None:
    assert NEW_YORK.state_abbrev == "NY"
    assert NEW_YORK.state_name == "New York"
    assert NEW_YORK.sst_member is False  # NY is NOT in SST
    assert NEW_YORK.has_sales_tax is True
    assert NEW_YORK.tier == 1
    assert NEW_YORK.self_seeded is True


def test_new_york_satisfies_protocol() -> None:
    assert isinstance(NEW_YORK, StateModule)
    assert isinstance(NewYork(), StateModule)


def test_new_york_is_registered() -> None:
    assert get_state_module("NY") is NEW_YORK


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable; section 1115(a)(30) exempts <$110 (threshold rule)
        ("groceries", False),  # exempt per section 1115(a)(1)
        ("prescription_drugs", False),
        ("prepared_food", True),
        ("digital_goods", True),  # prewritten software is taxable
        ("general", True),
    ],
)
def test_new_york_taxability(category: str, expected_taxable: bool) -> None:
    rule = NEW_YORK.taxability_for(category, dt.date(2026, 5, 4))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_new_york_unknown_category_returns_none() -> None:
    assert NEW_YORK.taxability_for("alpaca-fur", dt.date(2026, 5, 4)) is None


def test_new_york_clothing_uses_below_exempt_threshold() -> None:
    """Section 1115(a)(30): clothing/footwear under $110 per item is
    exempt from the state 4% rate. Encoded with ``below_exempt``
    semantic and a $110 threshold.
    """
    rule = NEW_YORK.taxability_for("clothing", dt.date(2026, 5, 4))
    assert rule is not None
    assert rule.taxable_threshold_amount == Decimal("110.00")
    assert rule.threshold_semantic == "below_exempt"
    assert "1115(a)(30)" in (rule.notes or "")


def test_new_york_parse_rates_yields_state_4_pct() -> None:
    """NY's statewide rate is 4.0% per N.Y. Tax Law section 1105.

    Post-v0.26 the loader also yields the MCTD district, per-county
    rows, and per-city rows; the state row must still be present and
    correct.
    """
    rows = list(NEW_YORK.parse_rates(None, "v0.26-state-county-mctd-city"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    row = state_rows[0]
    assert row.authority_name == "New York"
    assert row.rate_pct == Decimal("4.000")
    assert row.parent_authority_name is None


def test_new_york_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(NEW_YORK.parse_rates(None, "test"))
    rows_with_path = list(NEW_YORK.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_new_york_parse_rates_yields_mctd_district() -> None:
    """The MCTD surcharge is emitted exactly once as a district at 0.375%."""
    rows = list(NEW_YORK.parse_rates(None, "v0.26-state-county-mctd-city"))
    district_rows = [r for r in rows if r.authority_type == "district"]
    assert len(district_rows) == 1
    mctd = district_rows[0]
    assert mctd.authority_name == NY_MCTD_DISTRICT_NAME
    assert mctd.rate_pct == NY_MCTD_RATE
    assert mctd.rate_pct == Decimal("0.375")
    assert mctd.parent_authority_name == "New York"


def test_new_york_parse_rates_yields_nyc_city_at_4_5_pct() -> None:
    """New York City's city portion is 4.5% on top of state + MCTD."""
    rows = list(NEW_YORK.parse_rates(None, "v0.26-state-county-mctd-city"))
    by_name = {r.authority_name: r for r in rows if r.authority_type == "city"}
    nyc = by_name["New York City"]
    assert nyc.rate_pct == Decimal("4.500")
    assert nyc.parent_authority_name == "New York County"


def test_new_york_parse_rates_yields_yonkers_city_at_1_5_pct() -> None:
    """Yonkers' city portion is 1.5% on top of state + Westchester + MCTD."""
    rows = list(NEW_YORK.parse_rates(None, "v0.26-state-county-mctd-city"))
    by_name = {r.authority_name: r for r in rows if r.authority_type == "city"}
    yonkers = by_name["Yonkers"]
    assert yonkers.rate_pct == Decimal("1.500")
    assert yonkers.parent_authority_name == "Westchester County"


def test_new_york_parse_rates_yields_county_rates() -> None:
    """Per-county RateRows match :data:`NY_COUNTY_RATE_PCT`."""
    rows = list(NEW_YORK.parse_rates(None, "v0.26-state-county-mctd-city"))
    by_name = {r.authority_name: r for r in rows if r.authority_type == "county"}
    # Spot-check a handful of representative counties.
    assert by_name["Erie County"].rate_pct == Decimal("4.750")
    assert by_name["Monroe County"].rate_pct == Decimal("4.000")
    assert by_name["Westchester County"].rate_pct == Decimal("3.000")
    assert by_name["Nassau County"].rate_pct == Decimal("4.250")
    assert by_name["Suffolk County"].rate_pct == Decimal("4.375")
    assert by_name["New York County"].rate_pct == Decimal("0.000")


def test_new_york_combined_nyc_rate_is_8_875_pct() -> None:
    """NYC combined rate must be 8.875% = state 4 + city 4.5 + MCTD 0.375.

    The county portion is 0% for New York County (Manhattan), which is
    the canonical county for the consolidated NYC entry.
    """
    nyc_county, nyc_city_rate, _ = NY_CITIES["New York City"]
    state = NY_STATE_RATE_PCT
    county = NY_COUNTY_RATE_PCT[nyc_county]
    mctd = NY_MCTD_RATE if nyc_county in NY_MCTD_COUNTIES else Decimal("0")
    combined = state + county + mctd + nyc_city_rate
    assert combined == Decimal("8.875")


def test_new_york_combined_yonkers_rate_is_8_875_pct() -> None:
    """Yonkers combined rate must be 8.875% (different breakdown than NYC).

    state 4 + Westchester 3 + MCTD 0.375 + Yonkers 1.5 = 8.875%
    """
    county, city_rate, _ = NY_CITIES["Yonkers"]
    state = NY_STATE_RATE_PCT
    county_rate = NY_COUNTY_RATE_PCT[county]
    mctd = NY_MCTD_RATE if county in NY_MCTD_COUNTIES else Decimal("0")
    combined = state + county_rate + mctd + city_rate
    assert combined == Decimal("8.875")


def test_new_york_combined_buffalo_rate_is_8_75_pct() -> None:
    """Buffalo combined rate: state 4 + Erie 4.75 + no MCTD + no city = 8.75%."""
    county, city_rate, _ = NY_CITIES["Buffalo"]
    state = NY_STATE_RATE_PCT
    county_rate = NY_COUNTY_RATE_PCT[county]
    mctd = NY_MCTD_RATE if county in NY_MCTD_COUNTIES else Decimal("0")
    assert mctd == Decimal("0")  # Erie is not an MCTD county
    combined = state + county_rate + mctd + city_rate
    assert combined == Decimal("8.750")


def test_new_york_mctd_counts_to_twelve() -> None:
    """The MCTD covers exactly 12 NY counties (NYC's 5 + 7 surrounding)."""
    assert len(NY_MCTD_COUNTIES) == 12


def test_new_york_parse_boundaries_yields_nyc_zips_with_mctd() -> None:
    """NYC ZIP 10001 (Manhattan) must bind to state + county + MCTD + city."""
    rows = list(NEW_YORK.parse_boundaries(None, "v0.26-state-county-mctd-city"))
    nyc_rows = [b for b in rows if b.zip5 == "10001"]
    names = sorted(b.authority_name for b in nyc_rows)
    assert names == [
        NY_MCTD_DISTRICT_NAME,
        "New York",
        "New York City",
        "New York County",
    ]


def test_new_york_parse_boundaries_covers_all_5_boroughs() -> None:
    """Manhattan, Bronx, Brooklyn, Queens, and Staten Island ZIPs all bind to NYC."""
    rows = list(NEW_YORK.parse_boundaries(None, "v0.26-state-county-mctd-city"))
    nyc_zips = {b.zip5 for b in rows if b.authority_name == "New York City"}
    # Spot-check one ZIP per borough.
    assert "10001" in nyc_zips  # Manhattan
    assert "10451" in nyc_zips  # Bronx
    assert "11201" in nyc_zips  # Brooklyn
    assert "11354" in nyc_zips  # Queens
    assert "10301" in nyc_zips  # Staten Island


def test_new_york_parse_boundaries_buffalo_has_no_mctd() -> None:
    """Buffalo ZIP 14202 binds to state + Erie County + Buffalo (no MCTD).

    Erie County is upstate and outside the MCTD; the loader must NOT
    emit an MCTD boundary row for Buffalo ZIPs.
    """
    rows = list(NEW_YORK.parse_boundaries(None, "v0.26-state-county-mctd-city"))
    buf_rows = [b for b in rows if b.zip5 == "14202"]
    names = sorted(b.authority_name for b in buf_rows)
    assert names == ["Buffalo", "Erie County", "New York"]
    assert NY_MCTD_DISTRICT_NAME not in names


def test_new_york_parse_boundaries_yonkers_has_mctd() -> None:
    """Yonkers ZIP 10701 binds to state + Westchester + MCTD + Yonkers.

    Westchester is one of the 12 MCTD counties; the loader MUST emit
    the MCTD boundary row for Yonkers ZIPs.
    """
    rows = list(NEW_YORK.parse_boundaries(None, "v0.26-state-county-mctd-city"))
    yonk_rows = [b for b in rows if b.zip5 == "10701"]
    names = sorted(b.authority_name for b in yonk_rows)
    assert names == [
        NY_MCTD_DISTRICT_NAME,
        "New York",
        "Westchester County",
        "Yonkers",
    ]


def test_new_york_special_cases_empty() -> None:
    assert list(NEW_YORK.special_cases()) == []


def test_new_york_holidays_for_returns_empty() -> None:
    """NY has no annual sales-tax holidays at the state level."""
    assert list(NEW_YORK.holidays_for(2026)) == []
    assert list(NEW_YORK.holidays_for(2025)) == []


def test_new_york_seeds_thirty_cities() -> None:
    """Top-30 by population scope; no more, no less."""
    assert len(NY_CITIES) == 30


def test_new_york_every_city_has_at_least_one_zip() -> None:
    """Every covered city must seed at least one ZIP for the boundary loader."""
    for city, (county, _city_rate, zips) in NY_CITIES.items():
        assert len(zips) >= 1, f"{city} has no ZIPs"
        # Every county referenced by a city must appear in NY_COUNTY_RATE_PCT.
        assert (
            county in NY_COUNTY_RATE_PCT
        ), f"{city} references {county} which is missing from NY_COUNTY_RATE_PCT"
