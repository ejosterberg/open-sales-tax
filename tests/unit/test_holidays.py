# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the v0.5 sales-tax holidays feature.

Pure tests: per-state holiday data + HolidayWindow dataclass +
HolidayPeriod ORM model behavior.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.db.models import HolidayPeriod
from opensalestax.states import all_states
from opensalestax.states.florida import FLORIDA
from opensalestax.states.maryland import MARYLAND
from opensalestax.states.massachusetts import MASSACHUSETTS
from opensalestax.states.protocol import HolidayWindow
from opensalestax.states.texas import TEXAS

# (state, expected count of 2026 holidays, headline-holiday name fragment)
HOLIDAY_STATES = [
    (TEXAS, 3, "Back-to-School"),
    (FLORIDA, 4, "Disaster Preparedness"),
    (MASSACHUSETTS, 1, "Annual Sales Tax Holiday"),
    (MARYLAND, 2, "Shop Maryland"),
]


@pytest.mark.parametrize("state,expected_count,_name_fragment", HOLIDAY_STATES)
def test_holiday_count_2026(state, expected_count: int, _name_fragment: str) -> None:
    """Each state with annual holidays returns the expected count for 2026."""
    holidays = list(state.holidays_for(2026))
    assert len(holidays) == expected_count
    assert all(isinstance(h, HolidayWindow) for h in holidays)


@pytest.mark.parametrize("state,_count,name_fragment", HOLIDAY_STATES)
def test_each_state_has_signature_holiday(state, _count, name_fragment: str) -> None:
    """The headline holiday for each state is in the 2026 list."""
    holidays = list(state.holidays_for(2026))
    matching = [h for h in holidays if name_fragment in h.name]
    assert matching, f"expected a holiday with {name_fragment!r} in {state.state_name}"


@pytest.mark.parametrize("state,_count,_name_fragment", HOLIDAY_STATES)
def test_holidays_are_chronologically_ordered_within_year(state, _count, _name_fragment) -> None:
    """Sanity: starts_on dates are non-decreasing within each year."""
    starts = [h.starts_on for h in state.holidays_for(2026)]
    assert starts == sorted(starts)


@pytest.mark.parametrize("state,_count,_name_fragment", HOLIDAY_STATES)
def test_holiday_dates_are_in_2026(state, _count, _name_fragment) -> None:
    """Every 2026 holiday's dates fall in 2026."""
    for h in state.holidays_for(2026):
        assert h.starts_on.year == 2026
        assert h.ends_on.year == 2026
        assert h.starts_on <= h.ends_on


def test_states_without_holidays_return_empty() -> None:
    """States like CA, MN, NY have no annual holidays in v0.5."""
    from opensalestax.states.california import CALIFORNIA
    from opensalestax.states.minnesota import MINNESOTA
    from opensalestax.states.new_york import NEW_YORK

    for state in (CALIFORNIA, MINNESOTA, NEW_YORK):
        assert list(state.holidays_for(2026)) == []


def test_holidays_for_unknown_year_returns_empty() -> None:
    """States return empty for years they don't have data for (no extrapolation)."""
    for state, _, _ in HOLIDAY_STATES:
        assert list(state.holidays_for(2099)) == []


def test_every_state_module_implements_holidays_for() -> None:
    """Every registered state has a holidays_for that returns an iterable."""
    for state in all_states():
        result = state.holidays_for(2026)
        # Should be iterable (consume to verify it doesn't raise)
        list(result)


# ---------------------------------------------------------------------------
# HolidayPeriod ORM model behavior (pure; no DB)
# ---------------------------------------------------------------------------
def test_holiday_period_covers() -> None:
    h = HolidayPeriod(
        state_id=1,
        name="Test",
        starts_on=dt.date(2026, 8, 7),
        ends_on=dt.date(2026, 8, 9),
    )
    assert h.covers(dt.date(2026, 8, 7))  # inclusive start
    assert h.covers(dt.date(2026, 8, 8))
    assert h.covers(dt.date(2026, 8, 9))  # inclusive end
    assert not h.covers(dt.date(2026, 8, 6))
    assert not h.covers(dt.date(2026, 8, 10))


def test_holiday_period_applies_to_no_categories_means_all() -> None:
    """applicable_categories=None covers every category."""
    h = HolidayPeriod(
        state_id=1,
        name="Open Holiday",
        starts_on=dt.date(2026, 8, 7),
        ends_on=dt.date(2026, 8, 9),
        applicable_categories=None,
    )
    assert h.applies_to("clothing", Decimal("50"))
    assert h.applies_to("anything_at_all", Decimal("999999"))


def test_holiday_period_applies_to_respects_categories() -> None:
    h = HolidayPeriod(
        state_id=1,
        name="Clothing Only",
        starts_on=dt.date(2026, 8, 7),
        ends_on=dt.date(2026, 8, 9),
        applicable_categories=["clothing", "school_supplies"],
    )
    assert h.applies_to("clothing", Decimal("50"))
    assert h.applies_to("school_supplies", Decimal("20"))
    assert not h.applies_to("electronics", Decimal("50"))
    assert not h.applies_to("general", Decimal("10"))


def test_holiday_period_respects_max_amount() -> None:
    h = HolidayPeriod(
        state_id=1,
        name="Capped",
        starts_on=dt.date(2026, 8, 7),
        ends_on=dt.date(2026, 8, 9),
        applicable_categories=["clothing"],
        max_amount_per_item=Decimal("100"),
    )
    assert h.applies_to("clothing", Decimal("99.99"))
    assert h.applies_to("clothing", Decimal("100.00"))  # inclusive
    assert not h.applies_to("clothing", Decimal("100.01"))
    assert not h.applies_to("clothing", Decimal("500"))
