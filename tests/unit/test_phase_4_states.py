# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Phase 4 tier-1 additions: PA, IL, MD, MA, AZ."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import all_states, get_state_module
from opensalestax.states.arizona import ARIZONA, Arizona
from opensalestax.states.illinois import ILLINOIS, Illinois
from opensalestax.states.maryland import MARYLAND, Maryland
from opensalestax.states.massachusetts import MASSACHUSETTS, Massachusetts
from opensalestax.states.pennsylvania import PENNSYLVANIA, Pennsylvania
from opensalestax.states.protocol import StateModule

# (instance, abbrev, name, expected statewide rate, class)
PHASE_4_STATES = [
    (PENNSYLVANIA, "PA", "Pennsylvania", Decimal("6.000"), Pennsylvania),
    (ILLINOIS, "IL", "Illinois", Decimal("6.250"), Illinois),
    (MARYLAND, "MD", "Maryland", Decimal("6.000"), Maryland),
    (MASSACHUSETTS, "MA", "Massachusetts", Decimal("6.250"), Massachusetts),
    (ARIZONA, "AZ", "Arizona", Decimal("5.600"), Arizona),
]


@pytest.mark.parametrize("instance,abbrev,name,_rate,_cls", PHASE_4_STATES)
def test_metadata(instance, abbrev: str, name: str, _rate, _cls) -> None:
    assert instance.state_abbrev == abbrev
    assert instance.state_name == name
    assert instance.sst_member is False
    assert instance.has_sales_tax is True
    assert instance.tier == 1
    assert instance.self_seeded is True


@pytest.mark.parametrize("instance,_abbrev,_name,_rate,cls", PHASE_4_STATES)
def test_satisfies_protocol(instance, _abbrev, _name, _rate, cls) -> None:
    assert isinstance(instance, StateModule)
    assert isinstance(cls(), StateModule)


@pytest.mark.parametrize("_instance,abbrev,_name,_rate,_cls", PHASE_4_STATES)
def test_is_registered(_instance, abbrev: str, _name, _rate, _cls) -> None:
    module = get_state_module(abbrev)
    assert module is not None and module.state_abbrev == abbrev


@pytest.mark.parametrize("instance,_abbrev,_name,rate,_cls", PHASE_4_STATES)
def test_parse_rates_yields_statewide(instance, _abbrev, _name, rate: Decimal, _cls) -> None:
    """The first emitted row is the statewide rate at the expected percentage.

    Some Phase 4 states (AZ as of v0.23) additionally emit per-county
    and per-city rates after the statewide row, so we don't assert a
    specific row count -- only that the statewide row leads.
    """
    rows = list(instance.parse_rates(None, "v0.4-statewide"))
    assert len(rows) >= 1
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1, "exactly one state-level rate expected"
    assert state_rows[0].rate_pct == rate


@pytest.mark.parametrize("instance,_abbrev,_name,_rate,_cls", PHASE_4_STATES)
def test_general_taxable(instance, _abbrev, _name, _rate, _cls) -> None:
    rule = instance.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None and rule.is_taxable is True


class TestArizonaTPT:
    """v0.23 ratchet: AZ now ships per-county + top-20-city TPT data."""

    def test_state_county_city_rates_yielded(self) -> None:
        rows = list(ARIZONA.parse_rates(None, "v0.23-tpt"))
        # 1 state + 8 counties touched by AZ_CITIES + 20 cities = 29 rows
        types = sorted(r.authority_type for r in rows)
        assert types.count("state") == 1
        assert types.count("county") >= 5
        assert types.count("city") >= 15
        # Phoenix specifically must appear with 2.8% city rate
        phoenix = next(r for r in rows if r.authority_name == "Phoenix")
        assert phoenix.authority_type == "city"
        assert phoenix.rate_pct == Decimal("2.800")
        # Maricopa County must appear with 0.7% county portion
        maricopa = next(r for r in rows if r.authority_name == "Maricopa County")
        assert maricopa.authority_type == "county"
        assert maricopa.rate_pct == Decimal("0.700")

    def test_phoenix_zip_emits_three_authorities(self) -> None:
        """ZIP 85042 (Phoenix) must bind to state + Maricopa + Phoenix."""
        rows = list(ARIZONA.parse_boundaries(None, "v0.23-tpt"))
        phx_rows = [b for b in rows if b.zip5 == "85042"]
        names = sorted(b.authority_name for b in phx_rows)
        assert names == ["Arizona", "Maricopa County", "Phoenix"]

    def test_combined_rate_phoenix_arithmetic(self) -> None:
        """state 5.6% + Maricopa 0.7% + Phoenix 2.8% should sum to 9.1%."""
        rows = list(ARIZONA.parse_rates(None, "v0.23-tpt"))
        state = next(r for r in rows if r.authority_type == "state")
        maricopa = next(r for r in rows if r.authority_name == "Maricopa County")
        phoenix = next(r for r in rows if r.authority_name == "Phoenix")
        combined = state.rate_pct + maricopa.rate_pct + phoenix.rate_pct
        assert combined == Decimal("9.100")


def test_pennsylvania_clothing_is_non_taxable() -> None:
    """PA is a major clothing-exemption state -- the headline outlier."""
    rule = PENNSYLVANIA.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False
    assert "non-taxable" in (rule.notes or "").lower()


def test_illinois_groceries_have_reduced_rate_marker() -> None:
    """IL's unusual 1% reduced rate is encoded via rate_modifier."""
    rule = ILLINOIS.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.rate_modifier == Decimal("1.000")


def test_massachusetts_clothing_caveat_documented() -> None:
    """MA's $175 threshold is mentioned in the rule's notes."""
    rule = MASSACHUSETTS.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert "175" in (rule.notes or "")


def test_arizona_acknowledges_tpt_model() -> None:
    """AZ's 'general' rule notes the TPT-vs-sales-tax distinction."""
    rule = ARIZONA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert "TPT" in (rule.notes or "")


def test_phase_4_brings_tier_1_count_to_16() -> None:
    """7 (Phase 1) + 1 (CA, P2) + 3 (TX/NY/FL, P3) + 5 (PA/IL/MD/MA/AZ, P4) = 16."""
    tier_1 = [s for s in all_states() if s.tier == 1]
    abbrevs = {s.state_abbrev for s in tier_1}
    expected = {
        # Phase 1
        "MN",
        "WI",
        "AK",
        "DE",
        "MT",
        "NH",
        "OR",
        # Phase 2
        "CA",
        # Phase 3
        "TX",
        "NY",
        "FL",
        # Phase 4
        "PA",
        "IL",
        "MD",
        "MA",
        "AZ",
    }
    assert expected.issubset(abbrevs)
