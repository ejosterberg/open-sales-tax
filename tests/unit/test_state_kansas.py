# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Kansas state module (tier-2 -> tier-1 promotion)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.kansas import KANSAS, KANSAS_GENERAL_RATE_PCT, Kansas
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_kansas_metadata() -> None:
    assert KANSAS.state_abbrev == "KS"
    assert KANSAS.state_name == "Kansas"
    assert KANSAS.sst_member is True  # KS is a Streamlined Sales Tax member
    assert KANSAS.has_sales_tax is True
    assert KANSAS.tier == 1
    assert KANSAS.state_fips == "20"


def test_kansas_inherits_sst_base() -> None:
    """Kansas subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(KANSAS, SstStateModule)
    assert isinstance(Kansas(), SstStateModule)


def test_kansas_satisfies_protocol() -> None:
    assert isinstance(KANSAS, StateModule)
    assert isinstance(Kansas(), StateModule)


def test_kansas_is_registered() -> None:
    assert get_state_module("KS") is KANSAS
    assert get_state_module("ks") is KANSAS  # case-insensitive


def test_kansas_is_not_in_tier2_anymore() -> None:
    """KS was promoted out of _tier2.py; it must no longer be registered as tier 2."""
    from opensalestax.states._tier2 import TIER_2_STATES

    abbrevs = {s.state_abbrev for s in TIER_2_STATES}
    assert "KS" not in abbrevs


def test_kansas_general_rate_constant() -> None:
    """Documentary constant matches the statutory 6.5% state rate."""
    assert Decimal("6.500") == KANSAS_GENERAL_RATE_PCT


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; NO Kansas back-to-school holiday
        ("groceries", True),  # taxable but state portion 0% via rate_modifier (K.S.A. 79-3603(p))
        ("prescription_drugs", False),  # exempt per K.S.A. 79-3606(p)
        ("prepared_food", True),  # general 6.5%; excluded from grocery phase-down
        ("digital_goods", True),  # taxable per K.S.A. 79-3603(d), 2021 S.B. 50
        ("general", True),  # baseline TPP at 6.5% per K.S.A. 79-3603(a)
    ],
)
def test_kansas_taxability(category: str, expected_taxable: bool) -> None:
    rule = KANSAS.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "K.S.A." in (rule.notes or "")


def test_kansas_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert KANSAS.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_kansas_clothing_no_holiday_in_notes() -> None:
    """Clothing rule notes the absence of a back-to-school holiday."""
    rule = KANSAS.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "79-3603(a)" in (rule.notes or "")
    notes_lower = (rule.notes or "").lower()
    # Documents that KS has NEVER enacted a sales-tax holiday.
    assert "no" in notes_lower
    assert "holiday" in notes_lower


def test_kansas_groceries_use_rate_modifier_zero() -> None:
    """Grocery phase-down: state portion 0% via rate_modifier; locals still apply.

    Mirrors the AR Grocery Tax Relief Act pattern: is_taxable=True
    with rate_modifier=Decimal("0.000") signals to a future engine
    that the special state-portion rate is 0.000% while local rates
    still apply at the normal local rate.
    """
    rule = KANSAS.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("0.000")
    notes = rule.notes or ""
    assert "79-3603(p)" in notes  # the phase-down statute
    assert "2106" in notes  # House Bill 2106 (2022)
    # Document the phase-down history.
    assert "6.5%" in notes
    assert "4.0%" in notes
    assert "2.0%" in notes
    assert "0.000%" in notes
    assert "2025" in notes  # final year of phase-down


def test_kansas_prescription_drugs_cite_subsection_p() -> None:
    """Prescription-drug exemption is in K.S.A. 79-3606(p)."""
    rule = KANSAS.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "79-3606(p)" in (rule.notes or "")


def test_kansas_digital_goods_notes_sb50() -> None:
    """KS taxes specified digital products at 6.5% per 2021 S.B. 50 (K.S.A. 79-3603(d))."""
    rule = KANSAS.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "79-3603(d)" in notes
    assert "S.B. 50" in notes  # 2021 Senate Bill 50


def test_kansas_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites K.S.A. section 79-3603(a) (the imposition statute)."""
    rule = KANSAS.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "79-3603(a)" in (rule.notes or "")


def test_kansas_jurisdiction_types_include_district() -> None:
    """KS uses the canonical SST jurisdiction-type code mapping (assumed).

    The default mapping includes ``45`` state, ``00`` county, ``01``
    city, and ``63`` district. Districts cover Community Improvement
    Districts (CIDs), Transportation Development Districts (TDDs),
    and Star Bond / redevelopment districts authorized under K.S.A.
    chapter 12.
    """
    types = Kansas().jurisdiction_types
    assert types["45"] == "state"
    assert types["00"] == "county"
    assert types["01"] == "city"
    assert types["63"] == "district"


# ---------------------------------------------------------------------------
# Inherited SST parser smoke check
# ---------------------------------------------------------------------------
def test_kansas_parse_boundaries_signature() -> None:
    """parse_boundaries returns a callable; we don't ship a KS fixture in this PR."""
    method = KANSAS.parse_boundaries
    assert callable(method)


# ---------------------------------------------------------------------------
# Sales tax holidays -- KS has NONE (regression test exercises 2024-2030)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("year", [2024, 2025, 2026, 2027, 2028, 2029, 2030])
def test_kansas_has_no_holidays(year: int) -> None:
    """KS has never enacted a recurring sales-tax holiday.

    Multiple legislative proposals (most recently 2024 H.B. 2680)
    have been introduced but none has passed. This regression
    exercises a window of years to ensure the empty-iterator
    default from :class:`SstStateModule.holidays_for` is never
    accidentally overridden with a future-year extrapolation.
    """
    assert list(KANSAS.holidays_for(year)) == []


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine)
# ---------------------------------------------------------------------------
def test_kansas_special_cases_empty() -> None:
    cases = list(KANSAS.special_cases())
    assert cases == []
