# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the West Virginia state module (tier-2 -> tier-1 promotion)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import HolidayWindow, StateModule
from opensalestax.states.west_virginia import WEST_VIRGINIA, WestVirginia


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_west_virginia_metadata() -> None:
    assert WEST_VIRGINIA.state_abbrev == "WV"
    assert WEST_VIRGINIA.state_name == "West Virginia"
    assert WEST_VIRGINIA.sst_member is True  # WV is a Streamlined Sales Tax member
    assert WEST_VIRGINIA.has_sales_tax is True
    assert WEST_VIRGINIA.tier == 1
    assert WEST_VIRGINIA.state_fips == "54"


def test_west_virginia_inherits_sst_base() -> None:
    """WV subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(WEST_VIRGINIA, SstStateModule)
    assert isinstance(WestVirginia(), SstStateModule)


def test_west_virginia_satisfies_protocol() -> None:
    assert isinstance(WEST_VIRGINIA, StateModule)
    assert isinstance(WestVirginia(), StateModule)


def test_west_virginia_is_registered() -> None:
    assert get_state_module("WV") is WEST_VIRGINIA
    assert get_state_module("wv") is WEST_VIRGINIA  # case-insensitive


def test_west_virginia_is_not_in_tier2_anymore() -> None:
    """WV was promoted out of _tier2.py; it must no longer be registered as tier 2."""
    from opensalestax.states._tier2 import TIER_2_STATES

    abbrevs = {s.state_abbrev for s in TIER_2_STATES}
    assert "WV" not in abbrevs


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; 4-day August holiday window
        ("groceries", False),  # exempt per W. Va. Code 11-15-3a (since 2013-07-01)
        ("prescription_drugs", False),  # exempt per W. Va. Code 11-15-9(a)(11)
        ("prepared_food", True),  # general 6%; excluded from grocery exemption
        ("digital_goods", True),  # taxable per W. Va. Code 11-15B-2 (2008+)
        ("general", True),  # baseline TPP at 6% per W. Va. Code 11-15-3
    ],
)
def test_west_virginia_taxability(category: str, expected_taxable: bool) -> None:
    rule = WEST_VIRGINIA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "W. Va. Code" in (rule.notes or "")


def test_west_virginia_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert WEST_VIRGINIA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_west_virginia_clothing_rule_cites_holiday_statute() -> None:
    """Clothing rule references the August holiday statute."""
    rule = WEST_VIRGINIA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "11-15-9o" in (rule.notes or "")


def test_west_virginia_groceries_exempt_with_phase_out_history() -> None:
    """Groceries are FULLY EXEMPT (regression guard against tier-2 default).

    The tier-2 default also marks groceries non-taxable, but WV's
    exemption is the result of a multi-year phase-out culminating
    in 2013-07-01 elimination per section 11-15-3a -- that history
    must be documented in the rule's notes for future maintainers.
    """
    rule = WEST_VIRGINIA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "11-15-3a" in notes
    # Phase-out history must be documented in the rule (per the brief).
    assert "2013-07-01" in notes
    assert (
        "phased down" in notes.lower() or "phase-out" in notes.lower() or "phased" in notes.lower()
    )


def test_west_virginia_prescription_drugs_cite_subsection_11() -> None:
    """Prescription-drug exemption is in section 11-15-9(a)(11)."""
    rule = WEST_VIRGINIA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "11-15-9(a)(11)" in (rule.notes or "")


def test_west_virginia_digital_goods_cite_11_15B_2() -> None:
    """WV taxes specified digital products per W. Va. Code 11-15B-2 (SST conformity)."""
    rule = WEST_VIRGINIA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "11-15B-2" in notes


def test_west_virginia_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites W. Va. Code section 11-15-3 (the imposition statute)."""
    rule = WEST_VIRGINIA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "11-15-3" in (rule.notes or "")


def test_west_virginia_general_rule_mentions_home_rule() -> None:
    """General rule documents the W. Va. Code 8-13C municipal home-rule local tax."""
    rule = WEST_VIRGINIA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert "8-13C" in (rule.notes or "")


# ---------------------------------------------------------------------------
# Inherited SST parser smoke checks
# ---------------------------------------------------------------------------
def test_west_virginia_parse_boundaries_signature() -> None:
    """parse_boundaries returns an iterable; we don't ship a WV fixture in this PR.

    The inherited :class:`SstStateModule` parser handles the actual SST
    file. This test confirms the method exists; the underlying parser
    will simply yield nothing if given an empty source.
    """
    method = WEST_VIRGINIA.parse_boundaries
    assert callable(method)


# ---------------------------------------------------------------------------
# Sales tax holiday -- WV has ONE annual statutory holiday split across
# 5 scopes (W. Va. Code section 11-15-9o), each encoded as a separate
# HolidayWindow because max_amount_per_item is single-value.
# ---------------------------------------------------------------------------
def test_west_virginia_holiday_count_2026() -> None:
    """WV has 5 HolidayWindow scopes in 2026 under W. Va. Code 11-15-9o."""
    holidays = list(WEST_VIRGINIA.holidays_for(2026))
    assert len(holidays) == 5
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_west_virginia_holiday_dates_2026() -> None:
    """2026 WV Sales Tax Holiday: first Friday in August (Aug 7) - Monday Aug 10.

    Per W. Va. Code section 11-15-9o the holiday runs from 12:00
    a.m. on the first Friday in August through 11:59 p.m. on the
    following Monday (a 4-day window).
    """
    holidays = list(WEST_VIRGINIA.holidays_for(2026))
    for holiday in holidays:
        assert holiday.starts_on == dt.date(2026, 8, 7)
        assert holiday.ends_on == dt.date(2026, 8, 10)
        # Sanity: starts on a Friday, ends on a Monday.
        assert holiday.starts_on.weekday() == 4  # Friday
        assert holiday.ends_on.weekday() == 0  # Monday
        # And it really is the FIRST Friday in August (no earlier Friday this month).
        earlier = holiday.starts_on - dt.timedelta(days=7)
        assert earlier.month == 7  # the prior Friday is in July


def test_west_virginia_holiday_per_scope_caps() -> None:
    """Each scope has the statutory per-item cap from section 11-15-9o.

    Caps per the brief and W. Va. Code section 11-15-9o:
    - clothing/footwear: $125
    - school supplies: $50
    - school instructional materials: $20
    - sports equipment: $150
    - computers / tablets: $500
    """
    holidays = {
        cat: holiday
        for holiday in WEST_VIRGINIA.holidays_for(2026)
        for cat in (holiday.applicable_categories or ())
    }
    assert holidays["clothing"].max_amount_per_item == Decimal("125.00")
    assert holidays["school_supplies"].max_amount_per_item == Decimal("50.00")
    assert holidays["school_instructional_materials"].max_amount_per_item == Decimal("20.00")
    assert holidays["sports_equipment"].max_amount_per_item == Decimal("150.00")
    assert holidays["computers"].max_amount_per_item == Decimal("500.00")


def test_west_virginia_holiday_scopes_are_separate_windows() -> None:
    """Each scope is its own HolidayWindow (single-value max_amount_per_item).

    This is the same multi-window pattern used by VA and MO -- the
    HolidayWindow dataclass cannot represent multi-tier caps within
    one window, so each scope gets its own.
    """
    holidays = list(WEST_VIRGINIA.holidays_for(2026))
    # Every holiday has exactly one applicable_category in WV's 5-scope split.
    for holiday in holidays:
        assert holiday.applicable_categories is not None
        assert len(holiday.applicable_categories) == 1
    all_categories = {h.applicable_categories[0] for h in holidays if h.applicable_categories}
    expected = {
        "clothing",
        "school_supplies",
        "school_instructional_materials",
        "sports_equipment",
        "computers",
    }
    assert all_categories == expected


def test_west_virginia_holiday_notes_cite_statute() -> None:
    """Every holiday window's notes cite W. Va. Code section 11-15-9o."""
    for holiday in WEST_VIRGINIA.holidays_for(2026):
        assert holiday.notes is not None
        assert "11-15-9o" in holiday.notes


def test_west_virginia_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design)."""
    assert list(WEST_VIRGINIA.holidays_for(2025)) == []
    assert list(WEST_VIRGINIA.holidays_for(2027)) == []
    assert list(WEST_VIRGINIA.holidays_for(2099)) == []


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine)
# ---------------------------------------------------------------------------
def test_west_virginia_special_cases_empty() -> None:
    cases = list(WEST_VIRGINIA.special_cases())
    assert cases == []
