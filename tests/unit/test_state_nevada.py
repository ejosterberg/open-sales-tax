# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Nevada state module (Phase 7 -- tier-2 to tier-1 promotion).

Nevada is an SST member with a 6.85% statewide minimum combined rate
(2.00% NRS Chapter 372 + 2.60% NRS Chapter 374 LSST + 2.25% NRS
Chapter 377 City-County Relief Tax). Per-county add-on rates
(Clark ~1.525%, Washoe ~1.415%, etc.) are NOT modeled in v1.

The Nevada National Guard Sales Tax Holiday (NRS 372.7282) is a
buyer-eligibility holiday rather than a category-based holiday, and
is intentionally NOT yielded from ``Nevada.holidays_for`` because
the engine does not currently model buyer eligibility. Encoding it
as a date-only / category-wide HolidayWindow would systematically
under-collect tax for every Nevada general consumer during the
3-day window. See the module docstring for the full deferral
rationale and the "buyer-eligibility holiday gap" tests below.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.nevada import (
    NEVADA,
    NEVADA_STATEWIDE_MINIMUM_RATE_PCT,
    Nevada,
)
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_nevada_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 32, tier 1."""
    assert NEVADA.state_abbrev == "NV"
    assert NEVADA.state_name == "Nevada"
    assert NEVADA.state_fips == "32"
    assert NEVADA.sst_member is True
    assert NEVADA.has_sales_tax is True
    assert NEVADA.tier == 1


def test_nevada_inherits_sst_base() -> None:
    """Nevada subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(NEVADA, SstStateModule)
    assert isinstance(Nevada(), SstStateModule)


def test_nevada_satisfies_protocol() -> None:
    """Nevada structurally implements the StateModule Protocol."""
    assert isinstance(NEVADA, StateModule)
    assert isinstance(Nevada(), StateModule)


def test_nevada_is_registered() -> None:
    """The registry returns the Nevada instance under 'NV' (case-insensitive)."""
    assert get_state_module("NV") is NEVADA
    assert get_state_module("nv") is NEVADA


def test_nevada_not_in_tier2_anymore() -> None:
    """Regression: Nevada was promoted out of _tier2.py and must not
    appear in TIER_2_CLASSES or TIER_2_STATES. A double-registration
    would silently overwrite the tier-1 instance with a tier-2 one.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "NV" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "NV" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in NRS Chapter 372
        ("groceries", False),  # NRS section 372.284
        ("prescription_drugs", False),  # NRS section 372.283
        ("prepared_food", True),  # excluded from NRS 372.284 grocery exemption
        ("digital_goods", False),  # outside TPP per NRS 372.085 (intangible)
        ("general", True),  # NRS section 372.105 imposition
    ],
)
def test_nevada_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying an NRS citation.
    """
    rule = NEVADA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "NRS" in (rule.notes or "")


def test_nevada_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert NEVADA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_nevada_groceries_cite_section_284() -> None:
    """Grocery exemption is in NRS section 372.284 (food for human consumption)."""
    rule = NEVADA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "372.284" in (rule.notes or "")


def test_nevada_prescription_drugs_cite_section_283() -> None:
    """Prescription medicines are exempt under NRS section 372.283."""
    rule = NEVADA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "372.283" in (rule.notes or "")


def test_nevada_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites NRS section 372.105 (the imposition statute) and
    documents the 6.85% rate composition (2.00% + 2.60% + 2.25%).
    """
    rule = NEVADA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "372.105" in notes
    # Rate composition must be documented in the general rule's notes.
    assert "6.85" in notes
    assert "2.00" in notes  # State Sales Tax portion
    assert "2.60" in notes  # Local School Support Tax portion
    assert "2.25" in notes  # City-County Relief Tax portion


def test_nevada_digital_goods_is_not_taxable_with_tangibility_rationale() -> None:
    """Digital goods are NOT taxable in NV: NRS 372.085 limits TPP to tangible
    property, and electronically-delivered goods do not satisfy the
    tangibility requirement per the Nevada Department of Taxation's
    longstanding position. Notable contrast with peer SST states (Iowa,
    Indiana) -- the rule's notes must call out the contrast.
    """
    rule = NEVADA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "372.085" in notes
    notes_lower = notes.lower()
    assert "tangible" in notes_lower


def test_nevada_clothing_rule_documents_buyer_eligibility_holiday_caveat() -> None:
    """Clothing rule must reference the National Guard holiday (NRS 372.7282)
    and explain that it is NOT modeled in v1 because of the buyer-
    eligibility gap. Without this note, a future maintainer could
    mistakenly believe NV has no holiday law.
    """
    rule = NEVADA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "372.7282" in notes
    notes_lower = notes.lower()
    assert "national guard" in notes_lower
    assert "buyer-eligibility" in notes_lower or "buyer eligibility" in notes_lower


# ---------------------------------------------------------------------------
# Sales-tax holidays -- the buyer-eligibility holiday is INTENTIONALLY
# not yielded by holidays_for() in v1. See module docstring.
# ---------------------------------------------------------------------------
def test_nevada_holidays_for_all_years_returns_empty() -> None:
    """Nevada's only statutory sales-tax holiday is the National Guard
    holiday (NRS 372.7282), which is buyer-eligibility-restricted and
    NOT modeled in v1 to avoid systematic under-collection on every
    non-eligible Nevada buyer during the 3-day window. Until the engine
    grows a buyer-eligibility / exemption-certificate model,
    holidays_for() must return an empty iterator for every year.
    """
    for year in range(2024, 2031):
        holidays = list(NEVADA.holidays_for(year))
        assert holidays == [], (
            f"Nevada must NOT yield the National Guard holiday from "
            f"holidays_for() in v1 (buyer-eligibility gap). Year: {year}."
        )


def test_nevada_module_docstring_documents_buyer_eligibility_deferral() -> None:
    """The buyer-eligibility deferral rationale MUST appear in the module
    docstring -- it is the most important piece of context for an
    integrator or future maintainer who wonders why the National Guard
    holiday is not encoded as a HolidayWindow. Removing or weakening
    this language is a documentation regression.
    """
    import opensalestax.states.nevada as nevada_module

    docstring = nevada_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The statute identifier must appear.
    assert "372.7282" in docstring
    # The holiday must be named.
    assert "national guard" in docstring_lower
    # The deferral mechanism must be explained.
    assert "buyer-eligibility" in docstring_lower or "buyer eligibility" in docstring_lower
    assert "not modeled" in docstring_lower or "not yield" in docstring_lower


def test_nevada_module_docstring_documents_deferred_locals() -> None:
    """The county-add-on deferral (Clark ~1.525%, Washoe ~1.415%) MUST be
    documented in the module docstring. Without the under-collection
    warning, an integrator using NV addresses in Las Vegas or Reno would
    silently under-collect by ~1.5% with no indication anything is wrong.
    """
    import opensalestax.states.nevada as nevada_module

    docstring = nevada_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The statewide minimum rate must be called out.
    assert "6.85" in docstring
    # Per-county add-ons must be documented.
    assert "clark" in docstring_lower
    assert "washoe" in docstring_lower
    # The under-collection failure mode must be flagged.
    assert "under-collect" in docstring_lower or "under collect" in docstring_lower


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine in v1)
# ---------------------------------------------------------------------------
def test_nevada_special_cases_empty() -> None:
    """v1 ships no SpecialCase rows for Nevada. The buyer-eligibility
    holiday and county-add-on caveats are documented in the module
    docstring and in references.md rather than encoded as engine-
    consumed special cases (the SpecialCase API is reserved for
    Phase 5+).
    """
    cases = list(NEVADA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Rate composition: documentary constant
# ---------------------------------------------------------------------------
def test_nevada_statewide_minimum_rate_constant_is_6_85_pct() -> None:
    """Documentary constant: Nevada's statewide minimum combined rate is
    6.85% (sum of 2.00% NRS 372 State + 2.60% NRS 374 LSST + 2.25% NRS
    377 City-County Relief Tax). The actual rate that flows into the
    engine comes from the SST quarterly file via the inherited parser;
    this constant gives grep-ability and a stable test fixture.
    """
    assert Decimal("6.850") == NEVADA_STATEWIDE_MINIMUM_RATE_PCT
    # Verify the composition adds up exactly (catches any future typo
    # in the documentary constant).
    composed = Decimal("2.000") + Decimal("2.600") + Decimal("2.250")
    assert composed == NEVADA_STATEWIDE_MINIMUM_RATE_PCT
