# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Maryland state module (tier 1, non-SST).

MD is **not** an SST member. Statewide rate is **6%** per the
Maryland Comptroller (marylandtaxes.gov). Maryland is unusual in
that local jurisdictions do **not** add sales tax (some impose
meals taxes, but those are administered separately).

Taxability matrix (per Md. Code Ann., Tax-General):

- **Clothing** -- TAXABLE year-round. The annual ``Shop Maryland
  Tax-Free Week`` (second Sunday of August through Saturday)
  exempts qualifying apparel and footwear $100 or less per item;
  modeled when the holidays feature lands.
- **Groceries** -- NON-taxable for "food sold for human
  consumption" (Tax-Gen sec 11-206).
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE since 2021 (HB 932).

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
            "Clothing IS taxable in Maryland year-round. The annual "
            "Shop Maryland Tax-Free Week (mid-August) exempts apparel "
            "and footwear $100 or less per item; modeled when the "
            "holidays feature lands."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes="Food for human consumption is non-taxable (Md. Tax-Gen section 11-206).",
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
        notes="Digital goods are taxable in Maryland since 2021 (HB 932).",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Maryland:
    """Maryland state module (tier 1; statewide rate only)."""

    state_abbrev: str = "MD"
    state_name: str = "Maryland"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="Maryland",
            authority_type="state",
            rate_pct=Decimal("6.000"),
            effective_from=dt.date(2008, 1, 3),
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


_PROTOCOL_CHECK: StateModule = Maryland()
del _PROTOCOL_CHECK

MARYLAND = register(Maryland())
