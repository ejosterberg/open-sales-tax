# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the tier-2 SST state modules.

**Phase 7 complete in v0.11.0**: every SST member state has been
promoted to tier 1, so the tier-2 set is now empty. The original
22 SST members were promoted across v0.1 (MN, WI), v0.8 (AR, GA,
IA, IN), v0.9 (KS, KY, MI, NE, NV), v0.10 (NJ, NC, ND, OH, OK),
and v0.11 (RI, SD, TN, UT, VT, WA, WV, WY).

These tests now serve as a regression: any future tier-2 state
registered in ``_tier2.py`` must satisfy the same Protocol /
metadata contract. With the tuple empty, only the count test
runs meaningfully -- the per-state parametrized tests yield no
parameters and pytest reports them as 0 collected (which is
fine; pytest's parametrize over empty tuple is a no-op).
"""

from __future__ import annotations

import datetime as dt

import pytest

from opensalestax.states import get_state_module
from opensalestax.states._sst_base import SstStateModule
from opensalestax.states._tier2 import TIER_2_CLASSES, TIER_2_STATES
from opensalestax.states.protocol import StateModule

# Phase 7 complete -- the tier-2 set is now empty.
EXPECTED_TIER_2_ABBREVS: frozenset[str] = frozenset()


def test_count_matches_expected() -> None:
    """Phase 7 complete: every SST member is now tier-1."""
    assert len(TIER_2_STATES) == 0
    assert len(TIER_2_CLASSES) == 0
    assert {s.state_abbrev for s in TIER_2_STATES} == EXPECTED_TIER_2_ABBREVS


@pytest.mark.parametrize("instance", TIER_2_STATES, ids=lambda s: s.state_abbrev)
def test_each_tier2_state_satisfies_protocol(instance: SstStateModule) -> None:
    """Every tier-2 state is a structural StateModule.

    Currently no parameters (Phase 7 complete). Kept as the future
    regression contract.
    """
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


def test_unknown_category_returns_none_on_any_sst_module() -> None:
    """Unknown category returns None (engine treats as taxable default).

    Uses Kentucky -- a tier-1 SST module -- as the test fixture since
    the tier-2 tuple is empty post-Phase-7. The contract being tested
    is the same: any SstStateModule subclass returns None for unknown
    categories.
    """
    kentucky = get_state_module("KY")
    assert kentucky is not None
    assert kentucky.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_phase_7_sst_members_all_tier_1() -> None:
    """Sanity check: every SST member is now tier 1.

    The 22 SST members + 5 no-tax states + every non-SST tier-1
    state should all be in the registry at tier 1. (Tier-0 states
    AL/HI/NM are excluded.)
    """
    from opensalestax.states import supported_abbrevs

    abbrevs = supported_abbrevs()
    # Every former tier-2 SST state is now in the registry as tier-1.
    expected = {
        # Phase 1 SST tier-1
        "MN",
        "WI",
        # v0.8 SST promotions
        "AR",
        "GA",
        "IA",
        "IN",
        # v0.9 SST promotions
        "KS",
        "KY",
        "MI",
        "NE",
        "NV",
        # v0.10 SST promotions
        "NJ",
        "NC",
        "ND",
        "OH",
        "OK",
        # v0.11 SST promotions (final batch)
        "RI",
        "SD",
        "TN",
        "UT",
        "VT",
        "WA",
        "WV",
        "WY",
        # No-tax states
        "AK",
        "DE",
        "MT",
        "NH",
        "OR",
    }
    assert expected.issubset(abbrevs), f"missing: {expected - abbrevs}"
