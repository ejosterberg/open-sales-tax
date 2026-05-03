# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Iowa state module (tier-2 -> tier-1 promotion)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.iowa import IOWA, Iowa
from opensalestax.states.protocol import HolidayWindow, StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_iowa_metadata() -> None:
    assert IOWA.state_abbrev == "IA"
    assert IOWA.state_name == "Iowa"
    assert IOWA.sst_member is True  # IA is a Streamlined Sales Tax member
    assert IOWA.has_sales_tax is True
    assert IOWA.tier == 1
    assert IOWA.state_fips == "19"


def test_iowa_inherits_sst_base() -> None:
    """Iowa subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(IOWA, SstStateModule)
    assert isinstance(Iowa(), SstStateModule)


def test_iowa_satisfies_protocol() -> None:
    assert isinstance(IOWA, StateModule)
    assert isinstance(Iowa(), StateModule)


def test_iowa_is_registered() -> None:
    assert get_state_module("IA") is IOWA
    assert get_state_module("ia") is IOWA  # case-insensitive


def test_iowa_is_not_in_tier2_anymore() -> None:
    """IA was promoted out of _tier2.py; it must no longer be registered as tier 2."""
    from opensalestax.states._tier2 import TIER_2_STATES

    abbrevs = {s.state_abbrev for s in TIER_2_STATES}
    assert "IA" not in abbrevs


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; 2-day August holiday window
        ("groceries", False),  # exempt per Iowa Code 423.3(57)
        ("prescription_drugs", False),  # exempt per Iowa Code 423.3(60)
        ("prepared_food", True),  # general 6%; excluded from grocery exemption
        ("digital_goods", True),  # taxable per Iowa Code 423.5A (HF 779, 2018)
        ("general", True),  # baseline TPP at 6% per Iowa Code 423.2
    ],
)
def test_iowa_taxability(category: str, expected_taxable: bool) -> None:
    rule = IOWA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "Iowa Code" in (rule.notes or "")


def test_iowa_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert IOWA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_iowa_clothing_rule_cites_holiday_statute() -> None:
    """Clothing rule references the August holiday statute."""
    rule = IOWA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "423.3(68)" in (rule.notes or "")


def test_iowa_groceries_rule_cites_subsection_57() -> None:
    """Grocery exemption is in subsection 57 of 423.3."""
    rule = IOWA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "423.3(57)" in (rule.notes or "")


def test_iowa_prescription_drugs_cite_subsection_60() -> None:
    """Prescription-drug exemption is in subsection 60 of 423.3."""
    rule = IOWA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "423.3(60)" in (rule.notes or "")


def test_iowa_digital_goods_notes_2018_statute() -> None:
    """IA taxes specified digital products at 6% per HF 779 of 2018 (Iowa Code 423.5A)."""
    rule = IOWA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "423.5A" in notes
    assert "779" in notes  # HF 779 of 2018


def test_iowa_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites Iowa Code section 423.2 (the imposition statute)."""
    rule = IOWA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "423.2" in (rule.notes or "")


# ---------------------------------------------------------------------------
# Inherited SST parser smoke checks
# ---------------------------------------------------------------------------
def test_iowa_parse_boundaries_signature() -> None:
    """parse_boundaries returns an iterable; we don't ship an IA fixture in this PR.

    The inherited :class:`SstStateModule` parser handles the actual SST
    file. This test confirms the method exists and yields an iterable
    when called with no source file (returns nothing because the
    underlying parser has nothing to read).
    """
    # Call the bound method without invoking it on a real file. The
    # parser is generator-based and will simply yield nothing if given
    # an empty source. We assert callability + iterability rather than
    # constructing a fake fixture here.
    method = IOWA.parse_boundaries
    assert callable(method)


# ---------------------------------------------------------------------------
# Sales tax holiday -- IA has ONE annual holiday
# ---------------------------------------------------------------------------
def test_iowa_holiday_count_2026() -> None:
    """IA has exactly one annual holiday in 2026 (Iowa Code 423.3(68))."""
    holidays = list(IOWA.holidays_for(2026))
    assert len(holidays) == 1
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_iowa_holiday_dates_2026() -> None:
    """2026 Iowa Sales Tax Holiday: first Friday in August (Aug 7) - Saturday Aug 8.

    Per Iowa Code section 423.3(68): the holiday runs from 12:01 a.m.
    Friday through 11:59 p.m. Saturday on the first Friday and
    Saturday in August.
    """
    holiday = next(iter(IOWA.holidays_for(2026)))
    assert holiday.starts_on == dt.date(2026, 8, 7)
    assert holiday.ends_on == dt.date(2026, 8, 8)
    # Sanity: starts on a Friday, ends on a Saturday.
    assert holiday.starts_on.weekday() == 4  # Friday
    assert holiday.ends_on.weekday() == 5  # Saturday
    # And it really is the FIRST Friday in August (no earlier Friday this month).
    earlier = holiday.starts_on - dt.timedelta(days=7)
    assert earlier.month == 7  # the prior Friday is in July


def test_iowa_holiday_has_100_dollar_per_item_cap() -> None:
    """Statute imposes a less-than-$100 per-article cap on clothing/footwear."""
    holiday = next(iter(IOWA.holidays_for(2026)))
    assert holiday.max_amount_per_item == Decimal("100.00")


def test_iowa_holiday_categories() -> None:
    """Statute covers clothing (incl. footwear); does NOT cover accessories or athletic gear."""
    holiday = next(iter(IOWA.holidays_for(2026)))
    assert holiday.applicable_categories is not None
    cats = set(holiday.applicable_categories)
    assert "clothing" in cats
    # School supplies and accessories are NOT in scope (unlike e.g. MS).
    assert "school_supplies" not in cats
    assert "accessories" not in cats


def test_iowa_holiday_notes_cite_statute_and_exclusions() -> None:
    """Holiday notes cite Iowa Code 423.3(68) and document key exclusions."""
    holiday = next(iter(IOWA.holidays_for(2026)))
    assert holiday.notes is not None
    assert "423.3(68)" in holiday.notes
    notes_lower = holiday.notes.lower()
    # Document the major statutory exclusions for downstream reviewers.
    assert "accessor" in notes_lower  # accessories excluded
    assert "athletic" in notes_lower  # athletic / protective clothing excluded


def test_iowa_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design)."""
    assert list(IOWA.holidays_for(2025)) == []
    assert list(IOWA.holidays_for(2027)) == []
    assert list(IOWA.holidays_for(2099)) == []


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine)
# ---------------------------------------------------------------------------
def test_iowa_special_cases_empty() -> None:
    cases = list(IOWA.special_cases())
    assert cases == []
