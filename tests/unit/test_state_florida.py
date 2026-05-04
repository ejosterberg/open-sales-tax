# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Florida state module (per-county DR-15DSS loader)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.fl_data import (
    FL_CITIES,
    FL_COUNTY_SURTAX_PCT,
    FL_STATE_EFFECTIVE_FROM,
    FL_STATE_RATE_PCT,
)
from opensalestax.states.florida import FLORIDA, Florida
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Metadata + protocol conformance
# ---------------------------------------------------------------------------
def test_florida_metadata() -> None:
    assert FLORIDA.state_abbrev == "FL"
    assert FLORIDA.state_name == "Florida"
    assert FLORIDA.sst_member is False
    assert FLORIDA.has_sales_tax is True
    assert FLORIDA.tier == 1
    assert FLORIDA.self_seeded is True


def test_florida_satisfies_protocol() -> None:
    assert isinstance(FLORIDA, StateModule)
    assert isinstance(Florida(), StateModule)


def test_florida_is_registered() -> None:
    assert get_state_module("FL") is FLORIDA


# ---------------------------------------------------------------------------
# County coverage
# ---------------------------------------------------------------------------
def test_florida_seeds_all_67_counties() -> None:
    """Florida has exactly 67 counties; the surtax table must be complete."""
    assert len(FL_COUNTY_SURTAX_PCT) == 67


def test_florida_county_surtax_rates_within_legal_range() -> None:
    """Discretionary surtax (Fla. Stat. 212.054) caps at 1.5% in 2026."""
    for county, rate in FL_COUNTY_SURTAX_PCT.items():
        assert Decimal("0.000") <= rate <= Decimal("1.500"), (
            f"{county} surtax {rate} out of legal 0.0%-1.5% range"
        )


@pytest.mark.parametrize(
    "county,expected_pct",
    [
        # Spot-check the well-known county rates per FL DOR DR-15DSS 2026.
        ("Miami-Dade County", Decimal("1.000")),
        ("Orange County", Decimal("0.500")),
        ("Hillsborough County", Decimal("1.500")),
        ("Broward County", Decimal("1.000")),
        ("Duval County", Decimal("1.500")),
        ("Pinellas County", Decimal("1.000")),
        ("Leon County", Decimal("1.500")),
        ("Citrus County", Decimal("0.000")),  # No surtax -- combined 6%
    ],
)
def test_florida_well_known_county_surtaxes(county: str, expected_pct: Decimal) -> None:
    assert FL_COUNTY_SURTAX_PCT[county] == expected_pct


def test_florida_county_names_match_census_keys() -> None:
    """Every county we encode must match the Census `county_names.py` lookup
    so the engine can join boundaries to authorities cleanly.
    """
    from opensalestax.data.county_names import COUNTY_NAMES

    fl_census_counties = {
        name for (state_abbrev, _fips), name in COUNTY_NAMES.items() if state_abbrev == "FL"
    }
    for county_name in FL_COUNTY_SURTAX_PCT:
        assert county_name in fl_census_counties, (
            f"FL county {county_name!r} not in Census county_names.py"
        )


# ---------------------------------------------------------------------------
# City coverage (ZIP-binding anchors only; no city-level rate)
# ---------------------------------------------------------------------------
def test_florida_seeds_top_30_cities() -> None:
    """Brief specifies the top 30 cities by population."""
    assert len(FL_CITIES) == 30


def test_florida_every_city_county_is_known() -> None:
    """Every city's county must appear in FL_COUNTY_SURTAX_PCT."""
    for _city, (county_name, _zips) in FL_CITIES.items():
        assert county_name in FL_COUNTY_SURTAX_PCT, (
            f"City references unknown county {county_name!r}"
        )


def test_florida_every_city_has_at_least_one_zip() -> None:
    for city, (_county, zips) in FL_CITIES.items():
        assert len(zips) >= 1, f"{city} has no ZIPs"


def test_florida_zips_are_5_digit_strings() -> None:
    for city, (_county, zips) in FL_CITIES.items():
        for zip5 in zips:
            assert len(zip5) == 5, f"{city} ZIP {zip5!r} not 5 digits"
            assert zip5.isdigit(), f"{city} ZIP {zip5!r} not all digits"


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),
        ("groceries", False),
        ("prescription_drugs", False),
        ("prepared_food", True),
        ("digital_goods", True),
        ("general", True),
    ],
)
def test_florida_taxability(category: str, expected_taxable: bool) -> None:
    rule = FLORIDA.taxability_for(category, dt.date(2026, 5, 4))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_florida_unknown_category_returns_none() -> None:
    assert FLORIDA.taxability_for("alpaca-fur", dt.date(2026, 5, 4)) is None


# ---------------------------------------------------------------------------
# parse_rates
# ---------------------------------------------------------------------------
def test_florida_parse_rates_yields_state_row() -> None:
    rows = list(FLORIDA.parse_rates(None, "fl-data-2026"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    row = state_rows[0]
    assert row.authority_name == "Florida"
    assert row.rate_pct == FL_STATE_RATE_PCT
    assert row.rate_pct == Decimal("6.000")
    assert row.effective_from == FL_STATE_EFFECTIVE_FROM
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_florida_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(FLORIDA.parse_rates(None, "test"))
    rows_with_path = list(FLORIDA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_florida_parse_rates_yields_miami_dade_at_1pct() -> None:
    """Miami-Dade County combined: state 6% + 1% surtax = 7%."""
    rows = list(FLORIDA.parse_rates(None, "fl-data"))
    miami_dade = next(r for r in rows if r.authority_name == "Miami-Dade County")
    assert miami_dade.authority_type == "county"
    assert miami_dade.rate_pct == Decimal("1.000")
    assert miami_dade.parent_authority_name == "Florida"


def test_florida_parse_rates_yields_orange_at_half_pct() -> None:
    """Orange County (Orlando): state 6% + 0.5% school surtax = 6.5%."""
    rows = list(FLORIDA.parse_rates(None, "fl-data"))
    orange = next(r for r in rows if r.authority_name == "Orange County")
    assert orange.rate_pct == Decimal("0.500")


def test_florida_parse_rates_yields_no_city_rate_rows() -> None:
    """FL has no city-level general sales tax -- never emit city RateRows."""
    rows = list(FLORIDA.parse_rates(None, "fl-data"))
    assert not any(r.authority_type == "city" for r in rows)


def test_florida_parse_rates_emits_county_for_every_covered_city() -> None:
    """Every county touched by FL_CITIES must appear in the rate output."""
    rows = list(FLORIDA.parse_rates(None, "fl-data"))
    emitted_counties = {r.authority_name for r in rows if r.authority_type == "county"}
    cities_counties = {county for county, _ in FL_CITIES.values()}
    missing = cities_counties - emitted_counties
    assert not missing, f"Counties touched by cities but not emitted: {missing}"


# ---------------------------------------------------------------------------
# parse_boundaries
# ---------------------------------------------------------------------------
def test_florida_parse_boundaries_yields_miami_zips() -> None:
    """Miami ZIP 33130 must bind to state Florida + Miami-Dade County."""
    rows = list(FLORIDA.parse_boundaries(None, "fl-data"))
    miami_rows = [b for b in rows if b.zip5 == "33130"]
    names = sorted(b.authority_name for b in miami_rows)
    assert names == ["Florida", "Miami-Dade County"]


def test_florida_parse_boundaries_yields_orlando_zips() -> None:
    """Orlando ZIP 32801 must bind to state Florida + Orange County."""
    rows = list(FLORIDA.parse_boundaries(None, "fl-data"))
    orl_rows = [b for b in rows if b.zip5 == "32801"]
    names = sorted(b.authority_name for b in orl_rows)
    assert names == ["Florida", "Orange County"]


def test_florida_parse_boundaries_yields_no_city_authority() -> None:
    """FL has no city-level general sales tax -- never emit city BoundaryRows."""
    rows = list(FLORIDA.parse_boundaries(None, "fl-data"))
    assert not any(b.authority_type == "city" for b in rows)


def test_florida_parse_boundaries_covers_all_30_cities() -> None:
    """Every covered city's ZIPs must appear in the boundary output."""
    rows = list(FLORIDA.parse_boundaries(None, "fl-data"))
    emitted_zips = {b.zip5 for b in rows}
    for city, (_county, zips) in FL_CITIES.items():
        for zip5 in zips:
            assert zip5 in emitted_zips, f"{city} ZIP {zip5} missing from boundaries"


# ---------------------------------------------------------------------------
# Holiday + special-case behavior unchanged
# ---------------------------------------------------------------------------
def test_florida_special_cases_empty() -> None:
    assert list(FLORIDA.special_cases()) == []


def test_florida_holidays_2026_count() -> None:
    """FL ships 4 sales-tax holidays for 2026 (Disaster Prep / Freedom Month
    / Back-to-School / Tool Time).
    """
    assert len(list(FLORIDA.holidays_for(2026))) == 4


def test_florida_holidays_unknown_year_returns_empty() -> None:
    assert list(FLORIDA.holidays_for(2025)) == []
    assert list(FLORIDA.holidays_for(2099)) == []
