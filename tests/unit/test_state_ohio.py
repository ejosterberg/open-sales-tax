# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Ohio state module (tier-2 -> tier-1 promotion)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.ohio import OHIO, Ohio
from opensalestax.states.protocol import HolidayWindow, StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_ohio_metadata() -> None:
    assert OHIO.state_abbrev == "OH"
    assert OHIO.state_name == "Ohio"
    assert OHIO.sst_member is True  # OH is a Streamlined Sales Tax full member
    assert OHIO.has_sales_tax is True
    assert OHIO.tier == 1
    assert OHIO.state_fips == "39"


def test_ohio_inherits_sst_base() -> None:
    """Ohio subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(OHIO, SstStateModule)
    assert isinstance(Ohio(), SstStateModule)


def test_ohio_satisfies_protocol() -> None:
    assert isinstance(OHIO, StateModule)
    assert isinstance(Ohio(), StateModule)


def test_ohio_is_registered() -> None:
    assert get_state_module("OH") is OHIO
    assert get_state_module("oh") is OHIO  # case-insensitive


def test_ohio_is_not_in_tier2_anymore() -> None:
    """OH was promoted out of _tier2.py; it must no longer be registered as tier 2."""
    from opensalestax.states._tier2 import TIER_2_STATES

    abbrevs = {s.state_abbrev for s in TIER_2_STATES}
    assert "OH" not in abbrevs


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; 3-day August holiday window
        ("groceries", False),  # exempt per ORC 5739.02(B)(2) (off-premises food)
        ("prescription_drugs", False),  # exempt per ORC 5739.02(B)(18)
        ("prepared_food", True),  # general 5.75%; on-premises food excluded from exemption
        ("digital_goods", True),  # taxable per ORC 5739.01(B)(12) + 5739.01(OOO)
        ("general", True),  # baseline TPP at 5.75% per ORC 5739.02(A)(1)
    ],
)
def test_ohio_taxability(category: str, expected_taxable: bool) -> None:
    rule = OHIO.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "Ohio Rev. Code" in (rule.notes or "")


def test_ohio_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert OHIO.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_ohio_clothing_rule_cites_holiday_statute() -> None:
    """Clothing rule references the August holiday statute (ORC 5739.02(B)(55))."""
    rule = OHIO.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "5739.02(B)(55)" in (rule.notes or "")


def test_ohio_groceries_rule_cites_off_premises_subsection() -> None:
    """Grocery exemption is subsection (B)(2) of 5739.02 -- off-premises food."""
    rule = OHIO.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "5739.02(B)(2)" in (rule.notes or "")
    # The off-premises distinction is critical to OH's grocery rule and must be documented.
    assert "off the premises" in (rule.notes or "").lower()


def test_ohio_prescription_drugs_cite_subsection_18() -> None:
    """Prescription-drug exemption is subsection (B)(18) of 5739.02."""
    rule = OHIO.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "5739.02(B)(18)" in (rule.notes or "")


def test_ohio_digital_goods_notes_specified_digital_products() -> None:
    """OH taxes specified digital products at 5.75% per ORC 5739.01(B)(12) + 5739.01(OOO)."""
    rule = OHIO.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # Both the inclusion-in-sale citation and the definition citation must appear.
    assert "5739.01(B)(12)" in notes
    assert "5739.01(OOO)" in notes


def test_ohio_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites Ohio Rev. Code section 5739.02(A)(1) (5.75% rate)."""
    rule = OHIO.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "5739.02(A)(1)" in (rule.notes or "")
    # The 5.75% rate must be explicitly documented in the notes.
    assert "5.75%" in (rule.notes or "")


# ---------------------------------------------------------------------------
# Inherited SST parser smoke checks
# ---------------------------------------------------------------------------
def test_ohio_parse_boundaries_signature() -> None:
    """parse_boundaries returns an iterable; we don't ship an OH fixture in this PR.

    The inherited :class:`SstStateModule` parser handles the actual SST
    file. This test confirms the method exists and is callable.
    """
    method = OHIO.parse_boundaries
    assert callable(method)


def test_ohio_parse_rates_signature() -> None:
    """parse_rates is callable; SST file processing is exercised by the SST parser tests."""
    method = OHIO.parse_rates
    assert callable(method)


# ---------------------------------------------------------------------------
# Sales tax holiday -- OH has the traditional 3-day back-to-school holiday in 2026
# (the expanded section 5739.41 holiday was cancelled by HB 186 of the 136th
# General Assembly, signed December 19, 2025).
# ---------------------------------------------------------------------------
def test_ohio_holiday_count_2026() -> None:
    """OH has exactly one annual holiday in 2026 (the traditional 3-day version)."""
    holidays = list(OHIO.holidays_for(2026))
    assert len(holidays) == 1
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_ohio_holiday_dates_2026() -> None:
    """2026 Ohio Sales Tax Holiday: first Friday of August (Aug 7) through Sunday Aug 9.

    Per ORC 5739.02(B)(55): the holiday runs from 12:00 a.m. Friday
    through 11:59 p.m. Sunday on the first Friday of August. After
    HB 186 of the 136th General Assembly (signed December 19, 2025)
    cancelled the expanded section 5739.41 holiday for 2026, Ohio
    reverts to the traditional 3-day version for 2026.
    """
    holiday = next(iter(OHIO.holidays_for(2026)))
    assert holiday.starts_on == dt.date(2026, 8, 7)
    assert holiday.ends_on == dt.date(2026, 8, 9)
    # Sanity: starts on a Friday, ends on a Sunday.
    assert holiday.starts_on.weekday() == 4  # Friday
    assert holiday.ends_on.weekday() == 6  # Sunday
    # And it really is the FIRST Friday of August (no earlier Friday this month).
    earlier = holiday.starts_on - dt.timedelta(days=7)
    assert earlier.month == 7  # the prior Friday is in July


def test_ohio_holiday_has_75_dollar_per_item_cap() -> None:
    """Statute imposes a $75 per-item cap on clothing (the higher of the per-category caps).

    The HolidayWindow schema's max_amount_per_item field cannot encode
    the per-category split (clothing $75 vs. supplies $20 vs.
    instructional materials $20); the higher $75 cap is stored and the
    notes field documents the split for downstream callers.
    """
    holiday = next(iter(OHIO.holidays_for(2026)))
    assert holiday.max_amount_per_item == Decimal("75.00")


def test_ohio_holiday_categories() -> None:
    """Statute covers clothing, school supplies, and instructional materials.

    Per ORC 5739.02(B)(55): three eligible categories, each with its
    own per-item cap (clothing $75, supplies $20, instructional
    materials $20).
    """
    holiday = next(iter(OHIO.holidays_for(2026)))
    assert holiday.applicable_categories is not None
    cats = set(holiday.applicable_categories)
    assert "clothing" in cats
    assert "school_supplies" in cats
    assert "instructional_materials" in cats
    # Most-TPP coverage from the section 5739.41 expanded framework was cancelled
    # for 2026 by HB 186; "general" should NOT be in the 2026 holiday categories.
    assert "general" not in cats


def test_ohio_holiday_notes_cite_statute_and_per_category_caps() -> None:
    """Holiday notes cite ORC 5739.02(B)(55) and document the per-category cap split."""
    holiday = next(iter(OHIO.holidays_for(2026)))
    assert holiday.notes is not None
    notes = holiday.notes
    assert "5739.02(B)(55)" in notes
    # Per-category caps must be documented since the schema can't carry them directly.
    assert "$75" in notes
    assert "$20" in notes
    # The HB 186 cancellation of the expanded 5739.41 framework must be documented
    # so future maintainers understand why 2026 is the traditional 3-day version.
    assert "HB 186" in notes
    assert "5739.41" in notes


def test_ohio_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design).

    2024 and 2025 had EXPANDED holidays under section 5739.41 that
    differed substantially from the traditional 3-day window; 2027+
    depends on whether the Tax Commissioner certifies the Expanded
    Sales Tax Holiday Fund. Future maintainers must add each year
    explicitly after verifying which framework applies.
    """
    assert list(OHIO.holidays_for(2024)) == []
    assert list(OHIO.holidays_for(2025)) == []
    assert list(OHIO.holidays_for(2027)) == []
    assert list(OHIO.holidays_for(2099)) == []


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine)
# ---------------------------------------------------------------------------
def test_ohio_special_cases_empty() -> None:
    cases = list(OHIO.special_cases())
    assert cases == []
