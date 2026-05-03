# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Maine state module (Phase 8 -- non-SST tier-0 -> tier-1)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.maine import MAINE, Maine
from opensalestax.states.protocol import StateModule


def test_maine_metadata() -> None:
    assert MAINE.state_abbrev == "ME"
    assert MAINE.state_name == "Maine"
    assert MAINE.sst_member is False  # ME is NOT in SST
    assert MAINE.has_sales_tax is True
    assert MAINE.tier == 1
    assert MAINE.self_seeded is True  # signals the loader to skip file lookup


def test_maine_satisfies_protocol() -> None:
    assert isinstance(MAINE, StateModule)
    assert isinstance(Maine(), StateModule)


def test_maine_is_registered() -> None:
    assert get_state_module("ME") is MAINE


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in Me. Rev. Stat. tit. 36 section 1760
        ("groceries", False),  # 'grocery staples' exempt per section 1760(3)
        ("prescription_drugs", False),  # section 1760(5)
        ("prepared_food", True),  # section 1811(1) -- statutory 8%, engine applies 5.5%
        (
            "digital_goods",
            True,
        ),  # section 1752(17) TPP includes products transferred electronically
        ("general", True),  # section 1811(1)
    ],
)
def test_maine_taxability(category: str, expected_taxable: bool) -> None:
    rule = MAINE.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_maine_unknown_category_returns_none() -> None:
    assert MAINE.taxability_for("lobster-trap", dt.date(2026, 5, 3)) is None


def test_maine_parse_rates_yields_5_5_pct() -> None:
    """Maine's statewide rate is 5.5% effective 2013-10-01 (PL 2013, c. 368, Pt. M)."""
    rows = list(MAINE.parse_rates(None, "v0.12-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Maine"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("5.500")
    assert row.effective_from == dt.date(2013, 10, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None  # state-level rate has no parent


def test_maine_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(MAINE.parse_rates(None, "test"))
    rows_with_path = list(MAINE.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_maine_parse_boundaries_returns_empty() -> None:
    """Maine has NO general local sales tax -- no sub-state boundaries to ship."""
    rows = list(MAINE.parse_boundaries(None, "v0.12-statewide"))
    assert rows == []


def test_maine_special_cases_empty() -> None:
    """Category-specific higher rates (8% prepared food, 9% lodging, 10% auto rental,
    14% cannabis) are documented but not yet exposed via SpecialCase (engine support
    pending category-aware-rate extension).
    """
    cases = list(MAINE.special_cases())
    assert cases == []


def test_maine_holidays_for_all_years_returns_empty() -> None:
    """Regression test: Maine has NO sales-tax holidays in any year.

    Confirmed against Maine Revenue Services 2026-05-03. Several bills to
    establish a back-to-school holiday have been introduced but none have
    been enacted. This test exists specifically to catch any future
    regression where a contributor accidentally adds a holiday window
    (e.g. by copy-pasting from a state that does have one).
    """
    for year in range(2024, 2031):
        holidays = list(MAINE.holidays_for(year))
        assert holidays == [], f"Maine should have no holidays in {year}"


def test_maine_groceries_notes_cite_section_1760_3() -> None:
    """Grocery exemption must cite the controlling statute and the
    'grocery staples' definition's notable exclusions (alcohol, candy,
    soft drinks, prepared food) so a reader does not assume ALL food is
    exempt.
    """
    rule = MAINE.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "1760(3)" in notes
    assert "1752(3-B)" in notes
    notes_lower = notes.lower()
    # Must call out the exclusions a layperson might miss.
    assert "candy" in notes_lower
    assert "prepared food" in notes_lower


def test_maine_prescription_drugs_cite_section_1760_5() -> None:
    """Prescription-drug exemption must cite the controlling statute."""
    rule = MAINE.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert "1760(5)" in (rule.notes or "")


def test_maine_prepared_food_notes_call_out_8pct_undercollection() -> None:
    """Prepared-food rule must explicitly document that the statutory rate
    is 8% but the engine applies 5.5%, under-collecting by 2.5 points,
    so an integrator does not silently miscompute meal taxes without
    noticing the gap.
    """
    rule = MAINE.taxability_for("prepared_food", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "8%" in notes
    notes_lower = notes.lower()
    assert "under-collect" in notes_lower or "undercollect" in notes_lower
    assert "1811(1)" in notes


def test_maine_general_notes_call_out_no_local_tax() -> None:
    """The general rule must call out Maine's no-local-tax status -- this
    is a load-bearing distinction that integrators rely on (mirrors
    IN/KY/MI/RI). Otherwise a caller could assume Maine has a typical
    state+county+city stack and look for sub-state authorities that don't
    exist.
    """
    rule = MAINE.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    notes_lower = (rule.notes or "").lower()
    assert "no general local" in notes_lower or "no local" in notes_lower
    assert "5.5%" in (rule.notes or "")


def test_maine_digital_goods_cite_section_1752_17() -> None:
    """Digital-goods rule must cite Me. Rev. Stat. tit. 36 section 1752(17)
    (the TPP definition that expressly includes products transferred
    electronically). The 2026-01-01 LD 210 expansion to subscription
    services is a follow-up reference point that should also be noted.
    """
    rule = MAINE.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "1752(17)" in notes
    notes_lower = notes.lower()
    assert "transferred electronically" in notes_lower
    # 2026 expansion to subscription-based digital services
    assert "ld 210" in notes_lower or "subscription" in notes_lower
