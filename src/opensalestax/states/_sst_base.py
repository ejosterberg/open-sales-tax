# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Generic base class for tier-2 SST state modules.

The 22 SST member states that aren't tier-1 (MN, WI) all share
the same SST file format (validated 2026-05-03 against MN and WI;
strongly suspected to be uniform across the membership). Each
gets a small concrete subclass providing only the state-specific
metadata; all parsing is inherited.

Tier-2 modules use a **default taxability matrix**: everything
taxable except groceries. State maintainers can promote their
state to tier 1 by overriding ``taxability_for`` with state-
specific rules grounded in their statutory research.

This base satisfies the :class:`StateModule` Protocol structurally;
each subclass need only set the four metadata class attributes
and (optionally) override ``taxability_for``.
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
    StateTier,
    TaxabilityRule,
)

# Default jurisdiction-type code mapping; overridden per-state if
# a state's SST file uses different codes.
_DEFAULT_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Default taxability matrix for tier-2 states.
# Categories not listed default to taxable (calculator's behavior).
_DEFAULT_TAXABILITY: dict[str, TaxabilityRule] = {
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Default tier-2 rule: groceries treated as non-taxable. "
            "State maintainer should verify against their DOR; many "
            "but not all SST states exempt food and food ingredients."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class SstStateModule:
    """Generic StateModule base for SST member states with rate-only support.

    Subclasses MUST set: ``state_abbrev``, ``state_name``,
    ``sst_member`` (typically True), ``has_sales_tax`` (True for
    SST members), ``tier`` (typically 2), ``state_fips`` (the FIPS
    code SST uses in column 1 of the rate file).

    Subclasses MAY override: ``taxability_for`` to provide state-
    specific rules; ``parse_rates``/``parse_boundaries`` if their
    SST file deviates from the canonical layout.
    """

    state_abbrev: str = "??"
    state_name: str = "Unknown"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 2
    state_fips: str = ""

    # State-specific overrides may extend or replace these.
    jurisdiction_types: dict[str, str] = _DEFAULT_JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _DEFAULT_TAXABILITY

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """Generic SST rates parser; subclasses rarely override."""
        del version_label
        for record in parse_rates_csv(open_sst_csv(source_file)):
            authority_type = self.jurisdiction_types.get(record.jurisdiction_type)
            if authority_type is None:
                continue
            yield RateRow(
                authority_name=self._authority_name(record.jurisdiction_code, authority_type),
                authority_type=authority_type,  # type: ignore[arg-type]
                rate_pct=record.general_rate * 100,
                effective_from=record.effective_from,
                effective_to=record.effective_to,
                parent_authority_name=(self.state_name if authority_type != "state" else None),
            )

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]:
        """Generic SST boundary parser yielding state + county + city + district.

        Both ``z`` (ZIP5) and ``4`` (ZIP+4) records contribute. The
        z-records' ZIP5 range (zip5_low..zip5_high) is expanded
        inclusively -- one Dakota County row covering 55120-55124
        becomes 5 boundaries -- so single-row range coverage isn't
        silently dropped.
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

    def _authority_bindings(self, record):
        """Yield (authority_type, authority_name) pairs for one boundary record."""
        yield ("state", self.state_name)
        if record.county_fips:
            yield ("county", self._authority_name(record.county_fips, "county"))
        if record.city_code:
            yield ("city", self._authority_name(record.city_code, "city"))
        if record.district_code:
            yield ("district", self._authority_name(record.district_code, "district"))

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return the default tier-2 taxability rule for a category."""
        del effective_date
        return self.taxability.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked by tier-2 modules."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """No sales-tax holidays tracked by default tier-2 modules."""
        del year
        return iter(())

    # ---- helpers ----------------------------------------------------------
    def _authority_name(self, code: str, authority_type: str) -> str:
        if authority_type == "state":
            return self.state_name
        return f"{self.state_abbrev}-{authority_type}-{code}"

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.state_abbrev} tier={self.tier}>"


def _expand_zip5_range(low: str, high: str) -> Iterable[str]:
    """Yield each ZIP5 in the inclusive [low, high] range.

    SST z-records can collapse runs of contiguous ZIP5s into a
    single row (e.g. one Dakota County row covers 55120-55124).
    Expanding here keeps the downstream emit-one-boundary-per-zip
    logic simple.
    """
    if not low.isdigit() or len(low) != 5:
        return
    if not high or not high.isdigit() or len(high) != 5 or high < low:
        yield low
        return
    for n in range(int(low), int(high) + 1):
        yield f"{n:05d}"
