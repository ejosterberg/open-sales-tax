# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Oklahoma state module (v0.10 tier-2 -> tier-1 promotion)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.oklahoma import OKLAHOMA, OKLAHOMA_GENERAL_RATE_PCT, Oklahoma
from opensalestax.states.protocol import HolidayWindow, StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_oklahoma_metadata() -> None:
    assert OKLAHOMA.state_abbrev == "OK"
    assert OKLAHOMA.state_name == "Oklahoma"
    assert OKLAHOMA.state_fips == "40"
    assert OKLAHOMA.sst_member is True  # OK is a Streamlined Sales Tax member
    assert OKLAHOMA.has_sales_tax is True
    assert OKLAHOMA.tier == 1


def test_oklahoma_inherits_sst_base() -> None:
    """Oklahoma subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(OKLAHOMA, SstStateModule)
    assert isinstance(Oklahoma(), SstStateModule)


def test_oklahoma_satisfies_protocol() -> None:
    assert isinstance(OKLAHOMA, StateModule)
    assert isinstance(Oklahoma(), StateModule)


def test_oklahoma_is_registered() -> None:
    assert get_state_module("OK") is OKLAHOMA
    assert get_state_module("ok") is OKLAHOMA  # case-insensitive lookup


def test_oklahoma_is_not_in_tier2_anymore() -> None:
    """OK was promoted out of _tier2.py; it must no longer be registered as tier 2."""
    from opensalestax.states._tier2 import TIER_2_STATES

    abbrevs = {s.state_abbrev for s in TIER_2_STATES}
    assert "OK" not in abbrevs


def test_oklahoma_general_rate_constant() -> None:
    """Documentary constant matches the statutory 4.5% state rate per 68 O.S. 1354."""
    assert Decimal("4.500") == OKLAHOMA_GENERAL_RATE_PCT


# ---------------------------------------------------------------------------
# Taxability matrix -- statutory citations are mandatory in every notes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; 3-day August holiday window
        ("groceries", True),  # taxable but state portion 0% via rate_modifier (HB 1955)
        ("prescription_drugs", False),  # exempt per 68 O.S. 1357
        ("prepared_food", True),  # general 4.5%; excluded from grocery exemption
        ("digital_goods", False),  # NOT taxable (peer-state difference; OAC 710:65-19-156)
        ("general", True),  # baseline TPP at 4.5% per 68 O.S. 1354
    ],
)
def test_oklahoma_taxability(category: str, expected_taxable: bool) -> None:
    rule = OKLAHOMA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes = rule.notes or ""
    assert "68 O.S." in notes or "OAC 710:65" in notes


def test_oklahoma_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert OKLAHOMA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_oklahoma_groceries_use_rate_modifier_zero() -> None:
    """HB 1955 (2024) eliminated state-portion grocery tax effective 2024-08-29.

    Mirrors the AR Grocery Tax Relief Act + KS phase-down patterns:
    is_taxable=True with rate_modifier=Decimal("0.000") signals to a
    future engine that the special state-portion rate is 0.000% while
    local rates still apply at the normal local rate.
    """
    rule = OKLAHOMA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("0.000")
    notes = rule.notes or ""
    # Cite the bill and effective date.
    assert "HB 1955" in notes or "House Bill 1955" in notes
    assert "August 29, 2024" in notes
    assert "1357" in notes  # the amended exemptions section
    # Documents the broader-than-SST definition (includes candy, soft drinks, bottled water).
    assert "bottled water" in notes.lower()
    assert "candy" in notes.lower()
    assert "soft drinks" in notes.lower()
    # Local-side caveat must be explicit.
    assert "local" in notes.lower()


def test_oklahoma_prescription_drugs_cite_1357() -> None:
    """Prescription-drug exemption is in 68 O.S. section 1357."""
    rule = OKLAHOMA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "1357" in notes
    # Related medical-device exemption at 1357.6 should also be cited.
    assert "1357.6" in notes


def test_oklahoma_digital_goods_not_taxable() -> None:
    """OK does NOT tax electronically-delivered digital products.

    Notable peer-state difference from IA / IN / AR / KS, which
    DO tax specified digital products. Basis: OAC 710:65-19-156
    and OK Tax Commission letter rulings; 68 O.S. section 1354
    only reaches tangible personal property, and OK has not
    adopted the SST 'specified digital products' definitions.
    """
    rule = OKLAHOMA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    # Cite the OK Administrative Code section that establishes the exemption.
    assert "710:65-19-156" in notes
    assert "1354" in notes  # the imposition statute that doesn't reach digital goods
    # Document that this is a peer-state difference.
    notes_lower = notes.lower()
    assert "peer-state" in notes_lower or "unlike" in notes_lower


def test_oklahoma_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites 68 O.S. section 1354 (the imposition statute)."""
    rule = OKLAHOMA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "1354" in (rule.notes or "")


def test_oklahoma_clothing_cites_holiday_statute() -> None:
    """Clothing is taxable year-round; the holiday section 1357.10 is referenced."""
    rule = OKLAHOMA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "1357.10" in notes
    # The parallel county/municipal-side prohibition is also cited.
    assert "1377" in notes


def test_oklahoma_prepared_food_excluded_from_grocery_exemption() -> None:
    """Prepared food is taxable; the grocery exemption explicitly excludes it."""
    rule = OKLAHOMA.taxability_for("prepared_food", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "1354" in notes  # imposition
    assert "1357" in notes  # the exemption from which prepared food is excluded
    assert "HB 1955" in notes or "1955" in notes


# ---------------------------------------------------------------------------
# Jurisdiction-type code mapping
# ---------------------------------------------------------------------------
def test_oklahoma_jurisdiction_type_mapping_matches_canonical_sst() -> None:
    """OK uses the same SST type codes as MN and WI (assumption documented)."""
    types = OKLAHOMA.jurisdiction_types
    assert types["45"] == "state"
    assert types["00"] == "county"
    assert types["01"] == "city"
    assert types["63"] == "district"


# ---------------------------------------------------------------------------
# Inherited SST parser smoke check
# ---------------------------------------------------------------------------
def test_oklahoma_parse_boundaries_signature() -> None:
    """parse_boundaries returns a callable; we don't ship an OK fixture in this PR."""
    method = OKLAHOMA.parse_boundaries
    assert callable(method)


# ---------------------------------------------------------------------------
# Special cases
# ---------------------------------------------------------------------------
def test_oklahoma_special_cases_empty() -> None:
    cases = list(OKLAHOMA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Holiday tests -- OK has ONE annual back-to-school holiday (clothing only)
# ---------------------------------------------------------------------------
def test_oklahoma_holiday_count_2026() -> None:
    """OK's 2026 holiday is a single HolidayWindow (clothing/footwear only)."""
    holidays = list(OKLAHOMA.holidays_for(2026))
    assert len(holidays) == 1
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_oklahoma_holiday_dates_2026() -> None:
    """2026 holiday: first Friday of August (Aug 7) through Sunday (Aug 9)."""
    holidays = list(OKLAHOMA.holidays_for(2026))
    h = holidays[0]
    assert h.starts_on == dt.date(2026, 8, 7)
    assert h.ends_on == dt.date(2026, 8, 9)
    # Sanity: starts on a Friday, ends on a Sunday.
    assert h.starts_on.weekday() == 4  # Friday
    assert h.ends_on.weekday() == 6  # Sunday
    # And it really is the FIRST Friday in August: previous Friday
    # would have been in July.
    prev_friday = h.starts_on - dt.timedelta(days=7)
    assert prev_friday.month == 7


def test_oklahoma_holiday_clothing_cap_is_100() -> None:
    """Clothing/footwear scope: $100 per-item cap per 68 O.S. 1357.10."""
    holidays = list(OKLAHOMA.holidays_for(2026))
    h = holidays[0]
    assert h.applicable_categories == ("clothing",)
    assert h.max_amount_per_item == Decimal("100.00")
    assert h.notes is not None
    assert "1357.10" in h.notes
    # The county/municipal-side parallel statute must be cited too.
    assert "1377" in h.notes


def test_oklahoma_holiday_excludes_school_supplies() -> None:
    """Unlike AR/TX/etc, OK's holiday covers ONLY clothing/footwear.

    Documentation/regression test: the holiday list must NOT include
    school_supplies, electronic_devices, or similar scopes that other
    states cover. This catches an over-zealous future maintainer who
    might copy AR's multi-scope pattern into OK.
    """
    holidays = list(OKLAHOMA.holidays_for(2026))
    cats = {h.applicable_categories for h in holidays}
    assert cats == {("clothing",)}
    # The note should explicitly document the narrow scope.
    h = holidays[0]
    notes = h.notes or ""
    notes_lower = notes.lower()
    assert "school supplies" in notes_lower
    assert "only clothing and footwear" in notes_lower or "only" in notes_lower


def test_oklahoma_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design)."""
    assert list(OKLAHOMA.holidays_for(2025)) == []
    assert list(OKLAHOMA.holidays_for(2027)) == []
    assert list(OKLAHOMA.holidays_for(2099)) == []
