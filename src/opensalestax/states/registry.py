# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Registry of installed state modules.

Each state module calls :func:`register` at import time to make
itself discoverable by the engine. Lookup is by USPS abbreviation.

The registry is process-global and (intentionally) idempotent: if
a state module is registered twice with the same abbreviation, the
later registration wins. This keeps test fixtures simple.
"""

from __future__ import annotations

from collections.abc import Iterator

from opensalestax.states.protocol import StateModule

_REGISTRY: dict[str, StateModule] = {}


def register(state_module: StateModule) -> StateModule:
    """Register a state module under its ``state_abbrev``.

    Returns the module unchanged so the call can be used inline:

    >>> register(NoTaxState("DE", "Delaware"))  # doctest: +SKIP
    """
    _REGISTRY[state_module.state_abbrev.upper()] = state_module
    return state_module


def get_state_module(abbrev: str) -> StateModule | None:
    """Look up the module for a USPS state abbreviation.

    Case-insensitive. Returns ``None`` if no module is registered
    for this state -- the caller decides whether that's an error
    (state not supported) or an expected miss (state has tier 0).
    """
    return _REGISTRY.get(abbrev.upper())


def all_states() -> Iterator[StateModule]:
    """Yield every registered state module in insertion order."""
    yield from _REGISTRY.values()


def supported_abbrevs() -> set[str]:
    """Return the set of registered USPS abbreviations."""
    return set(_REGISTRY.keys())


def _reset_for_tests() -> None:
    """Clear the registry. Test-only helper.

    Production code MUST NOT call this. Used by tests that need to
    isolate state-module registration from cross-test pollution.
    """
    _REGISTRY.clear()
