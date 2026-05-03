# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the North Dakota state module (Phase 7 -- tier-2 to tier-1 promotion).

North Dakota is an SST member with a 5.0% state rate per N.D.C.C.
section 57-39.2-02.1. Cities and home-rule counties may impose
local option sales taxes (typical combined rates 5.0%-8.5%).
North Dakota has NO sales-tax holiday in any year.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.north_dakota import (
    NORTH_DAKOTA,
    NORTH_DAKOTA_GENERAL_RATE_PCT,
    NorthDakota,
)
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_north_dakota_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 38, tier 1."""
    assert NORTH_DAKOTA.state_abbrev == "ND"
    assert NORTH_DAKOTA.state_name == "North Dakota"
    assert NORTH_DAKOTA.state_fips == "38"
    assert NORTH_DAKOTA.sst_member is True
    assert NORTH_DAKOTA.has_sales_tax is True
    assert NORTH_DAKOTA.tier == 1


def test_north_dakota_satisfies_protocol() -> None:
    """North Dakota subclasses ``SstStateModule`` and structurally implements
    the Protocol via inheritance + a few attribute overrides.
    """
    assert isinstance(NORTH_DAKOTA, StateModule)
    assert isinstance(NorthDakota(), StateModule)
    assert isinstance(NORTH_DAKOTA, SstStateModule)


def test_north_dakota_is_registered() -> None:
    """The registry returns the North Dakota instance under 'ND'."""
    module = get_state_module("ND")
    assert module is NORTH_DAKOTA
    # Promotion sanity check: not the generic tier-2 default any more.
    assert module is not None
    assert module.tier == 1


def test_north_dakota_lookup_is_case_insensitive() -> None:
    """The registry lookup accepts mixed/lowercase forms."""
    assert get_state_module("nd") is NORTH_DAKOTA
    assert get_state_module("Nd") is NORTH_DAKOTA


def test_north_dakota_not_in_tier2_classes() -> None:
    """Regression: North Dakota must NOT appear in TIER_2_CLASSES or
    TIER_2_STATES after promotion. A double-registration would
    silently re-overwrite the tier-1 instance.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "ND" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "ND" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in chapter 57-39.2
        ("groceries", False),  # N.D.C.C. 57-39.2-04(46)
        ("prescription_drugs", False),  # N.D.C.C. 57-39.2-04(33)
        ("prepared_food", True),  # excluded from grocery exemption
        ("digital_goods", True),  # N.D.C.C. 57-39.2-02.1(1)(c) (HB 1041, 2019)
        ("general", True),  # N.D.C.C. 57-39.2-02.1
    ],
)
def test_north_dakota_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying the citation.
    """
    rule = NORTH_DAKOTA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present
    # Every rule must cite the ND code chapter so a future maintainer
    # can re-verify against the statute.
    assert "N.D.C.C." in (rule.notes or "")


def test_north_dakota_unknown_category_returns_none() -> None:
    """Unknown category -> None so the engine falls back to the
    conservative 'taxable at default rate' behavior.
    """
    assert NORTH_DAKOTA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_north_dakota_groceries_cite_subsection_46() -> None:
    """Grocery exemption is in subsection 46 of 57-39.2-04."""
    rule = NORTH_DAKOTA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "57-39.2-04(46)" in (rule.notes or "")


def test_north_dakota_prescription_drugs_cite_subsection_33() -> None:
    """Prescription-drug exemption must cite subsection 33 of 57-39.2-04."""
    rule = NORTH_DAKOTA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "57-39.2-04(33)" in (rule.notes or "")


def test_north_dakota_general_rule_cites_imposition_statute() -> None:
    """The general-TPP rule must cite the imposition statute 57-39.2-02.1."""
    rule = NORTH_DAKOTA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert "57-39.2-02.1" in (rule.notes or "")


def test_north_dakota_digital_goods_cite_2019_amendment() -> None:
    """Digital-goods rule must reference the 2019 HB 1041 expansion that
    brought specified digital products into the sales-tax base. Without
    that citation a future maintainer can not date the rule against
    subsequent legislative changes.
    """
    rule = NORTH_DAKOTA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "57-39.2-02.1" in notes
    # The 2019 bill citation must be present so the rule's evolution
    # is auditable.
    assert "1041" in notes  # HB 1041 of 2019
    assert "2019" in notes


def test_north_dakota_clothing_documents_no_holiday() -> None:
    """The clothing rule must document that ND has no back-to-school
    sales-tax holiday so a future contributor doesn't accidentally
    add one when copy-pasting from a state that does (e.g. Iowa).
    """
    rule = NORTH_DAKOTA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    notes_lower = (rule.notes or "").lower()
    assert "no" in notes_lower and "holiday" in notes_lower


# ---------------------------------------------------------------------------
# Holidays + special cases (no-holidays regression)
# ---------------------------------------------------------------------------
def test_north_dakota_holidays_for_all_years_returns_empty() -> None:
    """Regression: North Dakota has NO sales-tax holidays in any year.

    Confirmed against the North Dakota Office of State Tax
    Commissioner 2026-05-03. This test exists specifically to
    catch any future regression where a contributor accidentally
    adds a holiday window (e.g. by copy-pasting from a state that
    does have one).
    """
    for year in range(2024, 2031):
        holidays = list(NORTH_DAKOTA.holidays_for(year))
        assert holidays == [], f"North Dakota should have no holidays in {year}"


def test_north_dakota_special_cases_empty() -> None:
    """Phase 7 ships no SpecialCase rows for North Dakota. The local
    option tax landscape (city + home-rule county sales taxes) flows
    through the inherited SST parser as ordinary rate rows; nothing
    in the engine consumes special cases yet.
    """
    cases = list(NORTH_DAKOTA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Documentation regressions
# ---------------------------------------------------------------------------
def test_north_dakota_docstring_documents_local_tax_landscape() -> None:
    """ND DOES allow local option sales taxes (unlike KY / IN / MI);
    the docstring must explicitly document this so an integrator
    doesn't assume the 5% state rate is the entire combined rate.
    """
    import opensalestax.states.north_dakota as nd_module

    docstring = nd_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must call out that locals exist and the typical combined-rate
    # range (5.0%-8.5%) somewhere in the docstring.
    assert "local" in docstring_lower
    assert "5.0%" in docstring or "5%" in docstring
    assert "8.5%" in docstring


def test_north_dakota_docstring_documents_no_holiday() -> None:
    """The docstring must explicitly state that ND has no sales-tax
    holiday so a future maintainer doesn't have to re-derive that
    fact from scratch.
    """
    import opensalestax.states.north_dakota as nd_module

    docstring = nd_module.__doc__ or ""
    assert "NONE" in docstring or "no" in docstring.lower()
    assert "holiday" in docstring.lower()


# ---------------------------------------------------------------------------
# Documentary rate constant
# ---------------------------------------------------------------------------
def test_north_dakota_general_rate_constant_is_5_pct() -> None:
    """Documentary constant: North Dakota's general state rate is 5.0%.
    The actual rate that flows into the engine comes from the SST
    rate file via the inherited parser, but this constant gives
    grep-ability and a stable test fixture.
    """
    assert Decimal("5.000") == NORTH_DAKOTA_GENERAL_RATE_PCT


# ---------------------------------------------------------------------------
# Inherited SST parser smoke checks
# ---------------------------------------------------------------------------
def test_north_dakota_parse_boundaries_callable() -> None:
    """parse_boundaries is inherited from ``SstStateModule`` and is
    callable; we don't ship an ND fixture in this PR. The inherited
    parser yields nothing when given an empty source.
    """
    method = NORTH_DAKOTA.parse_boundaries
    assert callable(method)


def test_north_dakota_parse_rates_callable() -> None:
    """parse_rates is inherited from ``SstStateModule`` and callable."""
    method = NORTH_DAKOTA.parse_rates
    assert callable(method)


def test_north_dakota_inherits_default_jurisdiction_types() -> None:
    """ND DOES have local sales taxes (cities + home-rule counties),
    so it uses the default SST jurisdiction-type code mapping
    inherited from ``_sst_base`` (state 45, county 00, city 01,
    district 63). Unlike Kentucky / Indiana / Michigan, this
    state should NOT restrict the mapping to state-only.
    """
    # Default mapping has at least state + county + city codes.
    jt = NORTH_DAKOTA.jurisdiction_types
    assert "45" in jt and jt["45"] == "state"
    assert "00" in jt and jt["00"] == "county"
    assert "01" in jt and jt["01"] == "city"
