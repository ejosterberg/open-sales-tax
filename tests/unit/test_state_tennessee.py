# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Tennessee state module (v0.11 tier-2 -> tier-1 promotion).

Tennessee is the only SST **associate** member -- distinct from
the 23 SST full members. The promotion adds a TN-specific
taxability matrix (notably the 4.0% reduced grocery rate per
Tenn. Code Ann. section 67-6-228) and the annual back-to-school
Sales Tax Holiday under section 67-6-393 (4 separate scopes:
clothing, school supplies, school art supplies, computers).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import HolidayWindow, StateModule
from opensalestax.states.tennessee import (
    TENNESSEE,
    TENNESSEE_GENERAL_RATE_PCT,
    TENNESSEE_GROCERY_RATE_PCT,
    Tennessee,
)


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_tennessee_metadata() -> None:
    assert TENNESSEE.state_abbrev == "TN"
    assert TENNESSEE.state_name == "Tennessee"
    assert TENNESSEE.state_fips == "47"
    # TN is an SST ASSOCIATE member; we still flag sst_member=True
    # because SST data formats apply uniformly to associate members.
    assert TENNESSEE.sst_member is True
    assert TENNESSEE.has_sales_tax is True
    assert TENNESSEE.tier == 1


def test_tennessee_inherits_sst_base() -> None:
    """Tennessee subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(TENNESSEE, SstStateModule)
    assert isinstance(Tennessee(), SstStateModule)


def test_tennessee_satisfies_protocol() -> None:
    assert isinstance(TENNESSEE, StateModule)
    assert isinstance(Tennessee(), StateModule)


def test_tennessee_is_registered() -> None:
    assert get_state_module("TN") is TENNESSEE
    assert get_state_module("tn") is TENNESSEE  # case-insensitive lookup


def test_tennessee_is_not_in_tier2_anymore() -> None:
    """TN was promoted out of _tier2.py; it must no longer be registered as tier 2."""
    from opensalestax.states._tier2 import TIER_2_STATES

    abbrevs = {s.state_abbrev for s in TIER_2_STATES}
    assert "TN" not in abbrevs


def test_tennessee_general_rate_constant() -> None:
    """Documentary constant matches the statutory 7.0% state rate per Tenn. Code Ann. 67-6-202."""
    assert Decimal("7.000") == TENNESSEE_GENERAL_RATE_PCT


def test_tennessee_grocery_rate_constant() -> None:
    """Documentary constant matches the reduced 4.0% state grocery rate per Tenn. Code Ann. 67-6-228."""
    assert Decimal("4.000") == TENNESSEE_GROCERY_RATE_PCT


# ---------------------------------------------------------------------------
# Taxability matrix -- statutory citations are mandatory in every notes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; back-to-school holiday window
        ("groceries", True),  # taxable but reduced 4% state rate via rate_modifier
        ("prescription_drugs", False),  # exempt per Tenn. Code Ann. 67-6-320
        ("prepared_food", True),  # general 7%; excluded from reduced grocery rate
        ("digital_goods", True),  # taxable per Tenn. Code Ann. 67-6-233 (since 2009)
        ("general", True),  # baseline TPP at 7.0% per Tenn. Code Ann. 67-6-202
    ],
)
def test_tennessee_taxability(category: str, expected_taxable: bool) -> None:
    rule = TENNESSEE.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes = rule.notes or ""
    assert "Tenn. Code Ann." in notes or "67-6-" in notes


def test_tennessee_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert TENNESSEE.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_tennessee_groceries_use_rate_modifier_four_percent() -> None:
    """Tenn. Code Ann. section 67-6-228 imposes a reduced 4.0% state grocery rate.

    Mirrors the IL/MO/AR/OK reduced-grocery-rate patterns:
    is_taxable=True with rate_modifier=Decimal("4.000") signals to a
    future engine that the special state-portion rate is 4.000% while
    local rates still apply at the normal local rate.
    """
    rule = TENNESSEE.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("4.000")
    notes = rule.notes or ""
    # Cite the statute and current rate.
    assert "67-6-228" in notes
    assert "4.0%" in notes
    # Must document the historical rate progression OR effective date.
    assert "2017" in notes
    # Local-side caveat must be explicit (locals still apply at full local rate).
    assert "local" in notes.lower()
    assert "FULL local rate" in notes or "full local rate" in notes


def test_tennessee_prescription_drugs_cite_67_6_320() -> None:
    """Prescription-drug exemption is in Tenn. Code Ann. section 67-6-320."""
    rule = TENNESSEE.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "67-6-320" in notes
    # Related medical-device exemption at 67-6-314 should also be cited.
    assert "67-6-314" in notes


def test_tennessee_digital_goods_taxable_since_2009() -> None:
    """Tenn. Code Ann. section 67-6-233 (effective Jan 1, 2009) makes specified digital products taxable.

    TN was an early-adopter state for digital product taxation,
    predating most peer SST states by several years.
    """
    rule = TENNESSEE.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # Cite the imposition statute and effective date.
    assert "67-6-233" in notes
    assert "2009" in notes
    # Must mention early-adopter context (peer-state difference).
    notes_lower = notes.lower()
    assert "early-adopter" in notes_lower or "predating" in notes_lower


def test_tennessee_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites Tenn. Code Ann. section 67-6-202 (the imposition statute)."""
    rule = TENNESSEE.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "67-6-202" in notes
    # Must cite the local-option statute and combined-rate ceiling.
    assert "67-6-702" in notes


def test_tennessee_clothing_cites_holiday_statute() -> None:
    """Clothing is taxable year-round; the holiday section 67-6-393 is referenced."""
    rule = TENNESSEE.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "67-6-393" in notes
    assert "67-6-202" in notes  # imposition


def test_tennessee_prepared_food_excluded_from_reduced_grocery_rate() -> None:
    """Prepared food is taxable at general 7%; the reduced rate explicitly excludes it."""
    rule = TENNESSEE.taxability_for("prepared_food", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "67-6-202" in notes  # imposition
    assert "67-6-228" in notes  # the reduced rate from which prepared food is excluded


# ---------------------------------------------------------------------------
# Jurisdiction-type code mapping
# ---------------------------------------------------------------------------
def test_tennessee_jurisdiction_type_mapping_matches_canonical_sst() -> None:
    """TN uses the same SST type codes as MN and WI for state/county/city.

    TN deliberately diverges on code 63: empirically every active
    code-63 row in the TN SST rate file carries a rate at the
    Tenn. Code Ann. section 67-6-702 local-tax cap (2.25%-2.75%),
    indicating they encode county-equivalent overlays already
    collapsed into the city's combined local rate. Loading them
    would double-count and report combined rates above the legal
    9.75% max (e.g. Johnson City 37601 -> 12.0% before this fix).
    The mapping therefore deliberately drops code 63 to None.
    Legitimate transit / IMPROVE Act overlays ship under code 79
    and continue to load via the inherited default mapping.
    """
    types = TENNESSEE.jurisdiction_types
    assert types["45"] == "state"
    assert types["00"] == "county"
    assert types["01"] == "city"
    assert types["63"] is None  # see _JURISDICTION_TYPE comment in tennessee.py


# ---------------------------------------------------------------------------
# Inherited SST parser smoke check
# ---------------------------------------------------------------------------
def test_tennessee_parse_boundaries_signature() -> None:
    """parse_boundaries returns a callable; we don't ship a TN fixture in this PR."""
    method = TENNESSEE.parse_boundaries
    assert callable(method)


# ---------------------------------------------------------------------------
# Special cases
# ---------------------------------------------------------------------------
def test_tennessee_special_cases_empty() -> None:
    cases = list(TENNESSEE.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Holiday tests -- TN has ONE annual back-to-school holiday with 4 scopes
# ---------------------------------------------------------------------------
def test_tennessee_holiday_count_2026() -> None:
    """TN's 2026 back-to-school holiday has 4 separate HolidayWindow scopes.

    Per Tenn. Code Ann. 67-6-393: clothing, school supplies, school
    art supplies, computers -- each with its own per-item cap.
    """
    holidays = list(TENNESSEE.holidays_for(2026))
    assert len(holidays) == 4
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_tennessee_holiday_dates_2026() -> None:
    """All 4 holiday scopes share the same 3-day window: July 24-26, 2026.

    Last full Friday-Saturday-Sunday weekend wholly within July 2026
    (the literal "last Friday in July" is July 31, but per TN DOR
    practice the holiday uses the last full weekend wholly within
    July).
    """
    holidays = list(TENNESSEE.holidays_for(2026))
    for h in holidays:
        assert h.starts_on == dt.date(2026, 7, 24)
        assert h.ends_on == dt.date(2026, 7, 26)
        # Sanity: starts on a Friday, ends on a Sunday.
        assert h.starts_on.weekday() == 4  # Friday
        assert h.ends_on.weekday() == 6  # Sunday


def test_tennessee_holiday_clothing_cap_is_100() -> None:
    """Clothing scope: $100 per-item cap per Tenn. Code Ann. 67-6-393."""
    holidays = list(TENNESSEE.holidays_for(2026))
    clothing_holidays = [h for h in holidays if h.applicable_categories == ("clothing",)]
    assert len(clothing_holidays) == 1
    h = clothing_holidays[0]
    assert h.max_amount_per_item == Decimal("100.00")
    assert h.notes is not None
    assert "67-6-393" in h.notes


def test_tennessee_holiday_school_supplies_cap_is_100() -> None:
    """School supplies scope: $100 per-item cap per Tenn. Code Ann. 67-6-393."""
    holidays = list(TENNESSEE.holidays_for(2026))
    school_holidays = [h for h in holidays if h.applicable_categories == ("school_supplies",)]
    assert len(school_holidays) == 1
    h = school_holidays[0]
    assert h.max_amount_per_item == Decimal("100.00")
    assert h.notes is not None
    assert "67-6-393" in h.notes


def test_tennessee_holiday_school_art_supplies_cap_is_100() -> None:
    """School art supplies scope: $100 per-item cap per Tenn. Code Ann. 67-6-393."""
    holidays = list(TENNESSEE.holidays_for(2026))
    art_holidays = [h for h in holidays if h.applicable_categories == ("school_art_supplies",)]
    assert len(art_holidays) == 1
    h = art_holidays[0]
    assert h.max_amount_per_item == Decimal("100.00")
    assert h.notes is not None
    assert "67-6-393" in h.notes


def test_tennessee_holiday_computers_cap_is_1500() -> None:
    """Computers scope: $1,500 per-item cap per Tenn. Code Ann. 67-6-393."""
    holidays = list(TENNESSEE.holidays_for(2026))
    computer_holidays = [h for h in holidays if h.applicable_categories == ("computers",)]
    assert len(computer_holidays) == 1
    h = computer_holidays[0]
    assert h.max_amount_per_item == Decimal("1500.00")
    assert h.notes is not None
    assert "67-6-393" in h.notes


def test_tennessee_holiday_scope_set() -> None:
    """All 4 scopes (clothing, school_supplies, school_art_supplies, computers) are present.

    Defensive regression test: if a future maintainer drops a scope
    or adds an unintended scope (e.g., copies AR's electronics scope
    or FL's emergency-supplies scope), this test will fail.
    """
    holidays = list(TENNESSEE.holidays_for(2026))
    scopes = {h.applicable_categories for h in holidays}
    assert scopes == {
        ("clothing",),
        ("school_supplies",),
        ("school_art_supplies",),
        ("computers",),
    }


def test_tennessee_holidays_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design).

    TN ran one-time grocery holidays in 2022 and 2023, but those
    were ad-hoc legislative actions. The recurring back-to-school
    holiday under 67-6-393 is the only one modeled, and only for
    explicitly-encoded years (2026 at promotion time).
    """
    assert list(TENNESSEE.holidays_for(2025)) == []
    assert list(TENNESSEE.holidays_for(2027)) == []
    assert list(TENNESSEE.holidays_for(2099)) == []


def test_tennessee_holidays_chronological_order_within_year() -> None:
    """All 4 scopes share the same date window; trivially in order."""
    holidays = list(TENNESSEE.holidays_for(2026))
    starts = [h.starts_on for h in holidays]
    assert starts == sorted(starts)
