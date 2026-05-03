# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the District of Columbia state module (v0.6 tier-1 ratchet)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.district_of_columbia import (
    DISTRICT_OF_COLUMBIA,
    DistrictOfColumbia,
)
from opensalestax.states.protocol import StateModule


def test_dc_metadata() -> None:
    assert DISTRICT_OF_COLUMBIA.state_abbrev == "DC"
    assert DISTRICT_OF_COLUMBIA.state_name == "District of Columbia"
    assert DISTRICT_OF_COLUMBIA.sst_member is False  # DC is NOT in SST
    assert DISTRICT_OF_COLUMBIA.has_sales_tax is True
    assert DISTRICT_OF_COLUMBIA.tier == 1
    assert DISTRICT_OF_COLUMBIA.self_seeded is True


def test_dc_satisfies_protocol() -> None:
    assert isinstance(DISTRICT_OF_COLUMBIA, StateModule)
    assert isinstance(DistrictOfColumbia(), StateModule)


def test_dc_is_registered() -> None:
    assert get_state_module("DC") is DISTRICT_OF_COLUMBIA


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # DC has no clothing exemption (holiday repealed 2009)
        ("groceries", False),  # food for home consumption excluded from "retail sale"
        ("prescription_drugs", False),  # DC Code Sec 47-2005(14)
        ("prepared_food", True),  # 10% statutory rate; engine applies general for now
        ("digital_goods", True),  # DC Code Sec 47-2001(d-1) and (n)(1)(BB)
        ("general", True),
    ],
)
def test_dc_taxability(category: str, expected_taxable: bool) -> None:
    rule = DISTRICT_OF_COLUMBIA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes


def test_dc_unknown_category_returns_none() -> None:
    assert DISTRICT_OF_COLUMBIA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_dc_parse_rates_yields_two_dated_rate_rows() -> None:
    """DC emits two rate rows: 6% (current) and 7% (effective Oct 1, 2026)."""
    rows = list(DISTRICT_OF_COLUMBIA.parse_rates(None, "v0.6-statewide"))
    assert len(rows) == 2

    # First row: 6% with end-date Sept 30, 2026
    six = rows[0]
    assert six.authority_name == "District of Columbia"
    assert six.authority_type == "state"
    assert six.rate_pct == Decimal("6.000")
    assert six.effective_to == dt.date(2026, 9, 30)
    assert six.parent_authority_name is None

    # Second row: 7% effective Oct 1, 2026, no end date
    seven = rows[1]
    assert seven.authority_name == "District of Columbia"
    assert seven.authority_type == "state"
    assert seven.rate_pct == Decimal("7.000")
    assert seven.effective_from == dt.date(2026, 10, 1)
    assert seven.effective_to is None


def test_dc_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(DISTRICT_OF_COLUMBIA.parse_rates(None, "test"))
    rows_with_path = list(DISTRICT_OF_COLUMBIA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_dc_parse_rate_windows_are_contiguous() -> None:
    """The 6% window's effective_to is the day before the 7% window's effective_from."""
    rows = list(DISTRICT_OF_COLUMBIA.parse_rates(None, "test"))
    assert rows[0].effective_to is not None
    one_day = dt.timedelta(days=1)
    assert rows[0].effective_to + one_day == rows[1].effective_from


def test_dc_parse_boundaries_returns_empty() -> None:
    """v0.6 doesn't ship DC boundaries; PostGIS work is Phase 4+."""
    rows = list(DISTRICT_OF_COLUMBIA.parse_boundaries(None, "v0.6-statewide"))
    assert rows == []


def test_dc_special_cases_empty() -> None:
    cases = list(DISTRICT_OF_COLUMBIA.special_cases())
    assert cases == []


def test_dc_holidays_for_2026_is_empty() -> None:
    """DC repealed its back-to-school holiday in 2009 (D.C. Law 18-111)."""
    holidays = list(DISTRICT_OF_COLUMBIA.holidays_for(2026))
    assert holidays == []


def test_dc_holidays_for_other_years_also_empty() -> None:
    """DC has no annual sales-tax holidays in any year."""
    for year in (2024, 2025, 2027, 2030):
        holidays = list(DISTRICT_OF_COLUMBIA.holidays_for(year))
        assert holidays == [], f"DC should have no holidays in {year}"


def test_dc_groceries_cite_47_2001() -> None:
    """DC's grocery exemption flows from the 'retail sale' definition exclusion."""
    rule = DISTRICT_OF_COLUMBIA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    notes_lower = (rule.notes or "").lower()
    assert "47-2001" in notes_lower
    assert "home consumption" in notes_lower


def test_dc_prepared_food_notes_special_rate_caveat() -> None:
    """The prepared_food rule must flag the 10% special rate isn't engine-wired yet."""
    rule = DISTRICT_OF_COLUMBIA.taxability_for("prepared_food", dt.date(2026, 5, 3))
    assert rule is not None
    notes_lower = (rule.notes or "").lower()
    assert "10%" in notes_lower
    assert "47-2002.02" in notes_lower
