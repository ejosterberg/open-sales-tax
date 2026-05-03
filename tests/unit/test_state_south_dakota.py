# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the South Dakota state module (Phase 7 -- tier-2 to tier-1 promotion).

South Dakota is an SST member with a 4.2% state rate per SDCL
section 10-45-2 (effective 2023-07-01 per HB 1137 of the 98th SD
Legislative Session, with a statutory sunset on 2027-06-30).
Municipal gross receipts taxes under SDCL chapter 10-52 may
layer on top (combined rates typically 4.2%-6.2%). South Dakota
has NO sales-tax holiday in any year.

Notable peer-state difference: groceries are TAXABLE at the full
state rate per SDCL section 10-45-2.4 -- a regression test
explicitly guards this so a contributor copy-pasting from a
peer SST state (IA, KS, ND, NE, etc., all of which exempt
groceries) doesn't accidentally flip the rule.

South Dakota is the plaintiff in *South Dakota v. Wayfair, Inc.*,
138 S. Ct. 2080 (2018) -- the case that established the modern
economic-nexus standard for state sales-tax collection.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule
from opensalestax.states.south_dakota import (
    SOUTH_DAKOTA,
    SOUTH_DAKOTA_GENERAL_RATE_PCT,
    SOUTH_DAKOTA_RATE_SUNSET_ISO,
    SouthDakota,
)


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_south_dakota_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 46, tier 1."""
    assert SOUTH_DAKOTA.state_abbrev == "SD"
    assert SOUTH_DAKOTA.state_name == "South Dakota"
    assert SOUTH_DAKOTA.state_fips == "46"
    assert SOUTH_DAKOTA.sst_member is True
    assert SOUTH_DAKOTA.has_sales_tax is True
    assert SOUTH_DAKOTA.tier == 1


def test_south_dakota_satisfies_protocol() -> None:
    """South Dakota subclasses ``SstStateModule`` and structurally
    implements the StateModule Protocol via inheritance + a few
    attribute overrides.
    """
    assert isinstance(SOUTH_DAKOTA, StateModule)
    assert isinstance(SouthDakota(), StateModule)
    assert isinstance(SOUTH_DAKOTA, SstStateModule)


def test_south_dakota_is_registered() -> None:
    """The registry returns the South Dakota instance under 'SD'."""
    module = get_state_module("SD")
    assert module is SOUTH_DAKOTA
    # Promotion sanity check: not the generic tier-2 default any more.
    assert module is not None
    assert module.tier == 1


def test_south_dakota_lookup_is_case_insensitive() -> None:
    """The registry lookup accepts mixed/lowercase forms."""
    assert get_state_module("sd") is SOUTH_DAKOTA
    assert get_state_module("Sd") is SOUTH_DAKOTA


def test_south_dakota_not_in_tier2_classes() -> None:
    """Regression: South Dakota must NOT appear in TIER_2_CLASSES or
    TIER_2_STATES after promotion. A double-registration would
    silently re-overwrite the tier-1 instance.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "SD" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "SD" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in SDCL chapter 10-45
        ("groceries", True),  # SDCL 10-45-2.4 -- SD fully taxes groceries
        ("prescription_drugs", False),  # SDCL 10-45-14
        ("prepared_food", True),  # general TPP per SDCL 10-45-2
        ("digital_goods", True),  # SDCL 10-45-1.1 (SB 207, 2008)
        ("general", True),  # SDCL 10-45-2
    ],
)
def test_south_dakota_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct
    rule with a non-empty notes field carrying the citation.
    """
    rule = SOUTH_DAKOTA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present
    # Every rule must cite SDCL so a future maintainer can
    # re-verify against the statute.
    assert "SDCL" in (rule.notes or "")


def test_south_dakota_groceries_are_taxable_regression() -> None:
    """REGRESSION: SD is one of the few states that fully taxes
    groceries. SDCL section 10-45-2.4 expressly subjects food to
    the full state sales tax. A contributor copy-pasting from a
    peer SST state (IA, KS, ND, NE -- all of which EXEMPT groceries)
    could easily flip this to is_taxable=False; this test exists
    explicitly to catch that regression.
    """
    rule = SOUTH_DAKOTA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True, (
        "SD fully taxes groceries per SDCL section 10-45-2.4 -- "
        "if this test fails, someone has flipped the rule. Verify "
        "against the SD Department of Revenue (https://dor.sd.gov/) "
        "before changing."
    )
    notes = rule.notes or ""
    assert "10-45-2.4" in notes
    # Reference to the failed 2024 ballot measure is helpful context
    # for the next maintainer (and a defense against silent rule
    # reversal if grocery-tax reform passes in a later year).
    assert "Initiated Measure 28" in notes or "2024" in notes


def test_south_dakota_unknown_category_returns_none() -> None:
    """Unknown category -> None so the engine falls back to the
    conservative 'taxable at default rate' behavior.
    """
    assert SOUTH_DAKOTA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_south_dakota_prescription_drugs_cite_section_14() -> None:
    """Prescription-drug exemption must cite SDCL section 10-45-14."""
    rule = SOUTH_DAKOTA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "10-45-14" in (rule.notes or "")


def test_south_dakota_general_rule_cites_imposition_statute() -> None:
    """The general-TPP rule must cite the imposition statute SDCL section 10-45-2
    AND the rate-reduction bill (HB 1137 of 2023) AND the 2027-06-30 sunset.
    """
    rule = SOUTH_DAKOTA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "10-45-2" in notes
    # The rate-reduction bill citation is mandatory so the rule is
    # auditable against future legislative changes.
    assert "1137" in notes  # HB 1137 of 2023
    # The statutory sunset is the single most important thing to
    # document for this state -- if it disappears from the notes,
    # the next maintainer might miss the 2027 reversion.
    assert "2027" in notes


def test_south_dakota_digital_goods_cite_2008_amendment() -> None:
    """Digital-goods rule must reference the 2008 SB 207 expansion
    that brought specified digital products into SDCL chapter 10-45.
    Without that citation a future maintainer cannot date the rule
    against subsequent legislative changes.
    """
    rule = SOUTH_DAKOTA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "10-45-1.1" in notes
    assert "207" in notes  # SB 207 of 2008
    assert "2008" in notes


def test_south_dakota_clothing_documents_no_holiday() -> None:
    """The clothing rule must document that SD has no back-to-school
    sales-tax holiday so a future contributor doesn't accidentally
    add one when copy-pasting from a state that does (e.g. Iowa).
    """
    rule = SOUTH_DAKOTA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    notes_lower = (rule.notes or "").lower()
    assert "no" in notes_lower and "holiday" in notes_lower


# ---------------------------------------------------------------------------
# Holidays + special cases (no-holidays regression)
# ---------------------------------------------------------------------------
def test_south_dakota_holidays_for_all_years_returns_empty() -> None:
    """Regression: South Dakota has NO sales-tax holidays in any year.

    Confirmed against the South Dakota Department of Revenue
    (https://dor.sd.gov/) and a search of SDCL chapter 10-45 on
    2026-05-03 -- no recurring sales-tax holiday exists in SD law.
    This test exists specifically to catch any future regression
    where a contributor accidentally adds a holiday window.
    """
    for year in range(2024, 2031):
        holidays = list(SOUTH_DAKOTA.holidays_for(year))
        assert holidays == [], f"South Dakota should have no holidays in {year}"


def test_south_dakota_special_cases_empty() -> None:
    """Phase 7 ships no SpecialCase rows for South Dakota. The
    municipal local-tax landscape (SDCL chapter 10-52 gross receipts
    + 10-52A special tax + tribal taxes) flows through the
    inherited SST parser as ordinary rate rows; nothing in the
    engine consumes special cases yet.
    """
    cases = list(SOUTH_DAKOTA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Documentation regressions
# ---------------------------------------------------------------------------
def test_south_dakota_docstring_documents_wayfair() -> None:
    """SD is the plaintiff in *South Dakota v. Wayfair, Inc.* (2018);
    the docstring must reference Wayfair so the historical context
    isn't lost. The brief explicitly required this.
    """
    import opensalestax.states.south_dakota as sd_module

    docstring = sd_module.__doc__ or ""
    assert "Wayfair" in docstring
    assert "138 S. Ct. 2080" in docstring or "2018" in docstring


def test_south_dakota_docstring_documents_rate_sunset() -> None:
    """The docstring must explicitly document the 2027-06-30
    statutory sunset on the 4.2% rate so a future maintainer
    doesn't have to re-derive that fact from scratch. This is the
    single most important caveat about the SD module.
    """
    import opensalestax.states.south_dakota as sd_module

    docstring = sd_module.__doc__ or ""
    assert "2027-06-30" in docstring
    assert "sunset" in docstring.lower()
    # The reversion target rate (4.5%) must also be documented.
    assert "4.5%" in docstring


def test_south_dakota_docstring_documents_groceries_taxed() -> None:
    """The docstring must explicitly call out that groceries are
    fully taxed in SD -- a notable peer-state difference that
    integrators porting code from other SST states will trip on.
    """
    import opensalestax.states.south_dakota as sd_module

    docstring = sd_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must mention groceries + that they are taxable.
    assert "groceries" in docstring_lower or "food and food ingredients" in docstring_lower
    assert "10-45-2.4" in docstring  # the imposing statute


def test_south_dakota_docstring_documents_local_tax_landscape() -> None:
    """SD allows local-option sales taxes (unlike IN / KY / MI); the
    docstring must explicitly document the municipal taxes under
    SDCL chapter 10-52 so an integrator doesn't assume the 4.2%
    state rate is the entire combined rate.
    """
    import opensalestax.states.south_dakota as sd_module

    docstring = sd_module.__doc__ or ""
    docstring_lower = docstring.lower()
    assert "municipal" in docstring_lower
    assert "10-52" in docstring
    # Combined-rate ceiling should be documented.
    assert "6.2%" in docstring


# ---------------------------------------------------------------------------
# Documentary rate constants
# ---------------------------------------------------------------------------
def test_south_dakota_general_rate_constant_is_4_2_pct() -> None:
    """Documentary constant: South Dakota's general state rate is 4.2%.
    The actual rate that flows into the engine comes from the SST
    rate file via the inherited parser, but this constant gives
    grep-ability and a stable test fixture.
    """
    assert Decimal("4.200") == SOUTH_DAKOTA_GENERAL_RATE_PCT


def test_south_dakota_rate_sunset_constant_is_2027_06_30() -> None:
    """Documentary constant: SD's 4.2% rate sunsets on 2027-06-30
    per HB 1137 of the 98th SD Legislative Session (2023). If the
    legislature acts to extend, replace, or further reduce the rate
    before the sunset, this constant (and the module docstring) must
    be updated.
    """
    assert SOUTH_DAKOTA_RATE_SUNSET_ISO == "2027-06-30"


# ---------------------------------------------------------------------------
# Inherited SST parser smoke checks
# ---------------------------------------------------------------------------
def test_south_dakota_parse_rates_callable() -> None:
    """parse_rates is inherited from ``SstStateModule`` and callable."""
    method = SOUTH_DAKOTA.parse_rates
    assert callable(method)


def test_south_dakota_parse_boundaries_callable() -> None:
    """parse_boundaries is inherited from ``SstStateModule`` and is
    callable; we don't ship an SD fixture in this PR. The inherited
    parser yields nothing when given an empty source.
    """
    method = SOUTH_DAKOTA.parse_boundaries
    assert callable(method)


def test_south_dakota_inherits_default_jurisdiction_types() -> None:
    """SD DOES have local sales taxes (municipalities + tribal), so
    it uses the default SST jurisdiction-type code mapping inherited
    from ``_sst_base`` (state 45, county 00, city 01, district 63).
    Unlike Kentucky / Indiana / Michigan, this state should NOT
    restrict the mapping to state-only.
    """
    jt = SOUTH_DAKOTA.jurisdiction_types
    assert "45" in jt and jt["45"] == "state"
    assert "00" in jt and jt["00"] == "county"
    assert "01" in jt and jt["01"] == "city"
