# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Arizona state module (tier 1, non-SST).

AZ is **not** an SST member. The state imposes a **Transaction
Privilege Tax (TPT)** rather than a traditional sales tax -- a
distinction that affects who's legally liable (the seller, not
the buyer) but produces the same dollar result for retail sales.
The statewide TPT base rate is **5.6%** per the Arizona
Department of Revenue (azdor.gov).

**Phase 4 ships statewide only.** AZ's counties and (state-
administered) cities add their own rates; combined rates range
6.6%-11.2%. Loading per-jurisdiction rates is a future section.

Taxability matrix (per Ariz. Rev. Stat. 42-5061):

- **Clothing** -- TAXABLE.
- **Groceries** -- NON-taxable for "food for home consumption"
  at the state level. Some cities (Tucson is the prominent
  example) tax groceries at the local level; verify per-city.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE.

State maintainer: vacant -- the city-level grocery taxability
divergence is unusual; AZ benefits from a maintainer who can
verify per-locality. See MAINTAINERS.md.
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
        notes="Clothing is taxable in Arizona.",
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food for home consumption is non-taxable at the state TPT "
            "level. Some cities (e.g. Tucson) tax groceries at the local "
            "level; verify per-city when district rates are loaded in a "
            "future section."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Arizona.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable. AZ's TPT is "
            "imposed on the seller (not the buyer); the math is the same "
            "as a traditional sales tax."
        ),
    ),
}


class Arizona:
    """Arizona state module (tier 1; statewide TPT only)."""

    state_abbrev: str = "AZ"
    state_name: str = "Arizona"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="Arizona",
            authority_type="state",
            rate_pct=Decimal("5.600"),
            effective_from=dt.date(2013, 6, 1),
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
        """Arizona has no annual sales-tax holidays."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = Arizona()
del _PROTOCOL_CHECK

ARIZONA = register(Arizona())
