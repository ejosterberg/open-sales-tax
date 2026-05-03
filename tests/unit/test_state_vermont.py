# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Vermont state module (Phase 7 -- tier-2 to tier-1 promotion).

Vermont is an SST member with a 6.0% statewide rate per Vt. Stat. Ann.
tit. 32, section 9771, in effect since October 1, 2003 (raised from
5% by Act 68 of the 2003 Legislative Session).

Vermont's local-jurisdiction landscape is unusually simple:

- Counties impose NO sales tax.
- Municipalities (cities and towns) MAY adopt a Local Option Sales
  Tax (LOST) of EXACTLY 1% under 24 V.S.A. section 138 (originally
  Act 60 of 1997, expanded by Act 68 of 2003). The local option is
  fixed at 1% by statute.
- Approximately 17 of Vermont's ~247 incorporated municipalities have
  opted in (Burlington, South Burlington, Williston, Brattleboro,
  Stowe, Manchester, Killington, Dover, Wilmington, Montpelier, etc.).
- Combined rates are EXACTLY 6.0% (most of Vermont) or EXACTLY 7.0%
  (LOST-adopted municipalities) -- no fractional rates.

The 1% LOST is deferred to per-municipality data ingestion in v1; the
inherited SST parser will pick up per-municipality rows once an
empirical capture validates the VT SST file's jurisdiction-type codes.

Clothing is BROADLY EXEMPT in VT year-round per Vt. Stat. Ann. tit. 32,
section 9741(45) (VT joins PA, MA, MN, NJ in the broad-exemption club).
No per-item dollar cap; no date restriction (contrast with NY's
$110-per-item threshold and MA's $175-per-item threshold).

Sales-tax holidays: NONE. Vermont has no enacted sales-tax holiday in
any year and none is currently scheduled (verified 2026-05-03 against
the Vermont Department of Taxes). holidays_for() returns an empty
iterator for every year (mirrors NJ, NE, DC, ID, IN, ND, MI, KY,
NV, NC).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule
from opensalestax.states.vermont import (
    VERMONT,
    VERMONT_COMBINED_RATE_LOST_PCT,
    VERMONT_LOCAL_OPTION_RATE_PCT,
    VERMONT_STATEWIDE_RATE_PCT,
    Vermont,
)


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_vermont_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 50, tier 1."""
    assert VERMONT.state_abbrev == "VT"
    assert VERMONT.state_name == "Vermont"
    assert VERMONT.state_fips == "50"
    assert VERMONT.sst_member is True
    assert VERMONT.has_sales_tax is True
    assert VERMONT.tier == 1


def test_vermont_inherits_sst_base() -> None:
    """VT subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(VERMONT, SstStateModule)
    assert isinstance(Vermont(), SstStateModule)


def test_vermont_satisfies_protocol() -> None:
    """VT structurally implements the StateModule Protocol."""
    assert isinstance(VERMONT, StateModule)
    assert isinstance(Vermont(), StateModule)


def test_vermont_is_registered() -> None:
    """The registry returns the VT instance under 'VT' (case-insensitive)."""
    assert get_state_module("VT") is VERMONT
    assert get_state_module("vt") is VERMONT


def test_vermont_not_in_tier2_anymore() -> None:
    """Regression: VT was promoted out of _tier2.py and must not appear
    in TIER_2_CLASSES or TIER_2_STATES. A double-registration would
    silently overwrite the tier-1 instance with a tier-2 one.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "VT" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "VT" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", False),  # 32 V.S.A. 9741(45) broad exemption
        ("groceries", False),  # 32 V.S.A. 9741(13)
        ("prescription_drugs", False),  # 32 V.S.A. 9741(2)
        ("prepared_food", True),  # excluded from 32 V.S.A. 9741(13)
        ("digital_goods", True),  # 32 V.S.A. 9701(31)(B), Act 174 of 2014
        ("general", True),  # 32 V.S.A. 9771 imposition
    ],
)
def test_vermont_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying a Vt. Stat. Ann. citation.
    """
    rule = VERMONT.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes = rule.notes or ""
    assert "V.S.A." in notes or "Vt. Stat. Ann." in notes


def test_vermont_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert VERMONT.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_vermont_clothing_is_exempt_year_round_no_threshold() -> None:
    """VT joins PA/MA/MN/NJ in the broad year-round clothing exemption.

    Distinct from NY's $110-per-item threshold and MA's $175-per-item
    threshold: VT's exemption has NO per-item dollar cap and NO date
    restriction. The rule's notes must cite 32 V.S.A. 9741(45) and
    document the exclusions (accessories, sport/recreational
    equipment, protective equipment).

    Regression: this is the headline VT-specific quirk; weakening or
    removing this rule would silently start collecting tax on clothing
    in Vermont in production.
    """
    rule = VERMONT.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "9741(45)" in notes
    notes_lower = notes.lower()
    # Exclusions must be documented so a future maintainer doesn't
    # accidentally exempt accessories / sport equipment.
    assert "accessor" in notes_lower
    assert "sport" in notes_lower or "recreational" in notes_lower


def test_vermont_groceries_cite_section_9741_13() -> None:
    """Grocery exemption is in Vt. Stat. Ann. tit. 32, section 9741(13)."""
    rule = VERMONT.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "9741(13)" in (rule.notes or "")


def test_vermont_prescription_drugs_cite_section_9741_2() -> None:
    """Prescription drugs are exempt under Vt. Stat. Ann. tit. 32, section 9741(2)."""
    rule = VERMONT.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "9741(2)" in (rule.notes or "")


def test_vermont_digital_goods_cite_2014_act_and_definition_section() -> None:
    """Specified digital products were brought into the VT sales-tax base
    by H. 528 of the 2014 Legislative Session (Act 174 of 2014), with an
    effective date of July 1, 2015. The defined term lives at Vt. Stat.
    Ann. tit. 32, section 9701(31)(B). The notes must cite both the
    enabling chapter and the definition section so a future maintainer
    can re-verify the scope of taxable digital products.
    """
    rule = VERMONT.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # Defined-term cross-reference.
    assert "9701(31)" in notes
    # The enabling chapter -- either H. 528 or Act 174.
    assert "H. 528" in notes or "Act 174" in notes
    assert "2014" in notes


def test_vermont_prepared_food_cite_meals_and_rooms_tax() -> None:
    """Prepared food is taxable in VT but PRINCIPALLY under the 9% Meals
    and Rooms Tax (32 V.S.A. chapter 225) rather than the 6% general
    sales tax. The notes must flag this so an integrator selling
    restaurant meals in Vermont knows to apply the 9% rate outside
    this engine.
    """
    rule = VERMONT.taxability_for("prepared_food", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # The 9% Meals and Rooms Tax must be flagged.
    assert "9%" in notes or "9 %" in notes
    notes_lower = notes.lower()
    assert "meals" in notes_lower or "rooms" in notes_lower


def test_vermont_general_rule_cites_imposition_statute_and_rate() -> None:
    """General TPP rule cites Vt. Stat. Ann. tit. 32, section 9771 (the
    imposition statute) and documents the 6% rate plus the 1% local
    option authorized by 24 V.S.A. section 138.
    """
    rule = VERMONT.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "9771" in notes  # imposition statute
    # Rate must be documented in the general rule's notes.
    assert "6%" in notes or "6.0%" in notes
    # Local Option Sales Tax under 24 V.S.A. section 138 must be flagged.
    assert "138" in notes
    notes_lower = notes.lower()
    assert "local option" in notes_lower
    assert "1%" in notes  # the fixed local rate


# ---------------------------------------------------------------------------
# Sales-tax holidays -- VT has NONE.
# ---------------------------------------------------------------------------
def test_vermont_holidays_for_all_years_returns_empty() -> None:
    """VT has no enacted sales-tax holiday in any year.

    Vermont has never enacted a sales-tax holiday and none is currently
    in the legislative pipeline (verified 2026-05-03 against the Vermont
    Department of Taxes Sales Tax landing page). holidays_for() must
    return an empty iterator for every year (mirrors NJ, NE, DC, ID,
    IN, ND, MI, KY, NV, NC).

    Regression: a future contributor MUST NOT add a holiday window
    based on a neighboring state's framework -- if the General Assembly
    ever enacts one, it will have its own dates, scope, and per-item cap.
    """
    for year in range(2020, 2031):
        holidays = list(VERMONT.holidays_for(year))
        assert holidays == [], f"VT has no enacted holidays. Year: {year}."


# ---------------------------------------------------------------------------
# Module-docstring assertions: LOST + clothing exemption + Meals and
# Rooms Tax must be prominently documented or future maintainers +
# integrators won't know about the under-collection edge cases.
# ---------------------------------------------------------------------------
def test_vermont_module_docstring_documents_local_option_sales_tax() -> None:
    """The Local Option Sales Tax (24 V.S.A. section 138) MUST be
    documented in the module docstring. Without it, an integrator
    using VT addresses in Burlington / South Burlington / Brattleboro
    won't know that the engine's state-only baseline under-collects
    by 1 percentage point in those municipalities, and won't
    understand why the deferred-locals posture exists.
    """
    import opensalestax.states.vermont as vt_module

    docstring = vt_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The LOST statute identifier must appear.
    assert "138" in docstring
    # The mechanism must be spelled out.
    assert "local option" in docstring_lower
    # The 1% local rate must be documented.
    assert "1%" in docstring
    # The deferral mechanism must be explained.
    assert "deferred" in docstring_lower or "not modeled" in docstring_lower


def test_vermont_module_docstring_documents_clothing_exemption() -> None:
    """The broad clothing exemption (Vt. Stat. Ann. tit. 32, section
    9741(45)) MUST be prominently called out in the module docstring
    -- it is one of VT's two most distinctive features (along with
    being one of only ~5 states with a year-round broad clothing
    exemption). Removing or weakening this language is a documentation
    regression.
    """
    import opensalestax.states.vermont as vt_module

    docstring = vt_module.__doc__ or ""
    docstring_lower = docstring.lower()
    assert "9741(45)" in docstring
    assert "clothing" in docstring_lower
    assert "exempt" in docstring_lower


def test_vermont_module_docstring_documents_meals_and_rooms_tax() -> None:
    """The separate 9% Meals and Rooms Tax (32 V.S.A. chapter 225) MUST
    be documented in the module docstring. Without it, an integrator
    selling restaurant meals in Vermont won't know that this engine's
    6% general-sales-tax calculation under-collects by 3 percentage
    points relative to the correct 9% Meals and Rooms Tax rate.
    """
    import opensalestax.states.vermont as vt_module

    docstring = vt_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The Meals and Rooms Tax must be named.
    assert "meals" in docstring_lower
    assert "rooms" in docstring_lower
    # The 9% rate must be documented.
    assert "9%" in docstring


def test_vermont_module_docstring_documents_no_holidays() -> None:
    """The absence of any sales-tax holiday MUST be documented in the
    module docstring so a casual reader doesn't think VT participates
    in the August back-to-school cycle that AR/IA/MO/MS/OK/etc. share.
    A maintainer reading only the code might extrapolate from the
    general SST membership and add an erroneous holiday.
    """
    import opensalestax.states.vermont as vt_module

    docstring = vt_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The "no holiday" statement must appear unambiguously.
    assert "no sales-tax holiday" in docstring_lower or "no sales tax holiday" in docstring_lower


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine in v1)
# ---------------------------------------------------------------------------
def test_vermont_special_cases_empty() -> None:
    """v1 ships no SpecialCase rows for VT. The LOST / Meals and Rooms
    Tax / Sugar-Sweetened Beverage Tax caveats are documented in the
    module docstring and in references.md rather than encoded as
    engine-consumed special cases (the SpecialCase API is reserved
    for Phase 5+).
    """
    cases = list(VERMONT.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Documentary constants
# ---------------------------------------------------------------------------
def test_vermont_statewide_rate_constant_is_6_pct() -> None:
    """Documentary constant: VT's statewide rate is 6.0% per Vt. Stat.
    Ann. tit. 32, section 9771 (in effect since 2003-10-01, raised
    from 5% by Act 68 of 2003). The actual rate that flows into the
    engine comes from the SST quarterly file via the inherited
    parser; this constant gives grep-ability and a stable test
    fixture.
    """
    assert Decimal("6.000") == VERMONT_STATEWIDE_RATE_PCT


def test_vermont_local_option_rate_constant_is_1_pct() -> None:
    """Documentary constant: VT's Local Option Sales Tax (24 V.S.A.
    section 138) is fixed at exactly 1% by statute. A municipality
    cannot adopt 0.5% or 1.5%; the rate is either 0% (default) or
    exactly 1%.
    """
    assert Decimal("1.000") == VERMONT_LOCAL_OPTION_RATE_PCT


def test_vermont_combined_rate_constant_equals_state_plus_local() -> None:
    """Documentary constant: in LOST-adopted municipalities the combined
    rate is EXACTLY 7.0% (6% state + 1% local). Catches any future typo
    in either constant.
    """
    assert Decimal("7.000") == VERMONT_COMBINED_RATE_LOST_PCT
    # Verify the state + local relationship exactly.
    assert (
        VERMONT_STATEWIDE_RATE_PCT + VERMONT_LOCAL_OPTION_RATE_PCT == VERMONT_COMBINED_RATE_LOST_PCT
    )
