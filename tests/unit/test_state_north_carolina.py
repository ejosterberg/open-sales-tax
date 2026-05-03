# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the North Carolina state module (tier-2 -> tier-1 promotion).

North Carolina is an SST member with a 4.75% statewide rate per
N.C.G.S. section 105-164.4(a). The defining quirk -- exercised by
the dedicated grocery test below -- is the unusual "food county
tax" structure: groceries are EXEMPT from the 4.75% state portion
under N.C.G.S. section 105-164.13B(a) but a uniform 2% LOCAL food
county tax under N.C.G.S. section 105-468.1 applies in every NC
county. The encoding uses ``rate_modifier=Decimal("2.000")`` to
mark the 2% effective statewide grocery rate (mirrors the MS / VA
/ MO rate_modifier pattern).

NC also REPEALED its annual back-to-school sales-tax holiday
effective 2014 by S.L. 2013-316; the dedicated holiday-regression
test exercises a wide window of years to confirm
``holidays_for(year)`` returns empty for every year.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.north_carolina import (
    NORTH_CAROLINA,
    NORTH_CAROLINA_FOOD_COUNTY_TAX_PCT,
    NORTH_CAROLINA_GENERAL_RATE_PCT,
    NorthCarolina,
)
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_north_carolina_metadata() -> None:
    assert NORTH_CAROLINA.state_abbrev == "NC"
    assert NORTH_CAROLINA.state_name == "North Carolina"
    assert NORTH_CAROLINA.sst_member is True  # NC is a Streamlined Sales Tax member
    assert NORTH_CAROLINA.has_sales_tax is True
    assert NORTH_CAROLINA.tier == 1
    assert NORTH_CAROLINA.state_fips == "37"


def test_north_carolina_inherits_sst_base() -> None:
    """NC subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(NORTH_CAROLINA, SstStateModule)
    assert isinstance(NorthCarolina(), SstStateModule)


def test_north_carolina_satisfies_protocol() -> None:
    assert isinstance(NORTH_CAROLINA, StateModule)
    assert isinstance(NorthCarolina(), StateModule)


def test_north_carolina_is_registered() -> None:
    assert get_state_module("NC") is NORTH_CAROLINA
    assert get_state_module("nc") is NORTH_CAROLINA  # case-insensitive


def test_north_carolina_is_not_in_tier2_anymore() -> None:
    """NC was promoted out of _tier2.py; it must no longer be registered as tier 2.

    Regression check: a double-registration would silently re-overwrite
    the tier-1 instance with the generic SstStateModule default.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "NC" not in {s.state_abbrev for s in TIER_2_STATES}
    assert "NC" not in {cls().state_abbrev for cls in TIER_2_CLASSES}


def test_north_carolina_general_rate_constant() -> None:
    """Documentary constant matches the statutory 4.75% state rate
    (N.C.G.S. section 105-164.4(a), raised from 4.5% to 4.75% by
    S.L. 2011-145 section 31A.1 effective 2011-10-15).
    """
    assert Decimal("4.750") == NORTH_CAROLINA_GENERAL_RATE_PCT


def test_north_carolina_food_county_tax_constant() -> None:
    """Documentary constant matches the uniform 2% local food county
    tax under N.C.G.S. section 105-468.1 (the "Article 39A food
    county tax"), which applies in every one of the 100 NC counties.
    This is the value encoded as the ``rate_modifier`` on the
    groceries TaxabilityRule.
    """
    assert Decimal("2.000") == NORTH_CAROLINA_FOOD_COUNTY_TAX_PCT


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # taxable year-round; back-to-school holiday repealed 2014
        ("groceries", True),  # state portion exempt; 2% local food county tax via rate_modifier
        ("prescription_drugs", False),  # exempt per N.C.G.S. 105-164.13(13)
        ("prepared_food", True),  # full combined rate; excluded from food exemption
        ("digital_goods", True),  # taxable per N.C.G.S. 105-164.4(a)(6b) (S.L. 2009-451)
        ("general", True),  # baseline TPP at 4.75% per N.C.G.S. 105-164.4(a)
    ],
)
def test_north_carolina_taxability(category: str, expected_taxable: bool) -> None:
    rule = NORTH_CAROLINA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "N.C.G.S." in (rule.notes or "")


def test_north_carolina_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert NORTH_CAROLINA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_north_carolina_clothing_notes_holiday_repeal() -> None:
    """Clothing rule documents the 2014 repeal of the back-to-school holiday
    by S.L. 2013-316. This is a key historical context an integrator may
    miss if researching from older sources.
    """
    rule = NORTH_CAROLINA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "105-164.4(a)" in notes
    assert "2013-316" in notes  # repealing session law
    notes_lower = notes.lower()
    assert "repeal" in notes_lower
    assert "holiday" in notes_lower


def test_north_carolina_groceries_use_rate_modifier_two_percent() -> None:
    """The signature NC quirk: state portion exempt under section 105-164.13B,
    but a uniform 2% LOCAL food county tax under section 105-468.1 applies
    in every county. Encoded as ``is_taxable=True`` with
    ``rate_modifier=Decimal("2.000")`` to capture the 2% effective statewide
    grocery rate. Mirrors the MS/VA/MO rate_modifier pattern; differs in that
    NC's state portion is fully ZERO and the 2% is a separate statutory
    LOCAL food tax rather than a reduced state rate.
    """
    rule = NORTH_CAROLINA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("2.000")
    notes = rule.notes or ""
    # Both controlling statutes must be cited.
    assert "105-164.13B" in notes  # the state-level food exemption
    assert "105-468.1" in notes  # the uniform 2% local food county tax
    # The unusual state-vs-local split must be documented.
    notes_lower = notes.lower()
    assert "exempt" in notes_lower  # state portion
    assert "2.00%" in notes or "2%" in notes  # the local food tax rate
    # Document that this is a LOCAL tax, not a reduced state rate.
    assert "local" in notes_lower
    assert "county" in notes_lower
    # Document the over-collection caveat until rate_modifier is wired through.
    assert "rate_modifier" in notes


def test_north_carolina_prescription_drugs_cite_subsection_13() -> None:
    """Prescription-drug exemption is in N.C.G.S. section 105-164.13(13)."""
    rule = NORTH_CAROLINA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "105-164.13(13)" in (rule.notes or "")


def test_north_carolina_digital_goods_cite_2009_451_and_subsection_6b() -> None:
    """NC taxes specified digital products at 4.75% per N.C.G.S. section
    105-164.4(a)(6b), added by S.L. 2009-451 effective 2010-01-01.
    """
    rule = NORTH_CAROLINA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "105-164.4(a)(6b)" in notes
    assert "2009-451" in notes  # the originating session law
    # Document the SaaS / custom-software exclusion documented in NC DOR
    # Sales and Use Tax Bulletin section 44-2.
    notes_lower = notes.lower()
    assert "saas" in notes_lower or "remotely accessed" in notes_lower or "custom" in notes_lower


def test_north_carolina_general_rule_cites_imposition_statute() -> None:
    """General TPP rule cites N.C.G.S. section 105-164.4(a) (the imposition
    statute) and the 2011-10-15 rate increase from 4.5% to 4.75% by
    S.L. 2011-145.
    """
    rule = NORTH_CAROLINA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "105-164.4(a)" in notes
    assert "4.75%" in notes
    assert "2011-145" in notes  # the rate-increase session law


def test_north_carolina_jurisdiction_types_include_district() -> None:
    """NC defaults to the canonical SST jurisdiction-type code mapping
    (45=state, 00=county, 01=city, 63=district). NC's actual rate-file
    codes were not empirically validated at promotion time -- the
    assumption is consistent with the MN/WI/IA empirical default and is
    documented in the module docstring as a follow-up validation task.
    """
    types = NorthCarolina().jurisdiction_types
    assert types["45"] == "state"
    assert types["00"] == "county"
    assert types["01"] == "city"
    assert types["63"] == "district"


# ---------------------------------------------------------------------------
# Inherited SST parser smoke check
# ---------------------------------------------------------------------------
def test_north_carolina_parse_boundaries_signature() -> None:
    """parse_boundaries returns a callable; we don't ship an NC fixture in this PR."""
    method = NORTH_CAROLINA.parse_boundaries
    assert callable(method)


# ---------------------------------------------------------------------------
# Sales tax holidays -- NC has NONE since 2014 (regression test exercises
# a wide window of years)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("year", [2014, 2015, 2020, 2024, 2025, 2026, 2027, 2028, 2030])
def test_north_carolina_has_no_holidays(year: int) -> None:
    """NC's annual back-to-school sales-tax holiday (former N.C.G.S.
    section 105-164.13C) was REPEALED effective 2014 by S.L. 2013-316
    section 4.1. NC also repealed its Energy Star holiday by the same
    act. The General Assembly has not re-enacted any sales-tax holiday
    since.

    This regression exercises a wide window of years (including 2014,
    the first year of repeal) to ensure the empty-iterator default
    from :class:`SstStateModule.holidays_for` is never accidentally
    overridden with a future-year extrapolation.
    """
    assert list(NORTH_CAROLINA.holidays_for(year)) == []


def test_north_carolina_module_docstring_documents_food_county_tax() -> None:
    """The unusual 'state-exempt-but-2%-local-food-county-tax' structure
    MUST appear in the module docstring -- it's the most important piece
    of context an integrator needs to understand NC's grocery taxation
    model. Removing or weakening this language without a deliberate
    update is a documentation regression.
    """
    import opensalestax.states.north_carolina as nc_module

    docstring = nc_module.__doc__ or ""
    # Both controlling statutes must be cited in the docstring.
    assert "105-164.13B" in docstring  # state-level food exemption
    assert "105-468.1" in docstring  # uniform 2% local food county tax
    docstring_lower = docstring.lower()
    # Must explicitly state the food-county-tax structure.
    assert "food county tax" in docstring_lower or "local food" in docstring_lower
    # Must call out 2% as the effective statewide grocery rate.
    assert "2.00%" in docstring or "2%" in docstring


def test_north_carolina_module_docstring_documents_holiday_repeal() -> None:
    """The 2014 repeal of NC's back-to-school holiday MUST appear in the
    module docstring so a future maintainer doesn't mistake the empty
    ``holidays_for`` default for an oversight.
    """
    import opensalestax.states.north_carolina as nc_module

    docstring = nc_module.__doc__ or ""
    assert "2013-316" in docstring  # repealing session law
    docstring_lower = docstring.lower()
    assert "repeal" in docstring_lower
    assert "2014" in docstring  # effective date of the repeal


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine)
# ---------------------------------------------------------------------------
def test_north_carolina_special_cases_empty() -> None:
    """Phase 7 ships no SpecialCase rows for NC. The narrow per-county
    prepared-food and beverage taxes (e.g., Mecklenburg County's 1%
    Convention Center prepared-food tax) are documented in the
    prepared_food rule's notes rather than encoded as engine-consumed
    special cases.
    """
    cases = list(NORTH_CAROLINA.special_cases())
    assert cases == []
