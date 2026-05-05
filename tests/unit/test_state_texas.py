# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Texas state module (v0.26 top-50-city loader).

Texas is a non-SST state with a 6.25% statewide rate and a 2.0%
local cap that ceilings the combined rate at 8.25% (Tex. Tax Code
section 321.101(f)). The v0.26 ratchet ships per-county +
per-transit-district + per-city coverage for the top 50 cities
(minus the Atascocita CDP), sourced from the Texas Comptroller's
"City Sales and Use Tax Rates" + transit-authority publications
and cross-checked against Avalara per-city pages on 2026-05-04.

Tier-1 quirks worth dedicated tests:

- The combined rate at any covered ZIP must equal the published
  combined rate (8.25% almost everywhere; Arlington at 8.0% is the
  notable exception in this seed because it opted out of DART).
- Transit districts (Houston METRO / Dallas DART / Austin Capital
  Metro / SA VIA+ATD / FW FWTA / EP Sun Metro / CC RTA) are modeled
  as ``district`` authorities, mirroring the VA pattern.
- El Paso County is one of the few TX counties imposing a county
  sales tax (0.5%) -- worth a dedicated regression test.
- Three annual sales-tax holidays (April emergency-prep, May
  Energy Star, August back-to-school).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.protocol import HolidayWindow, StateModule
from opensalestax.states.texas import TEXAS, Texas
from opensalestax.states.tx_data import (
    TX_CITIES,
    TX_COUNTY_RATE_PCT,
    TX_STATE_RATE_PCT,
    TX_TRANSIT_DISTRICTS,
)


def test_texas_metadata() -> None:
    assert TEXAS.state_abbrev == "TX"
    assert TEXAS.state_name == "Texas"
    assert TEXAS.sst_member is False  # TX is NOT in SST
    assert TEXAS.has_sales_tax is True
    assert TEXAS.tier == 1
    assert TEXAS.self_seeded is True  # signals the loader to skip file lookup


def test_texas_satisfies_protocol() -> None:
    assert isinstance(TEXAS, StateModule)
    assert isinstance(Texas(), StateModule)


def test_texas_is_registered() -> None:
    assert get_state_module("TX") is TEXAS


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; August holiday exempts $100/under
        ("groceries", False),  # food for off-premise consumption per 151.314
        ("prescription_drugs", False),  # exempt per 151.313
        ("prepared_food", True),  # restaurant meals taxable
        ("digital_goods", True),  # downloaded software / music taxable
        ("general", True),  # baseline tangible personal property
    ],
)
def test_texas_taxability(category: str, expected_taxable: bool) -> None:
    rule = TEXAS.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_texas_unknown_category_returns_none() -> None:
    assert TEXAS.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


# ---------------------------------------------------------------------------
# parse_rates / parse_boundaries shape tests
# ---------------------------------------------------------------------------
def test_texas_parse_rates_yields_state_county_district_city() -> None:
    """v0.26 ratchet: TX now ships state + county + transit + 49 cities.

    Row counts (computed from the live TX_CITIES table to avoid brittle
    asserts when cities are added):

    - 1 state row at 6.25%
    - one county row per county in TX_COUNTY_RATE_PCT (all 254 TX
      counties so the ZIP_COUNTY-driven boundary loader can resolve
      every TX ZIP to its county authority -- v0.29)
    - one district row per distinct transit district touched
    - one city row per TX_CITIES entry
    """
    rows = list(TEXAS.parse_rates(None, "v0.26-top-50"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    county_rows = [r for r in rows if r.authority_type == "county"]
    district_rows = [r for r in rows if r.authority_type == "district"]
    city_rows = [r for r in rows if r.authority_type == "city"]

    assert len(state_rows) == 1
    assert state_rows[0].authority_name == "Texas"
    assert state_rows[0].rate_pct == TX_STATE_RATE_PCT
    assert state_rows[0].parent_authority_name is None

    # Every TX_COUNTY_RATE_PCT entry yields a county RateRow now
    # (previously only counties touched by a covered city).
    from opensalestax.states.tx_data import TX_COUNTY_RATE_PCT

    assert {r.authority_name for r in county_rows} == set(TX_COUNTY_RATE_PCT)
    # Every county touched by a covered city must still be present
    # (regression guard: a future maintainer pruning the dict can't
    # accidentally drop the original seed counties).
    city_touched_counties = {county for county, _, _, _ in TX_CITIES.values()}
    assert city_touched_counties.issubset({r.authority_name for r in county_rows})

    expected_transits = {transit for _, transit, _, _ in TX_CITIES.values() if transit is not None}
    assert {r.authority_name for r in district_rows} == expected_transits
    for r in district_rows:
        assert r.parent_authority_name == "Texas"
        assert r.rate_pct == TX_TRANSIT_DISTRICTS[r.authority_name]

    assert len(city_rows) == len(TX_CITIES)


def test_texas_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(TEXAS.parse_rates(None, "test"))
    rows_with_path = list(TEXAS.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_texas_parse_boundaries_yields_houston_zips() -> None:
    """Houston ZIP 77002 must bind to state + Harris + METRO + Houston."""
    rows = list(TEXAS.parse_boundaries(None, "v0.26-top-50"))
    houston_rows = [b for b in rows if b.zip5 == "77002"]
    names = sorted(b.authority_name for b in houston_rows)
    assert names == ["Harris County", "Houston", "Houston MTA (METRO)", "Texas"]


def test_texas_parse_boundaries_yields_arlington_no_transit() -> None:
    """Arlington opted out of DART; ZIP 76010 must bind WITHOUT a transit row."""
    rows = list(TEXAS.parse_boundaries(None, "v0.26-top-50"))
    arl_rows = [b for b in rows if b.zip5 == "76010"]
    names = sorted(b.authority_name for b in arl_rows)
    assert names == ["Arlington", "Tarrant County", "Texas"]
    types = sorted(b.authority_type for b in arl_rows)
    assert types == ["city", "county", "state"]
    assert "district" not in types


def test_texas_parse_boundaries_yields_el_paso_with_county_tax() -> None:
    """El Paso ZIP 79901 binds state + El Paso County + Sun Metro + city."""
    rows = list(TEXAS.parse_boundaries(None, "v0.26-top-50"))
    ep_rows = [b for b in rows if b.zip5 == "79901"]
    names = sorted(b.authority_name for b in ep_rows)
    assert names == ["El Paso", "El Paso County", "El Paso MTA (Sun Metro)", "Texas"]


def test_texas_special_cases_empty() -> None:
    assert list(TEXAS.special_cases()) == []


# ---------------------------------------------------------------------------
# Combined-rate arithmetic tests -- the load-bearing correctness check
# ---------------------------------------------------------------------------
def _combined_for(city_name: str, rows: list) -> Decimal:
    """Sum state + county + (optional) transit + city for a city in the seed."""
    by_name = {r.authority_name: r for r in rows}
    county_name, transit_name, _city_rate, _zips = TX_CITIES[city_name]
    total = by_name["Texas"].rate_pct + by_name[county_name].rate_pct
    if transit_name is not None:
        total += by_name[transit_name].rate_pct
    total += by_name[city_name].rate_pct
    return total


@pytest.mark.parametrize(
    "city_name",
    [
        # All major TX cities cap at 8.25% via different stack shapes
        "Houston",  # state 6.25 + Harris 0 + METRO 1.0 + city 1.0
        "Dallas",  # state 6.25 + Dallas 0 + DART 1.0 + city 1.0
        "Austin",  # state 6.25 + Travis 0 + Cap Metro 1.0 + city 1.0
        "San Antonio",  # state 6.25 + Bexar 0 + VIA+ATD 0.625 + city 1.375
        "Fort Worth",  # state 6.25 + Tarrant 0 + Trinity Metro 0.5 + city 1.5
        "El Paso",  # state 6.25 + El Paso Co 0.5 + Sun Metro 0.5 + city 1.0
        "Corpus Christi",  # state 6.25 + Nueces 0 + RTA 0.5 + city 1.5
        "Plano",  # state 6.25 + Collin 0 + DART 1.0 + city 1.0
        "Garland",  # state 6.25 + Dallas 0 + DART 1.0 + city 1.0
        "Irving",  # state 6.25 + Dallas 0 + DART 1.0 + city 1.0
        "Frisco",  # no transit -- state 6.25 + Collin 0 + city 2.0
        "Lubbock",  # no transit -- state 6.25 + Lubbock 0 + city 2.0
        "Amarillo",  # no transit -- state 6.25 + Potter 0 + city 2.0
        "Mesquite",  # no transit -- state 6.25 + Dallas 0 + city 2.0
        "Round Rock",  # no transit -- state 6.25 + Williamson 0 + city 2.0
    ],
)
def test_texas_combined_rate_caps_at_8_25(city_name: str) -> None:
    """Every major TX city in this list lands at the 8.25% local cap."""
    rows = list(TEXAS.parse_rates(None, "v0.26-top-50"))
    assert _combined_for(city_name, rows) == Decimal(
        "8.250"
    ), f"{city_name} combined rate did not equal 8.250%"


def test_texas_arlington_combined_is_8_00_not_8_25() -> None:
    """Arlington is the famous DART/FWTA opt-out -- combined 8.0%, not 8.25%.

    City stack: city 1.0 + crime control 0.5 + parks/street 0.25 = 1.75
    local; no transit. Total: 6.25 + 0 + 0 + 1.75 = 8.00%.
    """
    rows = list(TEXAS.parse_rates(None, "v0.26-top-50"))
    assert _combined_for("Arlington", rows) == Decimal("8.000")


def test_texas_no_combined_rate_exceeds_8_25_cap() -> None:
    """Tex. Tax Code section 321.101(f) caps combined local at 2.0% / 8.25%.

    Regression guard: if a future maintainer adds a city whose stack
    sums above 8.25%, this test catches it before deploy.
    """
    rows = list(TEXAS.parse_rates(None, "v0.26-top-50"))
    cap = Decimal("8.250")
    for city_name in TX_CITIES:
        combined = _combined_for(city_name, rows)
        assert combined <= cap, f"{city_name} combined rate {combined}% exceeds the 8.25% cap"


# ---------------------------------------------------------------------------
# County / transit data integrity
# ---------------------------------------------------------------------------
def test_texas_every_referenced_county_is_in_county_dict() -> None:
    """Every county_name in TX_CITIES must have a TX_COUNTY_RATE_PCT entry."""
    referenced = {county for county, _, _, _ in TX_CITIES.values()}
    missing = referenced - TX_COUNTY_RATE_PCT.keys()
    assert not missing, f"counties referenced but not in TX_COUNTY_RATE_PCT: {missing}"


def test_texas_every_referenced_transit_is_in_transit_dict() -> None:
    """Every transit_name in TX_CITIES must have a TX_TRANSIT_DISTRICTS entry."""
    referenced = {transit for _, transit, _, _ in TX_CITIES.values() if transit is not None}
    missing = referenced - TX_TRANSIT_DISTRICTS.keys()
    assert not missing, f"transit districts referenced but not in TX_TRANSIT_DISTRICTS: {missing}"


def test_texas_el_paso_is_only_non_zero_county_in_seed() -> None:
    """Among seeded cities, only El Paso County imposes a county sales tax.

    This is a knowledge regression guard: if a future maintainer adds a
    city in (e.g.) Hays or Bandera County which DO have county sales
    taxes, this test will fail and force them to also update the rate
    seed plus the combined-rate test list.
    """
    nonzero = {name: rate for name, rate in TX_COUNTY_RATE_PCT.items() if rate > Decimal("0.000")}
    assert nonzero == {"El Paso County": Decimal("0.500")}


def test_texas_houston_metro_zips_bind_to_metro() -> None:
    """Houston + Pasadena both sit in METRO; Baytown does NOT."""
    metro_cities = {
        name for name, (_, transit, _, _) in TX_CITIES.items() if transit == "Houston MTA (METRO)"
    }
    assert "Houston" in metro_cities
    assert "Pasadena" in metro_cities
    assert "Baytown" not in metro_cities  # Baytown is east of METRO boundary


# ---------------------------------------------------------------------------
# Sales-tax holiday tests
# ---------------------------------------------------------------------------
def test_texas_holidays_for_2026_returns_three_windows() -> None:
    """One April emergency-prep + one May Energy Star + one August BTS = 3."""
    holidays = list(TEXAS.holidays_for(2026))
    assert len(holidays) == 3
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_texas_holidays_for_unknown_year_returns_empty() -> None:
    """No extrapolation; future years require explicit data updates."""
    assert list(TEXAS.holidays_for(2025)) == []
    assert list(TEXAS.holidays_for(2027)) == []
    assert list(TEXAS.holidays_for(2099)) == []


def test_texas_2026_back_to_school_dates() -> None:
    """Texas back-to-school 2026: August 7-9 (first weekend of August)."""
    bts = next(h for h in TEXAS.holidays_for(2026) if "Back-to-School" in h.name)
    assert bts.starts_on == dt.date(2026, 8, 7)
    assert bts.ends_on == dt.date(2026, 8, 9)
    assert bts.applicable_categories == ("clothing", "school_supplies")
    assert bts.max_amount_per_item == Decimal("100.00")
