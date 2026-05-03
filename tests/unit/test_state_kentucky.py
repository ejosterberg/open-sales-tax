# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Kentucky state module (Phase 7 -- tier-2 to tier-1 promotion).

Kentucky is an SST member with a 6.0% state rate per KRS 139.200
and NO local sales tax. The combined rate at every Kentucky
address is exactly 6.0% (mirroring Indiana's no-local-sales-tax
landscape).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.kentucky import KENTUCKY, KENTUCKY_GENERAL_RATE_PCT, Kentucky
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_kentucky_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 21, tier 1."""
    assert KENTUCKY.state_abbrev == "KY"
    assert KENTUCKY.state_name == "Kentucky"
    assert KENTUCKY.state_fips == "21"
    assert KENTUCKY.sst_member is True
    assert KENTUCKY.has_sales_tax is True
    assert KENTUCKY.tier == 1


def test_kentucky_satisfies_protocol() -> None:
    """Kentucky subclasses ``SstStateModule`` and structurally implements the
    Protocol via inheritance + a few attribute overrides.
    """
    assert isinstance(KENTUCKY, StateModule)
    assert isinstance(Kentucky(), StateModule)
    assert isinstance(KENTUCKY, SstStateModule)


def test_kentucky_is_registered() -> None:
    """The registry returns the Kentucky instance under 'KY'."""
    module = get_state_module("KY")
    assert module is KENTUCKY
    # Promotion sanity check: not the generic tier-2 default any more.
    assert module is not None
    assert module.tier == 1


def test_kentucky_not_in_tier2_classes() -> None:
    """Regression: Kentucky must NOT appear in TIER_2_CLASSES or
    TIER_2_STATES after promotion. A double-registration would
    silently re-overwrite the tier-1 instance.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "KY" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "KY" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in Chapter 139
        ("groceries", False),  # KRS 139.485
        ("prescription_drugs", False),  # KRS 139.472
        ("prepared_food", True),  # excluded from grocery exemption
        ("digital_goods", True),  # KRS 139.200(2) (SB 6 / 2018 + HB 8 / 2022)
        ("general", True),  # KRS 139.200
    ],
)
def test_kentucky_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying the citation.
    """
    rule = KENTUCKY.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_kentucky_unknown_category_returns_none() -> None:
    """Unknown category -> None so the engine falls back to the
    conservative 'taxable at default rate' behavior.
    """
    assert KENTUCKY.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_kentucky_overrides_default_tier2_grocery_rule() -> None:
    """The default tier-2 matrix and Kentucky's matrix both exempt
    groceries, but Kentucky's notes must cite the controlling
    statute (KRS 139.485) -- otherwise we have no evidence that
    the rule was researched rather than inherited blindly.
    """
    rule = KENTUCKY.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "139.485" in (rule.notes or "")


def test_kentucky_prescription_drugs_cite_139_472() -> None:
    """Prescription-drug exemption must cite the controlling statute."""
    rule = KENTUCKY.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert "139.472" in (rule.notes or "")


def test_kentucky_general_rule_cites_139_200() -> None:
    """The general-TPP rule must cite the imposition statute."""
    rule = KENTUCKY.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert "139.200" in (rule.notes or "")


def test_kentucky_digital_goods_cite_sb6_and_hb8() -> None:
    """Digital-goods rule must reference both the 2018 SB 6 expansion
    of digital property treatment and the 2022 HB 8 expansion that
    brought ~30 service categories into the sales-tax base effective
    January 1, 2023. Without both citations a future maintainer can
    not date the rule against subsequent legislative changes.
    """
    rule = KENTUCKY.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "139.200" in notes
    # Both bills must be cited so the rule's evolution is auditable.
    assert "Senate Bill 6" in notes or "SB 6" in notes
    assert "House Bill 8" in notes or "HB 8" in notes
    # The HB 8 effective date is the load-bearing fact for callers
    # determining whether SaaS / services pre-2023 were taxable.
    assert "2023" in notes


# ---------------------------------------------------------------------------
# Holidays + special cases (no-holidays regression)
# ---------------------------------------------------------------------------
def test_kentucky_holidays_for_all_years_returns_empty() -> None:
    """Regression: Kentucky has NO sales-tax holidays in any year.

    Confirmed against the Kentucky Department of Revenue 2026-05-03.
    This test exists specifically to catch any future regression
    where a contributor accidentally adds a holiday window (e.g.
    by copy-pasting from a state that does have one).
    """
    for year in range(2024, 2031):
        holidays = list(KENTUCKY.holidays_for(year))
        assert holidays == [], f"Kentucky should have no holidays in {year}"


def test_kentucky_special_cases_empty() -> None:
    """Phase 7 ships no SpecialCase rows for Kentucky. The only
    quirks worth flagging (narrow local meals / lodging / motor
    vehicle rental taxes in select municipalities) are documented
    in the module docstring rather than encoded as engine-consumed
    special cases.
    """
    cases = list(KENTUCKY.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# No-local-tax landscape (the headline KY-vs-peer-states distinction)
# ---------------------------------------------------------------------------
def test_kentucky_module_docstring_documents_no_local_sales_tax() -> None:
    """The 'no local sales tax' caveat MUST appear in the module
    docstring -- it's the most important piece of context an
    integrator needs to understand Kentucky's combined-rate model.
    Removing or weakening this language without a deliberate
    update is a documentation regression.
    """
    import opensalestax.states.kentucky as kentucky_module

    docstring = kentucky_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must explicitly state that KY has NO local sales tax somewhere
    # in the docstring (case-insensitive).
    assert "no local sales tax" in docstring_lower, (
        "Kentucky module docstring must explicitly document the "
        "no-local-sales-tax landscape (notable difference from "
        "peer SST states)."
    )
    # And it must call out 6% as the entire combined rate.
    assert "6%" in docstring or "6.0%" in docstring


def test_kentucky_jurisdiction_types_only_maps_state() -> None:
    """Defensive: Kentucky's jurisdiction-type dict accepts ONLY the
    state-level code. This guarantees that any unexpected non-state
    row in a future SST quarterly file is silently dropped rather
    than miscategorized as a sub-state authority Kentucky doesn't
    have. Mirrors Indiana's defensive mapping.
    """
    assert KENTUCKY.jurisdiction_types == {"45": "state"}
    assert "00" not in KENTUCKY.jurisdiction_types  # county
    assert "01" not in KENTUCKY.jurisdiction_types  # city
    assert "63" not in KENTUCKY.jurisdiction_types  # district


def test_kentucky_general_rate_constant_is_6_pct() -> None:
    """Documentary constant: Kentucky's general state rate is 6.0%.
    The actual rate that flows into the engine comes from the SST
    rate file via the inherited parser, but this constant gives
    grep-ability and a stable test fixture.
    """
    assert Decimal("6.000") == KENTUCKY_GENERAL_RATE_PCT
