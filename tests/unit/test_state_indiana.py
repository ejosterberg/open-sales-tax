# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Indiana state module (Phase 7 -- tier-2 to tier-1 promotion).

Indiana is an SST member with the highest single-state sales-tax
rate in the country (7.0% per Ind. Code section 6-2.5-2-2(a)) and
NO local sales tax. The combined rate at every Indiana address is
exactly 7.0%.
"""

from __future__ import annotations

import datetime as dt

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.indiana import INDIANA, INDIANA_GENERAL_RATE_PCT, Indiana
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_indiana_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 18, tier 1."""
    assert INDIANA.state_abbrev == "IN"
    assert INDIANA.state_name == "Indiana"
    assert INDIANA.state_fips == "18"
    assert INDIANA.sst_member is True
    assert INDIANA.has_sales_tax is True
    assert INDIANA.tier == 1


def test_indiana_satisfies_protocol() -> None:
    """Indiana subclasses ``SstStateModule`` and structurally implements the
    Protocol via inheritance + a few attribute overrides.
    """
    assert isinstance(INDIANA, StateModule)
    assert isinstance(Indiana(), StateModule)
    assert isinstance(INDIANA, SstStateModule)


def test_indiana_is_registered() -> None:
    """The registry returns the Indiana instance under 'IN'."""
    module = get_state_module("IN")
    assert module is INDIANA
    # Promotion sanity check: not the generic tier-2 default any more.
    assert module is not None
    assert module.tier == 1


def test_indiana_not_in_tier2_classes() -> None:
    """Regression: Indiana must NOT appear in TIER_2_CLASSES or
    TIER_2_STATES after promotion. A double-registration would
    silently re-overwrite the tier-1 instance.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "IN" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "IN" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in Article 2.5
        ("groceries", False),  # Ind. Code section 6-2.5-5-20
        ("prescription_drugs", False),  # Ind. Code section 6-2.5-5-19
        ("prepared_food", True),  # excluded from grocery exemption
        ("digital_goods", True),  # Ind. Code section 6-2.5-4-16.4 (eff. 2018)
        ("general", True),  # Ind. Code section 6-2.5-2-1 / 6-2.5-2-2(a)
    ],
)
def test_indiana_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying the citation.
    """
    rule = INDIANA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_indiana_unknown_category_returns_none() -> None:
    """Unknown category -> None so the engine falls back to the
    conservative 'taxable at default rate' behavior.
    """
    assert INDIANA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_indiana_overrides_default_tier2_grocery_rule() -> None:
    """The default tier-2 matrix and Indiana's matrix both exempt
    groceries, but Indiana's notes must cite the controlling
    statute (section 6-2.5-5-20) -- otherwise we have no evidence
    that the rule was researched rather than inherited blindly.
    """
    rule = INDIANA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "6-2.5-5-20" in (rule.notes or "")


def test_indiana_prescription_drugs_cite_6_2_5_5_19() -> None:
    """Prescription-drug exemption must cite the controlling statute."""
    rule = INDIANA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert "6-2.5-5-19" in (rule.notes or "")


def test_indiana_digital_goods_cite_6_2_5_4_16_4_and_call_out_saas() -> None:
    """Digital-goods rule encodes the dominant taxable case (specified
    digital products with permanent right of use) and must document
    the SaaS / remotely-accessed-software exclusion under DOR
    Information Bulletin #8.
    """
    rule = INDIANA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "6-2.5-4-16.4" in notes
    notes_lower = notes.lower()
    assert "saas" in notes_lower or "remotely accessed" in notes_lower
    assert "permanent right" in notes_lower
    # The Information Bulletin is the published DOR position on the
    # SaaS distinction; the rule must cite it so a future maintainer
    # can re-verify when the bulletin is revised.
    assert "Information Bulletin #8" in notes


# ---------------------------------------------------------------------------
# Holidays + special cases
# ---------------------------------------------------------------------------
def test_indiana_holidays_for_all_years_returns_empty() -> None:
    """Regression: Indiana has NO sales-tax holidays in any year.

    Confirmed against the Indiana Department of Revenue 2026-05-03.
    This test exists specifically to catch any future regression
    where a contributor accidentally adds a holiday window (e.g.
    by copy-pasting from a state that does have one).
    """
    for year in range(2024, 2031):
        holidays = list(INDIANA.holidays_for(year))
        assert holidays == [], f"Indiana should have no holidays in {year}"


def test_indiana_special_cases_empty() -> None:
    """Phase 7 ships no SpecialCase rows for Indiana. The only quirks
    worth flagging (narrow local food-and-beverage / innkeeper taxes
    in select municipalities) are documented in the module docstring
    rather than encoded as engine-consumed special cases.
    """
    cases = list(INDIANA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# No-local-tax landscape (the headline IN-vs-peer-states distinction)
# ---------------------------------------------------------------------------
def test_indiana_module_docstring_documents_no_local_sales_tax() -> None:
    """The 'no local sales tax' caveat MUST appear in the module
    docstring -- it's the most important piece of context an
    integrator needs to understand Indiana's combined-rate model.
    Removing or weakening this language without a deliberate
    update is a documentation regression.
    """
    import opensalestax.states.indiana as indiana_module

    docstring = indiana_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must explicitly state that IN has NO local sales tax somewhere
    # in the docstring (case-insensitive, allow 'no local sales tax'
    # phrasing).
    assert "no local sales tax" in docstring_lower, (
        "Indiana module docstring must explicitly document the "
        "no-local-sales-tax landscape (notable difference from "
        "peer SST states)."
    )
    # And it must call out 7% as the entire combined rate.
    assert "7%" in docstring or "7.0%" in docstring


def test_indiana_jurisdiction_types_only_maps_state() -> None:
    """Defensive: Indiana's jurisdiction-type dict accepts ONLY the
    state-level code. This guarantees that any unexpected non-state
    row in a future SST quarterly file is silently dropped rather
    than miscategorized as a sub-state authority Indiana doesn't have.
    """
    assert INDIANA.jurisdiction_types == {"45": "state"}
    assert "00" not in INDIANA.jurisdiction_types  # county
    assert "01" not in INDIANA.jurisdiction_types  # city
    assert "63" not in INDIANA.jurisdiction_types  # district


def test_indiana_general_rate_constant_is_7_pct() -> None:
    """Documentary constant: Indiana's general state rate is 7.0%.
    The actual rate that flows into the engine comes from the SST
    rate file via the inherited parser, but this constant gives
    grep-ability and a stable test fixture.
    """
    from decimal import Decimal

    assert Decimal("7.000") == INDIANA_GENERAL_RATE_PCT
