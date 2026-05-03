# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Utah state module (Phase 7 -- tier-2 to tier-1 promotion).

Utah is an SST member with a 4.85% statewide combined sales tax
rate per Utah Code section 59-12-103, composed of 4.70% state +
0.10% statewide-uniform local-option + 0.05% mass transit basic.
Groceries are taxed at a REDUCED 1.75% state portion per section
59-12-103(2)(a)(ii) (encoded via ``rate_modifier``). Utah has NO
state sales-tax holiday in any year. Sales by Navajo-enrolled-
member businesses on the Navajo Nation portion of San Juan
County are subject only to the Navajo Nation gross receipts tax
and are NOT modeled in v1 (deferred sub-state regime).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule
from opensalestax.states.utah import (
    UTAH,
    UTAH_GENERAL_RATE_PCT,
    UTAH_GROCERY_STATE_RATE_PCT,
    Utah,
)


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_utah_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 49, tier 1."""
    assert UTAH.state_abbrev == "UT"
    assert UTAH.state_name == "Utah"
    assert UTAH.state_fips == "49"
    assert UTAH.sst_member is True  # UT is a Streamlined Sales Tax member
    assert UTAH.has_sales_tax is True
    assert UTAH.tier == 1


def test_utah_inherits_sst_base() -> None:
    """Utah subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(UTAH, SstStateModule)
    assert isinstance(Utah(), SstStateModule)


def test_utah_satisfies_protocol() -> None:
    assert isinstance(UTAH, StateModule)
    assert isinstance(Utah(), StateModule)


def test_utah_is_registered() -> None:
    assert get_state_module("UT") is UTAH
    assert get_state_module("ut") is UTAH  # case-insensitive lookup
    assert get_state_module("Ut") is UTAH


def test_utah_is_not_in_tier2_anymore() -> None:
    """UT was promoted out of _tier2.py; it must no longer be registered as tier 2.

    A double-registration would silently re-overwrite the tier-1
    instance with the tier-2 default at import time.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    abbrevs = {s.state_abbrev for s in TIER_2_STATES}
    assert "UT" not in abbrevs
    assert "UT" not in {cls().state_abbrev for cls in TIER_2_CLASSES}


# ---------------------------------------------------------------------------
# Documentary rate constants
# ---------------------------------------------------------------------------
def test_utah_general_rate_constant() -> None:
    """Documentary constant matches the 4.85% statewide combined rate.

    Per Utah Code section 59-12-103: 4.70% state +
    0.10% statewide-uniform local-option (section 59-12-204) +
    0.05% mass transit basic = 4.85%.
    """
    assert Decimal("4.850") == UTAH_GENERAL_RATE_PCT
    # Composition sanity: 4.70 + 0.10 + 0.05 must equal 4.85.
    assert (Decimal("4.70") + Decimal("0.10") + Decimal("0.05")) == UTAH_GENERAL_RATE_PCT


def test_utah_grocery_state_rate_constant() -> None:
    """Documentary constant for the reduced 1.75% state-portion grocery rate.

    Per Utah Code section 59-12-103(2)(a)(ii). This is the state-
    portion only; local rates apply at full local rate.
    """
    assert Decimal("1.75") == UTAH_GROCERY_STATE_RATE_PCT


# ---------------------------------------------------------------------------
# Module docstring -- mandatory documentation of key caveats
# ---------------------------------------------------------------------------
def test_utah_module_docstring_documents_rate_composition() -> None:
    """The module docstring must document the 4.85% rate composition.

    Per the per-state research brief: the Utah module docstring
    must spell out the three statutory components (4.70% state +
    0.10% statewide-uniform local + 0.05% mass transit basic)
    so future maintainers can audit each component independently.
    """
    import opensalestax.states.utah as utah_mod

    doc = utah_mod.__doc__ or ""
    assert "4.70%" in doc
    assert "0.10%" in doc
    assert "0.05%" in doc
    assert "4.85%" in doc
    # The composition statute must be cited.
    assert "59-12-103" in doc


def test_utah_module_docstring_documents_grocery_rate_modifier() -> None:
    """The module docstring must document the 1.75% reduced grocery rate.

    Per the per-state research brief: the Utah module docstring
    must spell out the reduced state grocery rate (1.75%) and the
    rate_modifier encoding so future maintainers don't accidentally
    apply the full 4.85% to groceries.
    """
    import opensalestax.states.utah as utah_mod

    doc = utah_mod.__doc__ or ""
    assert "1.75%" in doc
    assert "rate_modifier" in doc
    # The food-and-food-ingredients reduced-rate statute must be cited.
    assert "59-12-103(2)(a)(ii)" in doc


def test_utah_module_docstring_documents_navajo_nation_caveat() -> None:
    """The module docstring must document the Navajo Nation deferred regime.

    Per the per-state research brief: the Utah module docstring
    must explicitly document that the Navajo Nation gross receipts
    tax applies on the reservation portion of San Juan County and
    is NOT modeled by this engine in v1. This protects future
    maintainers and downstream users from silently mishandling
    sales by Navajo-enrolled-member businesses.
    """
    import opensalestax.states.utah as utah_mod

    doc = utah_mod.__doc__ or ""
    assert "Navajo Nation" in doc
    # The deferred-regime nature must be explicit.
    doc_lower = doc.lower()
    assert "deferred" in doc_lower or "not modeled" in doc_lower or "do not model" in doc_lower
    # Cite the Navajo Nation statute.
    assert "Navajo Nation Code" in doc or "Navajo Tax Commission" in doc


# ---------------------------------------------------------------------------
# Taxability matrix -- statutory citations are mandatory in every notes
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; UT has NO holiday
        ("groceries", True),  # taxable but state portion 1.75% via rate_modifier
        ("prescription_drugs", False),  # exempt per Utah Code 59-12-104(11)
        ("prepared_food", True),  # general 4.85%; excluded from grocery exemption
        ("digital_goods", True),  # taxable per Utah Code 59-12-103 + 59-12-102 (SB 65 of 2008)
        ("general", True),  # baseline TPP at 4.85% per Utah Code 59-12-103
    ],
)
def test_utah_taxability(category: str, expected_taxable: bool) -> None:
    """Every category yields a rule with a statutory citation."""
    rule = UTAH.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "Utah Code" in (rule.notes or "")


def test_utah_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert UTAH.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_utah_groceries_use_rate_modifier_1_75() -> None:
    """UT groceries: is_taxable=True with rate_modifier=Decimal('1.75').

    Per Utah Code section 59-12-103(2)(a)(ii) the state portion of
    the grocery tax is 1.75% (vs the general 4.85% statewide
    combined rate). Mirrors the Illinois (1.0%), Missouri (1.225%),
    and Virginia (1.0%) reduced-state-grocery-rate patterns.
    """
    rule = UTAH.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("1.75")
    notes = rule.notes or ""
    # Cite the controlling statute.
    assert "59-12-103(2)(a)(ii)" in notes
    # Local-side caveat must be explicit (locals tax groceries at full rate).
    assert "local" in notes.lower()
    # Document the Constitutional Amendment A (2024) struck-from-ballot history.
    assert "Amendment A" in notes
    assert "2024" in notes


def test_utah_prescription_drugs_cite_104_11() -> None:
    """Prescription-drug exemption is in Utah Code section 59-12-104(11)."""
    rule = UTAH.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "59-12-104(11)" in notes


def test_utah_digital_goods_taxable_per_sb_65() -> None:
    """UT taxes 'products transferred electronically' per SB 65 of 2008.

    Senate Bill 65 of the 2008 General Session amended Utah Code
    section 59-12-102 to expressly add 'products transferred
    electronically' to the sales-tax base; the imposition statute
    at section 59-12-103 then applies at 4.85%.
    """
    rule = UTAH.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "59-12-102" in notes
    # Cite SB 65 of 2008.
    assert "SB 65" in notes or "Senate Bill 65" in notes
    assert "2008" in notes


def test_utah_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites Utah Code section 59-12-103 + the rate composition."""
    rule = UTAH.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "59-12-103" in notes
    # The general rule's notes also document the Navajo Nation caveat
    # for the operator -- this is the calculation-time pointer for
    # downstream users who are building exemption-certificate flows.
    assert "Navajo Nation" in notes


def test_utah_clothing_documents_no_holiday() -> None:
    """Clothing rule documents that UT has NO state sales-tax holiday."""
    rule = UTAH.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    notes_lower = notes.lower()
    # Document the no-holiday status (no 2-day weekend exemption like IA / OK).
    assert "no state sales-tax holiday" in notes_lower or "no sales-tax holiday" in notes_lower


def test_utah_prepared_food_excluded_from_grocery_reduced_rate() -> None:
    """Prepared food tax at full 4.85%; excluded from the grocery reduced rate."""
    rule = UTAH.taxability_for("prepared_food", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # Cite both the imposition statute and the reduced-rate statute it's excluded from.
    assert "59-12-103" in notes
    assert "59-12-103(2)(a)(ii)" in notes


# ---------------------------------------------------------------------------
# Jurisdiction-type code mapping
# ---------------------------------------------------------------------------
def test_utah_jurisdiction_type_mapping_matches_canonical_sst() -> None:
    """UT uses the same SST type codes as MN and WI (assumption documented)."""
    types = UTAH.jurisdiction_types
    assert types["45"] == "state"
    assert types["00"] == "county"
    assert types["01"] == "city"
    assert types["63"] == "district"


# ---------------------------------------------------------------------------
# Inherited SST parser smoke check
# ---------------------------------------------------------------------------
def test_utah_parse_boundaries_signature() -> None:
    """parse_boundaries returns a callable; we don't ship a UT fixture in this PR.

    The inherited SstStateModule parser handles the actual SST file.
    This test confirms the method exists and is callable.
    """
    method = UTAH.parse_boundaries
    assert callable(method)


def test_utah_parse_rates_signature() -> None:
    """parse_rates returns a callable; rates flow from the SST quarterly file."""
    method = UTAH.parse_rates
    assert callable(method)


# ---------------------------------------------------------------------------
# Special cases
# ---------------------------------------------------------------------------
def test_utah_special_cases_empty() -> None:
    """No SpecialCase entries; Navajo Nation regime documented in docstring only."""
    cases = list(UTAH.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Sales-tax holidays -- Utah has NO state sales-tax holiday in any year
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("year", [2024, 2025, 2026, 2027, 2028, 2099])
def test_utah_holidays_always_empty(year: int) -> None:
    """Utah has no state sales-tax holiday in any year (verified 2026-05-03).

    Several legislative proposals (most recently HB 296 of 2017)
    have failed to enact a back-to-school holiday. The method
    returns an empty iterator for every year -- if a future
    legislature passes one, the method must be updated explicitly
    per year (no extrapolation).
    """
    holidays = list(UTAH.holidays_for(year))
    assert holidays == []
