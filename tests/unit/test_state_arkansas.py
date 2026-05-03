# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Arkansas state module (v0.8 tier-1 promotion)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.arkansas import ARKANSAS, Arkansas
from opensalestax.states.protocol import HolidayWindow, StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_arkansas_metadata() -> None:
    assert ARKANSAS.state_abbrev == "AR"
    assert ARKANSAS.state_name == "Arkansas"
    assert ARKANSAS.state_fips == "05"
    assert ARKANSAS.sst_member is True  # AR is an SST member
    assert ARKANSAS.has_sales_tax is True
    assert ARKANSAS.tier == 1


def test_arkansas_satisfies_protocol() -> None:
    assert isinstance(ARKANSAS, StateModule)
    assert isinstance(Arkansas(), StateModule)


def test_arkansas_is_a_sst_state_module() -> None:
    """AR uses the inherited SST parser; class hierarchy must hold."""
    assert isinstance(ARKANSAS, SstStateModule)


def test_arkansas_is_registered() -> None:
    assert get_state_module("AR") is ARKANSAS
    assert get_state_module("ar") is ARKANSAS  # case-insensitive lookup


# ---------------------------------------------------------------------------
# Taxability matrix -- statutory citations are mandatory in every notes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; August holiday window
        ("groceries", True),  # taxable but at REDUCED 0.000% (rate_modifier)
        ("prescription_drugs", False),  # exempt per 26-52-406
        ("prepared_food", True),  # general 6.5% rate; reduced does not apply
        ("digital_goods", True),  # taxable per Act 141 of 2017
        ("general", True),  # baseline tangible personal property
    ],
)
def test_arkansas_taxability(category: str, expected_taxable: bool) -> None:
    rule = ARKANSAS.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes_lower = rule.notes.lower()
    assert "26-52" in notes_lower or "act 141" in notes_lower


def test_arkansas_unknown_category_returns_none() -> None:
    assert ARKANSAS.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_arkansas_groceries_carry_zero_rate_modifier() -> None:
    """Groceries are taxable with rate_modifier=0.000 (Grocery Tax Relief Act).

    The Arkansas Grocery Tax Relief Act eliminated the state portion
    of the grocery sales tax effective January 1, 2026. The
    rate_modifier marks the special state rate; the engine doesn't
    yet apply rate_modifier (deferred to v0.6+). The notes field
    must document the statutory history.
    """
    rule = ARKANSAS.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("0.000")
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    # Cite the Grocery Tax Relief Act and the prior 0.125% rate
    assert "grocery tax relief act" in notes_lower
    assert "0.125%" in notes_lower or "0.125" in notes_lower
    assert "january 1, 2026" in notes_lower


def test_arkansas_prescription_drugs_cite_26_52_406() -> None:
    """Prescription drug exemption is in section 26-52-406."""
    rule = ARKANSAS.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert rule.notes is not None
    assert "26-52-406" in rule.notes


def test_arkansas_digital_goods_cite_act_141_of_2017() -> None:
    """AR taxes specified digital products at 6.5% per Act 141 of 2017."""
    rule = ARKANSAS.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "act 141" in notes_lower
    assert "2017" in notes_lower


def test_arkansas_clothing_notes_cite_holiday_statute() -> None:
    """Clothing is taxable year-round but the holiday section 26-52-444 is referenced."""
    rule = ARKANSAS.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    assert "26-52-444" in rule.notes


# ---------------------------------------------------------------------------
# Jurisdiction-type code mapping
# ---------------------------------------------------------------------------
def test_arkansas_jurisdiction_type_mapping_matches_canonical_sst() -> None:
    """AR uses the same SST type codes as MN and WI (assumption documented)."""
    mapping = ARKANSAS.jurisdiction_types
    assert mapping["45"] == "state"
    assert mapping["00"] == "county"
    assert mapping["01"] == "city"
    assert mapping["63"] == "district"


# ---------------------------------------------------------------------------
# Special cases (none in v0.8)
# ---------------------------------------------------------------------------
def test_arkansas_special_cases_empty() -> None:
    cases = list(ARKANSAS.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Holiday tests -- AR has ONE annual back-to-school holiday with multiple scopes
# ---------------------------------------------------------------------------
def test_arkansas_holiday_count_2026() -> None:
    """AR's 2026 holiday is encoded as 6 separate scopes (one per category)."""
    holidays = list(ARKANSAS.holidays_for(2026))
    assert len(holidays) == 6
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_arkansas_holiday_dates_2026() -> None:
    """2026 holiday: first Saturday of August (Aug 1) through Sunday (Aug 2)."""
    holidays = list(ARKANSAS.holidays_for(2026))
    for h in holidays:
        assert h.starts_on == dt.date(2026, 8, 1)
        assert h.ends_on == dt.date(2026, 8, 2)
    # Sanity: starts on a Saturday, ends on a Sunday.
    assert holidays[0].starts_on.weekday() == 5  # Saturday
    assert holidays[0].ends_on.weekday() == 6  # Sunday
    # And it really is the FIRST Saturday in August: previous Saturday
    # would have been in July.
    prev_saturday = holidays[0].starts_on - dt.timedelta(days=7)
    assert prev_saturday.month == 7


def test_arkansas_clothing_cap_is_100() -> None:
    """Clothing scope: $100 per-item cap per Ark. Code Ann. 26-52-444."""
    holidays = list(ARKANSAS.holidays_for(2026))
    clothing = next(h for h in holidays if h.applicable_categories == ("clothing",))
    assert clothing.max_amount_per_item == Decimal("100.00")
    assert clothing.notes is not None
    assert "26-52-444" in clothing.notes


def test_arkansas_clothing_accessories_cap_is_50() -> None:
    """Clothing accessories scope: $50 per-item cap per Ark. Code Ann. 26-52-444."""
    holidays = list(ARKANSAS.holidays_for(2026))
    accessories = next(h for h in holidays if h.applicable_categories == ("clothing_accessories",))
    assert accessories.max_amount_per_item == Decimal("50.00")
    assert accessories.notes is not None
    assert "26-52-444" in accessories.notes


def test_arkansas_school_supplies_have_no_cap() -> None:
    """School supplies scope: NO per-item cap under AR statute."""
    holidays = list(ARKANSAS.holidays_for(2026))
    supplies = next(h for h in holidays if h.applicable_categories == ("school_supplies",))
    assert supplies.max_amount_per_item is None


def test_arkansas_electronic_devices_have_no_cap() -> None:
    """Electronic devices (added by Act 944 of 2021) have NO per-item cap."""
    holidays = list(ARKANSAS.holidays_for(2026))
    electronics = next(h for h in holidays if h.applicable_categories == ("electronic_devices",))
    assert electronics.max_amount_per_item is None
    assert electronics.notes is not None
    assert "Act 944" in electronics.notes


def test_arkansas_holiday_categories_complete() -> None:
    """All 6 statutory scopes are encoded."""
    holidays = list(ARKANSAS.holidays_for(2026))
    cats = {h.applicable_categories for h in holidays}
    assert cats == {
        ("clothing",),
        ("clothing_accessories",),
        ("school_supplies",),
        ("school_art_supplies",),
        ("school_instructional_materials",),
        ("electronic_devices",),
    }


def test_arkansas_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design)."""
    assert list(ARKANSAS.holidays_for(2025)) == []
    assert list(ARKANSAS.holidays_for(2027)) == []
    assert list(ARKANSAS.holidays_for(2099)) == []
