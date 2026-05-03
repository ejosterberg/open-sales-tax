# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Illinois state module (tier 1, non-SST).

IL is **not** an SST member. State Retailer's Occupation Tax base
rate is **6.25%** per the Illinois Department of Revenue
(tax.illinois.gov). Many home-rule cities add their own rates;
combined rates range 6.25%-11%.

**Phase 4 ships statewide only.** IL's home-rule landscape is
nontrivial; full coverage waits for a CDOR-driven loader.

Taxability matrix (per IL Retailer's Occupation Tax Act):

- **Clothing** -- TAXABLE in Illinois (no general exemption).
- **Groceries** -- **TAXABLE at a reduced 1% rate.** This is
  unusual: most states either fully exempt groceries or fully
  tax them. v0.4 marks this as taxable in the matrix; the
  reduced rate isn't yet wired into the engine. Retailers
  selling groceries in IL should verify with IDOR.
- **Prescription drugs** -- TAXABLE at the reduced 1% rate
  (same caveat as groceries).
- **Prepared food** -- taxable at the standard rate.
- **Digital goods** -- TAXABLE.

State maintainer: vacant -- IL's reduced-rate categories need
the engine's rate-modifier feature to model accurately. See
MAINTAINERS.md.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
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

_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes="Clothing IS taxable in Illinois (no general exemption).",
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("1.000"),
        notes=(
            "Groceries are taxable at a REDUCED 1% rate in Illinois. "
            "v0.4 reports them as taxable with rate_modifier=1.0; the "
            "engine doesn't yet apply rate_modifier. Retailers selling "
            "groceries in IL should verify with IDOR until v0.5+ wires "
            "the modifier through."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=True,
        rate_modifier=Decimal("1.000"),
        notes="Prescription drugs taxed at reduced 1% rate (same caveat as groceries).",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food taxed at the standard 6.25% rate plus local additions.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Illinois.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Illinois:
    """Illinois state module (tier 1; statewide rate only)."""

    state_abbrev: str = "IL"
    state_name: str = "Illinois"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="Illinois",
            authority_type="state",
            rate_pct=Decimal("6.250"),
            effective_from=dt.date(1990, 1, 1),
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Illinois has no recurring annual sales-tax holiday in the current law."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = Illinois()
del _PROTOCOL_CHECK

ILLINOIS = register(Illinois())
