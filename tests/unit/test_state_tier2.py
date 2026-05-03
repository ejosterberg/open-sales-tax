# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the 12 tier-2 SST state modules.

Validates that every tier-2 state's metadata is correctly set
and the module satisfies the StateModule Protocol. Per-state
rate validation against real SST data is left to the per-state
maintainer (constitution sec 12) -- these tests are the smoke-
level guarantees.

Arkansas (AR), Georgia (GA), Indiana (IN), Iowa (IA), Kansas
(KS), Kentucky (KY), Michigan (MI), Nebraska (NE), Nevada
(NV), and North Dakota (ND) were promoted to tier 1 in
v0.8/v0.9/v0.10; they now live in their dedicated modules
under ``opensalestax/states/``.
"""

from __future__ import annotations

import datetime as dt

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES
from opensalestax.states.protocol import StateModule

# All 12 tier-2 states should be present (AR+GA+IA+IN+KS+KY+MI+ND+NE+NV were promoted to tier 1 in v0.8/v0.9/v0.10).
EXPECTED_TIER_2_ABBREVS = frozenset(
    {
        "NJ",
        "NC",
        "OH",
        "OK",
        "RI",
        "SD",
        "TN",
        "UT",
        "VT",
        "WA",
        "WV",
        "WY",
    }
)


def test_count_matches_expected() -> None:
    assert len(TIER_2_STATES) == 12
    assert len(TIER_2_CLASSES) == 12
    assert {s.state_abbrev for s in TIER_2_STATES} == EXPECTED_TIER_2_ABBREVS


@pytest.mark.parametrize("instance", TIER_2_STATES, ids=lambda s: s.state_abbrev)
def test_each_tier2_state_satisfies_protocol(instance: SstStateModule) -> None:
    """Every tier-2 state is a structural StateModule."""
    assert isinstance(instance, StateModule)


@pytest.mark.parametrize("instance", TIER_2_STATES, ids=lambda s: s.state_abbrev)
def test_each_tier2_state_metadata_is_valid(instance: SstStateModule) -> None:
    """USPS abbrev and FIPS code shape checks."""
    assert len(instance.state_abbrev) == 2
    assert instance.state_abbrev.isupper()
    assert instance.state_name
    assert instance.tier == 2
    assert instance.has_sales_tax is True
    assert instance.sst_member is True
    assert len(instance.state_fips) == 2
    assert instance.state_fips.isdigit()


@pytest.mark.parametrize("abbrev", sorted(EXPECTED_TIER_2_ABBREVS))
def test_each_tier2_state_is_registered(abbrev: str) -> None:
    """Each tier-2 state can be looked up via the registry."""
    module = get_state_module(abbrev)
    assert module is not None
    assert module.tier == 2
    assert module.state_abbrev == abbrev


@pytest.mark.parametrize("instance", TIER_2_STATES, ids=lambda s: s.state_abbrev)
def test_each_tier2_state_has_default_taxability(
    instance: SstStateModule,
) -> None:
    """The default tier-2 taxability matrix exempts groceries, taxes general."""
    today = dt.date(2026, 5, 3)
    grocery_rule = instance.taxability_for("groceries", today)
    general_rule = instance.taxability_for("general", today)
    assert grocery_rule is not None and grocery_rule.is_taxable is False
    assert general_rule is not None and general_rule.is_taxable is True


def test_tier2_unknown_category_returns_none() -> None:
    """Unknown category returns None (engine treats as taxable default)."""
    kentucky = get_state_module("KY")
    assert kentucky is not None
    assert kentucky.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_phase_1_states_all_registered() -> None:
    """Sanity check: all expected Phase 1 abbrevs are registered.

    Uses subset check rather than exact count -- other tests may
    register dummy entries (Q1, Q2, etc.) into the same global
    registry. The contract is that Phase 1 states are present, not
    that nothing else is.
    """
    from opensalestax.states import supported_abbrevs

    abbrevs = supported_abbrevs()
    # 12 tier-2 + MN+WI+AR+GA+IA+IN+KS+KY+MI+ND+NE+NV (tier 1 SST) + AK, DE, MT, NH, OR (no-tax)
    expected = EXPECTED_TIER_2_ABBREVS | {
        "MN",
        "WI",
        "AR",
        "GA",
        "IA",
        "IN",
        "KS",
        "KY",
        "MI",
        "ND",
        "NE",
        "NV",
        "AK",
        "DE",
        "MT",
        "NH",
        "OR",
    }
    assert expected.issubset(abbrevs), f"missing: {expected - abbrevs}"
