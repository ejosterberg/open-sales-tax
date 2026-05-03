# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Minnesota state module (tier 1).

MN is a Streamlined Sales Tax member. State base rate is 6.875%
(confirmed via the published MN DOR rate and the SST quarterly
file). Local additions vary by jurisdiction:

- counties typically add 0.0%-0.5%
- cities often add 0.5%-1.0%
- the Twin Cities metro transit-improvement area adds another
  0.5%-1.5%

Per :mod:`specs.research.sst-file-format`, MN's SST rate file
uses these jurisdiction-type codes (empirical, validated against
2026Q2 data):

- ``45`` = state (single row carrying 6.875%)
- ``00`` = county
- ``01`` = city / local
- ``63`` = special district (transit, etc.)

Taxability deviations from "everything is taxable":

- **Clothing** -- non-taxable (Minnesota Statutes 297A.67 subd 8).
  This is the contrast case with WI, where clothing IS taxable.
- **Groceries** -- non-taxable (food and food ingredients,
  297A.61 subd 31).
- **Prescription drugs** -- non-taxable (297A.67 subd 7).
- **Prepared food** -- taxable (the "restaurant exception").
- **Digital goods** -- taxable as of 2013 legislation.

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
    HolidayWindow,
    RateRow,
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# ---------------------------------------------------------------------------
# MN-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Static taxability matrix per Minnesota Statutes chapter 297A.
# Categories not listed default to taxable (calculator's behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=False,
        notes="Clothing is non-taxable in Minnesota (Minn. Stat. 297A.67 subd 8).",
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes="Food and food ingredients are non-taxable (Minn. Stat. 297A.61 subd 31).",
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable (Minn. Stat. 297A.67 subd 7).",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable (the restaurant exception).",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Minnesota as of 2013.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Minnesota:
    """Minnesota state module."""

    state_abbrev: str = "MN"
    state_name: str = "Minnesota"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """Parse an MN SST rates file into normalized RateRow records.

        Skips rows whose jurisdiction-type isn't recognized -- they
        won't be loaded into the rate engine but the rest of the
        file is still ingested. Future quarters that introduce new
        type codes will surface as gaps in coverage rather than
        silent miscalculations.
        """
        del version_label  # kept for Protocol; per-row version comes from data_version
        for record in parse_rates_csv(open_sst_csv(source_file)):
            authority_type = _JURISDICTION_TYPE.get(record.jurisdiction_type)
            if authority_type is None:
                continue
            yield RateRow(
                authority_name=_authority_name(record.jurisdiction_code, authority_type),
                authority_type=authority_type,  # type: ignore[arg-type]
                rate_pct=record.general_rate * 100,  # SST stores 0.06875, we want 6.875
                effective_from=record.effective_from,
                effective_to=record.effective_to,
                parent_authority_name="Minnesota" if authority_type != "state" else None,
            )

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]:
        """Parse an MN SST boundary file into normalized BoundaryRow records.

        Phase 1 only emits ZIP5-range records; Phase 4 will extend
        this with ZIP+4 + address-level data from the ``4`` records.
        """
        del version_label
        for record in parse_boundary_csv(open_sst_csv(source_file)):
            if record.record_type != "z":
                continue
            if not record.zip5_low:
                continue
            # County row -- assign to the county authority for that FIPS code.
            if record.county_fips:
                yield BoundaryRow(
                    authority_name=_authority_name(record.county_fips, "county"),
                    authority_type="county",
                    zip5=record.zip5_low,
                    zip4_low=None,
                    zip4_high=None,
                )

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return MN's taxability rule for a category on the given date.

        ``effective_date`` is accepted for the Protocol but Phase 1
        treats every rule as currently in force; we'll add date-
        gated overrides when the legislative-history layer lands.
        """
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for MN in Phase 1."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Minnesota has no annual sales-tax holidays."""
        del year
        return iter(())


def _authority_name(code: str, authority_type: str) -> str:
    """Build a deterministic authority name from a SST jurisdiction code.

    Phase 1 doesn't have a code->human-name lookup table (that's
    Phase 5 work). Names follow ``MN-<TYPE>-<CODE>`` so the engine
    can group authorities consistently and integrators can join
    against external code lists when needed.
    """
    if authority_type == "state":
        return "Minnesota"
    return f"MN-{authority_type}-{code}"


# Compile-time check + register
_PROTOCOL_CHECK: StateModule = Minnesota()
del _PROTOCOL_CHECK

MINNESOTA = register(Minnesota())
