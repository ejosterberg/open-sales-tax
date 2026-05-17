# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Unit tests for the v0.59.0 shipping P1 (per ShippingRule pattern)."""

from __future__ import annotations

from opensalestax.states.protocol import ShippingRule, ShippingRuleSet
from opensalestax.states.registry import all_states


def test_every_state_module_has_shipping_rule_set() -> None:
    """Every registered state module must implement shipping_rule_set().

    Adding a state without this method would AttributeError at
    request time. Pin the invariant.
    """
    missing = []
    for state in all_states():
        try:
            rs = state.shipping_rule_set()
            assert isinstance(
                rs, ShippingRuleSet
            ), f"{state.state_abbrev}: shipping_rule_set must return ShippingRuleSet"
        except AttributeError:
            missing.append(state.state_abbrev)
    assert not missing, f"States missing shipping_rule_set(): {missing}"


def test_shipping_rule_distribution_matches_research() -> None:
    """The per-state rule distribution matches the research doc.

    From specs/research/shipping-taxability.md:
      CONDITIONAL: 27 states (26 SST plurality + custom-class TX/NY/etc.)
      EXEMPT_IF_SEPARATELY_STATED: 19 states
      NONE: 5 states (AK, DE, MT, NH, OR)
      ALWAYS_TAXABLE: 1 (HI)
      MIXED: 1 (MD)
    """
    from collections import Counter

    counts = Counter()
    for state in all_states():
        rs = state.shipping_rule_set()
        counts[rs.default_rule] += 1

    assert counts[ShippingRule.CONDITIONAL] == 27, f"CONDITIONAL count: {counts}"
    assert counts[ShippingRule.EXEMPT_IF_SEPARATELY_STATED] == 19, f"EXEMPT count: {counts}"
    assert counts[ShippingRule.NONE] == 5, f"NONE count: {counts}"
    assert counts[ShippingRule.ALWAYS_TAXABLE] == 1, f"ALWAYS count: {counts}"
    # MD's default_rule is EXEMPT_IF_SEPARATELY_STATED (the shipping
    # default); its MIXED behavior is via handling_rule. So MIXED
    # doesn't appear as a default_rule. This is intentional.


def test_maryland_has_mixed_handling_rule() -> None:
    """MD is the only MIXED state; verify its handling_rule is set."""
    md = next(s for s in all_states() if s.state_abbrev == "MD")
    rs = md.shipping_rule_set()
    assert (
        rs.default_rule == ShippingRule.EXEMPT_IF_SEPARATELY_STATED
    ), "MD shipping (not handling) is exempt when separately stated"
    assert (
        rs.handling_rule == ShippingRule.ALWAYS_TAXABLE
    ), "MD handling is always taxable; distinct from shipping"


def test_no_tax_states_return_none_rule() -> None:
    """AK, DE, MT, NH, OR all return NONE."""
    no_tax_abbrevs = {"AK", "DE", "MT", "NH", "OR"}
    for state in all_states():
        if state.state_abbrev in no_tax_abbrevs:
            assert (
                state.shipping_rule_set().default_rule == ShippingRule.NONE
            ), f"{state.state_abbrev} should return NONE"


def test_hawaii_returns_always_taxable() -> None:
    """HI's GET applies to shipping unconditionally."""
    hi = next(s for s in all_states() if s.state_abbrev == "HI")
    assert hi.shipping_rule_set().default_rule == ShippingRule.ALWAYS_TAXABLE


def test_every_rule_carries_a_citation() -> None:
    """Every state's ShippingRuleSet must carry a citation string.

    Citations come from specs/research/shipping-taxability.md and
    document the DOR/statute source for the rule. Helps maintainers
    re-verify when state law changes.
    """
    missing = []
    for state in all_states():
        rs = state.shipping_rule_set()
        if not rs.citation:
            missing.append(state.state_abbrev)
    assert not missing, f"States missing citation: {missing}"
