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
def test_new_mexico_parse_rates_yields_4_875_pct() -> None:
    """NM's statewide GRT rate is 4.875% effective 2023-07-01 (HB 163 of 2022)."""
    rows = list(NEW_MEXICO.parse_rates(None, "v1-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "New Mexico"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("4.875")
    assert row.effective_from == dt.date(2023, 7, 1)
    # No scheduled sunset -- the contingent 4.500% trigger in HB 163 has
    # not fired and would require a successor row when/if it does.
    assert row.effective_to is None
    assert row.parent_authority_name is None  # state-level rate has no parent


def test_new_mexico_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(NEW_MEXICO.parse_rates(None, "test"))
    rows_with_path = list(NEW_MEXICO.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_new_mexico_parse_boundaries_returns_empty() -> None:
    """v1 doesn't ship NM boundaries; per-county load deferred (mirrors CO/LA)."""
    rows = list(NEW_MEXICO.parse_boundaries(None, "v1-statewide"))
    assert rows == []


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
