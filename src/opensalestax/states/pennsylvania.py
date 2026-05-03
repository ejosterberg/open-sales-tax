# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Pennsylvania state module (tier 1, non-SST).

PA is **not** an SST member. Statewide rate is **6%** per the
PA Department of Revenue (revenue.pa.gov). Allegheny County and
the City of Philadelphia add local surtaxes (1% and 2%
respectively), bringing combined rates to 7-8%.

**Phase 4 ships statewide only.** Loading the Allegheny +
Philadelphia surtaxes is a future section; we'd need a small
boundary table for the two affected ZIP ranges.

Taxability matrix (per 72 P.S. Article II):

- **Clothing** -- NON-TAXABLE in Pennsylvania. PA is one of a
  small set of states that broadly exempts clothing. Footwear
  for athletic / formal use may be taxable -- consult the PA
  Retailer's Information Guide for edge cases.
- **Groceries** -- NON-taxable.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE per Act 84 (2016).

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
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=False,
        notes=(
            "Clothing is NON-taxable in Pennsylvania (broad clothing "
            "exemption). Athletic/formal footwear has nuanced rules; "
            "consult the PA Retailer's Information Guide for edge cases."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes="Groceries are non-taxable in Pennsylvania.",
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in Pennsylvania.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable per Act 84 (2016).",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Pennsylvania:
    """Pennsylvania state module (tier 1; statewide rate only)."""

    state_abbrev: str = "PA"
    state_name: str = "Pennsylvania"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        del source_file, version_label
        yield RateRow(
            authority_name="Pennsylvania",
            authority_type="state",
            rate_pct=Decimal("6.000"),
            effective_from=dt.date(1968, 3, 1),
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
        """Pennsylvania has no annual sales-tax holidays."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = Pennsylvania()
del _PROTOCOL_CHECK

PENNSYLVANIA = register(Pennsylvania())
