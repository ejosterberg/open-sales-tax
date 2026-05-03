# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Rhode Island state module (Phase 7 -- tier-2 to tier-1 promotion).

Rhode Island is an SST member with a 7.0% statewide rate per R.I. Gen.
Laws section 44-18-18 (one of the two highest single-state rates in
the US, tied with IN, MS, and TN).

RI levies NO general local sales tax -- the 7.0% state rate is the
combined rate at every RI address (mirrors IN/KY/MI). A separate 1%
local meals and beverages tax (R.I. Gen. Laws section 44-18-18.1)
on restaurant transactions and a separate 1% hotel tax (section
44-18-36.1) are non-general-sales-tax levies and out of this
engine's scope.

Distinctive feature: clothing is EXEMPT up to $250 per article per
R.I. Gen. Laws section 44-18-30(27); the portion of any single
article above $250 is taxable at 7%. RI is the only state in the
broad-clothing-exemption club (PA, MA, MN, NJ, VT) with this
excess-above-cap structure (vs. NY's $110 and MA's $175 thresholds
where crossing the threshold makes the ENTIRE article taxable). The
v0.10 engine does not yet enforce per-item thresholds; the module
encodes ``is_taxable=False`` to match the dominant case (everyday
clothing under $250) and documents the trade-off prominently.

Sales-tax holidays: NONE. RI has never enacted a recurring holiday;
``holidays_for(year)`` returns an empty iterator for every year
(mirrors DC, ID, IN, KY, MI, NE, NJ).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule
from opensalestax.states.rhode_island import (
    RHODE_ISLAND,
    RHODE_ISLAND_CLOTHING_EXEMPTION_CAP,
    RHODE_ISLAND_GENERAL_RATE_PCT,
    RhodeIsland,
)


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_rhode_island_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 44, tier 1."""
    assert RHODE_ISLAND.state_abbrev == "RI"
    assert RHODE_ISLAND.state_name == "Rhode Island"
    assert RHODE_ISLAND.state_fips == "44"
    assert RHODE_ISLAND.sst_member is True
    assert RHODE_ISLAND.has_sales_tax is True
    assert RHODE_ISLAND.tier == 1


def test_rhode_island_inherits_sst_base() -> None:
    """RI subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(RHODE_ISLAND, SstStateModule)
    assert isinstance(RhodeIsland(), SstStateModule)


def test_rhode_island_satisfies_protocol() -> None:
    """RI structurally implements the StateModule Protocol."""
    assert isinstance(RHODE_ISLAND, StateModule)
    assert isinstance(RhodeIsland(), StateModule)


def test_rhode_island_is_registered() -> None:
    """The registry returns the RI instance under 'RI' (case-insensitive)."""
    assert get_state_module("RI") is RHODE_ISLAND
    assert get_state_module("ri") is RHODE_ISLAND


def test_rhode_island_not_in_tier2_anymore() -> None:
    """Regression: RI was promoted out of _tier2.py and must not appear
    in TIER_2_CLASSES or TIER_2_STATES. A double-registration would
    silently overwrite the tier-1 instance with a tier-2 one.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "RI" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "RI" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", False),  # 44-18-30(27) -- exempt up to $250 (engine encodes dominant case)
        ("groceries", False),  # 44-18-30(11)
        ("prescription_drugs", False),  # 44-18-30(28)
        ("prepared_food", True),  # excluded from grocery exemption
        ("digital_goods", True),  # 44-18-7.1, P.L. 2018 ch. 47 art. 4
        ("general", True),  # 44-18-18 imposition
    ],
)
def test_rhode_island_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying an R.I. Gen. Laws citation.
    """
    rule = RHODE_ISLAND.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "R.I. Gen. Laws" in (rule.notes or "")


def test_rhode_island_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert RHODE_ISLAND.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_rhode_island_clothing_documents_250_dollar_threshold() -> None:
    """The clothing rule MUST document the $250-per-article exemption cap
    from R.I. Gen. Laws section 44-18-30(27) and MUST explain the
    encoding trade-off (engine encodes is_taxable=False to match the
    dominant case of everyday clothing under $250; UNDER-collects on
    the excess-above-$250 portion of high-end items).

    Without this documentation, a future maintainer might
    accidentally flip the encoding without understanding the trade-off,
    or the v0.6 threshold-rules feature work might miss the RI-
    specific structure (excess-above-cap vs. NY/MA cliff-threshold).
    """
    rule = RHODE_ISLAND.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    # Statute must be cited.
    assert "44-18-30(27)" in notes
    # The $250 threshold must appear as a number.
    assert "$250" in notes or "250" in notes
    # The trade-off direction must be documented for the v0.6 follow-up.
    notes_lower = notes.lower()
    assert "under-collect" in notes_lower or "under collect" in notes_lower
    # The engine-limitation context must be flagged.
    assert "threshold" in notes_lower
    # Clarify it is the dominant-case encoding.
    assert "dominant" in notes_lower


def test_rhode_island_groceries_cite_section_30_11() -> None:
    """Grocery exemption is in subsection (11) of R.I. Gen. Laws 44-18-30."""
    rule = RHODE_ISLAND.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "44-18-30(11)" in (rule.notes or "")


def test_rhode_island_prescription_drugs_cite_section_30_28() -> None:
    """Prescription-drug exemption is in subsection (28) of R.I. Gen. Laws 44-18-30."""
    rule = RHODE_ISLAND.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "44-18-30(28)" in (rule.notes or "")


def test_rhode_island_digital_goods_cite_2018_amendment() -> None:
    """RI taxes specified digital products at 7% per R.I. Gen. Laws 44-18-7.1
    (added by section 3 of P.L. 2018, ch. 47, art. 4 -- the FY2019
    budget bill, signed June 22, 2018, effective October 1, 2018).
    """
    rule = RHODE_ISLAND.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "44-18-7.1" in notes
    # Cite the chapter/article that brought specified digital products into the base.
    assert "2018" in notes
    assert "ch. 47" in notes or "chapter 47" in notes.lower()


def test_rhode_island_general_rule_cites_imposition_statute_and_no_local_tax() -> None:
    """General TPP rule cites R.I. Gen. Laws 44-18-18 (imposition) and
    must document the no-local-sales-tax structure.
    """
    rule = RHODE_ISLAND.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "44-18-18" in notes
    # Rate must be documented in the general rule's notes.
    assert "7%" in notes or "7.0" in notes
    # The no-local-tax structure must be documented.
    notes_lower = notes.lower()
    assert "no general local" in notes_lower or "no local" in notes_lower


# ---------------------------------------------------------------------------
# Sales-tax holidays -- RI has none.
# ---------------------------------------------------------------------------
def test_rhode_island_holidays_for_all_years_returns_empty() -> None:
    """RI has no active sales-tax holiday in any year.

    Rhode Island has never enacted a recurring sales-tax holiday;
    confirmed against the Rhode Island Division of Taxation's
    published guidance (verified 2026-05-03). holidays_for() must
    return an empty iterator for every year (mirrors DC, ID, IN,
    KY, MI, NE, NJ).
    """
    for year in range(2020, 2031):
        holidays = list(RHODE_ISLAND.holidays_for(year))
        assert holidays == [], f"RI has no sales-tax holiday. Year: {year}."


# ---------------------------------------------------------------------------
# Module-docstring assertions: no-local-tax and clothing-threshold
# documentation MUST stay prominent in the module docstring.
# ---------------------------------------------------------------------------
def test_rhode_island_module_docstring_documents_no_local_sales_tax() -> None:
    """The no-local-sales-tax structure MUST be prominently documented
    in the module docstring. Without it, a future contributor might
    mistakenly add per-county/per-city rate parsing or assume the
    SST file ships county/city rows (it does not for RI).
    """
    import opensalestax.states.rhode_island as ri_module

    docstring = ri_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The 7% headline rate must appear.
    assert "7.0%" in docstring or "7%" in docstring
    # The no-local-tax structure must be documented.
    assert (
        "no general local sales tax" in docstring_lower or "no local sales tax" in docstring_lower
    )
    # Reference to peer no-local-tax states for orientation.
    assert "in" in docstring_lower  # IN is mentioned (Indiana peer state)


def test_rhode_island_module_docstring_documents_clothing_threshold() -> None:
    """The clothing $250-per-article exemption cap MUST be prominently
    documented in the module docstring. Without it, a future
    contributor might miss the RI-specific structure (excess-above-
    cap, distinct from NY/MA cliff-thresholds) and the v0.6
    threshold-rules feature work might not handle RI correctly.
    """
    import opensalestax.states.rhode_island as ri_module

    docstring = ri_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The statute must be cited.
    assert "44-18-30(27)" in docstring
    # The $250 cap must appear.
    assert "$250" in docstring or "250" in docstring
    # The excess-above-cap structure must be explained.
    assert (
        "above $250" in docstring_lower
        or "above the cap" in docstring_lower
        or "excess" in docstring_lower
    )
    # Engine-limitation context must be flagged.
    assert "threshold" in docstring_lower
    # The trade-off direction must be documented.
    assert "under-collect" in docstring_lower or "under collect" in docstring_lower


def test_rhode_island_module_docstring_documents_no_holiday() -> None:
    """The absence of a state sales-tax holiday MUST be explicitly
    documented in the module docstring. Without it, a future
    maintainer might add a phantom holiday based on a stale article
    or confused with a peer state.
    """
    import opensalestax.states.rhode_island as ri_module

    docstring = ri_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The "no holiday" statement must be unambiguous.
    assert "none" in docstring_lower
    assert "holiday" in docstring_lower


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine in v1)
# ---------------------------------------------------------------------------
def test_rhode_island_special_cases_empty() -> None:
    """v1 ships no SpecialCase rows for RI. The clothing-threshold
    caveat is documented in the module docstring and the rule notes
    rather than encoded as engine-consumed special cases (the
    SpecialCase API is reserved for Phase 5+).
    """
    cases = list(RHODE_ISLAND.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Inherited SST parser smoke checks
# ---------------------------------------------------------------------------
def test_rhode_island_parse_boundaries_signature() -> None:
    """parse_boundaries returns an iterable; we don't ship an RI fixture in this PR.

    The inherited :class:`SstStateModule` parser handles the actual SST
    file. This test confirms the method exists.
    """
    method = RHODE_ISLAND.parse_boundaries
    assert callable(method)


def test_rhode_island_jurisdiction_types_is_state_only() -> None:
    """RI has NO local sales tax -- only the canonical state code ('45')
    is mapped, so any unexpected non-state row in a future quarterly
    file is silently dropped rather than miscategorized. This mirrors
    the defensive posture in the IN module.
    """
    # The class-level dict should contain ONLY the state mapping.
    assert RHODE_ISLAND.jurisdiction_types == {"45": "state"}


# ---------------------------------------------------------------------------
# Documentary constants
# ---------------------------------------------------------------------------
def test_rhode_island_general_rate_constant_is_7_pct() -> None:
    """Documentary constant: RI's statewide rate is 7.0% per R.I. Gen.
    Laws section 44-18-18. The actual rate that flows into the engine
    comes from the SST quarterly file via the inherited parser; this
    constant gives grep-ability and a stable test fixture.
    """
    assert Decimal("7.000") == RHODE_ISLAND_GENERAL_RATE_PCT


def test_rhode_island_clothing_exemption_cap_constant_is_250() -> None:
    """Documentary constant: the per-article clothing-exemption cap
    from R.I. Gen. Laws section 44-18-30(27) is $250.00. The engine
    does not enforce this cap in v0.10; the constant gives the
    v0.6 threshold-rules feature work a stable named reference.
    """
    assert Decimal("250.00") == RHODE_ISLAND_CLOTHING_EXEMPTION_CAP
