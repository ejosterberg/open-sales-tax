# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Massachusetts state module (tier 1, non-SST).

MA is **not** an SST member. Statewide rate is **6.25%** per the
Massachusetts Department of Revenue (mass.gov/dor). Local
jurisdictions do not add sales tax (they may impose meals taxes,
administered separately).

Taxability matrix (per M.G.L. c. 64H):

- **Clothing** -- TAXABLE by default in this v0.4 module.
  **CAVEAT:** MA exempts clothing under **$175 per item** from
  the state 6.25% (c. 64H s 6(k)). Modeling this needs the
  threshold-rule machinery that lands alongside the holidays
  feature in v0.5+. Retailers should treat under-$175 apparel
  as non-taxable until the engine handles thresholds.
- **Groceries** -- NON-taxable for "food and food products".
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable. Local meals tax (0.75%) may apply.
- **Digital goods** -- TAXABLE for prewritten software; rules
  for streamed/digital media are nuanced.

State maintainer: vacant -- the under-$175 threshold rule is
the same shape as NY's $110 rule; both will benefit from the
threshold-feature work. See MAINTAINERS.md.
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
        notes=(
            "Clothing is taxable BY DEFAULT in this v0.4 module. MA "
            "exempts clothing under $175 per item (M.G.L. c. 64H s 6(k)); "
            "full modeling needs the threshold-rule feature that lands "
            "alongside holidays in v0.5+. Retailers selling under-$175 "
            "apparel should treat it as non-taxable until then."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes="Food and food products are non-taxable in Massachusetts.",
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable; local 0.75% meals tax may apply.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Prewritten software is taxable. Streamed/digital media has "
            "nuanced rules; verify case-by-case."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Massachusetts:
    """Massachusetts state module (tier 1; statewide rate only)."""

    state_abbrev: str = "MA"
    state_name: str = "Massachusetts"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="Massachusetts",
            authority_type="state",
            rate_pct=Decimal("6.250"),
            effective_from=dt.date(2009, 8, 1),
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
        """MA's annual sales-tax holiday weekend (set by joint resolution).

        2026 dates per MA Department of Revenue. Subsequent years
        require updating once the General Court designates them.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Annual Sales Tax Holiday (2026)",
                    starts_on=dt.date(2026, 8, 8),
                    ends_on=dt.date(2026, 8, 9),
                    applicable_categories=None,  # broad: most personal use
                    max_amount_per_item=Decimal("2500.00"),
                    notes=(
                        "Most retail items < $2500/item; excludes "
                        "telecommunications, tobacco, alcohol, motor vehicles, "
                        "boats, marijuana, meals."
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Massachusetts()
del _PROTOCOL_CHECK

MASSACHUSETTS = register(Massachusetts())
