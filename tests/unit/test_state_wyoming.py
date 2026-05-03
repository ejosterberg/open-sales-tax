# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Wyoming state module (Phase 7 -- final SST promotion).

Wyoming is an SST member with a 4.0% statewide rate per Wyo. Stat.
Ann. section 39-15-104(a). Counties may layer up to 1% general-purpose
(section 39-15-204(a)(i)) and up to 1% specific-purpose
(section 39-15-204(a)(iii)) local-option rates on top, with combined
rates typically running 4%-7% across the state.

Two notable peer-state differences encoded here:

- **Digital goods are NOT taxable** in WY -- the sales-tax base under
  Wyo. Stat. section 39-15-103(a)(i) is statutorily limited to
  tangible personal property plus a closed list of enumerated
  services; the Legislature has not extended the base to specified
  digital products. WY joins MI, NV, OK in the small minority of SST
  states without a digital-goods sales tax.
- **Groceries have been exempt since July 1, 2006** per Wyo. Stat.
  section 39-15-105(a)(iii)(C) (enacted by Senate Enrolled Act 64
  of the 2006 Wyoming Legislature).

Sales-tax holidays: NONE. Wyoming has never enacted a sales-tax
holiday of any kind. holidays_for() returns an empty iterator for
every year.

PHASE 7 MILESTONE: Wyoming is the FINAL SST member to be promoted
from tier 2 to tier 1. With this module shipped, every SST member
state has a fully-maintained tier-1 taxability matrix grounded in
primary statutory sources (Phase 7 complete).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule
from opensalestax.states.wyoming import (
    WYOMING,
    WYOMING_STATE_RATE_PCT,
    Wyoming,
)


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_wyoming_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 56, tier 1."""
    assert WYOMING.state_abbrev == "WY"
    assert WYOMING.state_name == "Wyoming"
    assert WYOMING.state_fips == "56"
    assert WYOMING.sst_member is True
    assert WYOMING.has_sales_tax is True
    assert WYOMING.tier == 1


def test_wyoming_inherits_sst_base() -> None:
    """WY subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(WYOMING, SstStateModule)
    assert isinstance(Wyoming(), SstStateModule)


def test_wyoming_satisfies_protocol() -> None:
    """WY structurally implements the StateModule Protocol."""
    assert isinstance(WYOMING, StateModule)
    assert isinstance(Wyoming(), StateModule)


def test_wyoming_is_registered() -> None:
    """The registry returns the WY instance under 'WY' (case-insensitive)."""
    assert get_state_module("WY") is WYOMING
    assert get_state_module("wy") is WYOMING


def test_wyoming_not_in_tier2_anymore() -> None:
    """REGRESSION: WY was promoted out of _tier2.py and must not appear
    in TIER_2_CLASSES or TIER_2_STATES. A double-registration would
    silently overwrite the tier-1 instance with a tier-2 one.

    This is the LAST tier-2-removal regression for an SST state -- WY's
    promotion completes Phase 7 and empties the SST tier-2 backlog.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "WY" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "WY" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in Wyo. Stat. ch. 15
        ("groceries", False),  # Wyo. Stat. 39-15-105(a)(iii)(C) eff. 2006-07-01
        ("prescription_drugs", False),  # Wyo. Stat. 39-15-105(a)(viii)
        ("prepared_food", True),  # excluded from grocery exemption
        ("digital_goods", False),  # NOT taxable -- base limited to TPP per 39-15-103
        ("general", True),  # Wyo. Stat. 39-15-104(a)
    ],
)
def test_wyoming_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying the citation.
    """
    rule = WYOMING.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present
    # Statutory citation must appear in every rule's notes
    # (constitution + per-state-research-brief).
    assert "Wyo. Stat." in (rule.notes or "")


def test_wyoming_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert WYOMING.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_wyoming_groceries_cite_section_39_15_105_a_iii_C() -> None:
    """Grocery exemption is in Wyo. Stat. section 39-15-105(a)(iii)(C),
    effective July 1, 2006. The notes must cite both the statute and the
    effective date so a future maintainer can verify the exemption is
    still in force.
    """
    rule = WYOMING.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "39-15-105(a)(iii)(C)" in notes
    # Effective date must be documented (it's been the law since 2006).
    assert "2006" in notes


def test_wyoming_prescription_drugs_cite_section_39_15_105_a_viii() -> None:
    """Prescription-drug exemption is in Wyo. Stat. section 39-15-105(a)(viii)."""
    rule = WYOMING.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "39-15-105(a)(viii)" in (rule.notes or "")


def test_wyoming_digital_goods_NOT_taxable_with_statutory_citation() -> None:
    """REGRESSION: Wyoming does NOT tax digital goods. This is one of the
    headline peer-state differences (IA, IN, WI, NJ all tax digital goods).

    The rule MUST encode is_taxable=False AND cite the controlling
    statute (Wyo. Stat. section 39-15-103) so a future maintainer can
    re-verify when / if the Legislature amends the Selective Sales Tax
    Act to extend the base to specified digital products.

    The rule should also document the tangible-medium exception
    (canned software on physical media IS taxable) so an integrator
    knows to categorize disk/USB shipments as 'general' rather than
    'digital_goods'.
    """
    rule = WYOMING.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False, (
        "Wyoming does NOT tax electronically-delivered digital goods -- "
        "the sales-tax base under Wyo. Stat. section 39-15-103(a)(i) is "
        "statutorily limited to tangible personal property plus a closed "
        "list of enumerated services. The Legislature has NOT extended "
        "the base to 'specified digital products'."
    )
    notes = rule.notes or ""
    notes_lower = notes.lower()
    # Must cite the controlling imposition statute.
    assert "39-15-103" in notes
    # The dominant rule (no tangible medium = no tax) must be explained.
    assert "tangible" in notes_lower
    # Document that physical software media remain taxable (the engine
    # exception integrators need to know about).
    assert "disk" in notes_lower or "usb" in notes_lower or "physical" in notes_lower


def test_wyoming_general_rule_cites_imposition_and_rate_statutes() -> None:
    """General TPP rule cites both the imposition statute (39-15-103) and
    the rate-setting statute (39-15-104(a)) and documents the 4% state
    rate plus the local-option overlay structure.
    """
    rule = WYOMING.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # Both the imposition and rate-setting statutes must be cited.
    assert "39-15-104(a)" in notes
    assert "39-15-103" in notes
    # The 4% state rate must appear in the general rule's notes.
    assert "4%" in notes or "4.0%" in notes
    # Local-option overlays must be flagged so an integrator understands
    # the combined rate isn't just 4%.
    assert "39-15-204" in notes


def test_wyoming_clothing_rule_documents_no_holiday() -> None:
    """The clothing rule MUST document the absence of a back-to-school
    holiday so a future maintainer doesn't accidentally add one based on
    a copy-paste from a state that does have one (e.g. AR, IA, OK).
    """
    rule = WYOMING.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes_lower = (rule.notes or "").lower()
    # Must be explicit about the no-holiday landscape.
    assert "no" in notes_lower and ("holiday" in notes_lower)


# ---------------------------------------------------------------------------
# Sales-tax holidays -- WY has NEVER enacted one.
# ---------------------------------------------------------------------------
def test_wyoming_holidays_for_all_years_returns_empty() -> None:
    """REGRESSION: Wyoming has NO sales-tax holidays in ANY year.

    Confirmed against the Wyoming Department of Revenue 2026-05-03.
    Wyoming has NEVER enacted a back-to-school holiday, disaster-prep
    holiday, Energy Star holiday, or any other recurring exemption
    period in its sales-tax history. This test exists specifically to
    catch any future regression where a contributor accidentally adds
    a holiday window (e.g. by copy-pasting from a state that does have
    one like AR, IA, OK, or TX).

    Mirrors MI, ID, IN, KY, NE, NJ, ND -- all peer SST states with no
    holidays.
    """
    for year in range(2024, 2031):
        holidays = list(WYOMING.holidays_for(year))
        assert holidays == [], f"Wyoming should have no holidays in {year}"


# ---------------------------------------------------------------------------
# Module-docstring + class-docstring assertions
# ---------------------------------------------------------------------------
def test_wyoming_module_docstring_documents_phase_7_milestone() -> None:
    """REGRESSION: the Phase 7 'final SST promotion' milestone MUST appear
    in the module docstring. WY is a historically significant promotion
    -- it completes the SST tier-2 -> tier-1 ratchet -- and that context
    is important for future maintainers reading the module cold.
    """
    import opensalestax.states.wyoming as wyoming_module

    docstring = wyoming_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The Phase 7 milestone must be explicitly documented.
    assert "phase 7" in docstring_lower
    # And the "final" / "last" framing must be there so a reader
    # immediately understands the historical significance.
    assert "final" in docstring_lower or "last" in docstring_lower


def test_wyoming_module_docstring_documents_no_digital_tax() -> None:
    """REGRESSION: the no-digital-goods-tax position MUST appear in the
    module docstring. It's one of WY's two most distinctive peer-state
    differences (along with the 2006 grocery exemption) and removing
    or weakening this language is a documentation regression that would
    leave future maintainers / integrators confused about why digital
    goods aren't being taxed.
    """
    import opensalestax.states.wyoming as wyoming_module

    docstring = wyoming_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The headline finding must appear.
    assert "not taxable" in docstring_lower or "not tax" in docstring_lower
    # Must mention digital goods specifically.
    assert "digital" in docstring_lower
    # Must cite the controlling statute so a maintainer can re-verify.
    assert "39-15-103" in docstring


def test_wyoming_module_docstring_documents_2006_grocery_exemption() -> None:
    """REGRESSION: the July 1, 2006 grocery-exemption effective date MUST
    appear in the module docstring. The exemption was enacted by Senate
    Enrolled Act 64 of the 2006 Wyoming Legislature; documenting both
    the date and the statute (39-15-105(a)(iii)(C)) gives future
    maintainers a clear paper trail.
    """
    import opensalestax.states.wyoming as wyoming_module

    docstring = wyoming_module.__doc__ or ""
    # Must document the exemption is grounded in a 2006 enactment.
    assert "2006" in docstring
    # Must cite the controlling statute.
    assert "39-15-105" in docstring


def test_wyoming_module_docstring_documents_no_holidays() -> None:
    """REGRESSION: the 'no sales-tax holidays' fact MUST be prominently
    documented so a future contributor doesn't add one based on
    outdated guidance or a hopeful misreading of the statutes.
    """
    import opensalestax.states.wyoming as wyoming_module

    docstring = wyoming_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must be unambiguous -- "never enacted" is the strongest framing.
    assert "never" in docstring_lower
    assert "holiday" in docstring_lower


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine in v1)
# ---------------------------------------------------------------------------
def test_wyoming_special_cases_empty() -> None:
    """v1 ships no SpecialCase rows for WY. Local-option county rates
    flow through the SST quarterly file via the inherited parser; the
    SpecialCase API is reserved for Phase 5+ (exemption certs etc.).
    """
    cases = list(WYOMING.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Documentary constants
# ---------------------------------------------------------------------------
def test_wyoming_state_rate_constant_is_4_pct() -> None:
    """Documentary constant: Wyoming's state rate is 4.0% per Wyo. Stat.
    section 39-15-104(a). The actual rate that flows into the engine
    comes from the SST quarterly file via the inherited parser; this
    constant gives grep-ability and a stable test fixture.

    The 4% rate has been in continuous effect since July 1, 1993
    (raised from 3% to 4% by Senate Enrolled Act 31 of the 1993
    Wyoming Legislature).
    """
    assert Decimal("4.000") == WYOMING_STATE_RATE_PCT
