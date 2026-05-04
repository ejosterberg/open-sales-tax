# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Georgia state module (tier 1, SST).

GA was promoted from tier 2 to tier 1 in v0.7+. The state base
rate is 4.0% per O.C.G.A. section 48-8-30 with a stack of local
sales taxes (LOST, SPLOST, ELOST, HOST, TSPLOST, MOST). Local
combined rates typically reach 7-9%.

Key encoded behaviors:

- Groceries are state-level exempt per O.C.G.A. section 48-8-3(57)
  but local sales taxes still apply (mirrors the Louisiana
  state-only-exempt pattern).
- Prescription drugs are exempt per O.C.G.A. section 48-8-3(54).
- Digital goods became taxable 2024-01-01 per Ga. Comp. R. and
  Regs. R. 560-12-2-.118 (SUT 2024-001).
- Georgia has NO sales-tax holidays as of 2026; the 2016 holiday
  was the last and the 2024-2025 reauthorization bills did not
  pass.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.states import get_state_module
from opensalestax.states.georgia import GEORGIA, Georgia
from opensalestax.states.protocol import StateModule


# ---------------------------------------------------------------------------
# Module metadata + registration
# ---------------------------------------------------------------------------
def test_georgia_metadata() -> None:
    assert GEORGIA.state_abbrev == "GA"
    assert GEORGIA.state_name == "Georgia"
    assert GEORGIA.sst_member is True  # GA is a full SST member since 2011-07-01
    assert GEORGIA.has_sales_tax is True
    assert GEORGIA.tier == 1  # promoted from tier 2 in v0.7+


def test_georgia_satisfies_protocol() -> None:
    assert isinstance(GEORGIA, StateModule)
    assert isinstance(Georgia(), StateModule)


def test_georgia_is_registered() -> None:
    assert get_state_module("GA") is GEORGIA
    assert get_state_module("ga") is GEORGIA  # case-insensitive


def test_georgia_no_longer_in_tier2_set() -> None:
    """After promotion GA must NOT appear in the tier-2 registry."""
    from opensalestax.states._tier2 import TIER_2_STATES

    assert "GA" not in {s.state_abbrev for s in TIER_2_STATES}


# ---------------------------------------------------------------------------
# Taxability matrix
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no GA clothing exemption; holiday gone since 2016
        ("groceries", False),  # state-exempt per 48-8-3(57); locals still apply
        ("prescription_drugs", False),  # exempt per 48-8-3(54)
        ("prepared_food", True),  # explicitly excluded from grocery exemption
        ("digital_goods", True),  # taxable since 2024-01-01 per R. 560-12-2-.118
        ("general", True),  # baseline TPP at 4% state + locals
    ],
)
def test_georgia_taxability(category: str, expected_taxable: bool) -> None:
    rule = GEORGIA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # constitution requires notes on every rule
    # Statutory citation MUST appear in every rule's notes (constitution +
    # per-state brief). GA citations all live under O.C.G.A. Title 48,
    # Chapter 8 -- accept any of the section/regulation references that
    # show up across categories.
    notes_lower = rule.notes.lower()
    assert any(
        token in notes_lower
        for token in (
            "48-8-3",
            "48-8-30",
            "48-8-80",
            "48-8-100",
            "48-8-110",
            "48-8-141",
            "48-8-200",
            "48-8-240",
            "560-12-2-.110",
            "560-12-2-.118",
        )
    )


def test_georgia_unknown_category_returns_none() -> None:
    """Unknown categories return None; engine treats as taxable default."""
    assert GEORGIA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_georgia_groceries_notes_state_vs_local_caveat() -> None:
    """Grocery rule must call out that locals still tax groceries."""
    rule = GEORGIA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "48-8-3(57)" in rule.notes
    # The state-vs-local split has to be visible in the rule's notes,
    # otherwise a downstream maintainer can't discover the caveat
    # without reading the module docstring.
    assert "local" in notes_lower
    assert "exempt" in notes_lower


def test_georgia_digital_goods_notes_2024_change() -> None:
    """Digital-goods rule must reference the 2024-01-01 effective date."""
    rule = GEORGIA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    assert "2024" in rule.notes
    assert "560-12-2-.118" in rule.notes


def test_georgia_prescription_drugs_cite_statute() -> None:
    """Prescription-drug rule must cite O.C.G.A. section 48-8-3(54)."""
    rule = GEORGIA.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    assert "48-8-3(54)" in rule.notes


# ---------------------------------------------------------------------------
# Rate parsing against the real GA SST quarterly file
# ---------------------------------------------------------------------------
def test_parse_rates_yields_state_base_4pct() -> None:
    """The GA module extracts the 4.0% state base rate from the SST file.

    GA's state-base row is ``13,45,13,0.04,0.04,0,0,20110101,29991231``
    -- 4% general / 4% food / 0% drug / 0% utility, effective from
    GA's SST membership start. The 0 in the drug column reflects
    the prescription-drug exemption per O.C.G.A. section 48-8-3(54).
    """
    fixture = state_fixture_dir("GA") / "GAR2026Q2FEB19.csv"
    rows = list(GEORGIA.parse_rates(fixture, "GA-SST-2026Q2FEB19"))

    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    state_row = state_rows[0]
    assert state_row.authority_name == "Georgia"
    assert state_row.rate_pct == Decimal("4.00")  # 0.04 * 100 = 4.00
    assert state_row.parent_authority_name is None  # state has no parent
    assert state_row.effective_from == dt.date(2011, 1, 1)


def test_parse_rates_classifies_counties() -> None:
    """GA local taxation is dominated by county rows (type 00)."""
    fixture = state_fixture_dir("GA") / "GAR2026Q2FEB19.csv"
    rows = list(GEORGIA.parse_rates(fixture, "GA-SST-2026Q2FEB19"))

    county_rows = [r for r in rows if r.authority_type == "county"]
    assert county_rows  # GA has many county rows -- 432 in the 2026Q2 file
    sample = county_rows[0]
    assert sample.parent_authority_name == "Georgia"
    # Authority names are friendly (Census ZCTA county lookup) when
    # the FIPS code is recognized; fall back to "GA-county-<fips>"
    # otherwise. Either is valid; GA's locals just need to bind.
    assert sample.authority_name.endswith("County") or sample.authority_name.startswith("GA-county-")
    # Most GA county additions are 1-4% (LOST + SPLOST + ELOST stack).
    assert sample.rate_pct >= Decimal("0")


def test_parse_rates_handles_special_districts() -> None:
    """Type-63 rows (TSPLOST regional districts, MARTA) come through."""
    fixture = state_fixture_dir("GA") / "GAR2026Q2FEB19.csv"
    rows = list(GEORGIA.parse_rates(fixture, "GA-SST-2026Q2FEB19"))

    district_rows = [r for r in rows if r.authority_type == "district"]
    assert district_rows  # GA's TSPLOST + MARTA districts are in this file


def test_parse_rates_total_count_matches_known_codes() -> None:
    """Every recognized type code appears in the output."""
    fixture = state_fixture_dir("GA") / "GAR2026Q2FEB19.csv"
    rows = list(GEORGIA.parse_rates(fixture, "GA-SST-2026Q2FEB19"))
    types_seen = {r.authority_type for r in rows}
    assert types_seen == {"state", "county", "city", "district"}


# ---------------------------------------------------------------------------
# Special cases
# ---------------------------------------------------------------------------
def test_georgia_special_cases_empty() -> None:
    """No SpecialCase entries tracked for GA in v0.7+."""
    cases = list(GEORGIA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Holidays (none -- regression protection per the orchestrator brief)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("year", [2024, 2025, 2026, 2027, 2028, 2029, 2030])
def test_georgia_no_holidays_any_year(year: int) -> None:
    """Georgia has had no sales-tax holidays since 2016 (regression test).

    Required by the orchestrator brief: holidays_for(year) MUST
    return empty for every year exercised here. Should the General
    Assembly re-authorize a holiday in a future session, this test
    will need explicit per-year updates -- exactly the friction the
    project wants (no silent extrapolation of speculative
    legislation).
    """
    assert list(GEORGIA.holidays_for(year)) == []
