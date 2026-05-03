# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the South Carolina state module (v0.6 tier-1 ratchet)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.protocol import HolidayWindow, StateModule
from opensalestax.states.south_carolina import SOUTH_CAROLINA, SouthCarolina


def test_south_carolina_metadata() -> None:
    assert SOUTH_CAROLINA.state_abbrev == "SC"
    assert SOUTH_CAROLINA.state_name == "South Carolina"
    assert SOUTH_CAROLINA.sst_member is False  # SC is NOT in SST
    assert SOUTH_CAROLINA.has_sales_tax is True
    assert SOUTH_CAROLINA.tier == 1
    assert SOUTH_CAROLINA.self_seeded is True  # signals loader to skip file lookup


def test_south_carolina_satisfies_protocol() -> None:
    assert isinstance(SOUTH_CAROLINA, StateModule)
    assert isinstance(SouthCarolina(), StateModule)


def test_south_carolina_is_registered() -> None:
    assert get_state_module("SC") is SOUTH_CAROLINA


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; holiday provides 72-hour window
        ("groceries", False),  # state-level exempt per 12-36-2120(75)
        ("prescription_drugs", False),  # exempt per 12-36-2120(28)
        ("prepared_food", True),  # exemption is for UNPREPARED food only
        ("digital_goods", False),  # SC quirk: e-delivered software not taxable (RR 03-5)
        ("general", True),  # baseline tangible personal property
    ],
)
def test_south_carolina_taxability(category: str, expected_taxable: bool) -> None:
    rule = SOUTH_CAROLINA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes_lower = rule.notes.lower()
    assert "12-36" in notes_lower or "rr 03-5" in notes_lower or "ruling 03-5" in notes_lower


def test_south_carolina_unknown_category_returns_none() -> None:
    assert SOUTH_CAROLINA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_south_carolina_parse_rates_yields_6pct() -> None:
    """South Carolina's statewide rate is 6% effective 2007-06-01."""
    rows = list(SOUTH_CAROLINA.parse_rates(None, "v0.6-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "South Carolina"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("6.000")
    assert row.effective_from == dt.date(2007, 6, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_south_carolina_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(SOUTH_CAROLINA.parse_rates(None, "test"))
    rows_with_path = list(SOUTH_CAROLINA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_south_carolina_parse_boundaries_returns_empty() -> None:
    """v0.6 doesn't ship SC boundaries; per-county load deferred."""
    rows = list(SOUTH_CAROLINA.parse_boundaries(None, "v0.6-statewide"))
    assert rows == []


def test_south_carolina_special_cases_empty() -> None:
    cases = list(SOUTH_CAROLINA.special_cases())
    assert cases == []


def test_south_carolina_groceries_notes_local_caveat() -> None:
    """The grocery rule must call out that local taxes may still apply."""
    rule = SOUTH_CAROLINA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    assert "local" in rule.notes.lower()
    assert "12-36-2120(75)" in rule.notes


def test_south_carolina_digital_goods_notes_quirk() -> None:
    """SC's non-taxable digital goods is unusual; the rule must say so."""
    rule = SOUTH_CAROLINA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert rule.notes is not None
    assert "physical media" in rule.notes.lower() or "diskette" in rule.notes.lower()


# ---------------------------------------------------------------------------
# Holiday tests (Tax Free Weekend) -- mirrors test_holidays.py shape
# ---------------------------------------------------------------------------
def test_south_carolina_holiday_count_2026() -> None:
    """SC has exactly one annual holiday (the August Tax Free Weekend)."""
    holidays = list(SOUTH_CAROLINA.holidays_for(2026))
    assert len(holidays) == 1
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_south_carolina_holiday_dates_2026() -> None:
    """2026 Tax Free Weekend: Friday Aug 7 through Sunday Aug 9."""
    (holiday,) = list(SOUTH_CAROLINA.holidays_for(2026))
    assert holiday.starts_on == dt.date(2026, 8, 7)
    assert holiday.ends_on == dt.date(2026, 8, 9)
    # Sanity: starts on a Friday, ends on a Sunday (statutory pattern).
    assert holiday.starts_on.weekday() == 4  # Friday
    assert holiday.ends_on.weekday() == 6  # Sunday


def test_south_carolina_holiday_has_no_per_item_cap() -> None:
    """Statute does not impose a per-item dollar threshold."""
    (holiday,) = list(SOUTH_CAROLINA.holidays_for(2026))
    assert holiday.max_amount_per_item is None


def test_south_carolina_holiday_categories_include_clothing_and_supplies() -> None:
    """Statute covers clothing, school supplies, computers, and bed/bath."""
    (holiday,) = list(SOUTH_CAROLINA.holidays_for(2026))
    assert holiday.applicable_categories is not None
    cats = set(holiday.applicable_categories)
    assert "clothing" in cats
    assert "school_supplies" in cats
    assert "computers" in cats
    assert "bed_and_bath" in cats


def test_south_carolina_holiday_notes_cite_statute() -> None:
    """The holiday window's notes must cite the authorizing statute."""
    (holiday,) = list(SOUTH_CAROLINA.holidays_for(2026))
    assert holiday.notes is not None
    assert "12-36-2120(57)" in holiday.notes


def test_south_carolina_holiday_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design)."""
    assert list(SOUTH_CAROLINA.holidays_for(2025)) == []
    assert list(SOUTH_CAROLINA.holidays_for(2027)) == []
    assert list(SOUTH_CAROLINA.holidays_for(2099)) == []
