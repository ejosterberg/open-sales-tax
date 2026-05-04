# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Illinois state module (top-20-city loader).

Illinois is a non-SST state with a 6.25% statewide rate. The
top-20-city ratchet ships per-county + per-RTA-district + per-city
coverage for the 20 most populous IL cities, sourced from the IDOR
Tax Rate Database / Tax Rate Finder publications and cross-checked
against Avalara per-city pages on 2026-05-04.

Tier-1 quirks worth dedicated tests:

- The combined rate at any covered ZIP must equal the published
  combined rate (Chicago 10.25%, Cicero 10.75% as the highest;
  Springfield 9.50% downstate without RTA; Rockford 8.75%).
- RTA is split into TWO district authorities (``RTA (Cook County)``
  at 1.00% and ``RTA (Collar Counties)`` at 0.75%) because the
  per-county rate within the RTA service area differs.
- Reduced 1% state rate on groceries / prescription drugs encoded
  via ``rate_modifier`` (mirrors the v0.4 work).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.il_data import (
    IL_CITIES,
    IL_COUNTY_RATE_PCT,
    IL_RTA_DISTRICTS,
    IL_STATE_RATE_PCT,
)
from opensalestax.states.illinois import ILLINOIS, Illinois
from opensalestax.states.protocol import StateModule


def test_illinois_metadata() -> None:
    assert ILLINOIS.state_abbrev == "IL"
    assert ILLINOIS.state_name == "Illinois"
    assert ILLINOIS.sst_member is False  # IL is NOT in SST
    assert ILLINOIS.has_sales_tax is True
    assert ILLINOIS.tier == 1
    assert ILLINOIS.self_seeded is True  # signals the loader to skip file lookup


def test_illinois_satisfies_protocol() -> None:
    assert isinstance(ILLINOIS, StateModule)
    assert isinstance(Illinois(), StateModule)


def test_illinois_is_registered() -> None:
    assert get_state_module("IL") is ILLINOIS


# ---------------------------------------------------------------------------
# parse_rates / parse_boundaries shape tests
# ---------------------------------------------------------------------------
def test_illinois_parse_rates_yields_state_county_district_city() -> None:
    """IL ships state + county + RTA district + 20 cities.

    Row counts (computed from the live IL_CITIES table to avoid
    brittle asserts when cities are added):

    - 1 state row at 6.25%
    - one county row per distinct county touched by a covered city
    - one district row per distinct RTA tier touched
    - one city row per IL_CITIES entry
    """
    rows = list(ILLINOIS.parse_rates(None, "v0.x-top-20"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    county_rows = [r for r in rows if r.authority_type == "county"]
    district_rows = [r for r in rows if r.authority_type == "district"]
    city_rows = [r for r in rows if r.authority_type == "city"]

    assert len(state_rows) == 1
    assert state_rows[0].authority_name == "Illinois"
    assert state_rows[0].rate_pct == IL_STATE_RATE_PCT
    assert state_rows[0].parent_authority_name is None

    expected_counties = {county for county, _, _, _ in IL_CITIES.values()}
    assert {r.authority_name for r in county_rows} == expected_counties

    expected_rtas = {
        rta for _, rta, _, _ in IL_CITIES.values() if rta is not None
    }
    assert {r.authority_name for r in district_rows} == expected_rtas
    for r in district_rows:
        assert r.parent_authority_name == "Illinois"
        assert r.rate_pct == IL_RTA_DISTRICTS[r.authority_name]

    assert len(city_rows) == len(IL_CITIES)


def test_illinois_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(ILLINOIS.parse_rates(None, "test"))
    rows_with_path = list(ILLINOIS.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_illinois_parse_boundaries_yields_chicago_zips() -> None:
    """Chicago ZIP 60601 must bind to state + Cook + RTA Cook + Chicago."""
    rows = list(ILLINOIS.parse_boundaries(None, "v0.x-top-20"))
    chi_rows = [b for b in rows if b.zip5 == "60601"]
    names = sorted(b.authority_name for b in chi_rows)
    assert names == ["Chicago", "Cook County", "Illinois", "RTA (Cook County)"]


def test_illinois_parse_boundaries_yields_naperville_collar_rta() -> None:
    """Naperville ZIP 60540 must bind to state + DuPage + RTA Collar + city."""
    rows = list(ILLINOIS.parse_boundaries(None, "v0.x-top-20"))
    nap_rows = [b for b in rows if b.zip5 == "60540"]
    names = sorted(b.authority_name for b in nap_rows)
    assert names == [
        "DuPage County",
        "Illinois",
        "Naperville",
        "RTA (Collar Counties)",
    ]


def test_illinois_parse_boundaries_yields_springfield_no_rta() -> None:
    """Springfield (downstate, outside RTA) binds WITHOUT a district row."""
    rows = list(ILLINOIS.parse_boundaries(None, "v0.x-top-20"))
    spi_rows = [b for b in rows if b.zip5 == "62701"]
    names = sorted(b.authority_name for b in spi_rows)
    assert names == ["Illinois", "Sangamon County", "Springfield"]
    types = sorted(b.authority_type for b in spi_rows)
    assert "district" not in types


def test_illinois_special_cases_empty() -> None:
    assert list(ILLINOIS.special_cases()) == []


def test_illinois_holidays_returns_empty() -> None:
    """IL has no recurring annual sales-tax holiday in current law."""
    assert list(ILLINOIS.holidays_for(2026)) == []
    assert list(ILLINOIS.holidays_for(2025)) == []


# ---------------------------------------------------------------------------
# Combined-rate arithmetic tests -- the load-bearing correctness check
# ---------------------------------------------------------------------------
def _combined_for(city_name: str, rows: list) -> Decimal:
    """Sum state + county + (optional) RTA + city for a city in the seed."""
    by_name = {r.authority_name: r for r in rows}
    county_name, rta_name, _city_rate, _zips = IL_CITIES[city_name]
    total = by_name["Illinois"].rate_pct + by_name[county_name].rate_pct
    if rta_name is not None:
        total += by_name[rta_name].rate_pct
    total += by_name[city_name].rate_pct
    return total


@pytest.mark.parametrize(
    ("city_name", "expected_combined"),
    [
        # Cook County (county 1.75 + RTA Cook 1.00) cities
        ("Chicago", Decimal("10.250")),            # +Chicago HR 1.25
        ("Cicero", Decimal("10.750")),             # +Cicero HR 1.75 (highest in IL major cities)
        ("Evanston", Decimal("10.250")),           # +Evanston HR 1.25
        ("Skokie", Decimal("10.250")),             # +Skokie HR 1.25
        ("Schaumburg", Decimal("10.000")),         # +Schaumburg HR 1.00
        ("Arlington Heights", Decimal("10.000")),  # +HR 1.00
        ("Palatine", Decimal("10.000")),           # +HR 1.00
        ("Des Plaines", Decimal("10.000")),        # +HR 1.00
        # Collar counties (county 0 + RTA Collar 0.75)
        ("Aurora", Decimal("8.250")),              # state 6.25 + Kane 0 + Aurora HR 1.25 + RTA 0.75
        ("Elgin", Decimal("8.500")),               # state + Kane + HR 1.50 + RTA 0.75
        ("Naperville", Decimal("7.750")),          # state + DuPage 0 + HR 0.75 + RTA 0.75
        ("Joliet", Decimal("8.750")),              # state + Will 0 + HR 1.75 + RTA 0.75
        ("Bolingbrook", Decimal("8.500")),         # state + Will + HR 1.50 + RTA 0.75
        ("Waukegan", Decimal("8.500")),            # state + Lake + HR 1.50 + RTA 0.75
        # Downstate (no RTA)
        ("Rockford", Decimal("8.750")),            # state + Winnebago 1.5 + HR 1.0
        ("Springfield", Decimal("9.500")),         # state + Sangamon 1.0 + HR 2.25
        ("Peoria", Decimal("9.000")),              # state + Peoria Co 1.0 + HR 1.75
        ("Champaign", Decimal("9.000")),           # state + Champaign Co 1.25 + HR 1.50
        ("Bloomington", Decimal("8.750")),         # state + McLean 0 + HR 2.50
        ("Decatur", Decimal("9.250")),             # state + Macon 1.5 + HR 1.50
    ],
)
def test_illinois_combined_rate_matches_published(
    city_name: str, expected_combined: Decimal
) -> None:
    """Each covered city's combined rate equals the IDOR-published rate."""
    rows = list(ILLINOIS.parse_rates(None, "v0.x-top-20"))
    assert _combined_for(city_name, rows) == expected_combined, (
        f"{city_name} combined rate did not match expected {expected_combined}%"
    )


def test_illinois_chicago_is_10_25_pct() -> None:
    """Regression guard: Chicago's combined rate is the load-bearing 10.25%."""
    rows = list(ILLINOIS.parse_rates(None, "v0.x-top-20"))
    assert _combined_for("Chicago", rows) == Decimal("10.250")


# ---------------------------------------------------------------------------
# County / RTA data integrity
# ---------------------------------------------------------------------------
def test_illinois_every_referenced_county_is_in_county_dict() -> None:
    """Every county_name in IL_CITIES must have an IL_COUNTY_RATE_PCT entry."""
    referenced = {county for county, _, _, _ in IL_CITIES.values()}
    missing = referenced - IL_COUNTY_RATE_PCT.keys()
    assert not missing, f"counties referenced but not in IL_COUNTY_RATE_PCT: {missing}"


def test_illinois_every_referenced_rta_is_in_rta_dict() -> None:
    """Every rta_name in IL_CITIES must have an IL_RTA_DISTRICTS entry."""
    referenced = {
        rta for _, rta, _, _ in IL_CITIES.values() if rta is not None
    }
    missing = referenced - IL_RTA_DISTRICTS.keys()
    assert not missing, f"RTA tiers referenced but not in IL_RTA_DISTRICTS: {missing}"


def test_illinois_rta_cook_is_1_pct_collar_is_0_75() -> None:
    """Per 70 ILCS 3615/4.03: RTA in Cook is 1.00%, in collars is 0.75%."""
    assert IL_RTA_DISTRICTS["RTA (Cook County)"] == Decimal("1.000")
    assert IL_RTA_DISTRICTS["RTA (Collar Counties)"] == Decimal("0.750")


def test_illinois_cook_county_rate_is_1_75_pct() -> None:
    """Cook County imposes a 1.75% home-rule sales tax."""
    assert IL_COUNTY_RATE_PCT["Cook County"] == Decimal("1.750")


def test_illinois_collar_counties_have_zero_county_rate() -> None:
    """The five RTA collar counties impose 0% county-level general-merchandise tax."""
    for county in (
        "DuPage County",
        "Kane County",
        "Lake County",
        "McHenry County",
        "Will County",
    ):
        assert IL_COUNTY_RATE_PCT[county] == Decimal("0.000"), (
            f"{county} should be 0% for general merchandise"
        )


def test_illinois_chicago_zips_bind_to_cook_rta() -> None:
    """All Chicago seeded ZIPs must bind to RTA (Cook County) -- not Collar."""
    cook_rta_cities = {
        name for name, (_, rta, _, _) in IL_CITIES.items()
        if rta == "RTA (Cook County)"
    }
    assert "Chicago" in cook_rta_cities
    assert "Cicero" in cook_rta_cities
    assert "Naperville" not in cook_rta_cities  # Naperville is in DuPage / Collar


def test_illinois_downstate_cities_have_no_rta() -> None:
    """Downstate cities (outside the six-county RTA area) must have rta=None."""
    for city in ("Rockford", "Springfield", "Peoria", "Champaign", "Bloomington", "Decatur"):
        _county, rta, _city_rate, _zips = IL_CITIES[city]
        assert rta is None, f"{city} is downstate and should not bind to any RTA"


# ---------------------------------------------------------------------------
# Taxability matrix (preserved from v0.4 with reduced-rate marker)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    ("category", "expected_taxable"),
    [
        ("clothing", True),
        ("groceries", True),  # taxable at REDUCED 1% state rate
        ("prescription_drugs", True),  # taxable at REDUCED 1% state rate
        ("prepared_food", True),
        ("digital_goods", True),
        ("general", True),
    ],
)
def test_illinois_taxability(category: str, expected_taxable: bool) -> None:
    rule = ILLINOIS.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_illinois_groceries_have_reduced_rate_modifier() -> None:
    """IL's unusual 1% reduced state rate is encoded via rate_modifier."""
    rule = ILLINOIS.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.rate_modifier == Decimal("1.000")


def test_illinois_prescription_drugs_reduced_rate_modifier() -> None:
    """Same reduced 1% state rate marker applies to prescription drugs."""
    rule = ILLINOIS.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.rate_modifier == Decimal("1.000")


def test_illinois_unknown_category_returns_none() -> None:
    assert ILLINOIS.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None
