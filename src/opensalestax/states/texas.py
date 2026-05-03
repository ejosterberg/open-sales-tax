# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Texas state module (tier 1, non-SST).

TX is **not** an SST member. Statewide rate is **6.25%** per the
Texas Comptroller (comptroller.texas.gov). Local jurisdictions
(cities, counties, transit authorities, special-purpose districts)
can add up to 2% combined, capping the maximum at 8.25%.

**Phase 3 ships statewide only.** Local-jurisdiction loading from
the Comptroller's downloadable rate file is deferred to a future
section -- TX uses origin-based sourcing for in-state sellers,
which adds complexity to the boundary model.

Taxability matrix (per Tex. Tax Code Chapter 151):

- **Clothing** -- TAXABLE (no exemption). Three annual sales-tax
  holidays modify this temporarily; modeled when the holidays
  feature lands.
- **Groceries** -- NON-taxable for "food products" sold for off-
  premise consumption (sec 151.314).
- **Prescription drugs** -- NON-taxable (sec 151.313).
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE for downloaded software, music,
  ringtones, etc.

Special note: TX has 3 annual sales-tax holidays (emergency-prep
in April, Energy Star + WaterSense in May, back-to-school in
August). Surface them via the holidays feature in v0.4+.

State maintainer: vacant -- see MAINTAINERS.md.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.states.protocol import (
    BoundaryRow,
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
            "Clothing IS taxable in Texas year-round; the August "
            "back-to-school sales-tax holiday provides a temporary "
            "exemption (modeled when the holidays feature lands)."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food products for off-premise consumption are non-taxable "
            "(Tex. Tax Code section 151.314). Prepared food is taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable (Tex. Tax Code section 151.313).",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food (restaurant meals, hot foods) is taxable.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods (downloaded software, music, etc.) are taxable in Texas.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}

_RATE_EFFECTIVE_FROM = dt.date(1990, 7, 1)


class Texas:
    """Texas state module (tier 1; statewide rate only in v0.3)."""

    state_abbrev: str = "TX"
    state_name: str = "Texas"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="Texas",
            authority_type="state",
            rate_pct=Decimal("6.250"),
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


_PROTOCOL_CHECK: StateModule = Texas()
del _PROTOCOL_CHECK

TEXAS = register(Texas())
