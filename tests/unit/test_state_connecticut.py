# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Connecticut state module (Phase 6, v0.6 -- tier-1 promotion)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.connecticut import CONNECTICUT, Connecticut
from opensalestax.states.protocol import HolidayWindow, StateModule


def test_connecticut_metadata() -> None:
    assert CONNECTICUT.state_abbrev == "CT"
    assert CONNECTICUT.state_name == "Connecticut"
    assert CONNECTICUT.sst_member is False  # CT is NOT in SST
    assert CONNECTICUT.has_sales_tax is True
    assert CONNECTICUT.tier == 1
    assert CONNECTICUT.self_seeded is True  # signals the loader to skip file lookup


def test_connecticut_satisfies_protocol() -> None:
    assert isinstance(CONNECTICUT, StateModule)
    assert isinstance(Connecticut(), StateModule)


def test_connecticut_is_registered() -> None:
    assert get_state_module("CT") is CONNECTICUT


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # CT taxes clothing year-round (under-$50 exemption repealed 2015)
        ("groceries", False),  # Conn. Gen. Stat. section 12-412(13)
        ("prescription_drugs", False),  # section 12-412(4)
        ("prepared_food", True),  # 7.35% combined; v0.6 applies 6.35% only
        ("digital_goods", True),  # P.A. 19-117 / section 12-407(a)(13)
        ("general", True),  # section 12-408(1)(A)
    ],
)
def test_connecticut_taxability(category: str, expected_taxable: bool) -> None:
    rule = CONNECTICUT.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_connecticut_unknown_category_returns_none() -> None:
    assert CONNECTICUT.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_connecticut_parse_rates_yields_635_pct() -> None:
    """Connecticut's statewide rate is 6.35% effective 2011-07-01 (P.A. 11-6)."""
    rows = list(CONNECTICUT.parse_rates(None, "v0.6-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Connecticut"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("6.350")
    assert row.effective_from == dt.date(2011, 7, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None  # state-level rate has no parent


def test_connecticut_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(CONNECTICUT.parse_rates(None, "test"))
    rows_with_path = list(CONNECTICUT.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_connecticut_parse_boundaries_returns_empty() -> None:
    """CT is state-only; no county/city sub-state authorities to ship."""
    rows = list(CONNECTICUT.parse_boundaries(None, "v0.6-statewide"))
    assert rows == []


def test_connecticut_special_cases_empty() -> None:
    """The 7.75%/7.35%/15% category rates and Mashantucket Pequot regime are
    documented in the module docstring but not yet exposed via SpecialCase
    (engine support pending).
    """
    cases = list(CONNECTICUT.special_cases())
    assert cases == []


def test_connecticut_clothing_notes_cite_repealed_exemption() -> None:
    """The clothing rule notes the under-$50 exemption was repealed in 2015."""
    rule = CONNECTICUT.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "2015" in (rule.notes or "")
    assert "12-408" in (rule.notes or "")


def test_connecticut_digital_goods_notes_cite_pa_19_117() -> None:
    """Digital-goods rule must cite the 2019 statutory amendment."""
    rule = CONNECTICUT.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert "19-117" in (rule.notes or "")


def test_connecticut_2026_holiday_is_sales_tax_free_week() -> None:
    """Annual third-Sunday-in-August Sales Tax Free Week (Conn. Gen. Stat. 12-407e).

    For 2026, the third Sunday of August is August 16; the holiday runs
    through Saturday August 22.
    """
    holidays = list(CONNECTICUT.holidays_for(2026))
    assert len(holidays) == 1
    h = holidays[0]
    assert isinstance(h, HolidayWindow)
    assert "Sales Tax Free Week" in h.name
    assert h.starts_on == dt.date(2026, 8, 16)
    assert h.ends_on == dt.date(2026, 8, 22)
    # Sunday through following Saturday = 7 days inclusive
    assert (h.ends_on - h.starts_on).days == 6
    assert h.applicable_categories == ("clothing",)
    assert h.max_amount_per_item == Decimal("100.00")
    assert "12-407e" in (h.notes or "")


def test_connecticut_holiday_starts_on_third_sunday_of_august() -> None:
    """Statutory invariant: the holiday begins on the third Sunday of August."""
    h = next(iter(CONNECTICUT.holidays_for(2026)))
    # Sunday is weekday 6 (Mon=0)
    assert h.starts_on.weekday() == 6
    assert h.starts_on.month == 8
    # Third Sunday means day-of-month is 15-21
    assert 15 <= h.starts_on.day <= 21


def test_connecticut_holidays_for_unknown_year_returns_empty() -> None:
    """Future years require explicit data updates; no extrapolation."""
    assert list(CONNECTICUT.holidays_for(2099)) == []
    assert list(CONNECTICUT.holidays_for(2025)) == []
