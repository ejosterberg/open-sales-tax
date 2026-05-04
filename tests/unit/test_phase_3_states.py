# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Phase 3 tier-1 states: TX, NY, FL.

Each module follows the California pattern (self_seeded, statewide
rate, full taxability matrix). Tests verify metadata, registration,
Protocol conformance, statewide rate, and taxability matrices.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.florida import FLORIDA, Florida
from opensalestax.states.new_york import NEW_YORK, NewYork
from opensalestax.states.protocol import StateModule
from opensalestax.states.texas import TEXAS, Texas

# (instance, abbrev, full name, expected statewide rate)
PHASE_3_STATES = [
    (TEXAS, "TX", "Texas", Decimal("6.250"), Texas),
    (NEW_YORK, "NY", "New York", Decimal("4.000"), NewYork),
    (FLORIDA, "FL", "Florida", Decimal("6.000"), Florida),
]


@pytest.mark.parametrize(
    "instance,abbrev,name,_rate,_cls", PHASE_3_STATES, ids=lambda v: getattr(v, "__name__", str(v))
)
def test_metadata(instance, abbrev: str, name: str, _rate, _cls) -> None:
    assert instance.state_abbrev == abbrev
    assert instance.state_name == name
    assert instance.sst_member is False  # all 3 are non-SST
    assert instance.has_sales_tax is True
    assert instance.tier == 1
    assert instance.self_seeded is True


@pytest.mark.parametrize(
    "instance,_abbrev,_name,_rate,cls", PHASE_3_STATES, ids=lambda v: getattr(v, "__name__", str(v))
)
def test_satisfies_protocol(instance, _abbrev, _name, _rate, cls) -> None:
    assert isinstance(instance, StateModule)
    # A fresh instance also satisfies the Protocol
    assert isinstance(cls(), StateModule)


@pytest.mark.parametrize(
    "_instance,abbrev,_name,_rate,_cls",
    PHASE_3_STATES,
    ids=lambda v: getattr(v, "__name__", str(v)),
)
def test_is_registered(_instance, abbrev: str, _name, _rate, _cls) -> None:
    module = get_state_module(abbrev)
    assert module is not None
    assert module.state_abbrev == abbrev


@pytest.mark.parametrize(
    "instance,_abbrev,_name,rate,_cls", PHASE_3_STATES, ids=lambda v: getattr(v, "__name__", str(v))
)
def test_parse_rates_yields_statewide(instance, _abbrev, _name, rate: Decimal, _cls) -> None:
    """The first emitted row is the statewide rate at the expected percentage.

    Some Phase 3 states (TX as of v0.26) additionally emit per-county,
    per-transit-district, and per-city rates after the statewide row,
    so we don't assert a specific row count -- only that the statewide
    row leads.
    """
    rows = list(instance.parse_rates(None, "v0.3-statewide"))
    assert len(rows) >= 1
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1, "exactly one state-level rate expected"
    assert state_rows[0].rate_pct == rate
    assert state_rows[0].parent_authority_name is None


@pytest.mark.parametrize("instance,_abbrev,_name,_rate,_cls", PHASE_3_STATES)
def test_parse_boundaries_state_or_seeded(instance, _abbrev, _name, _rate, _cls) -> None:
    """NY/FL still defer boundary loading; TX seeds its top-50 cities (v0.26).

    For NY/FL the boundary list is empty (state-only via Census ZCTA);
    for TX it emits state + county + (optional) transit + city rows
    for every covered ZIP.
    """
    rows = list(instance.parse_boundaries(None, "v0.3-statewide"))
    if instance.state_abbrev == "TX":
        assert len(rows) > 0, "TX should seed boundaries for top-50 cities"
        types = {r.authority_type for r in rows}
        assert "state" in types
        assert "county" in types
        assert "city" in types
    else:
        assert rows == []


@pytest.mark.parametrize("instance,_abbrev,_name,_rate,_cls", PHASE_3_STATES)
def test_taxability_general_is_taxable(instance, _abbrev, _name, _rate, _cls) -> None:
    rule = instance.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True


@pytest.mark.parametrize("instance,_abbrev,_name,_rate,_cls", PHASE_3_STATES)
def test_taxability_groceries_is_non_taxable(instance, _abbrev, _name, _rate, _cls) -> None:
    rule = instance.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False


@pytest.mark.parametrize("instance,_abbrev,_name,_rate,_cls", PHASE_3_STATES)
def test_taxability_prescription_drugs_is_non_taxable(
    instance, _abbrev, _name, _rate, _cls
) -> None:
    rule = instance.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is False


@pytest.mark.parametrize("instance,_abbrev,_name,_rate,_cls", PHASE_3_STATES)
def test_taxability_clothing_is_taxable_in_all_three(instance, _abbrev, _name, _rate, _cls) -> None:
    """TX, FL: TAXABLE year-round. NY: TAXABLE by default in this v0.3
    module (the under-$110 exemption requires the threshold-rule feature
    in v0.4+).
    """
    rule = instance.taxability_for("clothing", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    # Each state's clothing rule cites either a holiday note (TX/FL) or
    # the threshold caveat (NY).
    notes = (rule.notes or "").lower()
    assert (
        "holiday" in notes
        or "threshold" in notes
        or "verify" in notes
        or "118" in notes
        or "exemption" in notes
    )


def test_phase_3_increases_tier_1_count_to_11() -> None:
    """7 (Phase 1) + 1 (CA, Phase 2) + 3 (Phase 3) = 11 tier-1 states."""
    from opensalestax.states import all_states

    tier_1 = [s for s in all_states() if s.tier == 1]
    abbrevs = {s.state_abbrev for s in tier_1}
    expected = {"MN", "WI", "AK", "DE", "MT", "NH", "OR", "CA", "TX", "NY", "FL"}
    assert expected.issubset(abbrevs)
