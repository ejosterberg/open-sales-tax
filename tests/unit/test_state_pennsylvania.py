# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Pennsylvania state module (tier-1, non-SST).

Pennsylvania is a non-SST state with a 6.0% statewide rate
(72 P.S. section 7202(a)) and just two local sales taxes:

- Allegheny County (Pittsburgh metro): +1.0% -> 7.0% combined
- Philadelphia City/County (coterminous): +2.0% -> 8.0% combined
- All other 65 PA counties: no local tax -> 6.0% flat

These tests verify the rate stack lands at 6.000% / 7.000% /
8.000% for the right cities and that the broad PA exemptions
(clothing, groceries, prescription drugs) are correctly encoded
with their statutory citations. Digital goods are taxable per
Act 84 (2016).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.pa_data import (
    PA_CITIES,
    PA_COUNTY_RATE_PCT,
    PA_STATE_RATE_PCT,
)
from opensalestax.states.pennsylvania import PENNSYLVANIA, Pennsylvania
from opensalestax.states.protocol import StateModule


def test_pennsylvania_metadata() -> None:
    assert PENNSYLVANIA.state_abbrev == "PA"
    assert PENNSYLVANIA.state_name == "Pennsylvania"
    assert PENNSYLVANIA.sst_member is False  # PA is NOT in SST
    assert PENNSYLVANIA.has_sales_tax is True
    assert PENNSYLVANIA.tier == 1
    assert PENNSYLVANIA.self_seeded is True


def test_pennsylvania_satisfies_protocol() -> None:
    assert isinstance(PENNSYLVANIA, StateModule)
    assert isinstance(Pennsylvania(), StateModule)


def test_pennsylvania_is_registered() -> None:
    assert get_state_module("PA") is PENNSYLVANIA


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", False),  # 72 P.S. section 7204(26) broad exemption
        ("groceries", False),  # 72 P.S. section 7204(29) food exemption
        ("prescription_drugs", False),  # 72 P.S. section 7204(17)
        ("prepared_food", True),
        ("digital_goods", True),  # taxable per Act 84 of 2016
        ("general", True),  # 72 P.S. section 7202 imposes the 6% sales tax
    ],
)
def test_pennsylvania_taxability(category: str, expected_taxable: bool) -> None:
    rule = PENNSYLVANIA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    # Every rule MUST cite a Pennsylvania statute (72 P.S.) or 61 Pa. Code.
    assert rule.notes
    assert "72 P.S." in rule.notes or "61 Pa. Code" in rule.notes or "Act 84" in rule.notes


def test_pennsylvania_unknown_category_returns_none() -> None:
    assert PENNSYLVANIA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_pennsylvania_state_rate_constant_is_6_pct() -> None:
    """PA_STATE_RATE_PCT must be exactly 6.000 (Decimal, not float)."""
    assert Decimal("6.000") == PA_STATE_RATE_PCT


def test_pennsylvania_county_rate_table_has_67_counties() -> None:
    """Pennsylvania has 67 counties; the rate table must enumerate all of them
    so a future maintainer can tell the difference between 'no local tax'
    and 'this county is missing from the data'.
    """
    assert len(PA_COUNTY_RATE_PCT) == 67


def test_pennsylvania_only_two_counties_have_local_tax() -> None:
    """Only Allegheny (1%) and Philadelphia (2%) impose a local sales tax."""
    nonzero = {name: rate for name, rate in PA_COUNTY_RATE_PCT.items() if rate > 0}
    assert nonzero == {
        "Allegheny County": Decimal("1.000"),
        "Philadelphia County": Decimal("2.000"),
    }


def test_pennsylvania_parse_rates_yields_state_6_pct() -> None:
    """Pennsylvania's statewide rate is 6.000%."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6-state-county-city"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    row = state_rows[0]
    assert row.authority_name == "Pennsylvania"
    assert row.rate_pct == Decimal("6.000")
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_pennsylvania_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(PENNSYLVANIA.parse_rates(None, "test"))
    rows_with_path = list(PENNSYLVANIA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_pennsylvania_parse_rates_yields_philadelphia_county_2_pct() -> None:
    """Philadelphia County's local rate is 2.000% (encoded at the county level)."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6-state-county-city"))
    by_name = {r.authority_name: r for r in rows}
    phila_co = by_name["Philadelphia County"]
    assert phila_co.authority_type == "county"
    assert phila_co.rate_pct == Decimal("2.000")
    assert phila_co.parent_authority_name == "Pennsylvania"


def test_pennsylvania_parse_rates_yields_allegheny_county_1_pct() -> None:
    """Allegheny County's local rate is 1.000%."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6-state-county-city"))
    by_name = {r.authority_name: r for r in rows}
    allegheny = by_name["Allegheny County"]
    assert allegheny.authority_type == "county"
    assert allegheny.rate_pct == Decimal("1.000")
    assert allegheny.parent_authority_name == "Pennsylvania"


def test_pennsylvania_parse_rates_emits_zero_pct_city_rates() -> None:
    """Per the architectural choice, ALL PA city authorities have rate_pct=0.

    The local tax (where it exists) is encoded as the county rate
    so we don't have to make a "is it a county tax or city tax"
    decision for Philadelphia (which is coterminous).
    """
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6-state-county-city"))
    city_rows = [r for r in rows if r.authority_type == "city"]
    # 15 cities seeded
    assert len(city_rows) == 15
    for r in city_rows:
        assert r.rate_pct == Decimal("0.000"), (
            f"City {r.authority_name} should have 0% city rate; "
            f"local tax is encoded at the county level"
        )


def test_pennsylvania_parse_rates_pittsburgh_parented_under_allegheny() -> None:
    """Pittsburgh sits under Allegheny County in the authority hierarchy."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6"))
    by_name = {r.authority_name: r for r in rows}
    pittsburgh = by_name["Pittsburgh"]
    assert pittsburgh.authority_type == "city"
    assert pittsburgh.parent_authority_name == "Allegheny County"


def test_pennsylvania_parse_rates_philadelphia_parented_under_phila_county() -> None:
    """Philadelphia city sits under Philadelphia County."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6"))
    by_name = {r.authority_name: r for r in rows}
    phila = by_name["Philadelphia"]
    assert phila.authority_type == "city"
    assert phila.parent_authority_name == "Philadelphia County"


def test_pennsylvania_parse_boundaries_yields_philadelphia_19102() -> None:
    """Center City Philadelphia ZIP 19102 must bind state + county + city."""
    rows = list(PENNSYLVANIA.parse_boundaries(None, "v0.6"))
    phila_rows = [b for b in rows if b.zip5 == "19102"]
    names = sorted(b.authority_name for b in phila_rows)
    assert names == ["Pennsylvania", "Philadelphia", "Philadelphia County"]


def test_pennsylvania_parse_boundaries_yields_pittsburgh_15222() -> None:
    """Downtown Pittsburgh ZIP 15222 must bind state + Allegheny + Pittsburgh."""
    rows = list(PENNSYLVANIA.parse_boundaries(None, "v0.6"))
    pgh_rows = [b for b in rows if b.zip5 == "15222"]
    names = sorted(b.authority_name for b in pgh_rows)
    assert names == ["Allegheny County", "Pennsylvania", "Pittsburgh"]


def test_pennsylvania_combined_rate_philadelphia_is_8_pct() -> None:
    """End-to-end: Philadelphia ZIPs add up to state 6% + county 2% = 8%."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6"))
    by_name = {r.authority_name: r for r in rows}
    state = by_name["Pennsylvania"].rate_pct
    county = by_name["Philadelphia County"].rate_pct
    city = by_name["Philadelphia"].rate_pct
    assert state + county + city == Decimal("8.000")


def test_pennsylvania_combined_rate_pittsburgh_is_7_pct() -> None:
    """End-to-end: Pittsburgh ZIPs add up to state 6% + county 1% = 7%."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6"))
    by_name = {r.authority_name: r for r in rows}
    state = by_name["Pennsylvania"].rate_pct
    county = by_name["Allegheny County"].rate_pct
    city = by_name["Pittsburgh"].rate_pct
    assert state + county + city == Decimal("7.000")


@pytest.mark.parametrize(
    "city_name",
    [
        "Allentown", "Erie", "Reading", "Scranton", "Bethlehem",
        "Lancaster", "Harrisburg", "York", "Altoona", "State College",
        "Wilkes-Barre", "Chester", "Norristown",
    ],
)
def test_pennsylvania_other_cities_combined_rate_is_6_pct(city_name: str) -> None:
    """The 13 PA cities outside Allegheny/Philadelphia all land at 6.0% flat."""
    rows = list(PENNSYLVANIA.parse_rates(None, "v0.6"))
    by_name = {r.authority_name: r for r in rows}
    city = by_name[city_name]
    state = by_name["Pennsylvania"].rate_pct
    county = by_name[city.parent_authority_name or ""].rate_pct
    assert state + county + city.rate_pct == Decimal("6.000"), (
        f"{city_name} should be at the 6% statewide flat (no local tax)"
    )


def test_pennsylvania_top_15_cities_seeded() -> None:
    """Verify the top-15 city seed is exactly the 15 cities in the brief."""
    expected_cities = {
        "Philadelphia", "Pittsburgh", "Allentown", "Erie", "Reading",
        "Scranton", "Bethlehem", "Lancaster", "Harrisburg", "York",
        "Altoona", "State College", "Wilkes-Barre", "Chester",
        "Norristown",
    }
    assert set(PA_CITIES.keys()) == expected_cities


def test_pennsylvania_special_cases_empty() -> None:
    assert list(PENNSYLVANIA.special_cases()) == []


def test_pennsylvania_holidays_for_any_year_returns_empty() -> None:
    """Pennsylvania has no annual sales-tax holidays."""
    assert list(PENNSYLVANIA.holidays_for(2026)) == []
    assert list(PENNSYLVANIA.holidays_for(2025)) == []
    assert list(PENNSYLVANIA.holidays_for(2099)) == []


def test_pennsylvania_clothing_cites_72_ps_7204() -> None:
    """Clothing exemption must cite 72 P.S. section 7204(26)."""
    rule = PENNSYLVANIA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "7204(26)" in (rule.notes or "")


def test_pennsylvania_groceries_cite_72_ps_7204() -> None:
    """Groceries exemption must cite 72 P.S. section 7204(29)."""
    rule = PENNSYLVANIA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "7204(29)" in (rule.notes or "")


def test_pennsylvania_prescription_drugs_cite_72_ps_7204() -> None:
    """Prescription drugs exemption must cite 72 P.S. section 7204(17)."""
    rule = PENNSYLVANIA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "7204(17)" in (rule.notes or "")


def test_pennsylvania_digital_goods_cite_act_84() -> None:
    """Digital goods taxability must cite Act 84 of 2016."""
    rule = PENNSYLVANIA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "Act 84" in (rule.notes or "")
