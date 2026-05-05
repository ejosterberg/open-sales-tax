# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the New Mexico state module (Phase 6 Batch C / tier-0 -> tier-1).

New Mexico is a non-SST state that imposes a **Gross Receipts Tax**
(NOT a sales tax) under NMSA 1978 Chapter 7, Article 9. v1 ships
the **state portion only** (4.875% effective 2023-07-01 under HB 163
of 2022) and **does not model county / municipal local-option GRT**.
That deferral mirrors CO/LA/SC/MS/MO/NV precedent and is documented in:

- The module docstring (verified by explicit tests below)
- ``specs/research/references.md`` (NM section)

The currently-active NM holiday is the Annual Back-to-School
Tax-Free Holiday (NMSA 7-9-95), which HB 218 of 2025 moved from
"first Friday in August" to "last Friday in July" through following
Sunday. For 2026 that means **July 31 - August 2**. The statute
enumerates SIX scopes (clothing, bookbags, computers, computer
hardware, calculators, school supplies) each with its own per-item
dollar cap; the module emits one ``HolidayWindow`` per scope.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.new_mexico import NEW_MEXICO, NewMexico
from opensalestax.states.nm_data import NM_LOCATION_RATES, NM_STATE_RATE_PCT
from opensalestax.states.protocol import HolidayWindow, StateModule


# ---------------------------------------------------------------------------
# Metadata + Protocol + registration
# ---------------------------------------------------------------------------
def test_new_mexico_metadata() -> None:
    assert NEW_MEXICO.state_abbrev == "NM"
    assert NEW_MEXICO.state_name == "New Mexico"
    assert NEW_MEXICO.sst_member is False  # NM is NOT an SST member
    assert NEW_MEXICO.has_sales_tax is True  # GRT modeled as sales tax for v1
    assert NEW_MEXICO.tier == 1
    assert NEW_MEXICO.self_seeded is True  # signals loader to skip cache file


def test_new_mexico_satisfies_protocol() -> None:
    assert isinstance(NEW_MEXICO, StateModule)
    assert isinstance(NewMexico(), StateModule)


def test_new_mexico_is_registered() -> None:
    assert get_state_module("NM") is NEW_MEXICO


# ---------------------------------------------------------------------------
# Taxability matrix (state portion only)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no general clothing exemption (only Aug holiday)
        ("groceries", False),  # NMSA 7-9-92 deduction + state hold-harmless
        ("prescription_drugs", False),  # NMSA 7-9-73.2 deduction
        ("prepared_food", True),  # food deduction excludes prepared meals
        ("digital_goods", True),  # taxable since 2019-07-01 per HB 6 of 2019
        ("general", True),  # baseline tangible personal property at 4.875%
    ],
)
def test_new_mexico_taxability(category: str, expected_taxable: bool) -> None:
    rule = NEW_MEXICO.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution +
    # brief). Accept any of the NM citations that show up across categories.
    notes_lower = rule.notes.lower()
    assert any(
        token in notes_lower
        for token in (
            "7-9-4",
            "7-9-92",
            "7-9-73.2",
            "7-9-95",
            "7-9-3.5",
            "hb 6",
            "hb 163",
        )
    )


def test_new_mexico_unknown_category_returns_none() -> None:
    assert NEW_MEXICO.taxability_for("green-chile-magic", dt.date(2026, 5, 3)) is None


# ---------------------------------------------------------------------------
# parse_rates / parse_boundaries / special_cases
# ---------------------------------------------------------------------------
def test_new_mexico_parse_rates_yields_state_4_875_pct() -> None:
    """NM's statewide GRT rate is 4.875% effective 2023-07-01 (HB 163 of 2022).

    Post-NM-locations ratchet the loader also yields per-county and
    per-location rows for the top-30 covered locations; we still
    verify the state row is present and correct.
    """
    rows = list(NEW_MEXICO.parse_rates(None, "v1-state-county-city"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    row = state_rows[0]
    assert row.authority_name == "New Mexico"
    assert row.rate_pct == Decimal("4.875")
    assert row.effective_from == dt.date(2023, 7, 1)
    # No scheduled sunset -- the contingent 4.500% trigger in HB 163 has
    # not fired and would require a successor row when/if it does.
    assert row.effective_to is None
    assert row.parent_authority_name is None  # state-level rate has no parent


def test_new_mexico_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    rows_with_none = list(NEW_MEXICO.parse_rates(None, "test"))
    rows_with_path = list(NEW_MEXICO.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_new_mexico_special_cases_empty() -> None:
    cases = list(NEW_MEXICO.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Documentation regression tests -- the GRT-vs-sales-tax model and
# deferred-locals deferral MUST be prominently documented per the
# orchestrator brief.
# ---------------------------------------------------------------------------
def test_new_mexico_module_docstring_documents_grt_model() -> None:
    """The module docstring must prominently document the GRT-not-sales-tax model.

    Required by the orchestrator brief. A future maintainer (or
    downstream caller reading the source) MUST be able to see that
    NM imposes a Gross Receipts Tax on sellers, not a sales tax on
    buyers, without hunting for the explanation.
    """
    import opensalestax.states.new_mexico as nm_module

    module_doc = nm_module.__doc__
    assert module_doc is not None
    doc_lower = module_doc.lower()
    # Must mention the GRT model name.
    assert "gross receipts tax" in doc_lower
    # Must explicitly say "NOT a sales tax" (or equivalent).
    assert "not a sales tax" in doc_lower or "not a traditional retail sales tax" in doc_lower
    # Must explain the seller-incidence concept.
    assert "seller" in doc_lower
    # Must mention pass-through to consumers (so readers grasp the
    # consumer-experience equivalence with sales tax).
    assert "pass" in doc_lower or "passes" in doc_lower or "passed" in doc_lower
    # Sanity: the GRT discussion is substantial enough that a short
    # docstring would mean we lost the explanation.
    assert len(module_doc) > 4000


def test_new_mexico_module_docstring_documents_deferred_locals() -> None:
    """The module docstring must prominently document the deferred-locals deferral.

    NM has 33 counties + ~106 municipalities each with their own
    local-option GRT. v1 ships state portion only and the docstring
    must call this out so a downstream caller knows under-collection
    is expected outside unincorporated rural areas.
    """
    import opensalestax.states.new_mexico as nm_module

    module_doc = nm_module.__doc__
    assert module_doc is not None
    doc_lower = module_doc.lower()
    # Must mention counties and/or municipalities.
    assert "counties" in doc_lower or "municipalities" in doc_lower
    # Must call out the not-modeled state of local GRT.
    assert "not modeled" in doc_lower or "deferred" in doc_lower
    # Must reference the precedent (CO / LA) so the reader sees this
    # as part of an established pattern.
    assert "colorado" in doc_lower or "louisiana" in doc_lower
    # Must reference the TRD location-code data source for the future
    # per-county loader.
    assert "trd" in doc_lower or "taxation and revenue" in doc_lower


def test_new_mexico_module_docstring_documents_grocery_state_and_local_exemption() -> None:
    """The module docstring must explain the unusual NM hold-harmless mechanism.

    NM is unlike most other state-level grocery-exemption states (e.g.,
    GA, where the state exempts but locals still tax) -- NM's state
    general fund reimburses locals via NMSA 7-1-6.46 / 7-1-6.47 so
    consumers see zero tax on groceries at every NM address. A
    future maintainer adding per-county data MUST be aware of this
    so the per-county rules don't accidentally re-tax groceries.
    """
    import opensalestax.states.new_mexico as nm_module

    module_doc = nm_module.__doc__
    assert module_doc is not None
    doc_lower = module_doc.lower()
    assert "7-9-92" in module_doc
    assert "hold-harmless" in doc_lower or "hold harmless" in doc_lower
    # The 2005-01-01 effective date for the food deduction.
    assert "2005" in module_doc


def test_new_mexico_module_docstring_documents_august_holiday() -> None:
    """The module docstring must document the back-to-school holiday.

    Including the HB 218 of 2025 amendment that moved the date
    formula from 'first Friday in August' to 'last Friday in July'
    (a foot-gun for any maintainer who reads the older Justia
    statute summary).
    """
    import opensalestax.states.new_mexico as nm_module

    module_doc = nm_module.__doc__
    assert module_doc is not None
    doc_lower = module_doc.lower()
    assert "back-to-school" in doc_lower or "back to school" in doc_lower
    assert "7-9-95" in module_doc
    # The HB 218 amendment must be called out so a future maintainer
    # knows to look there when verifying dates.
    assert "hb 218" in doc_lower or "2025" in module_doc


def test_new_mexico_class_docstring_documents_grt_and_locals() -> None:
    """The NewMexico class docstring also calls out the GRT model and deferral.

    Many tooling surfaces (e.g., FastAPI auto-doc, IDE hover) show
    the class docstring rather than the module docstring; both
    headline notes have to be visible there too.
    """
    assert NewMexico.__doc__ is not None
    class_doc_lower = NewMexico.__doc__.lower()
    assert "gross receipts tax" in class_doc_lower
    assert "not a sales tax" in class_doc_lower or "not modeled" in class_doc_lower


def test_new_mexico_groceries_notes_state_and_local_exemption() -> None:
    """The grocery rule's notes must explain the hold-harmless distribution."""
    rule = NEW_MEXICO.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "7-9-92" in rule.notes
    assert "hold-harmless" in notes_lower or "hold harmless" in notes_lower
    # The georgia-contrast is the easiest way for a reader to grasp
    # why NM groceries are different from GA groceries.
    assert "georgia" in notes_lower or "local" in notes_lower


def test_new_mexico_general_notes_grt_caveat() -> None:
    """The general rule must explain that NM imposes GRT not sales tax."""
    rule = NEW_MEXICO.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "gross receipts" in notes_lower
    # The local-deferral caveat must also surface in the general rule
    # so a developer reading just the general-category notes still
    # understands the under-collection limitation.
    assert "local" in notes_lower
    assert "not modeled" in notes_lower or "deferred" in notes_lower


def test_new_mexico_digital_goods_notes_post_2019_change() -> None:
    """The digital-goods rule must reference the 2019-07-01 HB 6 change.

    Pre-2019 NM digital goods were treated under a narrower base; the
    rule has to remind a maintainer that current taxability is tied
    to a specific Act, not a long-standing position.
    """
    rule = NEW_MEXICO.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "2019" in rule.notes
    assert "hb 6" in notes_lower


# ---------------------------------------------------------------------------
# Holiday tests (Back-to-School, July 31 - August 2, 2026, six scopes)
# ---------------------------------------------------------------------------
def test_new_mexico_holiday_count_2026() -> None:
    """NM has SIX holiday windows in 2026 (one per statutory scope).

    NMSA 7-9-95 enumerates clothing, bookbags, computers, computer
    hardware, calculators, and school supplies each with their own
    per-item dollar cap; the module emits a separate ``HolidayWindow``
    per scope so the engine can apply the per-item-cap rule
    independently per category.
    """
    holidays = list(NEW_MEXICO.holidays_for(2026))
    assert len(holidays) == 6
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_new_mexico_holiday_dates_2026() -> None:
    """2026 holiday: Friday July 31 through Sunday August 2 (per HB 218 of 2025).

    NMSA 7-9-95 as amended by HB 218 of the 2025 Regular Session
    specifies "the last Friday in July through the following Sunday".
    July 31, 2026 is a Friday (the last Friday in July 2026); the
    holiday ends Sunday August 2, 2026.
    """
    holidays = list(NEW_MEXICO.holidays_for(2026))
    for holiday in holidays:
        assert holiday.starts_on == dt.date(2026, 7, 31)
        assert holiday.ends_on == dt.date(2026, 8, 2)
        # Sanity: starts on a Friday, ends on a Sunday (statutory pattern).
        assert holiday.starts_on.weekday() == 4  # Friday
        assert holiday.ends_on.weekday() == 6  # Sunday


def test_new_mexico_holiday_per_item_caps_2026() -> None:
    """Each scope has the statutory per-item cap from NMSA 7-9-95.

    - Clothing/footwear: < $100 -> encoded as 99.99
    - Bookbags: < $100 -> 99.99
    - Computers: <= $1,000 -> 1000.00 (statute uses inclusive 'or less')
    - Computer hardware: <= $500 -> 500.00 (inclusive)
    - Calculators: < $200 -> 199.99
    - School supplies: < $30 -> 29.99
    """
    holidays = {h.name: h for h in NEW_MEXICO.holidays_for(2026)}
    expected = {
        "New Mexico Back-to-School: Clothing and Footwear (2026)": Decimal("99.99"),
        "New Mexico Back-to-School: Bookbags and Backpacks (2026)": Decimal("99.99"),
        "New Mexico Back-to-School: Computers (2026)": Decimal("1000.00"),
        "New Mexico Back-to-School: Computer Hardware (2026)": Decimal("500.00"),
        "New Mexico Back-to-School: Handheld Calculators (2026)": Decimal("199.99"),
        "New Mexico Back-to-School: School Supplies (2026)": Decimal("29.99"),
    }
    assert set(holidays.keys()) == set(expected.keys())
    for name, expected_cap in expected.items():
        assert holidays[name].max_amount_per_item == expected_cap


def test_new_mexico_holiday_categories_disjoint() -> None:
    """Each holiday window targets exactly one statutory category.

    Encoding scopes as separate windows lets the engine apply
    per-item caps independently. The categories must be unique
    across windows so the engine never matches two caps to the
    same line item.
    """
    holidays = list(NEW_MEXICO.holidays_for(2026))
    all_categories: list[str] = []
    for holiday in holidays:
        assert holiday.applicable_categories is not None
        # Each NM scope is exactly one category in this v1 encoding.
        assert len(holiday.applicable_categories) == 1
        all_categories.extend(holiday.applicable_categories)
    # No duplicate categories across windows.
    assert len(all_categories) == len(set(all_categories))
    # Sanity: the six expected categories are present.
    assert set(all_categories) == {
        "clothing",
        "bookbags",
        "computers",
        "computer_hardware",
        "calculators",
        "school_supplies",
    }


def test_new_mexico_holiday_notes_cite_statute_and_merchant_election_caveat() -> None:
    """Every holiday window's notes cite NMSA 7-9-95 and the merchant-election caveat.

    The merchant-election caveat is the most important downstream
    operational difference between NM's holiday and most other
    states' back-to-school holidays -- callers building a POS or
    e-commerce checkout MUST surface the elect-in/out choice to
    the merchant. The note has to repeat per-window because the
    engine quotes one window's notes at a time.
    """
    holidays = list(NEW_MEXICO.holidays_for(2026))
    for holiday in holidays:
        assert holiday.notes is not None
        assert "7-9-95" in holiday.notes
        notes_lower = holiday.notes.lower()
        assert "merchant" in notes_lower
        assert "election" in notes_lower or "elect" in notes_lower
        # The HB 218 amendment must surface so a downstream maintainer
        # can verify the date formula.
        assert "hb 218" in notes_lower or "last friday" in notes_lower


def test_new_mexico_holiday_chronological_order() -> None:
    """All 2026 holiday windows share the same start/end dates."""
    holidays = list(NEW_MEXICO.holidays_for(2026))
    starts = {h.starts_on for h in holidays}
    ends = {h.ends_on for h in holidays}
    # Single shared window for all six scopes.
    assert starts == {dt.date(2026, 7, 31)}
    assert ends == {dt.date(2026, 8, 2)}
    for holiday in holidays:
        assert holiday.starts_on <= holiday.ends_on


def test_new_mexico_holiday_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design).

    The legislature has amended the date formula twice in twenty
    years (the HB 218 of 2025 shift from 'first Friday in August'
    to 'last Friday in July' is only the most recent example);
    later years require explicit data updates.
    """
    assert list(NEW_MEXICO.holidays_for(2024)) == []
    assert list(NEW_MEXICO.holidays_for(2025)) == []
    assert list(NEW_MEXICO.holidays_for(2027)) == []
    assert list(NEW_MEXICO.holidays_for(2099)) == []


# ---------------------------------------------------------------------------
# Per-location combined-rate tests (NM TRD GRT Rate Schedule, top-30 cities)
# ---------------------------------------------------------------------------
def test_new_mexico_parse_rates_emits_state_county_city_layers() -> None:
    """parse_rates yields one state row + N county rows + M location rows."""
    rows = list(NEW_MEXICO.parse_rates(None, "v1-state-county-city"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    county_rows = [r for r in rows if r.authority_type == "county"]
    city_rows = [r for r in rows if r.authority_type == "city"]
    assert len(state_rows) == 1
    # Counties seeded == unique counties referenced by NM_LOCATION_RATES.
    expected_counties = {county for (county, _r, _z) in NM_LOCATION_RATES.values()}
    assert {r.authority_name for r in county_rows} == expected_counties
    # Every location is emitted as a city authority.
    assert {r.authority_name for r in city_rows} == set(NM_LOCATION_RATES)
    # Every county's rate is 0% (combined-local is folded into the city).
    for r in county_rows:
        assert r.rate_pct == Decimal("0.000")
        assert r.parent_authority_name == "New Mexico"


# DOR-verified combined rates (NM TRD GRT Rate Schedule effective
# 2026-01-01) -- the eight cities the orchestrator brief calls out
# as the maintainer-verified test grid. Combined = state 4.875% +
# city authority's local-combined rate.
@pytest.mark.parametrize(
    "city,county,expected_combined_pct",
    [
        ("Albuquerque", "Bernalillo County", Decimal("7.875")),
        ("Santa Fe", "Santa Fe County", Decimal("8.4375")),
        ("Las Cruces", "Doña Ana County", Decimal("8.000")),
        ("Rio Rancho", "Sandoval County", Decimal("7.6875")),
        ("Roswell", "Chaves County", Decimal("7.5625")),
        ("Farmington", "San Juan County", Decimal("8.125")),
        ("Hobbs", "Lea County", Decimal("6.5625")),
        ("Carlsbad", "Eddy County", Decimal("7.8333")),
    ],
)
def test_new_mexico_dor_verified_combined_rates(
    city: str, county: str, expected_combined_pct: Decimal
) -> None:
    """Eight DOR-verified cities reproduce the published TRD combined rate.

    Combined = state 4.875% + city authority's local-combined rate
    (with county at 0% per the published-combined-rate model). These
    rates are spot-checked against the NM TRD GRT Rate Schedule
    effective 2026-01-01 and form the maintainer-verified test grid
    per the orchestrator brief.
    """
    rows = list(NEW_MEXICO.parse_rates(None, "v1-state-county-city"))
    by_name = {r.authority_name: r for r in rows}
    assert city in by_name, f"{city} not emitted as a RateRow"
    city_row = by_name[city]
    assert city_row.authority_type == "city"
    assert city_row.parent_authority_name == county
    combined = NM_STATE_RATE_PCT + city_row.rate_pct
    assert combined == expected_combined_pct, (
        f"{city}: expected combined {expected_combined_pct}%, got {combined}% "
        f"(state {NM_STATE_RATE_PCT}% + local {city_row.rate_pct}%)"
    )


def test_new_mexico_albuquerque_combined_in_target_range() -> None:
    """ABQ combined rate must be in the 7-8% range per orchestrator brief.

    The brief explicitly states 'Albuquerque/Santa Fe/Las Cruces return
    correct combined rates (~7-8%) instead of state-only 4.875%' as the
    success criterion. This test guards against an accidental regression
    that would put ABQ back at the state-only 4.875%.
    """
    rows = list(NEW_MEXICO.parse_rates(None, "v1-state-county-city"))
    by_name = {r.authority_name: r for r in rows}
    abq = by_name["Albuquerque"]
    combined = NM_STATE_RATE_PCT + abq.rate_pct
    assert Decimal("7.0") <= combined <= Decimal("8.5"), (
        f"Albuquerque combined rate {combined}% out of target 7-8.5% range -- "
        f"would mean local GRT regressed to under-collecting"
    )


def test_new_mexico_top_30_brief_cities_present() -> None:
    """The eight DOR-verified cities from the brief must all be present.

    These eight (ABQ, SF, LC, RR, Roswell, Farmington, Hobbs, Carlsbad)
    are the orchestrator-brief-required minimum coverage. The remaining
    21 in NM_LOCATION_RATES round out the top-30 and may be tuned in
    future ratchets without failing this regression test.
    """
    required_cities = {
        "Albuquerque", "Santa Fe", "Las Cruces", "Rio Rancho",
        "Roswell", "Farmington", "Hobbs", "Carlsbad",
    }
    assert required_cities.issubset(set(NM_LOCATION_RATES))


def test_new_mexico_location_count_at_least_25() -> None:
    """Coverage must include at least 25 NM locations (target is top-30).

    Lets the brief's 'top-30' coverage flex to 25-30 to accommodate
    municipalities that share ZIPs with another covered location and
    can't be cleanly distinguished without +4 ZIP precision.
    """
    assert len(NM_LOCATION_RATES) >= 25


def test_new_mexico_parse_boundaries_yields_albuquerque_zip() -> None:
    """ABQ ZIP 87102 binds to state + Bernalillo County + Albuquerque."""
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-state-county-city"))
    abq_rows = [b for b in rows if b.zip5 == "87102"]
    names = sorted(b.authority_name for b in abq_rows)
    assert names == ["Albuquerque", "Bernalillo County", "New Mexico"]


def test_new_mexico_parse_boundaries_yields_santa_fe_zip() -> None:
    """Santa Fe ZIP 87501 binds to state + Santa Fe County + Santa Fe."""
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-state-county-city"))
    sf_rows = [b for b in rows if b.zip5 == "87501"]
    names = sorted(b.authority_name for b in sf_rows)
    assert names == ["New Mexico", "Santa Fe", "Santa Fe County"]


def test_new_mexico_parse_boundaries_yields_las_cruces_zip() -> None:
    """Las Cruces ZIP 88001 binds to state + Doña Ana County + Las Cruces."""
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-state-county-city"))
    lc_rows = [b for b in rows if b.zip5 == "88001"]
    names = sorted(b.authority_name for b in lc_rows)
    assert names == ["Doña Ana County", "Las Cruces", "New Mexico"]


def test_new_mexico_parse_boundaries_dedupes_county_per_zip() -> None:
    """Each NM ZIP must bind to AT MOST ONE county.

    Many NM ZIPs span multiple counties in the Census ZCTA file; the
    loader must pick exactly one (preferring the city-anchor county
    when the ZIP is in NM_LOCATION_RATES) so the engine doesn't
    double-count any county-level layer.
    """
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-state-county-city"))
    by_zip: dict[str, list[str]] = {}
    for b in rows:
        if b.authority_type == "county":
            by_zip.setdefault(b.zip5, []).append(b.authority_name)
    multi = {z: counties for z, counties in by_zip.items() if len(counties) > 1}
    assert multi == {}, (
        f"Found ZIPs bound to multiple NM counties (would double-count "
        f"local layers): {multi}"
    )


def test_new_mexico_parse_boundaries_dedupes_city_per_zip() -> None:
    """Each NM ZIP must bind to AT MOST ONE NM_LOCATION city.

    If a ZIP appears in two NM_LOCATION_RATES entries' tuple of ZIPs,
    the engine would try to apply two different combined-local rates
    to the same address. The seeded location ZIP lists must therefore
    be disjoint.
    """
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-state-county-city"))
    by_zip: dict[str, list[str]] = {}
    for b in rows:
        if b.authority_type == "city":
            by_zip.setdefault(b.zip5, []).append(b.authority_name)
    multi = {z: cities for z, cities in by_zip.items() if len(cities) > 1}
    assert multi == {}, (
        f"Found ZIPs bound to multiple NM locations (would double-count "
        f"the local GRT): {multi}"
    )


def test_new_mexico_parse_boundaries_emits_many_zips() -> None:
    """Sanity: post-ratchet NM emits boundary rows for many ZIPs.

    Census ZCTA pass should bind every NM ZIP in the seeded counties,
    not just the ZIPs explicitly listed in NM_LOCATION_RATES.
    """
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-state-county-city"))
    state_zips = {b.zip5 for b in rows if b.authority_type == "state"}
    # The 29 seeded locations alone reach ~50 ZIPs; the Census pass
    # against the seeded counties (Bernalillo, Santa Fe, Doña Ana,
    # Sandoval, Chaves, San Juan, Lea, Eddy, Curry, Otero, McKinley,
    # Valencia, San Miguel, Luna, Roosevelt, Grant, Rio Arriba, Cibola,
    # Sierra, Taos, Lincoln) lifts coverage well past 100 ZIPs.
    assert len(state_zips) > 100, (
        f"Expected post-ratchet NM ZIP coverage > 100; got {len(state_zips)} "
        f"-- ratchet may not be wired correctly"
    )


def test_new_mexico_parse_boundaries_state_authority_matches_state_name() -> None:
    """State BoundaryRows use the canonical state name 'New Mexico'."""
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-state-county-city"))
    state_authorities = {b.authority_name for b in rows if b.authority_type == "state"}
    assert state_authorities == {"New Mexico"}


def test_new_mexico_location_rate_decimal_precision_under_4_digits() -> None:
    """Encoded local-combined rates use at most 4 fractional digits.

    NM TRD publishes rates to four decimal places (e.g., 8.4375%). Any
    rate with more digits is a rounding-error tell that should be
    re-checked against the source.
    """
    for city, (_county, rate, _zips) in NM_LOCATION_RATES.items():
        # Strip trailing zeros, then count fractional digits.
        normalized = rate.normalize()
        sign, digits, exponent = normalized.as_tuple()
        # Pure integer rate (e.g., Decimal('3') -> exponent positive)
        # is fine; only check fractional precision.
        if isinstance(exponent, int) and exponent < 0:
            assert -exponent <= 4, (
                f"{city} local-combined rate {rate} has more than 4 "
                f"fractional digits -- check the source"
            )


def test_new_mexico_bernalillo_town_lives_in_sandoval_county() -> None:
    """The town of Bernalillo is in SANDOVAL County, NOT Bernalillo County.

    Common NM-trivia foot-gun: the city of Albuquerque sits in
    Bernalillo County, but the town of Bernalillo (north of ABQ on
    I-25) sits in Sandoval County. Guarding against an accidental
    swap.
    """
    county, _rate, _zips = NM_LOCATION_RATES["Bernalillo"]
    assert county == "Sandoval County"


def test_new_mexico_las_vegas_lives_in_san_miguel_county_not_nv() -> None:
    """Las Vegas in NM_LOCATION_RATES is the NM city, NOT the NV city.

    Sanity guard: the NM Las Vegas is in San Miguel County. If a
    future maintainer accidentally seeds Nevada's Las Vegas (Clark
    County), this test fails immediately.
    """
    county, _rate, _zips = NM_LOCATION_RATES["Las Vegas"]
    assert county == "San Miguel County"
