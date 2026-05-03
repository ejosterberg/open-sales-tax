# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the state-module registry."""

from __future__ import annotations

from opensalestax.states import (
    all_states,
    get_state_module,
    supported_abbrevs,
)
from opensalestax.states.no_tax import NoTaxState
from opensalestax.states.registry import register


def test_no_tax_states_are_registered_on_import() -> None:
    """Importing opensalestax.states should register the 5 no-tax states."""
    abbrevs = supported_abbrevs()
    # All 5 no-tax states must be present
    for code in ("AK", "DE", "MT", "NH", "OR"):
        assert code in abbrevs, f"{code} should be auto-registered by no_tax module"


def test_get_state_module_is_case_insensitive() -> None:
    upper = get_state_module("AK")
    lower = get_state_module("ak")
    assert upper is not None
    assert upper is lower


def test_get_state_module_returns_none_for_unknown() -> None:
    assert get_state_module("ZZ") is None


def test_register_returns_module_unchanged() -> None:
    instance = NoTaxState("Q1", "Test State 1")
    returned = register(instance)
    assert returned is instance
    assert get_state_module("Q1") is instance


def test_register_is_idempotent_with_overwrite() -> None:
    """Re-registering the same abbrev replaces the prior module."""
    a = NoTaxState("Q2", "First")
    b = NoTaxState("Q2", "Second")
    register(a)
    register(b)
    assert get_state_module("Q2") is b


def test_all_states_yields_registered_modules() -> None:
    abbrevs = {m.state_abbrev for m in all_states()}
    for code in ("AK", "DE", "MT", "NH", "OR"):
        assert code in abbrevs
