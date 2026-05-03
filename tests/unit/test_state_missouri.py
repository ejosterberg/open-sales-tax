# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Missouri state module (Phase 6 Batch B -- v0.7 tier-1).

Missouri is a non-SST state with a 4.225% statewide rate (composed
of 3.0% general revenue + 1.0% Proposition C education + 0.125%
parks/soils + 0.1% conservation) and several tier-1 quirks worth
dedicated tests:

- Reduced 1.225% effective state rate on groceries (Mo. Rev. Stat.
  section 144.014) modeled via the ``rate_modifier`` pattern from
  Illinois / Virginia.
- TWO annual sales-tax holidays: Show-Me Green (Mo. Rev. Stat.
  section 144.526) and Back-to-School (Mo. Rev. Stat. section
  144.049). Show-Me Green uses fixed calendar dates (April 19-25);
  back-to-school uses a weekday formula (first Friday of August
  through Sunday).
- Digital downloads non-taxable (sales tax applies only to tangible
  personal property per Mo. Rev. Stat. section 144.020).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.missouri import MISSOURI, Missouri
from opensalestax.states.protocol import HolidayWindow, StateModule


def test_missouri_metadata() -> None:
    assert MISSOURI.state_abbrev == "MO"
    assert MISSOURI.state_name == "Missouri"
    assert MISSOURI.sst_member is False  # MO is NOT in SST
    assert MISSOURI.has_sales_tax is True
    assert MISSOURI.tier == 1
    assert MISSOURI.self_seeded is True  # signals the loader to skip file lookup


def test_missouri_satisfies_protocol() -> None:
    assert isinstance(MISSOURI, StateModule)
    assert isinstance(Missouri(), StateModule)


def test_missouri_is_registered() -> None:
    assert get_state_module("MO") is MISSOURI


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; August holiday exempts $100/under
        ("groceries", True),  # reduced state rate via rate_modifier (1.225%)
        ("prescription_drugs", False),  # exempt per 144.030.2(18)
        ("prepared_food", True),
        ("digital_goods", False),  # sales tax applies only to tangible property
        ("general", True),  # 144.020 imposes 4.225% on tangible personal property
    ],
)
def test_missouri_taxability(category: str, expected_taxable: bool) -> None:
    rule = MISSOURI.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    # Every rule MUST cite a Missouri Revised Statutes section in its notes.
    assert rule.notes
    assert "144." in rule.notes


def test_missouri_unknown_category_returns_none() -> None:
    assert MISSOURI.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_missouri_parse_rates_yields_4225_pct() -> None:
    """Missouri's statewide rate is 4.225% (3.0% + 1.0% + 0.125% + 0.1%)."""
    rows = list(MISSOURI.parse_rates(None, "v0.7-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Missouri"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("4.225")
    assert row.effective_to is None
    assert row.parent_authority_name is None  # state-level rate has no parent


def test_missouri_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(MISSOURI.parse_rates(None, "test"))
    rows_with_path = list(MISSOURI.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_missouri_parse_boundaries_returns_empty() -> None:
    """v0.7 doesn't ship MO local boundaries (custom MO DOR loader deferred)."""
    assert list(MISSOURI.parse_boundaries(None, "v0.7-statewide")) == []


def test_missouri_special_cases_empty() -> None:
    assert list(MISSOURI.special_cases()) == []


def test_missouri_groceries_have_reduced_rate_marker() -> None:
    """MO's reduced 1.225% state grocery rate is encoded via rate_modifier.

    Per Mo. Rev. Stat. section 144.014, qualifying food for home
    consumption is taxed at 1.225% instead of the full 4.225% state
    rate -- the 3.000% general-revenue portion does not apply, but
    the 0.100% conservation, 0.125% parks/soils, and 1.000% education
    portions do, totaling 1.225%. Encoded using the same
    rate_modifier-as-absolute-percentage convention as Illinois (1.0)
    and Virginia (1.0).
    """
    rule = MISSOURI.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("1.225")
    assert "144.014" in (rule.notes or "")
    assert "1.225" in (rule.notes or "")


def test_missouri_digital_goods_non_taxable_with_caveat() -> None:
    """Digital goods are non-taxable when delivered electronically.

    Missouri sales tax applies only to tangible personal property
    (Mo. Rev. Stat. section 144.020); electronically-delivered
    digital goods are not tangible. Tangible-media sales (e.g.,
    boxed CD) remain taxable.
    """
    rule = MISSOURI.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = (rule.notes or "").lower()
    assert "tangible" in notes


def test_missouri_clothing_notes_back_to_school_holiday() -> None:
    """The clothing rule must reference the back-to-school holiday + statute."""
    rule = MISSOURI.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = (rule.notes or "").lower()
    assert "holiday" in notes
    assert "144.049" in (rule.notes or "")


def test_missouri_prescription_drugs_cite_144_030() -> None:
    """Prescription-drug exemption must cite Mo. Rev. Stat. section 144.030.2(18)."""
    rule = MISSOURI.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "144.030" in (rule.notes or "")


# ---------------------------------------------------------------------------
# Sales-tax holiday tests
# ---------------------------------------------------------------------------
def test_missouri_holidays_for_2026_returns_six_windows() -> None:
    """One Show-Me Green window + five back-to-school scope windows = 6 total."""
    holidays = list(MISSOURI.holidays_for(2026))
    assert len(holidays) == 6
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_missouri_holidays_for_unknown_year_returns_empty() -> None:
    """No extrapolation; future years require explicit data updates."""
    assert list(MISSOURI.holidays_for(2025)) == []
    assert list(MISSOURI.holidays_for(2027)) == []
    assert list(MISSOURI.holidays_for(2099)) == []


def test_missouri_2026_show_me_green_dates_april_19_to_25() -> None:
    """Mo. Rev. Stat. section 144.526: fixed calendar window April 19-25."""
    show_me_green = next(h for h in MISSOURI.holidays_for(2026) if "Show-Me Green" in h.name)
    assert show_me_green.starts_on == dt.date(2026, 4, 19)
    assert show_me_green.ends_on == dt.date(2026, 4, 25)
    assert show_me_green.applicable_categories == ("energy_star",)
    assert show_me_green.max_amount_per_item == Decimal("1500.00")
    assert "144.526" in (show_me_green.notes or "")


def test_missouri_2026_back_to_school_dates_first_friday_to_sunday() -> None:
    """Mo. Rev. Stat. section 144.049: first Friday of August through Sunday.

    For 2026 the first Friday of August is August 7, so the holiday
    runs August 7-9, 2026 (a 3-day weekend window).
    """
    back_to_school_windows = [h for h in MISSOURI.holidays_for(2026) if "Back-to-School" in h.name]
    assert len(back_to_school_windows) == 5  # clothing, supplies, computers, peripherals, software
    expected_start = dt.date(2026, 8, 7)
    expected_end = dt.date(2026, 8, 9)
    for h in back_to_school_windows:
        assert h.starts_on == expected_start
        assert h.ends_on == expected_end
        # Friday is weekday 4; verify the start is indeed a Friday
        assert h.starts_on.weekday() == 4
        # Sunday is weekday 6; verify the end is indeed a Sunday
        assert h.ends_on.weekday() == 6


def test_missouri_2026_back_to_school_per_item_caps() -> None:
    """Each scope of the back-to-school holiday has the statutory cap."""
    by_name = {h.name: h for h in MISSOURI.holidays_for(2026)}

    clothing = next(h for n, h in by_name.items() if "Clothing" in n)
    assert clothing.max_amount_per_item == Decimal("100.00")
    assert clothing.applicable_categories == ("clothing",)

    supplies = next(h for n, h in by_name.items() if "School Supplies" in n)
    assert supplies.max_amount_per_item == Decimal("50.00")
    assert supplies.applicable_categories == ("school_supplies",)

    computers = next(h for n, h in by_name.items() if "Personal Computers" in n)
    assert computers.max_amount_per_item == Decimal("1500.00")
    assert computers.applicable_categories == ("computers",)

    peripherals = next(h for n, h in by_name.items() if "Computer Peripherals" in n)
    assert peripherals.max_amount_per_item == Decimal("1500.00")
    assert peripherals.applicable_categories == ("computer_peripherals",)

    software = next(h for n, h in by_name.items() if "Computer Software" in n)
    assert software.max_amount_per_item == Decimal("350.00")
    assert software.applicable_categories == ("computer_software",)


def test_missouri_every_holiday_cites_statute() -> None:
    """Per the project quality bar: every HolidayWindow.notes must cite
    the governing Missouri Revised Statutes section.
    """
    for h in MISSOURI.holidays_for(2026):
        assert h.notes
        # Must cite either 144.526 (Show-Me Green) or 144.049 (Back-to-School)
        assert "144.526" in h.notes or "144.049" in h.notes


def test_missouri_holidays_chronologically_ordered() -> None:
    """Show-Me Green (April) precedes Back-to-School (August) windows."""
    starts = [h.starts_on for h in MISSOURI.holidays_for(2026)]
    assert starts == sorted(starts)
    # The first should be Show-Me Green in April
    assert starts[0] == dt.date(2026, 4, 19)
    # The remainder should all be Back-to-School in August
    for s in starts[1:]:
        assert s == dt.date(2026, 8, 7)
