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

## CATEGORY-SPECIFIC RATE NOT MODELED (deferred from v1)

- **3% on data / information technology services** -- effective
  **2025-07-01** under HB 352 (Budget Reconciliation and Financing
  Act of 2025, signed 2025-05-20). Applies a 3% sales-and-use-tax
  rate (not the 6% general rate) to data or information technology
  services and system/application software publishing services --
  NAICS 518, 519, 5132, and 5415 (see MD Comptroller Technical
  Bulletin No. 56). This is a NEW category-specific rate; it does
  **not** change the 6% general rate on tangible personal property.
  OpenSalesTax does not yet model per-category rates, so the engine
  applies the 6% general rate to all taxable categories and does not
  emit the 3% IT-services rate. When the category-aware-rate engine
  extension lands (same extension pending for Maine's 8%/9%/10%
  rates), this module should emit a 3% ``RateRow`` with
  ``applies_to_categories`` set for the covered service categories.
  Confirmed 2026-07-11 during the daily state-tax audit; general
  rate remains 6% with no local sales tax.

State maintainer: vacant -- see MAINTAINERS.md.
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
    ShippingRule,
    ShippingRuleSet,
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

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Maryland's two annual sales-tax holidays.

        2026 dates per the Maryland Comptroller. Both are
        recurring statutorily; subsequent years follow the same
        calendar pattern.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Shop Maryland Energy (2026)",
                    starts_on=dt.date(2026, 2, 14),
                    ends_on=dt.date(2026, 2, 16),
                    applicable_categories=("energy_star",),
                    max_amount_per_item=None,
                    notes="Energy Star products + solar water heaters; President's Day weekend.",
                ),
                HolidayWindow(
                    name="Shop Maryland Tax-Free Week (2026)",
                    starts_on=dt.date(2026, 8, 9),
                    ends_on=dt.date(2026, 8, 15),
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Clothing and footwear $100 or less per item; "
                        "first $40 of a backpack/book bag also exempt. "
                        "Second Sunday of August through following Saturday."
                    ),
                ),
            ]
        )

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return MD's mixed shipping rule.

        Maryland distinguishes "shipping" (exempt when separately
        stated) from "handling" (always taxable). The engine routes
        ``is_handling_charge=True`` requests through ``handling_rule``;
        ordinary shipping flows through ``default_rule``.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.EXEMPT_IF_SEPARATELY_STATED,
            handling_rule=ShippingRule.ALWAYS_TAXABLE,
            citation="MD COMAR 03.06.01.30 + Tax-General Article 11-101(l)",
        )


_PROTOCOL_CHECK: StateModule = Maryland()
del _PROTOCOL_CHECK

MARYLAND = register(Maryland())
