# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Virginia state module (Phase 6 Batch B).

Virginia is a non-SST state with a layered rate structure (state
4.3% + mandatory local 1% = 5.3% statewide minimum, with regional
add-ons taking certain areas to 6.0%, 6.3%, or 7.0%) and several
tier-1 quirks worth dedicated tests:

- Reduced 1% effective rate on groceries and personal hygiene
  products (Va. Code section 58.1-611.1) modeled via the
  ``rate_modifier`` pattern from Illinois.
- Combined 3-day August Sales Tax Holiday (Va. Code section
  58.1-639.1) covering four scopes (school supplies, clothing,
  Energy Star/WaterSense, hurricane preparedness) with distinct
  per-item caps.
- Digital downloads of prewritten software treated as non-taxable
  per long-standing Virginia Tax Commissioner policy.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.protocol import HolidayWindow, StateModule
from opensalestax.states.virginia import VIRGINIA, Virginia


def test_virginia_metadata() -> None:
    assert VIRGINIA.state_abbrev == "VA"
    assert VIRGINIA.state_name == "Virginia"
    assert VIRGINIA.sst_member is False  # VA is NOT in SST
    assert VIRGINIA.has_sales_tax is True
    assert VIRGINIA.tier == 1
    assert VIRGINIA.self_seeded is True


def test_virginia_satisfies_protocol() -> None:
    assert isinstance(VIRGINIA, StateModule)
    assert isinstance(Virginia(), StateModule)


def test_virginia_is_registered() -> None:
    assert get_state_module("VA") is VIRGINIA


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; August holiday exempts $100/under
        ("groceries", True),  # reduced rate via rate_modifier (1% effective)
        ("prescription_drugs", False),  # exempt per 58.1-609.10
        ("prepared_food", True),
        ("digital_goods", False),  # electronic delivery not tangible property
        ("general", True),
    ],
)
def test_virginia_taxability(category: str, expected_taxable: bool) -> None:
    rule = VIRGINIA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    # Every rule MUST cite a Virginia Code section in its notes.
    assert rule.notes
    assert "58.1-" in rule.notes or "Calculation only" in rule.notes


def test_virginia_unknown_category_returns_none() -> None:
    assert VIRGINIA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_virginia_parse_rates_yields_statewide_minimum_53_pct() -> None:
    """VA's statewide minimum combined rate is 5.3% (4.3% state + 1% local).

    Post-v0.25 the loader also yields per-district (Hampton Roads,
    Northern Virginia, Central Virginia at +0.7%) and per-city
    rows for the 12 covered cities; we still verify the state row
    is present and correct.
    """
    rows = list(VIRGINIA.parse_rates(None, "v0.25-state-district-city"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    row = state_rows[0]
    assert row.authority_name == "Virginia"
    assert row.rate_pct == Decimal("5.300")
    assert row.effective_from == dt.date(2013, 7, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_virginia_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(VIRGINIA.parse_rates(None, "test"))
    rows_with_path = list(VIRGINIA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_virginia_parse_rates_yields_four_regional_districts() -> None:
    """v0.31: Hampton Roads / Northern VA / Central VA at 0.7%
    PLUS Historic Triangle at 1.0%.
    """
    rows = list(VIRGINIA.parse_rates(None, "v0.31-statewide"))
    districts = [r for r in rows if r.authority_type == "district"]
    names = sorted(r.authority_name for r in districts)
    assert names == [
        "Central Virginia Region",
        "Hampton Roads Region",
        "Historic Triangle Region",
        "Northern Virginia Region",
    ]
    by_name = {r.authority_name: r for r in districts}
    assert by_name["Hampton Roads Region"].rate_pct == Decimal("0.700")
    assert by_name["Northern Virginia Region"].rate_pct == Decimal("0.700")
    assert by_name["Central Virginia Region"].rate_pct == Decimal("0.700")
    assert by_name["Historic Triangle Region"].rate_pct == Decimal("1.000")
    for r in districts:
        assert r.parent_authority_name == "Virginia"


def test_virginia_parse_boundaries_yields_virginia_beach_zips() -> None:
    """VA Beach ZIP 23451 must bind to state + Virginia Beach city
    (FIPS jurisdiction) + Hampton Roads district + Virginia Beach
    (friendly city anchor) after v0.31 statewide ratchet.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    vb_rows = [b for b in rows if b.zip5 == "23451"]
    names = sorted(b.authority_name for b in vb_rows)
    assert names == [
        "Hampton Roads Region",
        "Virginia",
        "Virginia Beach",
        "Virginia Beach city",
    ]


def test_virginia_parse_boundaries_roanoke_has_no_district() -> None:
    """Roanoke is outside any regional add-on -- only state + Roanoke
    city (FIPS jurisdiction) + Roanoke (friendly city anchor)
    bindings; no district binding.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    roanoke_rows = [b for b in rows if b.zip5 == "24011"]
    names = sorted(b.authority_name for b in roanoke_rows)
    # No district binding for Roanoke (it lands at the 5.3% statewide minimum).
    assert names == ["Roanoke", "Roanoke city", "Virginia"]
    # Sanity: confirm there really is NO district authority bound.
    assert all(b.authority_type != "district" for b in roanoke_rows)


def test_virginia_special_cases_empty() -> None:
    assert list(VIRGINIA.special_cases()) == []


def test_virginia_groceries_have_reduced_rate_marker() -> None:
    """VA's reduced 1% effective grocery rate is encoded via rate_modifier.

    Per Va. Code section 58.1-611.1, the state 4.3% portion was
    eliminated effective Jan 1, 2023; only the mandatory 1% local
    option still applies, so the effective rate on groceries and
    essential personal hygiene products is 1% statewide. Encoded
    using the same rate_modifier pattern as Illinois.
    """
    rule = VIRGINIA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("1.000")
    notes = (rule.notes or "").lower()
    assert "58.1-611.1" in (rule.notes or "")
    assert "1%" in notes or "1.000" in notes


def test_virginia_digital_goods_non_taxable_with_caveat() -> None:
    """Digital goods are non-taxable when delivered electronically.

    This is one of the few states where digital downloads of
    prewritten software are NOT taxable; the rule's notes must
    cite the Virginia Tax Commissioner rulings and the tangible-
    medium caveat.
    """
    rule = VIRGINIA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = (rule.notes or "").lower()
    assert "tangible" in notes  # caveat about physical-media sales


def test_virginia_clothing_notes_august_holiday() -> None:
    """The clothing rule must reference the August Sales Tax Holiday."""
    rule = VIRGINIA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = (rule.notes or "").lower()
    assert "holiday" in notes
    assert "58.1-639.1" in (rule.notes or "")


# ---------------------------------------------------------------------------
# Sales-tax holiday tests
# ---------------------------------------------------------------------------
def test_virginia_holidays_for_2026_returns_four_scopes() -> None:
    """The single statutory holiday is encoded as 4 scope-specific windows."""
    holidays = list(VIRGINIA.holidays_for(2026))
    assert len(holidays) == 4
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_virginia_holidays_for_unknown_year_returns_empty() -> None:
    """No extrapolation; future years require explicit data updates."""
    assert list(VIRGINIA.holidays_for(2025)) == []
    assert list(VIRGINIA.holidays_for(2027)) == []
    assert list(VIRGINIA.holidays_for(2099)) == []


def test_virginia_2026_holiday_dates_first_friday_to_sunday() -> None:
    """Va. Code 58.1-639.1: first Friday of August through following Sunday.

    For 2026 the first Friday of August is August 7, so the holiday
    runs August 7-9, 2026 (a 3-day window).
    """
    holidays = list(VIRGINIA.holidays_for(2026))
    expected_start = dt.date(2026, 8, 7)
    expected_end = dt.date(2026, 8, 9)
    for h in holidays:
        assert h.starts_on == expected_start
        assert h.ends_on == expected_end
        # Friday is weekday 4; verify the start is indeed a Friday
        assert h.starts_on.weekday() == 4
        # Sunday is weekday 6; verify the end is indeed a Sunday
        assert h.ends_on.weekday() == 6


def test_virginia_2026_holiday_per_item_caps() -> None:
    """Each scope has the statutory per-item cap encoded."""
    by_name = {h.name: h for h in VIRGINIA.holidays_for(2026)}

    school = next(h for n, h in by_name.items() if "School Supplies" in n)
    assert school.max_amount_per_item == Decimal("20.00")
    assert school.applicable_categories == ("school_supplies",)

    clothing = next(h for n, h in by_name.items() if "Clothing" in n)
    assert clothing.max_amount_per_item == Decimal("100.00")
    assert clothing.applicable_categories == ("clothing",)

    energy = next(h for n, h in by_name.items() if "Energy Star" in n)
    assert energy.max_amount_per_item == Decimal("2500.00")
    assert "energy_star" in (energy.applicable_categories or ())
    assert "water_efficient" in (energy.applicable_categories or ())

    hurricane = next(h for n, h in by_name.items() if "Hurricane" in n)
    # Conservative engine-level cap is the lowest statutory tier ($60);
    # higher tiers ($350 chainsaws, $1,000 generators) are documented
    # in notes for v0.6+ threshold-rule enforcement.
    assert hurricane.max_amount_per_item == Decimal("60.00")
    assert hurricane.applicable_categories == ("emergency_supplies",)
    notes = hurricane.notes or ""
    assert "1,000" in notes or "1000" in notes  # generator tier
    assert "350" in notes  # chainsaw tier


def test_virginia_every_holiday_cites_statute() -> None:
    """Per the project quality bar: every HolidayWindow.notes must cite
    the governing statute.
    """
    for h in VIRGINIA.holidays_for(2026):
        assert h.notes
        assert "58.1-639.1" in h.notes


def test_virginia_holidays_chronologically_ordered() -> None:
    """All four scopes share the same dates; sorted starts_on is monotonic."""
    starts = [h.starts_on for h in VIRGINIA.holidays_for(2026)]
    assert starts == sorted(starts)


# ---------------------------------------------------------------------------
# Statewide ZIP coverage tests (v0.31 ratchet, parallels TX/NY/MO/IL/PA)
# ---------------------------------------------------------------------------
def test_virginia_parse_rates_emits_all_133_jurisdictions() -> None:
    """All 133 VA jurisdictions (95 counties + 38 independent cities)
    must be emitted as RateRows so the ZIP_COUNTY-driven boundary
    loader can resolve every VA ZIP to a queryable county authority.
    """
    rows = list(VIRGINIA.parse_rates(None, "v0.31-statewide"))
    counties = [r for r in rows if r.authority_type == "county"]
    assert len(counties) == 133
    # Per the local-1%-in-state-rate fold, every county is at 0% local.
    for r in counties:
        assert r.rate_pct == Decimal("0.000"), (
            f"{r.authority_name} should be 0% local (the mandatory 1% "
            f"local is folded into the 5.3% state rate)"
        )
    # Spot-check a few jurisdictions at the right names.
    by_name = {r.authority_name: r for r in counties}
    assert "Loudoun County" in by_name
    assert "Fairfax County" in by_name
    assert "Alexandria city" in by_name
    assert "Williamsburg city" in by_name


def test_virginia_parse_boundaries_loudoun_picks_up_nova() -> None:
    """A Loudoun County ZIP outside the top-12 city seed (e.g.,
    Leesburg 20175) must bind to state + Loudoun County + Northern
    Virginia Region after the v0.31 ratchet -- previously it would
    fall back to state-only at 5.3%.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    leesburg_rows = [b for b in rows if b.zip5 == "20175"]
    names = sorted(b.authority_name for b in leesburg_rows)
    assert names == ["Loudoun County", "Northern Virginia Region", "Virginia"]


def test_virginia_parse_boundaries_isle_of_wight_picks_up_hampton_roads() -> None:
    """An Isle of Wight County ZIP (Smithfield 23430) must bind to
    state + Isle of Wight County + Hampton Roads Region after v0.31.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    smith_rows = [b for b in rows if b.zip5 == "23430"]
    names = sorted(b.authority_name for b in smith_rows)
    assert "Isle of Wight County" in names
    assert "Hampton Roads Region" in names
    assert "Virginia" in names


def test_virginia_parse_boundaries_williamsburg_stacks_historic_triangle() -> None:
    """Williamsburg ZIP 23185 must pick up BOTH Hampton Roads (+0.7%)
    AND Historic Triangle (+1.0%) districts -- combined 7.0% rate.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    wms_rows = [b for b in rows if b.zip5 == "23185"]
    district_names = sorted(b.authority_name for b in wms_rows if b.authority_type == "district")
    assert "Hampton Roads Region" in district_names
    assert "Historic Triangle Region" in district_names


def test_virginia_parse_boundaries_dedupes_county_per_zip() -> None:
    """A ZIP must bind to AT MOST ONE county/jurisdiction to avoid
    double-counting any regional district add-on.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    by_zip: dict[str, list[str]] = {}
    for b in rows:
        if b.authority_type == "county":
            by_zip.setdefault(b.zip5, []).append(b.authority_name)
    multi = {z: counties for z, counties in by_zip.items() if len(counties) > 1}
    assert multi == {}, (
        f"Found ZIPs bound to multiple VA jurisdictions (would double-count " f"district): {multi}"
    )


def test_virginia_parse_boundaries_rural_zip_no_district() -> None:
    """A ZIP outside every regional district (e.g., Charlottesville
    22902 -- Charlottesville city has NO regional district) lands at
    the 5.3% statewide minimum -- only state + city jurisdiction
    bindings, NO district.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    cville_rows = [b for b in rows if b.zip5 == "22902"]
    district_rows = [b for b in cville_rows if b.authority_type == "district"]
    assert district_rows == [], (
        f"Charlottesville is outside all four VA regional districts; "
        f"found unexpected district bindings: {district_rows}"
    )


def test_virginia_parse_boundaries_emits_many_zips() -> None:
    """Sanity: post-v0.31 VA must emit boundary rows for many hundreds
    of ZIPs (the Census ZCTA file lists ~900 VA ZCTAs), not just the
    ~80 ZIPs in VA_CITIES.
    """
    rows = list(VIRGINIA.parse_boundaries(None, "v0.31-statewide"))
    state_zips = {b.zip5 for b in rows if b.authority_type == "state"}
    assert len(state_zips) > 700, (
        f"Expected statewide ZCTA coverage (~900 VA ZIPs); got only "
        f"{len(state_zips)} -- ratchet may not be wired correctly"
    )
