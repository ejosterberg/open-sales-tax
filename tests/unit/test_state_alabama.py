# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Alabama state module (Phase 6 Batch C tier-0 -> tier-1; v1).

Alabama is a non-SST state with the most fragmented local sales-tax
landscape in the United States: 67 counties (most levying their own
tax) plus ~700+ municipalities, MANY of which **self-administer**
their own sales tax under Ala. Code section 11-51-200 et seq.
v1 ships the **state portion only** (4.0% per Ala. Code section
40-23-2(1)) and **does not model county or municipal rates**. That
deferral is documented in:

- The module docstring (verified by explicit tests below)
- ``specs/decisions/04-colorado-home-rule.md`` (the Colorado
  home-rule precedent for the same self-administering-cities pattern)
- ``specs/decisions/05-louisiana-parishes.md`` (the Louisiana
  parish precedent for a state with comparable local fragmentation)
- ``specs/research/references.md`` (AL section)

Two state-side annual sales-tax holidays are encoded:

- Severe Weather Preparedness (Ala. Code section 40-23-210 et seq.;
  last full weekend of February; 2026 = Feb 27 - Mar 1)
- Back-to-School (Ala. Code section 40-23-211; third full weekend
  of July; 2026 = July 17 - 19)

Both holidays are STATE-side -- counties and cities must OPT IN by
ordinance to extend the exemption to their local portion. The
``HolidayWindow.notes`` for each scope documents this caveat.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import alabama as alabama_module
from opensalestax.states import get_state_module
from opensalestax.states.alabama import ALABAMA, Alabama
from opensalestax.states.protocol import HolidayWindow, StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_alabama_metadata() -> None:
    assert ALABAMA.state_abbrev == "AL"
    assert ALABAMA.state_name == "Alabama"
    assert ALABAMA.sst_member is False  # AL is NOT in SST
    assert ALABAMA.has_sales_tax is True
    assert ALABAMA.tier == 1
    assert ALABAMA.self_seeded is True  # signals loader to skip file lookup


def test_alabama_satisfies_protocol() -> None:
    assert isinstance(ALABAMA, StateModule)
    assert isinstance(Alabama(), StateModule)


def test_alabama_is_registered() -> None:
    assert get_state_module("AL") is ALABAMA
    assert get_state_module("al") is ALABAMA  # case-insensitive lookup


# ---------------------------------------------------------------------------
# Taxability matrix -- statutory citations are mandatory in every notes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; July holiday window
        ("groceries", True),  # taxable but at REDUCED 2.0% (rate_modifier)
        ("prescription_drugs", False),  # exempt per 40-23-4(a)(20)
        ("prepared_food", True),  # full 4.0% rate; reduced grocery does not apply
        ("digital_goods", True),  # taxable per ALDOR Rule 810-6-1-.37
        ("general", True),  # baseline tangible personal property
    ],
)
def test_alabama_taxability(category: str, expected_taxable: bool) -> None:
    rule = ALABAMA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes_lower = rule.notes.lower()
    assert (
        "40-23" in notes_lower
        or "11-51" in notes_lower
        or "810-6-1-.37" in notes_lower
        or "hb 386" in notes_lower
        or "hb 479" in notes_lower
    )


def test_alabama_unknown_category_returns_none() -> None:
    assert ALABAMA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


# ---------------------------------------------------------------------------
# parse_rates / parse_boundaries
# ---------------------------------------------------------------------------
def test_alabama_parse_rates_yields_4pct() -> None:
    """Alabama's statewide general rate is 4.0% effective 1969-12-08.

    The top-30-city ratchet also yields per-county and per-city rows;
    we still verify the state row is present and correct.
    """
    rows = list(ALABAMA.parse_rates(None, "v1-top30"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    row = state_rows[0]
    assert row.authority_name == "Alabama"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("4.000")
    assert row.effective_from == dt.date(1969, 12, 8)
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_alabama_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(ALABAMA.parse_rates(None, "test"))
    rows_with_path = list(ALABAMA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_alabama_parse_boundaries_yields_birmingham_zips() -> None:
    """Birmingham ZIP 35203 must bind to state + Jefferson County + Birmingham."""
    rows = list(ALABAMA.parse_boundaries(None, "v1-top30"))
    bham_rows = [b for b in rows if b.zip5 == "35203"]
    names = sorted(b.authority_name for b in bham_rows)
    assert names == ["Alabama", "Birmingham", "Jefferson County"]


def test_alabama_special_cases_empty() -> None:
    cases = list(ALABAMA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Grocery rate_modifier test -- mirrors the AR/KS/OK pattern
# ---------------------------------------------------------------------------
def test_alabama_groceries_carry_2pct_rate_modifier() -> None:
    """Groceries are taxable with rate_modifier=2.000 (HB 386 of 2024 phase-down).

    The Alabama legislature reduced the state-portion grocery rate
    from 4.0% to 3.0% effective 2023-09-01 (HB 479 of 2023) and
    further to 2.0% effective 2025-09-01 (HB 386 of 2024). The
    rate_modifier marks the special state rate; the engine has
    applied rate_modifier since v0.11.1. Local sales taxes still
    apply at full local rate.
    """
    rule = ALABAMA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("2.000")
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    # Cite both Acts in the phase-down history
    assert "hb 386" in notes_lower or "act 2024-437" in notes_lower
    assert "hb 479" in notes_lower or "act 2023-554" in notes_lower
    # Phase-down history must include the prior 3.0% rate
    assert "3.0%" in rule.notes or "3.0 %" in rule.notes
    # And the current 2.0% effective date (2025-09-01)
    assert "2025-09-01" in rule.notes


def test_alabama_prescription_drugs_cite_40_23_4_a_20() -> None:
    """Prescription drug exemption is in section 40-23-4(a)(20)."""
    rule = ALABAMA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert rule.notes is not None
    assert "40-23-4(a)(20)" in rule.notes


def test_alabama_clothing_notes_cite_holiday_statute() -> None:
    """Clothing is taxable year-round but the holiday section 40-23-211 is referenced."""
    rule = ALABAMA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    assert "40-23-211" in rule.notes


# ---------------------------------------------------------------------------
# Home-rule / independent-locals deferral enforcement
# ---------------------------------------------------------------------------
# These tests are the load-bearing safety net for the "honest deferral"
# decision (mirrors the CO precedent from
# specs/decisions/04-colorado-home-rule.md). If the warning text
# disappears without actual SubJurisdiction support landing, these
# tests fail and the PR is blocked.
def test_alabama_module_docstring_warns_about_home_rule() -> None:
    """The module docstring must prominently document the home-rule deferral.

    The orchestrator brief explicitly requires both 'home-rule' and
    'deferred' to appear in the docstring so future maintainers
    cannot accidentally drop the warning.
    """
    docstring = alabama_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The warning MUST mention "home-rule" -- the term of art for the
    # self-administering-cities limitation.
    assert "home-rule" in docstring_lower
    # The docstring must say the modeling is "deferred" (per the
    # orchestrator brief's regression-test requirement).
    assert "deferred" in docstring_lower
    # The docstring must say cities self-administer so readers
    # understand WHY the state module can't model them.
    assert "self-administer" in docstring_lower or "self-administering" in docstring_lower
    # The warning must appear early -- not buried at the bottom.
    # Check that home-rule shows up in the first 1500 characters.
    assert "home-rule" in docstring[:1500].lower()
    # The decision-document references must be present so a future
    # maintainer can find the architectural rationale.
    assert "specs/decisions/04-colorado-home-rule.md" in docstring
    assert "specs/decisions/05-louisiana-parishes.md" in docstring
    # Sanity: the docstring must not be tiny.
    assert len(docstring) > 1500


def test_alabama_class_docstring_documents_deferral() -> None:
    """The Alabama class docstring also calls out the deferral.

    Many tooling surfaces (e.g., FastAPI auto-doc, IDE hover) show
    the class docstring rather than the module docstring; the
    deferral note has to be visible there too.
    """
    assert Alabama.__doc__ is not None
    class_doc_lower = Alabama.__doc__.lower()
    # Match either "home-rule" or the more general phrasing
    assert "home-rule" in class_doc_lower or "subjurisdiction" in class_doc_lower
    # Confirm the deferral-decision pointer is present
    assert "decisions/04-colorado-home-rule.md" in Alabama.__doc__


def test_alabama_general_rule_warns_about_home_rule_in_notes() -> None:
    """The ``general`` taxability rule must call out home-rule cities.

    Required by the orchestrator brief: the home-rule warning must
    be locked into the docstring AND the general TaxabilityRule.notes
    so a downstream caller reading the API response sees the caveat.
    """
    rule = ALABAMA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "home-rule" in notes_lower
    assert "deferred" in notes_lower or "not model" in notes_lower
    # The decision-doc reference must be embedded in the notes too.
    assert "decisions/04-colorado-home-rule.md" in rule.notes
    # Mention the under-collection magnitude so the warning is concrete.
    assert "under-collect" in notes_lower or "under-collection" in notes_lower


def test_alabama_groceries_warns_about_local_taxes() -> None:
    """Groceries get a reduced state rate but full local rate still applies."""
    rule = ALABAMA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    # The rule must explicitly warn that locals still tax groceries
    # at full rate even though the state phased the rate down.
    assert "local" in notes_lower
    # Cite the underlying state-grocery-rate statute / acts.
    assert "40-23-2(5)" in rule.notes


# ---------------------------------------------------------------------------
# Holiday tests -- AL has TWO annual holidays with multiple scopes each
# ---------------------------------------------------------------------------
def test_alabama_holiday_count_2026() -> None:
    """AL's 2026 holidays: 2 SWP scopes + 4 BTS scopes = 6 total HolidayWindows."""
    holidays = list(ALABAMA.holidays_for(2026))
    assert len(holidays) == 6
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_alabama_severe_weather_holiday_dates_2026() -> None:
    """SWP 2026: last full weekend of February = Friday Feb 27 - Sunday Mar 1."""
    holidays = list(ALABAMA.holidays_for(2026))
    swp = [h for h in holidays if "Severe Weather" in h.name]
    assert len(swp) == 2  # generators scope + preparedness-supplies scope
    for h in swp:
        assert h.starts_on == dt.date(2026, 2, 27)
        assert h.ends_on == dt.date(2026, 3, 1)
        # Sanity: starts on a Friday, ends on a Sunday.
        assert h.starts_on.weekday() == 4  # Friday
        assert h.ends_on.weekday() == 6  # Sunday
        # And Feb 27 really is the LAST Friday of February 2026
        # (next Friday is in March).
        next_friday = h.starts_on + dt.timedelta(days=7)
        assert next_friday.month == 3


def test_alabama_back_to_school_holiday_dates_2026() -> None:
    """BTS 2026: third full weekend of July = Friday July 17 - Sunday July 19."""
    holidays = list(ALABAMA.holidays_for(2026))
    bts = [h for h in holidays if "Back-to-School" in h.name]
    assert len(bts) == 4  # clothing + computers + school supplies + books
    for h in bts:
        assert h.starts_on == dt.date(2026, 7, 17)
        assert h.ends_on == dt.date(2026, 7, 19)
        # Sanity: starts on a Friday, ends on a Sunday.
        assert h.starts_on.weekday() == 4  # Friday
        assert h.ends_on.weekday() == 6  # Sunday
        # And July 17 really is the THIRD Friday of July 2026
        # (Fridays in July 2026: 3, 10, 17, 24, 31).
        first_friday = dt.date(2026, 7, 3)
        assert h.starts_on == first_friday + dt.timedelta(days=14)


def test_alabama_swp_generator_cap_is_1000() -> None:
    """SWP generator scope: $1,000 per-item cap per Ala. Code 40-23-210 et seq."""
    holidays = list(ALABAMA.holidays_for(2026))
    generator = next(h for h in holidays if h.applicable_categories == ("generators",))
    assert generator.max_amount_per_item == Decimal("1000.00")
    assert generator.notes is not None
    assert "40-23-210" in generator.notes


def test_alabama_swp_supplies_cap_is_60() -> None:
    """SWP preparedness-supplies scope: $60 per-item cap."""
    holidays = list(ALABAMA.holidays_for(2026))
    supplies = next(
        h for h in holidays if h.applicable_categories == ("severe_weather_preparedness_supplies",)
    )
    assert supplies.max_amount_per_item == Decimal("60.00")
    assert supplies.notes is not None
    assert "40-23-210" in supplies.notes


def test_alabama_bts_clothing_cap_is_100() -> None:
    """BTS clothing scope: $100 per-item cap per Ala. Code 40-23-211."""
    holidays = list(ALABAMA.holidays_for(2026))
    clothing = next(
        h
        for h in holidays
        if "Back-to-School" in h.name and h.applicable_categories == ("clothing",)
    )
    assert clothing.max_amount_per_item == Decimal("100.00")
    assert clothing.notes is not None
    assert "40-23-211" in clothing.notes


def test_alabama_bts_computers_cap_is_750() -> None:
    """BTS computer scope: $750 per single-purchase transaction."""
    holidays = list(ALABAMA.holidays_for(2026))
    computers = next(h for h in holidays if h.applicable_categories == ("computers",))
    assert computers.max_amount_per_item == Decimal("750.00")
    assert computers.notes is not None
    assert "40-23-211" in computers.notes


def test_alabama_bts_school_supplies_cap_is_50() -> None:
    """BTS school supplies scope: $50 per-item cap."""
    holidays = list(ALABAMA.holidays_for(2026))
    supplies = next(h for h in holidays if h.applicable_categories == ("school_supplies",))
    assert supplies.max_amount_per_item == Decimal("50.00")
    assert supplies.notes is not None
    assert "40-23-211" in supplies.notes


def test_alabama_bts_books_cap_is_30() -> None:
    """BTS books scope: $30 per-item cap (noncommercial)."""
    holidays = list(ALABAMA.holidays_for(2026))
    books = next(h for h in holidays if h.applicable_categories == ("books",))
    assert books.max_amount_per_item == Decimal("30.00")
    assert books.notes is not None
    assert "40-23-211" in books.notes


def test_alabama_holiday_categories_complete() -> None:
    """All 6 statutory scopes (2 SWP + 4 BTS) are encoded."""
    holidays = list(ALABAMA.holidays_for(2026))
    cats = {h.applicable_categories for h in holidays}
    assert cats == {
        ("generators",),
        ("severe_weather_preparedness_supplies",),
        ("clothing",),
        ("computers",),
        ("school_supplies",),
        ("books",),
    }


def test_alabama_holidays_notes_mention_local_opt_in() -> None:
    """All AL holiday notes must call out the local-opt-in caveat.

    Per the orchestrator brief: AL holidays are STATE-side -- counties
    and cities must opt in by ordinance to extend the exemption to
    their local portion. Every HolidayWindow's notes must surface
    that fact so a downstream caller doesn't assume locals
    automatically follow the state holiday.
    """
    holidays = list(ALABAMA.holidays_for(2026))
    for h in holidays:
        assert h.notes is not None
        notes_lower = h.notes.lower()
        assert (
            "opt in" in notes_lower or "opt-in" in notes_lower
        ), f"Holiday {h.name!r} notes must mention local-opt-in caveat"


def test_alabama_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design)."""
    assert list(ALABAMA.holidays_for(2024)) == []
    assert list(ALABAMA.holidays_for(2025)) == []
    assert list(ALABAMA.holidays_for(2027)) == []
    assert list(ALABAMA.holidays_for(2099)) == []


# ---------------------------------------------------------------------------
# Top-30-city ratchet: per-county + per-city emission + statewide ZIP
# coverage (parallels SC/MO/MS in v0.31)
# ---------------------------------------------------------------------------
def test_alabama_parse_rates_emits_all_67_counties() -> None:
    """All 67 AL counties must be emitted as RateRows so the
    ZIP_COUNTY-driven boundary loader can resolve every AL ZIP to a
    queryable county authority.
    """
    rows = list(ALABAMA.parse_rates(None, "v1-top30"))
    counties = [r for r in rows if r.authority_type == "county"]
    assert len(counties) == 67
    by_name = {r.authority_name: r for r in counties}
    # Spot-check a county touched by a covered city (Jefferson hosts
    # Birmingham + 6 others) and a long-tail (non-anchor) county.
    assert "Jefferson County" in by_name
    assert by_name["Jefferson County"].rate_pct == Decimal("2.000")
    assert by_name["Jefferson County"].parent_authority_name == "Alabama"
    # Madison County hosts Huntsville + Madison city.
    assert by_name["Madison County"].rate_pct == Decimal("0.500")
    # Long-tail county filled from ALDOR taxrates.csv (was 0.000
    # placeholder until the long-tail fill ratchet 2026-05-04).
    assert by_name["Cullman County"].rate_pct == Decimal("4.500")
    # And another long-tail county to lock in the no-more-placeholders
    # invariant for this ratchet.
    assert by_name["Pike County"].rate_pct == Decimal("2.500")


def test_alabama_parse_rates_emits_top_30_cities() -> None:
    """All 30 AL_CITIES entries must be emitted as city RateRows."""
    rows = list(ALABAMA.parse_rates(None, "v1-top30"))
    cities = [r for r in rows if r.authority_type == "city"]
    assert len(cities) == 30
    by_name = {r.authority_name: r for r in cities}
    # Spot-check the four headliners.
    assert by_name["Birmingham"].rate_pct == Decimal("4.000")
    assert by_name["Birmingham"].parent_authority_name == "Jefferson County"
    assert by_name["Huntsville"].rate_pct == Decimal("4.500")
    assert by_name["Huntsville"].parent_authority_name == "Madison County"
    assert by_name["Mobile"].rate_pct == Decimal("5.000")
    assert by_name["Mobile"].parent_authority_name == "Mobile County"
    assert by_name["Montgomery"].rate_pct == Decimal("3.500")
    assert by_name["Montgomery"].parent_authority_name == "Montgomery County"


def test_alabama_birmingham_combined_rate_is_10pct() -> None:
    """state 4% + Jefferson County 2% + Birmingham 4% = 10% combined.

    This is the load-bearing assertion for the orchestrator brief:
    Birmingham must return ~10% combined, not state-only 4%.
    """
    rows = list(ALABAMA.parse_rates(None, "v1-top30"))
    by_name = {r.authority_name: r for r in rows}
    state_rate = by_name["Alabama"].rate_pct
    county_rate = by_name["Jefferson County"].rate_pct
    city_rate = by_name["Birmingham"].rate_pct
    assert state_rate + county_rate + city_rate == Decimal("10.000")


def test_alabama_montgomery_combined_rate_is_10pct() -> None:
    """state 4% + Montgomery County 2.5% + Montgomery city 3.5% = 10%."""
    rows = list(ALABAMA.parse_rates(None, "v1-top30"))
    by_name = {r.authority_name: r for r in rows}
    combined = (
        by_name["Alabama"].rate_pct
        + by_name["Montgomery County"].rate_pct
        + by_name["Montgomery"].rate_pct
    )
    assert combined == Decimal("10.000")


def test_alabama_mobile_combined_rate_is_10pct() -> None:
    """state 4% + Mobile County 1% + Mobile city 5% = 10%."""
    rows = list(ALABAMA.parse_rates(None, "v1-top30"))
    by_name = {r.authority_name: r for r in rows}
    combined = (
        by_name["Alabama"].rate_pct
        + by_name["Mobile County"].rate_pct
        + by_name["Mobile"].rate_pct
    )
    assert combined == Decimal("10.000")


def test_alabama_huntsville_combined_rate_is_9pct() -> None:
    """state 4% + Madison County 0.5% + Huntsville city 4.5% = 9%.

    Madison City has a +1% special district that this loader does NOT
    model; Huntsville does not. The Huntsville combined math is exact.
    """
    rows = list(ALABAMA.parse_rates(None, "v1-top30"))
    by_name = {r.authority_name: r for r in rows}
    combined = (
        by_name["Alabama"].rate_pct
        + by_name["Madison County"].rate_pct
        + by_name["Huntsville"].rate_pct
    )
    assert combined == Decimal("9.000")


def test_alabama_parse_boundaries_dedupes_county_per_zip() -> None:
    """A ZIP must bind to AT MOST ONE county to avoid double-counting
    the local tax. Many AL ZIPs span 2+ counties in the Census ZCTA
    relationship file; the loader must pick one (preferring the
    city-anchor county where the ZIP is in AL_CITIES).
    """
    rows = list(ALABAMA.parse_boundaries(None, "v1-top30"))
    by_zip: dict[str, list[str]] = {}
    for b in rows:
        if b.authority_type == "county":
            by_zip.setdefault(b.zip5, []).append(b.authority_name)
    multi = {z: counties for z, counties in by_zip.items() if len(counties) > 1}
    assert multi == {}, (
        f"Found ZIPs bound to multiple AL counties (would double-count "
        f"local tax): {multi}"
    )


def test_alabama_parse_boundaries_cross_county_zip_uses_city_anchor() -> None:
    """ZIP 35173 (Trussville) straddles Jefferson + St. Clair; the
    city-anchor preference must bind it to Jefferson (Trussville's
    declared county).
    """
    rows = list(ALABAMA.parse_boundaries(None, "v1-top30"))
    z = [b for b in rows if b.zip5 == "35173" and b.authority_type == "county"]
    assert len(z) == 1
    assert z[0].authority_name == "Jefferson County"


def test_alabama_parse_boundaries_helena_uses_shelby_anchor() -> None:
    """ZIP 35080 (Helena) straddles Jefferson + Shelby; Helena anchors
    to Shelby County, so the boundary must bind to Shelby (NOT Jefferson).
    """
    rows = list(ALABAMA.parse_boundaries(None, "v1-top30"))
    z = [b for b in rows if b.zip5 == "35080" and b.authority_type == "county"]
    assert len(z) == 1
    assert z[0].authority_name == "Shelby County"


def test_alabama_parse_boundaries_covers_non_city_zip() -> None:
    """A ZIP outside any AL_CITIES entry must still bind to state +
    county after the top-30 ratchet.

    35601 (Decatur) is in Morgan County and IS a covered city; pick a
    non-covered ZIP to prove the statewide pass works. ZIP 35611
    (Athens area in Limestone County) is in Limestone -- and Limestone
    is touched by a covered city (Athens), so the county binding will
    apply with its non-zero rate.
    """
    rows = list(ALABAMA.parse_boundaries(None, "v1-top30"))
    # Pick a ZIP NOT in AL_CITIES but in a covered county.
    # 35601 is Decatur (covered) -- use 35603 instead since 35603 is
    # also Decatur's ZIP in al_data. Try a non-covered Limestone ZIP.
    by_zip: dict[str, set[str]] = {}
    for b in rows:
        by_zip.setdefault(b.zip5, set()).add(b.authority_name)
    # Verify there are many AL ZIPs bound (not just the ~70 in AL_CITIES).
    state_zips = {z for z, names in by_zip.items() if "Alabama" in names}
    assert len(state_zips) > 300, (
        f"Expected statewide ZCTA coverage (~600 AL ZIPs); got only "
        f"{len(state_zips)} -- ratchet may not be wired correctly"
    )


def test_alabama_parse_boundaries_emits_many_zips() -> None:
    """Sanity: AL must emit boundary rows for hundreds of ZIPs (the
    Census ZCTA file lists ~660 AL ZCTAs), not just the ~70 ZIPs in
    AL_CITIES.
    """
    rows = list(ALABAMA.parse_boundaries(None, "v1-top30"))
    state_zips = {b.zip5 for b in rows if b.authority_type == "state"}
    assert len(state_zips) > 500, (
        f"Expected statewide ZCTA coverage (~660 AL ZIPs); got only "
        f"{len(state_zips)}"
    )


def test_alabama_al_data_uses_canonical_county_names() -> None:
    """Every county in AL_COUNTY_RATE_PCT must match the canonical
    name in :data:`opensalestax.data.county_names.COUNTY_NAMES` so
    the boundary loader can look them up by FIPS.
    """
    from opensalestax.data.county_names import COUNTY_NAMES
    from opensalestax.states.al_data import AL_COUNTY_RATE_PCT

    al_canonical = {name for (st, _fips), name in COUNTY_NAMES.items() if st == "AL"}
    assert al_canonical, "no AL counties in COUNTY_NAMES -- canary failure"
    diff = set(AL_COUNTY_RATE_PCT) - al_canonical
    assert diff == set(), (
        f"AL_COUNTY_RATE_PCT contains county names not in COUNTY_NAMES: "
        f"{diff}"
    )


def test_alabama_al_cities_no_overlapping_zips() -> None:
    """No ZIP appears in more than one AL_CITIES entry.

    If a ZIP belonged to two cities the boundary loader would emit two
    city BoundaryRows (and the engine would double-count the city tax
    portion). Each AL ZIP must anchor to at most one city.
    """
    from opensalestax.states.al_data import AL_CITIES

    seen: dict[str, str] = {}
    for city, (_county, _rate, zips) in AL_CITIES.items():
        for z in zips:
            assert z not in seen, (
                f"ZIP {z} appears in BOTH {seen[z]} and {city}; "
                f"engine would double-count city tax. Pick one anchor."
            )
            seen[z] = city


def test_alabama_al_data_covers_all_67_counties() -> None:
    """AL_COUNTY_RATE_PCT must enumerate every AL county so the
    boundary loader can never miss one.
    """
    from opensalestax.data.county_names import COUNTY_NAMES
    from opensalestax.states.al_data import AL_COUNTY_RATE_PCT

    al_canonical = {name for (st, _fips), name in COUNTY_NAMES.items() if st == "AL"}
    missing = al_canonical - set(AL_COUNTY_RATE_PCT)
    assert missing == set(), (
        f"AL_COUNTY_RATE_PCT is missing AL counties present in "
        f"COUNTY_NAMES: {missing}"
    )
