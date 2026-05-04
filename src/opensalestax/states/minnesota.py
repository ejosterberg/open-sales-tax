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

from opensalestax.data.county_names import county_name as _generic_county_name
from opensalestax.data.sst import open_sst_csv
from opensalestax.data.sst_parser import parse_boundary_csv, parse_rates_csv
from opensalestax.states.mn_names import (
    city_name as _mn_city_name,
)
from opensalestax.states.mn_names import (
    district_name as _mn_district_name,
)
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

        Emits multiple bindings per ZIP: state, county (always),
        plus city and special-district (where the SST file
        records them). The MN DOR sales-tax-rate calculator at
        revenue.state.mn.us/sales-tax-rate-calculator stacks these
        same authorities.

        Both record types contribute:
        - ``z`` records cover ZIP5 RANGES (``zip5_low`` may differ
          from ``zip5_high``; e.g. one Dakota County row covers
          55120-55124 in a single record). The range is expanded
          to one boundary per ZIP in [low, high] inclusive.
        - ``4`` records carry ZIP+4 ranges (zip4_low/high) for
          address-precision matching at a single ZIP5.

        Per-ZIP de-duplication keeps the boundary table compact:
        the same (authority, zip5, zip4_low, zip4_high) tuple is
        only emitted once per parse pass.
        """
        del version_label
        seen: set[tuple[str, str, str, str | None, str | None]] = set()
        for record in parse_boundary_csv(open_sst_csv(source_file)):
            if record.record_type not in {"z", "4"}:
                continue
            if not record.zip5_low:
                continue
            zip4_low = record.zip4_low if record.record_type == "4" else None
            zip4_high = record.zip4_high if record.record_type == "4" else None

            for zip5 in _expand_zip5_range(record.zip5_low, record.zip5_high):
                for authority_type, authority_name in self._authority_bindings(record):
                    key = (authority_type, authority_name, zip5, zip4_low, zip4_high)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield BoundaryRow(
                        authority_name=authority_name,
                        authority_type=authority_type,
                        zip5=zip5,
                        zip4_low=zip4_low,
                        zip4_high=zip4_high,
                    )

    @staticmethod
    def _authority_bindings(record):
        """Yield (authority_type, authority_name) pairs for one boundary record.

        Order matches the engine's display preference (state ->
        county -> city -> district) so the per-jurisdiction
        breakdown reads top-down.
        """
        yield ("state", "Minnesota")
        if record.county_fips:
            yield ("county", _authority_name(record.county_fips, "county"))
        if record.city_code:
            yield ("city", _authority_name(record.city_code, "city"))
        if record.district_code:
            yield ("district", _authority_name(record.district_code, "district"))

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


def _expand_zip5_range(low: str, high: str) -> Iterable[str]:
    """Yield each ZIP5 in the inclusive [low, high] range.

    SST z-records can collapse runs of contiguous ZIP5s into a
    single row (e.g. 55120-55124). Expanding here keeps the
    downstream emit-one-boundary-per-zip logic simple. Falls back
    to a single-element iter when low == high or when the bounds
    aren't both 5-digit numerics.
    """
    if not low.isdigit() or len(low) != 5:
        return
    if not high or not high.isdigit() or len(high) != 5 or high < low:
        yield low
        return
    for n in range(int(low), int(high) + 1):
        yield f"{n:05d}"


def _authority_name(code: str, authority_type: str) -> str:
    """Return the friendly authority name for a SST jurisdiction code.

    Looks up the human-readable name from
    :mod:`opensalestax.states.mn_names` -- the curated MN DOR
    Fact Sheet 164 / 164S table -- so that calculator output
    ("Minneapolis", "Hennepin County", "Hennepin County Transit
    Sales Tax") matches what the MN DOR's calculator and what
    M.S. 297A.99 requires on retail receipts.

    Falls back to ``MN-<type>-<code>`` for any code not yet in
    the lookup -- a clear placeholder that surfaces gaps without
    silently breaking the load.
    """
    if authority_type == "state":
        return "Minnesota"
    if authority_type == "county":
        name = _generic_county_name("MN", code)
        if name is not None:
            return name
    elif authority_type == "city":
        name = _mn_city_name(code)
        if name is not None:
            return name
    elif authority_type == "district":
        name = _mn_district_name(code)
        if name is not None:
            return name
    return f"MN-{authority_type}-{code}"


# Compile-time check + register
_PROTOCOL_CHECK: StateModule = Minnesota()
del _PROTOCOL_CHECK

MINNESOTA = register(Minnesota())
