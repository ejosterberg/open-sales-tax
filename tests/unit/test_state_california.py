# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the California state module (v0.27 top-50-city CDTFA loader).

California is a non-SST state with a 7.25% statewide rate (the highest
in the US). The v0.27 ratchet ships per-county-district + per-city
coverage for the top 50 cities by 2020 census population (with East
Los Angeles included as the unincorporated CDP that carries the LA
County rate). Data sourced from CDTFA's "California City and County
Sales and Use Tax Rates" publication effective April 1, 2026 and
cross-checked against Avalara per-city pages on 2026-05-04.

Tier-1 quirks worth dedicated tests:

- Combined rates span 7.250% (Thousand Oaks / Simi Valley in Ventura
  County, no overlay) up to 10.750% (Hayward in Alameda County).
- LA County's 2.250% district stack is the largest county overlay in
  the seed (LACMTA + Measure M + Measure R + Measure H).
- Alameda County's 2.000% (BART + Measures B/BB/F/AA/C/W) is the
  second largest.
- Several cities have NO city portion (Anaheim, Irvine, Fontana,
  Ontario, Roseville, etc.) and ride only the state + county stack.
- East Los Angeles is a CDP -- no city tax of its own, but its ZIPs
  bind to LA County's district rate (combined 9.500%).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.ca_data import (
    CA_CITIES,
    CA_COUNTY_RATE_PCT,
    CA_STATE_RATE_PCT,
)
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
    rule = CALIFORNIA.taxability_for(category, dt.date(2026, 5, 4))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_california_unknown_category_returns_none() -> None:
    assert CALIFORNIA.taxability_for("alpaca-fur", dt.date(2026, 5, 4)) is None


def test_california_clothing_cites_no_exemption() -> None:
    """The clothing rule explicitly notes CA has no clothing exemption."""
    rule = CALIFORNIA.taxability_for("clothing", dt.date(2026, 5, 4))
    assert rule is not None
    assert "no clothing exemption" in (rule.notes or "").lower()


# ---------------------------------------------------------------------------
# parse_rates / parse_boundaries shape tests
# ---------------------------------------------------------------------------
def test_california_parse_rates_yields_state_county_city() -> None:
    """v0.27 ratchet: CA now ships state + per-county + 50 cities.

    Row counts (computed from the live CA_CITIES table to avoid
    brittle asserts when cities are added):

    - 1 state row at 7.25%
    - one county row per distinct county touched by a covered city
    - one city row per CA_CITIES entry
    """
    rows = list(CALIFORNIA.parse_rates(None, "v0.27-top-50"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    county_rows = [r for r in rows if r.authority_type == "county"]
    city_rows = [r for r in rows if r.authority_type == "city"]

    assert len(state_rows) == 1
    assert state_rows[0].authority_name == "California"
    assert state_rows[0].rate_pct == CA_STATE_RATE_PCT
    assert state_rows[0].rate_pct == Decimal("7.250")
    assert state_rows[0].effective_from == dt.date(2017, 1, 1)
    assert state_rows[0].parent_authority_name is None

    # parse_rates emits a RateRow for every county in CA_COUNTY_RATE_PCT,
    # not just those touched by a covered city. The boundary loader
    # binds every CA ZIP whose county is in the table to the county
    # authority, so every county needs a queryable rate.
    assert {r.authority_name for r in county_rows} == set(CA_COUNTY_RATE_PCT)
    for r in county_rows:
        assert r.parent_authority_name == "California"
        assert r.rate_pct == CA_COUNTY_RATE_PCT[r.authority_name]

    assert len(city_rows) == len(CA_CITIES)


def test_california_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(CALIFORNIA.parse_rates(None, "test"))
    rows_with_path = list(CALIFORNIA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_california_parse_boundaries_yields_los_angeles_zips() -> None:
    """LA ZIP 90001 must bind to state + Los Angeles County + Los Angeles."""
    rows = list(CALIFORNIA.parse_boundaries(None, "v0.27-top-50"))
    la_rows = [b for b in rows if b.zip5 == "90001"]
    names = sorted(b.authority_name for b in la_rows)
    assert names == ["California", "Los Angeles", "Los Angeles County"]
    types = sorted(b.authority_type for b in la_rows)
    assert types == ["city", "county", "state"]


def test_california_parse_boundaries_yields_san_francisco_consolidated() -> None:
    """SF ZIP 94102 binds to state + San Francisco (City and County) + city."""
    rows = list(CALIFORNIA.parse_boundaries(None, "v0.27-top-50"))
    sf_rows = [b for b in rows if b.zip5 == "94102"]
    names = sorted(b.authority_name for b in sf_rows)
    assert names == [
        "California",
        "San Francisco",
        "San Francisco (City and County)",
    ]


def test_california_parse_boundaries_yields_east_la_with_county_only() -> None:
    """East LA ZIP 90022 is a CDP -- binds to state + LA County + East LA city.

    East Los Angeles has no city sales tax of its own (CDP), but its
    ZIPs still emit a "city" boundary so the rate stack at the ZIP
    resolves to LA County's 2.25% district overlay (combined 9.500%).
    """
    rows = list(CALIFORNIA.parse_boundaries(None, "v0.27-top-50"))
    ela_rows = [b for b in rows if b.zip5 == "90022"]
    # 90022 is shared between LA city and East LA in the seed; both
    # entries emit boundary rows for the ZIP.
    cities_at_zip = {b.authority_name for b in ela_rows if b.authority_type == "city"}
    assert "East Los Angeles" in cities_at_zip


def test_california_special_cases_empty() -> None:
    assert list(CALIFORNIA.special_cases()) == []


def test_california_holidays_for_returns_empty() -> None:
    """California has no annual sales-tax holidays."""
    assert list(CALIFORNIA.holidays_for(2026)) == []
    assert list(CALIFORNIA.holidays_for(2025)) == []


# ---------------------------------------------------------------------------
# Combined-rate arithmetic tests -- the load-bearing correctness check
# ---------------------------------------------------------------------------
def _combined_for(city_name: str, rows: list) -> Decimal:
    """Sum state + county + city for a city in the seed."""
    by_name = {r.authority_name: r for r in rows}
    county_name, _city_rate, _zips = CA_CITIES[city_name]
    return (
        by_name["California"].rate_pct + by_name[county_name].rate_pct + by_name[city_name].rate_pct
    )


@pytest.mark.parametrize(
    "city_name,expected_combined",
    [
        # CDTFA-published combined rates (April 1, 2026 publication).
        # iter-62 reconciliation pass: 9 county rates + 14 city rates
        # updated 2026-05-09 against the CDTFA Excel; all 50 covered
        # cities now match CDTFA combined exactly. Comments below show
        # the post-reconciliation breakdown.
        ("Los Angeles", Decimal("9.750")),  # state 7.25 + LA Co 2.5 + city 0
        ("San Diego", Decimal("7.750")),  # state 7.25 + SD Co 0.5 + city 0
        ("San Jose", Decimal("10.000")),  # state 7.25 + SCl 2.5 + city 0.25
        ("San Francisco", Decimal("8.625")),  # state 7.25 + SF 1.375 + city 0
        ("Fresno", Decimal("8.350")),  # state 7.25 + Fresno 0.725 + city 0.375
        ("Sacramento", Decimal("8.750")),  # state 7.25 + Sac 0.5 + city 1.0
        ("Long Beach", Decimal("10.500")),  # state 7.25 + LA 2.5 + city 0.75
        ("Oakland", Decimal("10.750")),  # state 7.25 + Alameda 3.0 + city 0.5
        ("Bakersfield", Decimal("8.250")),  # state 7.25 + Kern 1.0 + city 0
        ("Anaheim", Decimal("7.750")),  # state 7.25 + OC 0.5 + city 0
        ("Santa Ana", Decimal("9.250")),  # state 7.25 + OC 0.5 + city 1.5
        ("Hayward", Decimal("10.750")),  # state 7.25 + Alameda 3.0 + city 0.5
        ("Oxnard", Decimal("9.250")),  # state 7.25 + Ventura 0 + city 2.0
        ("Thousand Oaks", Decimal("7.250")),  # state 7.25 only -- the floor
        ("Simi Valley", Decimal("7.250")),  # state 7.25 only
        ("Vallejo", Decimal("9.250")),  # state 7.25 + Solano 0.875 + city 1.125
        ("Modesto", Decimal("8.875")),  # state 7.25 + Stan 0.625 + city 1.0
        ("Concord", Decimal("9.750")),  # state 7.25 + CC 1.5 + city 1.0
        ("Stockton", Decimal("9.000")),  # state 7.25 + SJ 0.5 + city 1.25
        ("Sunnyvale", Decimal("9.750")),  # state 7.25 + SCl 2.5 + city 0
        ("East Los Angeles", Decimal("9.750")),  # CDP -- LA County rate
    ],
)
def test_california_combined_rate_matches_cdtfa(city_name: str, expected_combined: Decimal) -> None:
    """Every covered CA city's combined rate must match CDTFA Q2 2026."""
    rows = list(CALIFORNIA.parse_rates(None, "v0.27-top-50"))
    assert (
        _combined_for(city_name, rows) == expected_combined
    ), f"{city_name} combined rate did not equal {expected_combined}%"


def test_california_no_combined_rate_below_state_floor() -> None:
    """No covered city can have a combined rate below 7.250% (state floor).

    Regression guard: if a future maintainer accidentally encodes a
    negative county or city rate, this test catches it.
    """
    rows = list(CALIFORNIA.parse_rates(None, "v0.27-top-50"))
    floor = Decimal("7.250")
    for city_name in CA_CITIES:
        combined = _combined_for(city_name, rows)
        assert (
            combined >= floor
        ), f"{city_name} combined rate {combined}% is below the 7.250% state floor"


def test_california_no_combined_rate_exceeds_known_max() -> None:
    """No covered city should exceed 11.250% in this seed.

    iter-62 reconciliation lifted the cap: Lancaster and Palmdale
    (both LA County) sit at 11.250% per CDTFA Q2 2026. Cal. Rev. &
    Tax Code section 7251.1 caps the combined city-and-county
    district overlay at 3.500% on top of the 7.25% state rate, but
    grandfathered measures and statutory exceptions allow some LA
    County cities to exceed the nominal cap.
    """
    rows = list(CALIFORNIA.parse_rates(None, "v0.27-top-50"))
    cap = Decimal("11.250")
    for city_name in CA_CITIES:
        combined = _combined_for(city_name, rows)
        assert combined <= cap, f"{city_name} combined rate {combined}% exceeds the 11.250% cap"


# ---------------------------------------------------------------------------
# County / data integrity
# ---------------------------------------------------------------------------
def test_california_seeds_fifty_cities() -> None:
    """Top-50 by population + iter-93/94 fill-ins (real-bug additions).

    Pin grows past 50 as material under-collections are surfaced
    via WebFetch + CDTFA cross-check:
    - iter-93: Burbank (was 9.75%, CDTFA 10.5%, +0.75% gap)
    - iter-94: Walnut Creek (8.75% -> 9.25%) + San Mateo
      (9.375% -> 9.625%)
    - iter-98: El Cerrito (8.75% -> 10.75%, +2.0%) + Burlingame
      (9.375% -> 9.625%, +0.25%)
    - iter-99: Richmond + Antioch + Pittsburg (each +1.0%) +
      Redwood City (+0.5%)
    - iter-100: Mill Valley + Sausalito + Larkspur + San Anselmo
      (Marin Co, each +1.0%) + San Bruno + Pacifica (San Mateo Co,
      each +0.5%)
    - iter-101: Belmont (San Mateo Co +0.5%) + Rocklin (Placer Co
      +0.5%)
    - iter-102: San Carlos (San Mateo Co +0.5%) + San Ramon
      (Contra Costa Co +1.0%, 94582 only)
    - iter-103: Folsom (Sacramento Co; fixed county-misattribution
      bug -- 8.25% over via El Dorado pick -> 7.75% correct)
    - iter-104: Palo Alto (Santa Clara Co; closes 94302 PO-box ZIP
      0%) + East Palo Alto (San Mateo Co +0.5% city tax)
    - iter-105: Novato + Corte Madera (Marin Co, both +1.0%)
    - iter-106: Culver City (+1.0%) + El Segundo (+0.75%) +
      Whittier (+0.75%) + La Habra (OC anchor + 1.0%)
    - iter-107: Gardena + Lawndale + Hawthorne + Cerritos
      (each +0.75%, LA Co South Bay)
    - iter-108: Santa Monica (+1.0%) + West Hollywood (+0.75%)
    - iter-110: Alhambra + Monterey Park (LA Co +0.75% each, SGV)
    - iter-111: National City + Vista + San Marcos (SD Co +1.0% each)
    - iter-112: Cupertino + Milpitas (Santa Clara Co +0.25% each)
    - iter-113: Auburn (Placer Co cross-county fix; -1.0% over) +
      Loomis (Placer +0.25%) + Davis (Yolo Co cross-county fix +
      city +1.25%) + 5 SLO Co cities (San Luis Obispo / Atascadero
      / Paso Robles / Arroyo Grande / Morro Bay, each +0.5%)
    - iter-114: 6 Sonoma Co cities (Petaluma + Sonoma both
      cross-county rebinds, plus Sebastopol/Healdsburg/Rohnert Park/
      Cotati) + 3 Napa Co cities (Napa/American Canyon/Calistoga)
    - iter-115: 11 Riverside Co cities (Hemet/Temecula/Murrieta/
      Lake Elsinore/Menifee/Indio/Coachella/Palm Desert/La Quinta
      each +1.0% city; Cathedral City + Palm Springs +1.5%) +
      Porterville (Tulare Co +1.0% city)
    - iter-116: 6 SD Co cities (El Cajon +0.5, La Mesa +0.75,
      Imperial Beach/Lemon Grove/Del Mar/Solana Beach each +1.0)
      + Westminster (OC Co +1.5)
    - iter-118: Rancho Cordova + Galt (Sac Co) + Highland (SBd
      Co) + Norco + Calimesa (Riverside Co) -- all +1.0 or +1.5
      city
    - iter-119: 11 Central Valley + SJ Co cities (Tracy/Manteca/
      Lodi/Atwater/Los Banos/Clovis/Sanger/Selma/Reedley/
      Kingsburg + Dinuba cross-county Tulare rebind from Fresno)
    - iter-120: 9 Northern + Central CA cities (Mariposa fixes
      missing Mariposa Co + ZIP 95338's 0% bug; Turlock cross-
      county rebind Merced→Stanislaus + city 0.75; Ceres + Eureka
      + Arcata + Chico + Oroville + Paradise + Fort Bragg with
      city overlays)
    - iter-121: 8 Central Coast + Sierra cities (Truckee +0.125
      Nevada Co TBID; Hollister +0.25 San Benito; Watsonville
      cross-county rebind Monterey→Santa Cruz; Scotts Valley
      +0.25 Santa Cruz; Marina/Seaside/Pacific Grove +0.5 each
      Monterey; Santa Maria +1.0 Santa Barbara)
    - iter-122: 7 Solano + Yolo Co cities (Fairfield/Benicia/
      Suisun City/Dixon city overlays; Rio Vista cross-county
      rebind Sacramento→Solano; West Sacramento +1.25 Yolo;
      Winters +0.25 Yolo)
    - iter-123: 8 Contra Costa Co cities (Brentwood/Martinez/
      Pleasant Hill/Lafayette/Moraga each +1.0 city; Hercules/
      Pinole +1.5 each; Orinda +2.0)
    - iter-124: 13 LA Co cities (Beverly Hills/Downey/Norwalk/
      Bellflower/Carson/El Monte each +0.75; Inglewood +0.5;
      Compton/Lynwood/Paramount/South Gate/Pico Rivera/Montebello
      each +1.0)
    Future additions of similar materiality will continue to grow
    this set.
    """
    assert len(CA_CITIES) == 188


def test_california_every_referenced_county_is_in_county_dict() -> None:
    """Every county_name in CA_CITIES must have a CA_COUNTY_RATE_PCT entry."""
    referenced = {county for county, _, _ in CA_CITIES.values()}
    missing = referenced - CA_COUNTY_RATE_PCT.keys()
    assert not missing, f"counties referenced but not in CA_COUNTY_RATE_PCT: {missing}"


def test_california_every_city_has_at_least_one_zip() -> None:
    """Every covered city must seed at least one ZIP for the boundary loader."""
    for city, (county, _city_rate, zips) in CA_CITIES.items():
        assert len(zips) >= 1, f"{city} has no ZIPs"
        assert (
            county in CA_COUNTY_RATE_PCT
        ), f"{city} references {county} which is missing from CA_COUNTY_RATE_PCT"


def test_california_alameda_county_is_largest_district() -> None:
    """iter-62 reconciliation: Alameda County 3.000% is now the
    largest district stack in the seed (previously LA at 2.250%).

    Knowledge regression guard -- if a future maintainer adds a
    county with a higher district rate, this assertion forces an
    intentional update to the test (and to the docstring claims).
    """
    max_county = max(CA_COUNTY_RATE_PCT.values())
    assert max_county == Decimal("3.000")
    assert CA_COUNTY_RATE_PCT["Alameda County"] == max_county


def test_california_kern_county_has_unincorporated_district() -> None:
    """Kern County levies a 1.0% county-wide district per CDTFA Q2 2026
    Unincorporated row.

    Updated iter-62 from the prior 0.000% (which under-collected on
    every Kern ZIP not in CA_CITIES). Bakersfield's combined rate
    stays 8.250% -- the 1.0% was re-attributed from city to county.
    """
    assert CA_COUNTY_RATE_PCT["Kern County"] == Decimal("1.000")


def test_california_ventura_has_zero_county_district() -> None:
    """Ventura is one of the rare CA counties with NO county-wide district.

    Thousand Oaks and Simi Valley therefore have combined rates equal
    to state + city only.
    """
    assert CA_COUNTY_RATE_PCT["Ventura County"] == Decimal("0.000")
