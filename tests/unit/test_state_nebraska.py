# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Nebraska state module (Phase 7 -- tier-2 to tier-1 promotion).

Nebraska is an SST member with a 5.5% statewide rate (Neb. Rev. Stat.
section 77-2701.02 effective 2002-10-01 by L.B. 1085) and local-option
sales tax up to 2% under section 77-27,142. Combined rates typically
fall in the 5.5%-7.5% range. Nebraska has NEVER enacted a sales-tax
holiday; ``holidays_for(year)`` returns the empty iterator for every
year (mirroring DC, ID, IN).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.nebraska import NEBRASKA, NEBRASKA_GENERAL_RATE_PCT, Nebraska
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_nebraska_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 31, tier 1."""
    assert NEBRASKA.state_abbrev == "NE"
    assert NEBRASKA.state_name == "Nebraska"
    assert NEBRASKA.state_fips == "31"
    assert NEBRASKA.sst_member is True
    assert NEBRASKA.has_sales_tax is True
    assert NEBRASKA.tier == 1


def test_nebraska_inherits_sst_base() -> None:
    """Nebraska subclasses ``SstStateModule`` so it inherits the SST quarterly parser."""
    assert isinstance(NEBRASKA, SstStateModule)
    assert isinstance(Nebraska(), SstStateModule)


def test_nebraska_satisfies_protocol() -> None:
    """Nebraska structurally implements the StateModule Protocol."""
    assert isinstance(NEBRASKA, StateModule)
    assert isinstance(Nebraska(), StateModule)


def test_nebraska_is_registered() -> None:
    """The registry returns the Nebraska instance under 'NE' (case-insensitive)."""
    assert get_state_module("NE") is NEBRASKA
    assert get_state_module("ne") is NEBRASKA
    # Promotion sanity check: not the generic tier-2 default any more.
    module = get_state_module("NE")
    assert module is not None
    assert module.tier == 1


def test_nebraska_not_in_tier2_classes() -> None:
    """Regression: Nebraska must NOT appear in TIER_2_CLASSES or
    TIER_2_STATES after promotion. A double-registration would
    silently re-overwrite the tier-1 instance.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "NE" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "NE" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption; taxable year-round
        ("groceries", False),  # Neb. Rev. Stat. section 77-2704.24
        ("prescription_drugs", False),  # Neb. Rev. Stat. section 77-2704.09
        ("prepared_food", True),  # excluded from grocery exemption
        ("digital_goods", True),  # Neb. Rev. Stat. section 77-2701.16(2)(e)
        ("general", True),  # Neb. Rev. Stat. section 77-2703 / 77-2701.02
    ],
)
def test_nebraska_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying the citation.
    """
    rule = NEBRASKA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present
    # Statutory citation must reference Nebraska Revised Statutes (Chapter 77).
    assert "Neb. Rev. Stat." in (rule.notes or "")


def test_nebraska_unknown_category_returns_none() -> None:
    """Unknown category -> None so the engine falls back to the
    conservative 'taxable at default rate' behavior.
    """
    assert NEBRASKA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_nebraska_groceries_cite_77_2704_24() -> None:
    """Grocery exemption must cite the controlling statute (77-2704.24)
    so a future maintainer can re-verify after legislative amendment.
    """
    rule = NEBRASKA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "77-2704.24" in (rule.notes or "")


def test_nebraska_prescription_drugs_cite_77_2704_09() -> None:
    """Prescription-drug exemption must cite the controlling statute (77-2704.09)."""
    rule = NEBRASKA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "77-2704.09" in (rule.notes or "")


def test_nebraska_digital_goods_cite_77_2701_16() -> None:
    """Digital-goods rule must cite section 77-2701.16 (the gross-receipts
    definition that brings specified digital products into the tax base)
    and document the SaaS / remotely-accessed-software exclusion per
    Nebraska DOR published guidance.
    """
    rule = NEBRASKA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "77-2701.16" in notes
    notes_lower = notes.lower()
    # SaaS distinction must be documented for the next maintainer
    assert "saas" in notes_lower or "remotely accessed" in notes_lower


def test_nebraska_clothing_rule_notes_no_holiday() -> None:
    """Clothing rule must explicitly state Nebraska has no sales-tax holiday
    -- this is a notable distinction from peer SST states (e.g. IA's August
    holiday under Iowa Code 423.3(68)) and is easy to forget.
    """
    rule = NEBRASKA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    notes_lower = (rule.notes or "").lower()
    assert "holiday" in notes_lower
    assert "never" in notes_lower or "no " in notes_lower


def test_nebraska_general_rule_cites_imposition_and_rate_statutes() -> None:
    """General TPP rule must cite both the imposition statute (77-2703)
    and the rate-setting statute (77-2701.02).
    """
    rule = NEBRASKA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "77-2703" in notes
    assert "77-2701.02" in notes


# ---------------------------------------------------------------------------
# Holidays + special cases
# ---------------------------------------------------------------------------
def test_nebraska_holidays_for_all_years_returns_empty() -> None:
    """Regression: Nebraska has NO sales-tax holidays in any year.

    Confirmed against the Nebraska Department of Revenue 2026-05-03 and
    the Sales Tax Handbook compendium. This test exists specifically to
    catch any future regression where a contributor accidentally adds a
    holiday window (e.g. by copy-pasting from a state that does have one).
    """
    for year in range(2024, 2031):
        holidays = list(NEBRASKA.holidays_for(year))
        assert holidays == [], f"Nebraska should have no holidays in {year}"


def test_nebraska_special_cases_empty() -> None:
    """Phase 7 ships no SpecialCase rows for Nebraska. The Good Life
    District 2.75% reduced state rate (LB 1317 of 2024) is a sub-state
    geographic overlay that flows through the SST quarterly rate file
    rather than a SpecialCase entry; documented in the module docstring.
    """
    cases = list(NEBRASKA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# SST jurisdiction-type code mapping + rate constant
# ---------------------------------------------------------------------------
def test_nebraska_inherits_default_jurisdiction_types() -> None:
    """Nebraska inherits the canonical MN/WI jurisdiction-type code mapping
    pending empirical validation against an actual NER<...>.csv file.
    Documented as an assumption in the module docstring.
    """
    # The default mapping covers state, county, city, district codes.
    assert NEBRASKA.jurisdiction_types.get("45") == "state"
    assert NEBRASKA.jurisdiction_types.get("00") == "county"
    assert NEBRASKA.jurisdiction_types.get("01") == "city"
    assert NEBRASKA.jurisdiction_types.get("63") == "district"


def test_nebraska_general_rate_constant_is_5_5_pct() -> None:
    """Documentary constant: Nebraska's general state rate is 5.5%.
    The actual rate that flows into the engine comes from the SST
    rate file via the inherited parser, but this constant gives
    grep-ability and a stable test fixture.
    """
    assert Decimal("5.500") == NEBRASKA_GENERAL_RATE_PCT


# ---------------------------------------------------------------------------
# Documentation regressions (Good Life Districts + no-holiday landscape)
# ---------------------------------------------------------------------------
def test_nebraska_module_docstring_documents_good_life_districts() -> None:
    """The Good Life District (LB 1317 of 2024) reduced 2.75% state rate
    MUST appear in the module docstring -- it's a notable rate exception
    that integrators need to know about, even though the rate flows
    through the SST file rather than the taxability matrix. Removing or
    weakening this language is a documentation regression.
    """
    import opensalestax.states.nebraska as nebraska_module

    docstring = nebraska_module.__doc__ or ""
    assert "Good Life District" in docstring
    assert "LB 1317" in docstring
    assert "2.75%" in docstring


def test_nebraska_module_docstring_documents_no_sales_tax_holiday() -> None:
    """The 'no sales-tax holiday' fact MUST appear in the module docstring
    so a future contributor doesn't add one based on outdated guidance
    or copy-paste from a peer SST state.
    """
    import opensalestax.states.nebraska as nebraska_module

    docstring = nebraska_module.__doc__ or ""
    docstring_lower = docstring.lower()
    assert "no sales-tax holiday" in docstring_lower or "never enacted" in docstring_lower
    assert "holidays_for" in docstring  # references the empty-iterator method
