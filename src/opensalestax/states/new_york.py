# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""New York state module (tier 1, non-SST).

NY is **not** an SST member. Statewide rate is **4%** per
NY DTF (tax.ny.gov). Local additions vary widely; the MTA
surcharge of 0.375% applies in NYC + 7 surrounding counties,
and ~57 counties + ~18 cities impose their own local rates.
Combined rates range from 7% (most upstate counties) to 8.875%
(NYC).

**Phase 3 ships statewide only.** Local + MTA loading is
deferred to a future section once a NY DTF rate file is wired
into the loader.

Taxability matrix (per N.Y. Tax Law Article 28):

- **Clothing** -- TAXABLE with a state-level threshold:
  clothing/footwear priced under $110 per item is exempt from
  the state 4% rate (N.Y. Tax Law section 1115(a)(30)). The
  ``below_exempt`` semantic encodes this. The MTA 0.375%
  surcharge follows the same threshold; local jurisdictions may
  opt back in (NY DTF Publication 718-C lists current local
  treatment). v1 ships the state-portion threshold; per-locality
  re-imposition lands when the MTA + local rate file is wired in.
- **Groceries** -- NON-taxable for "food and food products"
  (sec 1115(a)(1)). Candy, soda, prepared food: taxable.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE for prewritten software (sec
  1101(b)(6)); the rule for streamed/digital media is more
  nuanced.

State maintainer: vacant -- see MAINTAINERS.md. NY's clothing
rule is one of the more complex in the US; promoting this to a
fully-correct tier-1 needs a NY-resident maintainer who can
verify against DTF guidance.
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
        taxable_threshold_amount=Decimal("110.00"),
        threshold_semantic="below_exempt",
        notes=(
            "New York: clothing/footwear under $110 per item is exempt "
            "from the state 4% rate (N.Y. Tax Law section 1115(a)(30)). "
            "Items at or above $110 are fully taxable. The MTA 0.375% "
            "surcharge follows the same threshold; local jurisdictions "
            "may opt back in -- see NY DTF Publication 718-C."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food products are non-taxable (N.Y. Tax Law "
            "section 1115(a)(1)). Candy, soda, prepared food are taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable in New York.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food (restaurant meals, etc.) is taxable.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Prewritten software is taxable (N.Y. Tax Law section "
            "1101(b)(6)). The rule for streamed/digital media is more "
            "nuanced; verify case-by-case."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}

_RATE_EFFECTIVE_FROM = dt.date(2005, 6, 1)  # current 4% rate


class NewYork:
    """New York state module (tier 1; statewide rate only in v0.3)."""

    state_abbrev: str = "NY"
    state_name: str = "New York"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="New York",
            authority_type="state",
            rate_pct=Decimal("4.000"),
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
        """New York has no annual sales-tax holidays at the state level."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = NewYork()
del _PROTOCOL_CHECK

NEW_YORK = register(NewYork())
