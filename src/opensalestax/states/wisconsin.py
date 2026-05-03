# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Wisconsin state module (tier 1).

WI is a Streamlined Sales Tax member. State base rate is 5.0%
(confirmed via the WI DOR and the SST quarterly file, which
shows ``55,45,55,0.05,0.05,0.05,0.05,19800101,99991231`` --
the 5.0% state rate effective since 1980).

WI's SST rate file uses the SAME jurisdiction-type code mapping
as MN (validated 2026-05-03 against `WIR2026Q2FEB18.csv`):

- ``45`` = state
- ``00`` = county (most WI counties add 0.5%)
- ``01`` = city / local (in WI this includes stadium districts)
- ``63`` = special district

Two notable WI rate-file differences from MN:

- **Open-end date sentinel is ``99991231``** (not MN's ``29991231``).
  The shared SST parser handles both via
  :data:`~opensalestax.data.sst_parser.NO_END_DATE_SENTINELS`.
- **Rate file is plain CSV, not ZIP.** Filename pattern is
  ``WIR<...>.csv`` rather than ``WIR<...>.zip``.

Taxability deviations from MN -- the architectural keystone for
tier-1 contrast:

- **Clothing** -- TAXABLE in WI (Wisconsin has no clothing exemption).
  This is the single most-cited contrast with MN.
- **Groceries** -- non-taxable (food and food ingredients exempt).
- **Prescription drugs** -- non-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- taxable.

State maintainer: vacant -- see MAINTAINERS.md.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from opensalestax.data.sst import open_sst_csv
from opensalestax.data.sst_parser import parse_boundary_csv, parse_rates_csv
from opensalestax.states.protocol import (
    BoundaryRow,
    RateRow,
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# WI uses the same jurisdiction-type code mapping as MN
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Wisconsin taxability matrix per Wisconsin Statutes ch. 77.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Wisconsin -- WI has no clothing exemption. "
            "(Contrast with MN, where clothing is non-taxable.)"
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes="Food and food ingredients are non-taxable in WI (Wis. Stat. 77.54(20n)).",
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable in Wisconsin.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in Wisconsin.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Wisconsin.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Wisconsin:
    """Wisconsin state module."""

    state_abbrev: str = "WI"
    state_name: str = "Wisconsin"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """Parse a WI SST rates file into normalized RateRow records."""
        del version_label
        for record in parse_rates_csv(open_sst_csv(source_file)):
            authority_type = _JURISDICTION_TYPE.get(record.jurisdiction_type)
            if authority_type is None:
                continue
            yield RateRow(
                authority_name=_authority_name(record.jurisdiction_code, authority_type),
                authority_type=authority_type,  # type: ignore[arg-type]
                rate_pct=record.general_rate * 100,
                effective_from=record.effective_from,
                effective_to=record.effective_to,
                parent_authority_name="Wisconsin" if authority_type != "state" else None,
            )

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]:
        """Parse a WI SST boundary file into normalized BoundaryRow records."""
        del version_label
        for record in parse_boundary_csv(open_sst_csv(source_file)):
            if record.record_type != "z":
                continue
            if not record.zip5_low:
                continue
            if record.county_fips:
                yield BoundaryRow(
                    authority_name=_authority_name(record.county_fips, "county"),
                    authority_type="county",
                    zip5=record.zip5_low,
                    zip4_low=None,
                    zip4_high=None,
                )

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return WI's taxability rule for a category on the given date."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for WI in Phase 1."""
        return iter(())


def _authority_name(code: str, authority_type: str) -> str:
    """Build a deterministic authority name from a SST jurisdiction code."""
    if authority_type == "state":
        return "Wisconsin"
    return f"WI-{authority_type}-{code}"


_PROTOCOL_CHECK: StateModule = Wisconsin()
del _PROTOCOL_CHECK

WISCONSIN = register(Wisconsin())
