# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Mississippi state module (v0.7 tier-1 ratchet)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.mississippi import MISSISSIPPI, Mississippi
from opensalestax.states.protocol import HolidayWindow, StateModule


def test_mississippi_metadata() -> None:
    assert MISSISSIPPI.state_abbrev == "MS"
    assert MISSISSIPPI.state_name == "Mississippi"
    assert MISSISSIPPI.sst_member is False  # MS is NOT in SST
    assert MISSISSIPPI.has_sales_tax is True
    assert MISSISSIPPI.tier == 1
    assert MISSISSIPPI.self_seeded is True  # signals loader to skip file lookup


def test_mississippi_satisfies_protocol() -> None:
    assert isinstance(MISSISSIPPI, StateModule)
    assert isinstance(Mississippi(), StateModule)


def test_mississippi_is_registered() -> None:
    assert get_state_module("MS") is MISSISSIPPI


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; July holiday window
        ("groceries", True),  # taxable but at REDUCED 5% (rate_modifier)
        ("prescription_drugs", False),  # exempt per 27-65-111(h)
        ("prepared_food", True),  # general 7% rate; SNAP reduction does not apply
        ("digital_goods", True),  # taxable per 27-65-26 (S.B. 2449, Laws 2023)
        ("general", True),  # baseline tangible personal property
    ],
)
def test_mississippi_taxability(category: str, expected_taxable: bool) -> None:
    rule = MISSISSIPPI.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes_lower = rule.notes.lower()
    assert "27-65" in notes_lower or "h.b. 1" in notes_lower or "s.b. 2449" in notes_lower


def test_mississippi_unknown_category_returns_none() -> None:
    assert MISSISSIPPI.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_mississippi_parse_rates_yields_7pct() -> None:
    """Mississippi's statewide rate is 7% (the highest single statewide
    rate in the country) effective 1992-07-01.

    Post-v0.25 the loader also yields per-county and per-city rows
    for the two cities with general-retail local taxes (Jackson 1%,
    Tupelo 0.25%); we still verify the state row is present and
    correct.
    """
    rows = list(MISSISSIPPI.parse_rates(None, "v0.25-state-county-city"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    row = state_rows[0]
    assert row.authority_name == "Mississippi"
    assert row.rate_pct == Decimal("7.000")
    assert row.effective_from == dt.date(1992, 7, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_mississippi_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(MISSISSIPPI.parse_rates(None, "test"))
    rows_with_path = list(MISSISSIPPI.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_mississippi_parse_rates_yields_jackson_and_tupelo() -> None:
    """Post-v0.25 MS yields per-city general-retail local rates.

    Only Jackson (1%) and Tupelo (0.25%) have authorizing acts for
    a city-level surcharge on general retail. Other MS cities have
    tourism-only taxes (hotels/restaurants) which are NOT modeled.
    """
    rows = list(MISSISSIPPI.parse_rates(None, "v0.25-state-county-city"))
    by_name = {r.authority_name: r for r in rows}
    assert by_name["Jackson"].authority_type == "city"
    assert by_name["Jackson"].rate_pct == Decimal("1.000")
    assert by_name["Jackson"].parent_authority_name == "Hinds County"
    assert by_name["Tupelo"].authority_type == "city"
    assert by_name["Tupelo"].rate_pct == Decimal("0.250")
    assert by_name["Tupelo"].parent_authority_name == "Lee County"


def test_mississippi_parse_boundaries_yields_jackson_zips() -> None:
    """Jackson ZIP 39201 must bind to state + Hinds County + Jackson."""
    rows = list(MISSISSIPPI.parse_boundaries(None, "v0.25-state-county-city"))
    jackson_rows = [b for b in rows if b.zip5 == "39201"]
    names = sorted(b.authority_name for b in jackson_rows)
    assert names == ["Hinds County", "Jackson", "Mississippi"]


def test_mississippi_special_cases_empty() -> None:
    cases = list(MISSISSIPPI.special_cases())
    assert cases == []


def test_mississippi_groceries_carries_reduced_rate_modifier() -> None:
    """Groceries are taxable but at the REDUCED 5% rate per H.B. 1, Laws 2025.

    The rate_modifier marks the special rate; the engine doesn't yet
    apply rate_modifier (deferred to v0.6+). The notes field must
    document both the modifier AND the cite to H.B. 1.
    """
    rule = MISSISSIPPI.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("5.000")
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "snap" in notes_lower
    assert "h.b. 1" in notes_lower or "house bill 1" in notes_lower
    assert "july 1, 2025" in notes_lower


def test_mississippi_digital_goods_notes_2023_statute() -> None:
    """MS taxes specified digital products at 7% per S.B. 2449, Laws 2023."""
    rule = MISSISSIPPI.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "27-65-26" in notes_lower
    assert "s.b. 2449" in notes_lower or "sb2449" in notes_lower


def test_mississippi_prescription_drugs_cite_subsection_h() -> None:
    """Prescription drug exemption is in subsection (h) of 27-65-111."""
    rule = MISSISSIPPI.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert rule.notes is not None
    assert "27-65-111(h)" in rule.notes


# ---------------------------------------------------------------------------
# Holiday tests -- MS has TWO annual holidays
# ---------------------------------------------------------------------------
def test_mississippi_holiday_count_2026() -> None:
    """MS has exactly two annual holidays in 2026."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    assert len(holidays) == 2
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_mississippi_back_to_school_dates_2026() -> None:
    """2026 Back-to-School: second Friday in July (July 10) - Sunday July 12.

    S.B. 2470, Laws 2024 moved the holiday from "last Friday/Saturday
    in July" to "second Friday-Sunday in July".
    """
    holidays = list(MISSISSIPPI.holidays_for(2026))
    bts = next(h for h in holidays if "Back-to-School" in h.name)
    assert bts.starts_on == dt.date(2026, 7, 10)
    assert bts.ends_on == dt.date(2026, 7, 12)
    # Sanity: second Friday in July through Sunday.
    assert bts.starts_on.weekday() == 4  # Friday
    assert bts.ends_on.weekday() == 6  # Sunday
    # And it really is the SECOND Friday (first Friday of July 2026 is July 3).
    first_friday = dt.date(2026, 7, 3)
    assert first_friday.weekday() == 4
    assert bts.starts_on == first_friday + dt.timedelta(days=7)


def test_mississippi_back_to_school_has_100_dollar_cap() -> None:
    """Statute imposes a $100 per-item cap on clothing/footwear/supplies."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    bts = next(h for h in holidays if "Back-to-School" in h.name)
    assert bts.max_amount_per_item == Decimal("100.00")


def test_mississippi_back_to_school_categories() -> None:
    """Statute covers clothing (incl. footwear) AND school supplies."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    bts = next(h for h in holidays if "Back-to-School" in h.name)
    assert bts.applicable_categories is not None
    cats = set(bts.applicable_categories)
    assert "clothing" in cats
    assert "school_supplies" in cats


def test_mississippi_back_to_school_notes_cite_statute() -> None:
    """Back-to-school holiday notes cite 27-65-111(bb) AND S.B. 2470."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    bts = next(h for h in holidays if "Back-to-School" in h.name)
    assert bts.notes is not None
    assert "27-65-111(bb)" in bts.notes
    assert "S.B. 2470" in bts.notes or "SB 2470" in bts.notes


def test_mississippi_second_amendment_dates_2026() -> None:
    """2026 Second Amendment Holiday: last Friday in August (Aug 28) - Sunday Aug 30."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    msaw = next(h for h in holidays if "Second Amendment" in h.name)
    assert msaw.starts_on == dt.date(2026, 8, 28)
    assert msaw.ends_on == dt.date(2026, 8, 30)
    # Sanity: starts on a Friday, ends on a Sunday.
    assert msaw.starts_on.weekday() == 4  # Friday
    assert msaw.ends_on.weekday() == 6  # Sunday
    # And it really is the LAST Friday in August: next Friday would
    # be in September.
    next_friday = msaw.starts_on + dt.timedelta(days=7)
    assert next_friday.month == 9


def test_mississippi_second_amendment_has_no_per_item_cap() -> None:
    """Statute imposes NO dollar cap on the Second Amendment holiday."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    msaw = next(h for h in holidays if "Second Amendment" in h.name)
    assert msaw.max_amount_per_item is None


def test_mississippi_second_amendment_categories() -> None:
    """Statute covers firearms, ammunition, and (statutorily-defined) hunting supplies."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    msaw = next(h for h in holidays if "Second Amendment" in h.name)
    assert msaw.applicable_categories is not None
    cats = set(msaw.applicable_categories)
    assert "firearms" in cats
    assert "ammunition" in cats
    assert "hunting_supplies" in cats


def test_mississippi_second_amendment_notes_cite_statute() -> None:
    """Second Amendment holiday notes cite 27-65-111(af)."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    msaw = next(h for h in holidays if "Second Amendment" in h.name)
    assert msaw.notes is not None
    assert "27-65-111(af)" in msaw.notes


def test_mississippi_holidays_chronological() -> None:
    """Back-to-School (July) precedes Second Amendment (August)."""
    holidays = list(MISSISSIPPI.holidays_for(2026))
    assert len(holidays) == 2
    # As yielded order should already be chronological.
    assert holidays[0].starts_on < holidays[1].starts_on


def test_mississippi_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design)."""
    assert list(MISSISSIPPI.holidays_for(2025)) == []
    assert list(MISSISSIPPI.holidays_for(2027)) == []
    assert list(MISSISSIPPI.holidays_for(2099)) == []


# ---------------------------------------------------------------------------
# Statewide ZIP coverage tests (v0.31 ratchet, parallels TX/NY/MO/IL/PA)
# ---------------------------------------------------------------------------
def test_mississippi_parse_rates_emits_all_82_counties() -> None:
    """All 82 MS counties must be emitted as RateRows so the
    ZIP_COUNTY-driven boundary loader can resolve every MS ZIP to a
    queryable county authority. Per Miss. Code Ann. section 27-65-241,
    no MS county imposes a general-retail county sales tax, so every
    county is at 0% verified.
    """
    rows = list(MISSISSIPPI.parse_rates(None, "v0.31-statewide"))
    counties = [r for r in rows if r.authority_type == "county"]
    assert len(counties) == 82
    for r in counties:
        assert r.rate_pct == Decimal("0.000"), (
            f"{r.authority_name} should be verified 0% per Miss. Code "
            f"Ann. section 27-65-241 (no general-retail county tax in MS)"
        )
    # Spot-check a non-Jackson/Tupelo county.
    by_name = {r.authority_name: r for r in counties}
    assert "Forrest County" in by_name  # Hattiesburg's county
    assert "Harrison County" in by_name  # Gulfport / Biloxi county
    assert "DeSoto County" in by_name


def test_mississippi_parse_boundaries_covers_non_city_zip() -> None:
    """A ZIP outside MS_CITIES must still bind to state + county
    after the v0.31 statewide ratchet. Hattiesburg 39406 (in
    Forrest County only per Census ZCTA) is NOT in MS_CITIES (the
    Hattiesburg Tourism Tax is hotel/restaurant-only, not modeled).
    Pre-v0.31 it would have only the Census state binding; post-
    v0.31 it must bind to "Mississippi" AND "Forrest County".
    """
    rows = list(MISSISSIPPI.parse_boundaries(None, "v0.31-statewide"))
    htsb_rows = [b for b in rows if b.zip5 == "39406"]
    names = sorted(b.authority_name for b in htsb_rows)
    assert names == ["Forrest County", "Mississippi"]


def test_mississippi_parse_boundaries_dedupes_county_per_zip() -> None:
    """A ZIP must bind to AT MOST ONE county to avoid future
    double-binding when per-county levies are added (Hattiesburg
    restaurant tax, etc.).
    """
    rows = list(MISSISSIPPI.parse_boundaries(None, "v0.31-statewide"))
    by_zip: dict[str, list[str]] = {}
    for b in rows:
        if b.authority_type == "county":
            by_zip.setdefault(b.zip5, []).append(b.authority_name)
    multi = {z: counties for z, counties in by_zip.items() if len(counties) > 1}
    assert multi == {}, f"Found ZIPs bound to multiple MS counties: {multi}"


def test_mississippi_parse_boundaries_jackson_city_still_bound() -> None:
    """Jackson ZIP 39201 must still pick up its city authority
    after the v0.31 ratchet (the Pass 2 fallback).
    """
    rows = list(MISSISSIPPI.parse_boundaries(None, "v0.31-statewide"))
    jackson_rows = [b for b in rows if b.zip5 == "39201"]
    names = sorted(b.authority_name for b in jackson_rows)
    assert names == ["Hinds County", "Jackson", "Mississippi"]


def test_mississippi_parse_boundaries_emits_many_zips() -> None:
    """Sanity: post-v0.31 MS must emit boundary rows for many
    hundreds of ZIPs (the Census ZCTA file lists ~360 MS ZCTAs),
    not just the ~16 ZIPs in MS_CITIES.
    """
    rows = list(MISSISSIPPI.parse_boundaries(None, "v0.31-statewide"))
    state_zips = {b.zip5 for b in rows if b.authority_type == "state"}
    assert len(state_zips) > 250, (
        f"Expected statewide ZCTA coverage (~360 MS ZIPs); got only "
        f"{len(state_zips)} -- ratchet may not be wired correctly"
    )
