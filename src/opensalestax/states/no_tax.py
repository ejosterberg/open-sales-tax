# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Generic state module for the 5 no-state-tax jurisdictions.

Alaska, Delaware, Montana, New Hampshire, and Oregon don't levy a
statewide sales tax. Each of them gets a :class:`NoTaxState`
instance registered with the engine. Calls to ``parse_rates`` and
``parse_boundaries`` return empty iterators (there's nothing to
parse); ``taxability_for`` always reports the category as
non-taxable.

Three of these states have known caveats that don't affect Phase 1:

- **Alaska**: ~110 boroughs and cities collect local sales tax,
  many through the Alaska Remote Seller Sales Tax Commission
  (ARSSTC). Phase 1 does not model these; future per-locality
  support tracked separately.
- **Montana**: a handful of resort communities (Whitefish, Big
  Sky, etc.) levy local "resort taxes." Same deferral.
- **Oregon**: some localities impose meals or motor-vehicle-rental
  taxes. Same deferral.

These caveats are documented in ``notes`` on each instance for
visibility in the ``/v1/states`` API response.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from opensalestax.states.protocol import (
    BoundaryRow,
    HolidayWindow,
    RateRow,
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register


class NoTaxState:
    """Generic state module for jurisdictions with no state-level sales tax.

    Conforms to the :class:`~opensalestax.states.protocol.StateModule`
    protocol. Five instances are registered when this module is
    imported (one each for AK, DE, MT, NH, OR).
    """

    sst_member: bool = False
    has_sales_tax: bool = False
    tier: StateTier = 1  # fully maintained: the rule "no tax" is complete

    def __init__(self, abbrev: str, name: str, notes: str = "") -> None:
        self.state_abbrev = abbrev
        self.state_name = name
        self.notes = notes

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """No rates to parse."""
        # Names retained for Protocol-signature compatibility.
        del source_file, version_label
        return iter(())

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]:
        """No boundaries to parse."""
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Every category is non-taxable in a no-tax state."""
        del effective_date  # rule applies for all dates
        return TaxabilityRule(
            item_category=item_category,
            is_taxable=False,
            notes=f"{self.state_name} levies no statewide sales tax.",
        )

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked at the state level for Phase 1."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """No-tax states have no sales-tax holidays (no tax to suspend)."""
        del year
        return iter(())

    def __repr__(self) -> str:
        return f"<NoTaxState {self.state_abbrev}>"


# Compile-time check: NoTaxState satisfies the StateModule Protocol.
# (Runtime check is in tests.)
_PROTOCOL_CHECK: StateModule = NoTaxState("XX", "Protocol Check")
del _PROTOCOL_CHECK


# ---------------------------------------------------------------------------
# Registered instances -- one per no-tax state
# ---------------------------------------------------------------------------
# NOTE: Alaska was previously registered here as a no-tax state but
# moved to ``opensalestax.states.alaska`` in v0.49 to model the ~20
# largest sales-tax-collecting AK municipalities via ARSSTC data.

DELAWARE = register(NoTaxState("DE", "Delaware"))

MONTANA = register(
    NoTaxState(
        "MT",
        "Montana",
        notes=(
            "No statewide sales tax. A handful of resort communities "
            "(Whitefish, Big Sky, etc.) levy local resort taxes; not "
            "modeled in Phase 1."
        ),
    )
)

NEW_HAMPSHIRE = register(NoTaxState("NH", "New Hampshire"))

OREGON = register(
    NoTaxState(
        "OR",
        "Oregon",
        notes=(
            "No statewide sales tax. Some localities impose meals or "
            "motor-vehicle-rental taxes; not modeled in Phase 1."
        ),
    )
)

NO_TAX_STATES = (DELAWARE, MONTANA, NEW_HAMPSHIRE, OREGON)
