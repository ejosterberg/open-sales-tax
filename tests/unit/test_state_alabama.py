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
    """Alabama's statewide general rate is 4.0% effective 1969-12-08."""
    rows = list(ALABAMA.parse_rates(None, "v1-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Alabama"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("4.000")
    assert row.effective_from == dt.date(1969, 12, 8)
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_alabama_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(ALABAMA.parse_rates(None, "test"))
    rows_with_path = list(ALABAMA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_alabama_parse_boundaries_returns_empty() -> None:
    """v1 doesn't ship AL boundaries; per-county / per-city load deferred."""
    rows = list(ALABAMA.parse_boundaries(None, "v1-statewide"))
    assert rows == []


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
