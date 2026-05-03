# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Florida state module (tier 1, non-SST).

FL is **not** an SST member. Statewide rate is **6%** per the
Florida Department of Revenue (floridarevenue.com). Counties may
add a discretionary surtax (DR-15DSS) of 0.5%-2.5%; combined
rates typically range 6.5%-8.5%.

**Phase 3 ships statewide only.** County surtax loading from
DR-15DSS is deferred to a future section.

Taxability matrix (per Fla. Stat. Chapter 212):

- **Clothing** -- TAXABLE (no general exemption). FL runs annual
  sales-tax holidays (Back to School, Disaster Preparedness,
  Tool Time, Freedom Month) that temporarily exempt qualifying
  items; modeled when the holidays feature lands.
- **Groceries** -- NON-taxable for "groceries" (Fla. Stat.
  212.08(1)). Prepared food, candy, soda: taxable.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE for downloaded software and
  digital content.

State maintainer: vacant -- see MAINTAINERS.md. FL's annual
sales-tax holidays are extensive (typically 4-5 per year, set
by annual legislation); a maintainer who tracks legislative
sessions is ideal.
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
            "Clothing IS taxable in Florida year-round. Annual "
            "back-to-school sales-tax holidays temporarily exempt "
            "qualifying items; modeled when the holidays feature lands."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Groceries are non-taxable in Florida (Fla. Stat. 212.08(1)). "
            "Prepared food, candy, and soda are taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable in Florida.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in Florida.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Florida.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}

_RATE_EFFECTIVE_FROM = dt.date(1988, 2, 1)  # FL's 6% rate has been stable since 1988


class Florida:
    """Florida state module (tier 1; statewide rate only in v0.3)."""

    state_abbrev: str = "FL"
    state_name: str = "Florida"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="Florida",
            authority_type="state",
            rate_pct=Decimal("6.000"),
            effective_from=_RATE_EFFECTIVE_FROM,
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
        """Florida runs 4-5 annual sales-tax holidays set by legislation.

        2026 dates encoded explicitly. Add subsequent years as the
        Florida Legislature's annual tax-relief bill is published.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Disaster Preparedness (2026)",
                    starts_on=dt.date(2026, 6, 1),
                    ends_on=dt.date(2026, 6, 14),
                    applicable_categories=("emergency_supplies",),
                    max_amount_per_item=None,
                    notes="Batteries, generators, ice chests, etc.",
                ),
                HolidayWindow(
                    name="Freedom Month (2026)",
                    starts_on=dt.date(2026, 7, 1),
                    ends_on=dt.date(2026, 7, 31),
                    applicable_categories=("recreation", "entertainment"),
                    max_amount_per_item=None,
                    notes="Outdoor recreation gear, event admissions, etc.",
                ),
                HolidayWindow(
                    name="Back-to-School (2026)",
                    starts_on=dt.date(2026, 8, 1),
                    ends_on=dt.date(2026, 8, 14),
                    applicable_categories=("clothing", "school_supplies", "computers"),
                    max_amount_per_item=Decimal("100.00"),
                    notes="Clothing $100/less, supplies $50/less, computers $1500/less.",
                ),
                HolidayWindow(
                    name="Tool Time (2026)",
                    starts_on=dt.date(2026, 9, 5),
                    ends_on=dt.date(2026, 9, 11),
                    applicable_categories=("tools",),
                    max_amount_per_item=None,
                    notes="Tools and shop supplies for skilled trade workers.",
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Florida()
del _PROTOCOL_CHECK

FLORIDA = register(Florida())
