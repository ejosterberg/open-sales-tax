# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Michigan state module (Phase 7 -- tier-2 to tier-1 promotion).

Michigan is an SST member with a 6% statewide rate (MCL section
205.52) and NO general local sales tax. The combined rate at every
Michigan address is exactly 6%. Notable peer-state difference:
Michigan does NOT tax most digital goods (per Treasury Revenue
Administrative Bulletin 2023-22 and Auto-Owners Insurance Co. v.
Department of Treasury, 313 Mich. App. 56 (2015)).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.michigan import (
    MICHIGAN,
    MICHIGAN_GENERAL_RATE_PCT,
    Michigan,
)
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_michigan_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 26, tier 1."""
    assert MICHIGAN.state_abbrev == "MI"
    assert MICHIGAN.state_name == "Michigan"
    assert MICHIGAN.state_fips == "26"
    assert MICHIGAN.sst_member is True
    assert MICHIGAN.has_sales_tax is True
    assert MICHIGAN.tier == 1


def test_michigan_satisfies_protocol() -> None:
    """Michigan subclasses ``SstStateModule`` and structurally implements
    the Protocol via inheritance + a few attribute overrides.
    """
    assert isinstance(MICHIGAN, StateModule)
    assert isinstance(Michigan(), StateModule)
    assert isinstance(MICHIGAN, SstStateModule)


def test_michigan_is_registered() -> None:
    """The registry returns the Michigan instance under 'MI'."""
    module = get_state_module("MI")
    assert module is MICHIGAN
    # Promotion sanity check: not the generic tier-2 default any more.
    assert module is not None
    assert module.tier == 1


def test_michigan_not_in_tier2_classes() -> None:
    """Regression: Michigan must NOT appear in TIER_2_CLASSES or
    TIER_2_STATES after promotion. A double-registration would
    silently re-overwrite the tier-1 instance.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "MI" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "MI" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in MCL Chapter 205
        ("groceries", False),  # MCL section 205.54g(1)(a)
        ("prescription_drugs", False),  # MCL section 205.54a(1)(g) / 205.94d
        ("prepared_food", True),  # excluded from grocery exemption
        ("digital_goods", False),  # NOT taxable -- RAB 2023-22, Auto-Owners
        ("general", True),  # MCL section 205.52(1)
    ],
)
def test_michigan_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying the citation.
    """
    rule = MICHIGAN.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_michigan_unknown_category_returns_none() -> None:
    """Unknown category -> None so the engine falls back to the
    conservative 'taxable at default rate' behavior.
    """
    assert MICHIGAN.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_michigan_groceries_cite_205_54g() -> None:
    """The grocery exemption must cite MCL section 205.54g (the controlling
    food-and-food-ingredients exemption in the General Sales Tax Act).
    """
    rule = MICHIGAN.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "205.54g" in (rule.notes or "")


def test_michigan_prescription_drugs_cite_controlling_statute() -> None:
    """Prescription-drug exemption must cite either MCL 205.54a (Sales Tax
    Act exemption) or MCL 205.94d (Use Tax Act parallel).
    """
    rule = MICHIGAN.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "205.54a" in notes or "205.94d" in notes


def test_michigan_digital_goods_NOT_taxable_with_rab_citation() -> None:
    """REGRESSION: Michigan does NOT tax most digital goods. This is the
    headline peer-state difference (IA, IN, WI all tax digital goods).

    The rule MUST encode is_taxable=False AND cite the controlling
    Revenue Administrative Bulletin (RAB 2023-22) so a future
    maintainer can re-verify when Treasury revises the bulletin.
    The rule should also reference the Auto-Owners decision, which
    confirms electronically-delivered prewritten software is not
    subject to Michigan use tax.
    """
    rule = MICHIGAN.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False, (
        "Michigan does NOT tax electronically-delivered digital goods -- "
        "this is a notable peer-state difference. See RAB 2023-22 and "
        "Auto-Owners Insurance Co. v. Department of Treasury, 313 Mich. "
        "App. 56 (2015), aff'd 500 Mich. 921 (2016)."
    )
    notes = rule.notes or ""
    notes_lower = notes.lower()
    # Must cite the RAB so a future maintainer can re-verify
    assert "rab" in notes_lower or "revenue administrative bulletin" in notes_lower
    # The dominant case the rule is encoding (no tangible medium = no tax)
    assert "Auto-Owners" in notes or "tangible" in notes_lower


def test_michigan_general_rule_cite_205_52() -> None:
    """The general TPP imposition rule must cite MCL section 205.52 (the
    rate-setting statute in the General Sales Tax Act).
    """
    rule = MICHIGAN.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "205.52" in (rule.notes or "")


# ---------------------------------------------------------------------------
# Holidays + special cases
# ---------------------------------------------------------------------------
def test_michigan_holidays_for_all_years_returns_empty() -> None:
    """REGRESSION: Michigan has NO sales-tax holidays in any year.

    Confirmed against the Michigan Department of Treasury 2026-05-03.
    Michigan has never enacted a back-to-school holiday, disaster-prep
    holiday, Energy Star holiday, or any other recurring exemption
    period. This test exists specifically to catch any future
    regression where a contributor accidentally adds a holiday
    window (e.g. by copy-pasting from a state that does have one).
    """
    for year in range(2024, 2031):
        holidays = list(MICHIGAN.holidays_for(year))
        assert holidays == [], f"Michigan should have no holidays in {year}"


def test_michigan_special_cases_empty() -> None:
    """Phase 7 ships no SpecialCase rows for Michigan. The only quirks
    worth flagging (narrow accommodations / convention-facility taxes
    in Wayne County and similar) are documented in the module
    docstring rather than encoded as engine-consumed special cases --
    they are not general sales taxes.
    """
    cases = list(MICHIGAN.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# No-local-tax landscape (the headline MI-vs-peer-states distinction)
# ---------------------------------------------------------------------------
def test_michigan_module_docstring_documents_no_local_sales_tax() -> None:
    """REGRESSION: the 'no local sales tax' caveat MUST appear in the
    module docstring -- it's the most important piece of context an
    integrator needs to understand Michigan's combined-rate model.
    Removing or weakening this language without a deliberate update
    is a documentation regression.
    """
    import opensalestax.states.michigan as michigan_module

    docstring = michigan_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must explicitly state that MI has NO local sales tax somewhere
    # in the docstring (case-insensitive, allow 'no general local sales tax'
    # or 'no local sales tax' phrasing).
    assert (
        "no local sales tax" in docstring_lower or "no general local sales tax" in docstring_lower
    ), (
        "Michigan module docstring must explicitly document the "
        "no-local-sales-tax landscape (notable difference from "
        "peer SST states)."
    )
    # And it must call out 6% as the entire combined rate.
    assert "6%" in docstring or "6.0%" in docstring


def test_michigan_jurisdiction_types_only_maps_state() -> None:
    """REGRESSION: Michigan's jurisdiction-type dict accepts ONLY the
    state-level code. This guarantees that any unexpected non-state
    row in a future SST quarterly file is silently dropped rather
    than miscategorized as a sub-state authority Michigan doesn't have.
    """
    assert MICHIGAN.jurisdiction_types == {"45": "state"}
    assert "00" not in MICHIGAN.jurisdiction_types  # county
    assert "01" not in MICHIGAN.jurisdiction_types  # city
    assert "63" not in MICHIGAN.jurisdiction_types  # district


def test_michigan_general_rate_constant_is_6_pct() -> None:
    """Documentary constant: Michigan's general state rate is 6.0%.
    The actual rate that flows into the engine comes from the SST
    rate file via the inherited parser, but this constant gives
    grep-ability and a stable test fixture.

    The 6% rate has been in effect since Proposal A of 1994 and is
    constitutionalized at Article IX section 8; further increases
    require a 3/4 supermajority of both legislative chambers.
    """
    assert Decimal("6.000") == MICHIGAN_GENERAL_RATE_PCT
