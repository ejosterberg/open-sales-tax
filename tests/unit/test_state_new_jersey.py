# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the New Jersey state module (Phase 7 -- tier-2 to tier-1 promotion).

New Jersey is an SST member with a 6.625% statewide rate per N.J.S.A.
section 54:32B-3 (reduced from 7% in 2017 and to its current 6.625%
on January 1, 2018 by P.L. 2016, c. 57).

NJ levies NO general local (county/municipal) sales tax outside two
narrow exceptions that are intentionally NOT modeled in v1:

- Urban Enterprise Zones (UEZs) per N.J.S.A. 52:27H-80 -- ~32
  municipalities where qualified retail purchases at certified
  UEZ sellers tax at half rate (3.3125%). Seller-eligibility
  restricted; encoding as a geographic override would over-collect
  on non-certified sellers in UEZ municipalities.
- Salem County per N.J.S.A. 54:32B-8.45 -- qualified retail sales
  at retail stores tax at half rate (3.3125%) (Delaware
  competition).

Atlantic City Luxury Tax (N.J.S.A. 40:48-8.15 et seq.) is a separate
3% city tax on hotels / restaurants / alcohol / amusements within
Atlantic City -- NOT a general sales tax and outside this engine's
scope.

Clothing is BROADLY EXEMPT in NJ year-round per N.J.S.A. 54:32B-8.4
(NJ joins PA, MA, MN, VT in the broad-exemption club). No per-item
dollar cap; no date restriction.

Sales-tax holidays: NONE currently. The 2022 Back-to-School holiday
(P.L. 2022, c. 21) ran in 2022 and 2023, then was REPEALED by P.L.
2024, c. 19 (signed 2024-06-28) effective immediately. holidays_for()
returns an empty iterator for every year.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.new_jersey import (
    NEW_JERSEY,
    NEW_JERSEY_REDUCED_RATE_PCT,
    NEW_JERSEY_STATEWIDE_RATE_PCT,
    NewJersey,
)
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration + Protocol
# ---------------------------------------------------------------------------
def test_new_jersey_metadata() -> None:
    """Tier-1 promotion: SST member, has sales tax, FIPS 34, tier 1."""
    assert NEW_JERSEY.state_abbrev == "NJ"
    assert NEW_JERSEY.state_name == "New Jersey"
    assert NEW_JERSEY.state_fips == "34"
    assert NEW_JERSEY.sst_member is True
    assert NEW_JERSEY.has_sales_tax is True
    assert NEW_JERSEY.tier == 1


def test_new_jersey_inherits_sst_base() -> None:
    """NJ subclasses SstStateModule so it inherits the SST quarterly parser."""
    assert isinstance(NEW_JERSEY, SstStateModule)
    assert isinstance(NewJersey(), SstStateModule)


def test_new_jersey_satisfies_protocol() -> None:
    """NJ structurally implements the StateModule Protocol."""
    assert isinstance(NEW_JERSEY, StateModule)
    assert isinstance(NewJersey(), StateModule)


def test_new_jersey_is_registered() -> None:
    """The registry returns the NJ instance under 'NJ' (case-insensitive)."""
    assert get_state_module("NJ") is NEW_JERSEY
    assert get_state_module("nj") is NEW_JERSEY


def test_new_jersey_not_in_tier2_anymore() -> None:
    """Regression: NJ was promoted out of _tier2.py and must not appear
    in TIER_2_CLASSES or TIER_2_STATES. A double-registration would
    silently overwrite the tier-1 instance with a tier-2 one.
    """
    from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES

    assert "NJ" not in {cls().state_abbrev for cls in TIER_2_CLASSES}
    assert "NJ" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", False),  # N.J.S.A. 54:32B-8.4 broad exemption
        ("groceries", False),  # N.J.S.A. 54:32B-8.2
        ("prescription_drugs", False),  # N.J.S.A. 54:32B-8.1
        ("prepared_food", True),  # excluded from N.J.S.A. 54:32B-8.2
        ("digital_goods", True),  # N.J.S.A. 54:32B-8.55
        ("general", True),  # N.J.S.A. 54:32B-3 imposition
    ],
)
def test_new_jersey_taxability(category: str, expected_taxable: bool) -> None:
    """Each of the six core categories returns the statutorily correct rule
    with a non-empty notes field carrying an N.J.S.A. citation.
    """
    rule = NEW_JERSEY.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    assert "N.J.S.A." in (rule.notes or "")


def test_new_jersey_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats them as taxable by default."""
    assert NEW_JERSEY.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_new_jersey_clothing_is_exempt_year_round_no_threshold() -> None:
    """NJ joins PA/MA/MN/VT in the broad year-round clothing exemption.

    Distinct from NY's $110-per-item threshold and MA's $175-per-item
    threshold: NJ's exemption has NO per-item dollar cap and NO date
    restriction. The rule's notes must cite N.J.S.A. 54:32B-8.4 and
    document the exclusions (fur clothing, accessories, sport
    equipment, protective equipment).
    """
    rule = NEW_JERSEY.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    notes = rule.notes or ""
    assert "54:32B-8.4" in notes
    notes_lower = notes.lower()
    # Exclusions must be documented so a future maintainer doesn't
    # accidentally exempt fur clothing / accessories.
    assert "fur" in notes_lower
    assert "accessor" in notes_lower


def test_new_jersey_groceries_cite_section_8_2() -> None:
    """Grocery exemption is in N.J.S.A. section 54:32B-8.2."""
    rule = NEW_JERSEY.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "54:32B-8.2" in (rule.notes or "")


def test_new_jersey_prescription_drugs_cite_section_8_1() -> None:
    """Prescription drugs are exempt under N.J.S.A. section 54:32B-8.1."""
    rule = NEW_JERSEY.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "54:32B-8.1" in (rule.notes or "")


def test_new_jersey_digital_goods_cite_imposition_statute_and_2011_chapter() -> None:
    """Specified digital products were brought into the NJ sales-tax base
    by P.L. 2011, c. 49, which amended the imposition statute (N.J.S.A.
    section 54:32B-3(a)) to read 'tangible personal property or a
    specified digital product.' The defined term lives at N.J.S.A.
    section 54:32B-2(zz). N.J.S.A. section 54:32B-8.56 (added by the
    same chapter) is a SEPARATE narrow exemption for prewritten software
    delivered electronically AND used directly and exclusively in the
    purchaser's business -- it does not change the general taxability
    of consumer-facing digital goods.
    """
    rule = NEW_JERSEY.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    # Imposition statute (the correct primary citation per the 2011
    # amendment to the Sales and Use Tax Act).
    assert "54:32B-3" in notes
    # The 2011 chapter that brought specified digital products into the base.
    assert "2011" in notes
    # The defined-term cross-reference.
    assert "54:32B-2(zz)" in notes or "specified digital product" in notes.lower()


def test_new_jersey_general_rule_cites_imposition_statute_and_rate() -> None:
    """General TPP rule cites N.J.S.A. 54:32B-3 (the imposition statute)
    and documents the 6.625% rate plus the UEZ + Salem County deferral.
    """
    rule = NEW_JERSEY.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    notes = rule.notes or ""
    assert "54:32B-3" in notes
    # Rate must be documented in the general rule's notes.
    assert "6.625" in notes
    # UEZ + Salem County exceptions must be flagged in the general rule.
    assert "52:27H-80" in notes  # UEZ statute
    assert "54:32B-8.45" in notes  # Salem County statute
    notes_lower = notes.lower()
    assert "urban enterprise" in notes_lower
    assert "salem" in notes_lower
    assert "3.3125" in notes  # half-rate


# ---------------------------------------------------------------------------
# Sales-tax holidays -- NJ has none recurring (the 2022 one-time event
# was not re-enacted).
# ---------------------------------------------------------------------------
def test_new_jersey_holidays_for_all_years_returns_empty() -> None:
    """NJ has no active sales-tax holiday in any year.

    NJ enacted a back-to-school holiday by P.L. 2022, c. 21 (codified
    at the now-repealed N.J.S.A. section 54:32B-8.66). The holiday ran
    in late August / early September of 2022 and 2023, then was
    REPEALED by P.L. 2024, c. 19 (Assembly Substitute A4702, signed
    by Governor Murphy on 2024-06-28 as part of the FY2025 budget
    package), effective immediately. The repeal struck the framework
    from the books before the 2024 holiday window would have run. The
    NJ Division of Taxation publishes no holiday notice for 2024,
    2025, 2026, or any future year. Until a future legislature
    re-enacts a holiday, holidays_for() must return an empty iterator
    for every year (mirrors NE, DC, ID, IN).
    """
    for year in range(2023, 2031):
        holidays = list(NEW_JERSEY.holidays_for(year))
        assert holidays == [], f"NJ has no active holidays. Year: {year}."


def test_new_jersey_holidays_historical_2022_2023_also_empty() -> None:
    """We do not back-fill the repealed 2022/2023 windows.

    The engine's value comes from accurate FORWARD-LOOKING calculation;
    backfilling a repealed holiday into ``holidays_for`` would risk
    a maintainer mistakenly extrapolating it forward. The 2022/2023
    history is documented in the module docstring and references.md
    instead.
    """
    assert list(NEW_JERSEY.holidays_for(2022)) == []


# ---------------------------------------------------------------------------
# Module-docstring assertions: UEZ + Salem County deferral must be
# prominently documented or future maintainers + integrators won't know
# about the under/over-collection edge cases.
# ---------------------------------------------------------------------------
def test_new_jersey_module_docstring_documents_uez_deferral() -> None:
    """The Urban Enterprise Zone (N.J.S.A. 52:27H-80) half-rate
    deferral MUST be documented in the module docstring. Without it,
    an integrator using NJ addresses in Newark / Camden / Paterson
    won't know that certified UEZ sellers should be collecting at
    3.3125% rather than 6.625%, and won't understand why the engine
    over-charges on those edge-case transactions.
    """
    import opensalestax.states.new_jersey as nj_module

    docstring = nj_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The UEZ statute identifier must appear.
    assert "52:27H-80" in docstring
    # The UEZ name must be spelled out.
    assert "urban enterprise zone" in docstring_lower
    # The half rate must be documented.
    assert "3.3125" in docstring
    # The deferral mechanism must be explained.
    assert "not modeled" in docstring_lower or "deferred" in docstring_lower


def test_new_jersey_module_docstring_documents_salem_county_deferral() -> None:
    """Salem County's half-rate (N.J.S.A. 54:32B-8.45) MUST be
    documented in the module docstring. Without it, a Salem County
    transaction would silently over-collect at 6.625% with no
    indication that the statute permits a 3.3125% rate at qualifying
    retail stores.
    """
    import opensalestax.states.new_jersey as nj_module

    docstring = nj_module.__doc__ or ""
    docstring_lower = docstring.lower()
    assert "54:32B-8.45" in docstring
    assert "salem" in docstring_lower
    assert "3.3125" in docstring
    # The deferral mechanism must be explained.
    assert "not modeled" in docstring_lower or "deferred" in docstring_lower


def test_new_jersey_module_docstring_documents_atlantic_city_luxury_tax() -> None:
    """The Atlantic City Luxury Tax (N.J.S.A. 40:48-8.15) MUST be
    documented as out-of-scope so an integrator selling hotel-room or
    restaurant-meal transactions in Atlantic City knows the engine's
    general-rate calculation is incomplete for those specific
    category transactions in that specific geography.
    """
    import opensalestax.states.new_jersey as nj_module

    docstring = nj_module.__doc__ or ""
    docstring_lower = docstring.lower()
    assert "40:48-8.15" in docstring
    assert "atlantic city" in docstring_lower
    assert "luxury" in docstring_lower


def test_new_jersey_module_docstring_documents_holiday_repeal_history() -> None:
    """The 2022 enactment + 2024 repeal history MUST appear in the module
    docstring so a future contributor doesn't add a holiday based on
    outdated guidance or copy-paste from a state that still has one.
    Without this, a maintainer reading only the code might re-add the
    repealed framework based on a stale internet article.
    """
    import opensalestax.states.new_jersey as nj_module

    docstring = nj_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # Enactment chapter (allow either spacing variant)
    assert "2022, c. 21" in docstring or "2022, c.21" in docstring
    # Repeal chapter
    assert "2024, c. 19" in docstring or "2024, c.19" in docstring
    # And a clear "no active / repealed" statement so a casual reader
    # doesn't think the holiday is still in effect.
    assert "repeal" in docstring_lower


def test_new_jersey_module_docstring_documents_clothing_exemption() -> None:
    """The broad clothing exemption (N.J.S.A. 54:32B-8.4) MUST be
    prominently called out in the module docstring -- it is one of
    NJ's two most distinctive features (along with the absence of
    general local sales tax). Removing or weakening this language
    is a documentation regression.
    """
    import opensalestax.states.new_jersey as nj_module

    docstring = nj_module.__doc__ or ""
    docstring_lower = docstring.lower()
    assert "54:32B-8.4" in docstring
    assert "clothing" in docstring_lower
    assert "exempt" in docstring_lower


# ---------------------------------------------------------------------------
# Special cases (none consumed by the engine in v1)
# ---------------------------------------------------------------------------
def test_new_jersey_special_cases_empty() -> None:
    """v1 ships no SpecialCase rows for NJ. The UEZ / Salem County /
    Atlantic City caveats are documented in the module docstring and
    in references.md rather than encoded as engine-consumed special
    cases (the SpecialCase API is reserved for Phase 5+).
    """
    cases = list(NEW_JERSEY.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Documentary constants
# ---------------------------------------------------------------------------
def test_new_jersey_statewide_rate_constant_is_6_625_pct() -> None:
    """Documentary constant: NJ's statewide rate is 6.625% per N.J.S.A.
    section 54:32B-3 (effective Jan 1, 2018; reduced from 7% in steps
    by P.L. 2016, c. 57). The actual rate that flows into the engine
    comes from the SST quarterly file via the inherited parser; this
    constant gives grep-ability and a stable test fixture.
    """
    assert Decimal("6.625") == NEW_JERSEY_STATEWIDE_RATE_PCT


def test_new_jersey_reduced_rate_constant_is_half_of_statewide() -> None:
    """Documentary constant: the NJ reduced rate (used by both UEZ
    qualifying sales under N.J.S.A. 52:27H-80 and Salem County
    qualifying sales under N.J.S.A. 54:32B-8.45) is exactly HALF the
    statewide rate -- i.e. 3.3125%. Catches any future typo in either
    constant.
    """
    assert Decimal("3.3125") == NEW_JERSEY_REDUCED_RATE_PCT
    # Verify the half-rate relationship exactly.
    assert NEW_JERSEY_REDUCED_RATE_PCT * 2 == NEW_JERSEY_STATEWIDE_RATE_PCT
