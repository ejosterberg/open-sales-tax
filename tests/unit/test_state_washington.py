# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Washington state module (Phase 7 -- tier-2 to tier-1 promotion).

Washington is an SST full member with a 6.5% statewide retail
sales-tax rate per RCW section 82.08.020(1) (rate stable since 1983).

Three things distinguish WA from most other tier-1 SST states:

- Wide combined-rate range (~6.5% to ~10.35%) -- King County /
  Seattle reaches the highest combined retail rates in the
  country alongside Chicago / parts of CA.
- Business & Occupation (B&O) gross-receipts tax under RCW
  chapter 82.04 is SEPARATE and OUT OF SCOPE -- the B&O is a
  seller-paid tax on the seller's gross income, not a
  buyer-facing transactional sales tax.
- Broad digital-services tax base under RCW 82.04.050(6) +
  82.04.192 (added by chapter 535, Laws of 2009) -- WA taxes
  digital products, digital codes, AND digital automated
  services (cloud / SaaS / streaming).

Sales-tax holidays: NONE. WA has never enacted a recurring
sales-tax holiday. holidays_for() returns an empty iterator for
every year.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule
from opensalestax.states.washington import (
    WASHINGTON,
    WASHINGTON_HIGHEST_COMBINED_RATE_PCT,
    WASHINGTON_STATEWIDE_RATE_PCT,
    Washington,
)


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_washington_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 53, tier 1."""
    assert WASHINGTON.state_abbrev == "WA"
    assert WASHINGTON.state_name == "Washington"
    assert WASHINGTON.state_fips == "53"
    assert WASHINGTON.sst_member is True
    assert WASHINGTON.has_sales_tax is True
    assert WASHINGTON.tier == 1


def test_washington_inherits_sst_base() -> None:
    """WA subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(WASHINGTON, SstStateModule)
    assert isinstance(Washington(), SstStateModule)


def test_washington_satisfies_protocol() -> None:
    """WA structurally implements the StateModule Protocol."""
    assert isinstance(WASHINGTON, StateModule)
    assert isinstance(Washington(), StateModule)


def test_washington_is_registered() -> None:
    """The registry returns the WA instance under 'WA' (case-insensitive)."""
    assert get_state_module("WA") is WASHINGTON
    assert get_state_module("wa") is WASHINGTON


def test_washington_not_in_tier2_anymore() -> None:
    """Regression: WA was promoted out of _tier2.py and must not appear
    in TIER_2_CLASSES or TIER_2_STATES. A double-registration would
    silently overwrite the tier-1 instance with a tier-2 one.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "WA" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "WA" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # WA has no clothing exemption (RCW 82.08.020 baseline)
        ("groceries", False),  # exempt per RCW 82.08.0293 (1977)
        ("prescription_drugs", False),  # exempt per RCW 82.08.0281
        ("prepared_food", True),  # excluded from RCW 82.08.0293; general 6.5%
        ("digital_goods", True),  # taxable per RCW 82.04.050(6) + 82.04.192 (2009)
        ("general", True),  # baseline TPP at 6.5% per RCW 82.08.020
    ],
)
def test_washington_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying an RCW citation.
    """
    rule = WASHINGTON.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "RCW" in (rule.notes or "")


def test_washington_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert WASHINGTON.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_washington_clothing_is_taxable_no_exemption_no_holiday() -> None:
    """WA does NOT join the broad clothing-exemption states (PA/MA/MN/NJ/VT)
    and has NO threshold (NY/RI) and NO recurring annual holiday. The rule
    must explicitly note all three negatives so a future maintainer doesn't
    copy from an exempt-clothing state by mistake.
    """
    rule = WASHINGTON.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    notes_lower = notes.lower()
    # Imposition statute citation
    assert "82.08.020" in notes
    # Negatives (no exemption / no threshold / no holiday) must be documented.
    assert "no general clothing exemption" in notes_lower or "no clothing exemption" in notes_lower
    assert "no recurring annual sales-tax holiday" in notes_lower or "no recurring" in notes_lower


def test_washington_groceries_cite_rcw_82_08_0293() -> None:
    """Grocery exemption is RCW 82.08.0293 (1977 -- one of the oldest)."""
    rule = WASHINGTON.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "82.08.0293" in notes
    # The 1977 vintage anchor -- documents this is one of the older food exemptions.
    assert "1977" in notes


def test_washington_prescription_drugs_cite_rcw_82_08_0281() -> None:
    """Prescription drugs are exempt under RCW 82.08.0281."""
    rule = WASHINGTON.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "82.08.0281" in (rule.notes or "")


def test_washington_digital_goods_cite_2009_statute() -> None:
    """Digital products / codes / automated services were brought into the
    WA sales-tax base by chapter 535, Laws of 2009 (S.S.B. 5295, effective
    2009-07-26), which amended the 'retail sale' definition (RCW
    82.04.050(6)) and added the defined terms in RCW 82.04.192. The
    digital-automated-services category in particular is the broadest in
    the country and reaches many cloud / SaaS / streaming services.
    """
    rule = WASHINGTON.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "82.04.192" in notes
    assert "82.04.050" in notes
    # The 2009 chapter that brought DAS / digital products into the base.
    assert "2009" in notes
    # The DAS feature must be called out as the distinguishing breadth.
    notes_lower = notes.lower()
    assert "digital automated services" in notes_lower or "digital_automated" in notes_lower


def test_washington_general_rule_cites_imposition_statute_and_rate() -> None:
    """General TPP rule cites RCW 82.08.020 (the imposition statute) and
    documents the 6.5% rate plus the wide combined-rate range and the
    B&O out-of-scope note.
    """
    rule = WASHINGTON.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # Imposition statute
    assert "82.08.020" in notes
    # Rate must be documented
    assert "6.5" in notes
    # Wide combined-rate range must be flagged in the general rule
    assert "10.35" in notes
    # B&O out-of-scope note must appear in the general rule (so an
    # integrator reading just the general rule sees the cross-reference)
    notes_lower = notes.lower()
    assert "b&o" in notes_lower or "business & occupation" in notes_lower
    assert "out of scope" in notes_lower or "out-of-scope" in notes_lower


# ---------------------------------------------------------------------------
# Sales-tax holidays -- WA has NONE.
# ---------------------------------------------------------------------------
def test_washington_holidays_for_all_years_returns_empty() -> None:
    """WA has no active sales-tax holiday in any year.

    Washington has never enacted a recurring sales-tax holiday.
    The 2024 manufacturing-input window (chapter 419, Laws of 2024)
    was a one-time temporary measure for a narrow set of qualifying
    manufacturing inputs, NOT a consumer-facing holiday, and is NOT
    re-encoded as a recurring window. Until a future legislature
    enacts an actual recurring consumer holiday, holidays_for() must
    return an empty iterator for every year (mirrors KY, IN, MI, DC,
    ID, NE, ND, NJ, NC, KS).
    """
    for year in range(2023, 2031):
        holidays = list(WASHINGTON.holidays_for(year))
        assert holidays == [], f"WA has no active holidays. Year: {year}."


# ---------------------------------------------------------------------------
# Module-docstring assertions: B&O out-of-scope, broad digital-services
# base, and wide combined-rate range MUST be prominently documented.
# ---------------------------------------------------------------------------
def test_washington_module_docstring_documents_bo_out_of_scope() -> None:
    """The Business & Occupation (B&O) gross-receipts tax (RCW chapter
    82.04) is uniquely a Washington feature among states with a general
    sales tax. The module docstring MUST explicitly document that the
    B&O is a separate seller-side tax and is OUT OF SCOPE for this
    engine. Without this, an integrator might attempt to compute B&O
    via the OpenSalesTax calculation API and get systematically wrong
    answers (the B&O has different rate-classification rules, no
    buyer-facing collection, and different filing mechanics).
    """
    import opensalestax.states.washington as wa_module

    docstring = wa_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The B&O statute chapter must appear.
    assert "82.04" in docstring
    # The B&O name must be spelled out.
    assert "business & occupation" in docstring_lower
    # Must say it's out of scope (or "not modeled").
    assert "out of scope" in docstring_lower or "not modeled" in docstring_lower
    # Must explain the seller-vs-buyer side distinction.
    assert "seller" in docstring_lower


def test_washington_module_docstring_documents_combined_rate_range() -> None:
    """The wide combined-rate range (~6.5%-10.35%) MUST be prominently
    documented in the module docstring. Without it, an integrator might
    assume a single statewide rate or a single 'Seattle' rate and
    mis-charge by 3+ percentage points depending on the buyer's
    specific street address.
    """
    import opensalestax.states.washington as wa_module

    docstring = wa_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The headline state rate
    assert "6.5" in docstring
    # The high-end combined rate (King County / Seattle)
    assert "10.35" in docstring
    # Must call out the variance / range explicitly
    assert "wide" in docstring_lower or "range" in docstring_lower or "variance" in docstring_lower


def test_washington_module_docstring_documents_broad_digital_base() -> None:
    """WA's broad digital-services tax base (digital products + digital
    codes + digital automated services per RCW 82.04.050(6) + 82.04.192)
    MUST be documented in the module docstring. The DAS category in
    particular reaches many cloud / SaaS / streaming offerings other
    states don't reach; an integrator selling such services into WA
    needs to know.
    """
    import opensalestax.states.washington as wa_module

    docstring = wa_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Defined-terms statute
    assert "82.04.192" in docstring
    # Imposition / definition statute
    assert "82.04.050" in docstring
    # The broad DAS feature must be called out
    assert "digital automated services" in docstring_lower
    # Origin year (2009) must be documented
    assert "2009" in docstring


def test_washington_module_docstring_documents_no_holiday() -> None:
    """The 'never enacted a recurring sales-tax holiday' fact MUST appear
    in the module docstring so a future contributor doesn't add a holiday
    based on outdated guidance or copy-paste from a holiday state.
    """
    import opensalestax.states.washington as wa_module

    docstring = wa_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must document the absence (allow various phrasings).
    assert "never enacted" in docstring_lower or "no recurring" in docstring_lower
    # Should reference the empty-iterator behavior.
    assert "holidays_for" in docstring


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine in v1)
# ---------------------------------------------------------------------------
def test_washington_special_cases_empty() -> None:
    """v1 ships no SpecialCase rows for WA. The B&O / wide-rate /
    broad-DAS caveats are documented in the module docstring and in
    references.md rather than encoded as engine-consumed special cases
    (the SpecialCase API is reserved for Phase 5+).
    """
    cases = list(WASHINGTON.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Documentary constants
# ---------------------------------------------------------------------------
def test_washington_statewide_rate_constant_is_6_5_pct() -> None:
    """Documentary constant: WA's statewide rate is 6.5% per RCW
    section 82.08.020(1) (stable since 1983). The actual rate that
    flows into the engine comes from the SST quarterly file via the
    inherited parser; this constant gives grep-ability and a stable
    test fixture.
    """
    assert Decimal("6.5") == WASHINGTON_STATEWIDE_RATE_PCT


def test_washington_highest_combined_rate_constant_is_10_35_pct() -> None:
    """Documentary constant: the ~10.35% combined-rate ceiling reached
    in parts of King County / Seattle is one of the highest combined
    retail sales-tax rates in the United States. This constant pins
    the documented high end so a future maintainer revising the
    docstring cannot silently drift the documented ceiling out of sync
    with the constant.
    """
    assert Decimal("10.35") == WASHINGTON_HIGHEST_COMBINED_RATE_PCT
    # Sanity: high end exceeds the state-only floor by at least 3pp,
    # which is the headline characteristic justifying the WIDE-range
    # documentation.
    assert Decimal("3.0") <= (WASHINGTON_HIGHEST_COMBINED_RATE_PCT - WASHINGTON_STATEWIDE_RATE_PCT)
