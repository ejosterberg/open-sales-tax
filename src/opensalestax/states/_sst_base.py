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
from collections.abc import Iterable, Mapping
from pathlib import Path

from opensalestax.data.county_names import county_name as _county_name
from opensalestax.data.sst import open_sst_csv
from opensalestax.data.sst_parser import parse_boundary_csv, parse_rates_csv
from opensalestax.data.zip_state import zip_in_state
from opensalestax.states.protocol import (
    BoundaryRow,
    HolidayWindow,
    RateRow,
    SpecialCase,
    StateTier,
    TaxabilityRule,
)

# Default jurisdiction-type code mapping. Empirically validated
# against every SST member state's 2024-2026 quarterly rate file:
#
# - **state**: all states use ``45``.
# - **county**: most use ``00``; NC / NV / TN use single-digit ``0``.
# - **city**: most use ``01``; TN / VT use single-digit ``1``.
# - **district**: ``63`` is the dominant code, but several states
#   publish additional district categories under different codes:
#   - ``02`` -- Vermont local-option taxes
#   - ``49`` -- South Dakota tribal / reservation districts
#   - ``69`` -- Arkansas / Wyoming special-purpose districts
#   - ``79`` -- Kansas / North Carolina / Tennessee transit / sports
#     authority districts
#
# Including all known codes here means most state modules don't
# need an override; per-state subclasses can still narrow or
# extend by setting ``jurisdiction_types`` explicitly.
_DEFAULT_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "0": "county",
    "01": "city",
    "1": "city",
    "02": "district",
    "2": "district",
    "49": "district",
    "63": "district",
    "69": "district",
    "79": "district",
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
    # Per-state jurisdiction-type code -> engine authority-type mapping.
    # A value of None signals "skip rate rows of this type entirely" --
    # used by states (e.g. TN) where the SST file uses a code that
    # encodes a county-equivalent overlay already collapsed into the
    # city's combined local rate; loading them would double-count.
    # ``Mapping`` (covariant) lets subclasses pass ``dict[str, str]``
    # without mypy complaining about the optional value type.
    jurisdiction_types: Mapping[str, str | None] = _DEFAULT_JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _DEFAULT_TAXABILITY

    # Effective-date cutoff for boundary-file filtering. Defaults to
    # ``None``, which means ``parse_boundaries`` uses today (via
    # :meth:`_boundaries_as_of`). Tests can override per-instance to
    # pin against a specific historical snapshot.
    boundaries_as_of: dt.date | None = None

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """Generic SST rates parser; subclasses rarely override."""
        del version_label
        # Merge the inclusive default mapping with any per-state
        # override so subclasses can ADD codes (or rebind one) but
        # never accidentally drop the defaults. Pre-fix, every
        # state module shipped its own override that quietly
        # excluded the new codes added to the default (single-digit
        # '0'/'1', '49'/'69'/'79' districts), silently dropping
        # those rate rows on load.
        types = {**_DEFAULT_JURISDICTION_TYPE, **self.jurisdiction_types}
        for record in parse_rates_csv(open_sst_csv(source_file)):
            authority_type = types.get(record.jurisdiction_type)
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

        **Effective-date filtering:** SST quarterly boundary files
        retain HISTORICAL records (e.g. TN's 2026Q2 file carries
        type-z rows that bound 37027 to Brentwood (city 54780) for
        the window 2024-01-01..2024-03-31 alongside the currently
        active row that bounds 37027 to Davidson County only). The
        ``Boundary`` table has no effective_from/to columns -- so
        loading every historical row would create a forever-growing
        union of jurisdictions, double-counting cities that no
        longer apply. Filter to records active on
        :func:`_boundaries_as_of` (defaults to today) at parse time
        so only currently-effective bindings reach the DB. State
        modules can override the class attribute ``boundaries_as_of``
        when they need to load a specific historical snapshot
        (typically only useful for tests).
        """
        del version_label
        as_of = self._boundaries_as_of()
        seen: set[tuple[str, str, str, str | None, str | None]] = set()
        for record in parse_boundary_csv(open_sst_csv(source_file)):
            # 'z' = zip-wide, '4' = ZIP+4 range, 'a' = address-level
            # (VT). 'a' records are pre-collapsed by the parser to a
            # single zip5-wide binding (zip4 omitted) so the loose
            # lookup picks them up the same as 'z' rows.
            if record.record_type not in {"z", "4", "a"}:
                continue
            if not record.zip5_low:
                continue
            if not _record_active_on(record, as_of):
                continue
            zip4_low = record.zip4_low if record.record_type == "4" else None
            zip4_high = record.zip4_high if record.record_type == "4" else None

            for zip5 in _expand_zip5_range(record.zip5_low, record.zip5_high):
                # Drop cross-border ZIPs: SST publishes records that
                # claim ZIPs outside the loading state (e.g. SD's
                # quarterly carries a Z-record covering 51001-56136
                # which the range expansion would otherwise bind to
                # Minnesota / Iowa / Nebraska / Wisconsin ZIPs).
                # The Census ZCTA->county relationship file is the
                # authoritative source for "which state is this ZIP
                # physically in"; we drop any expansion that doesn't
                # match the loading state. ZIPs not in the Census
                # table (PO-box-only, business-only) pass through --
                # treating "unknown" as "trust the SST file".
                in_state = zip_in_state(zip5, self.state_abbrev)
                if in_state is False:
                    continue
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
        if authority_type == "county":
            friendly = _county_name(self.state_abbrev, code)
            if friendly is not None:
                return friendly
        return f"{self.state_abbrev}-{authority_type}-{code}"

    def _boundaries_as_of(self) -> dt.date:
        """Return the cutoff date used to filter SST boundary records.

        ``parse_boundaries`` consults this to drop expired and
        future-dated rows -- the SST boundary file otherwise carries
        years of historical bindings that, since :class:`Boundary`
        has no effective_from/to columns, would all stack on top of
        each other and create per-ZIP city/county "ghost" overlaps.
        Subclasses or test fixtures can override the
        :attr:`boundaries_as_of` class attribute to load a pinned
        historical snapshot instead of "today".
        """
        return self.boundaries_as_of or dt.date.today()

    def __repr__(self) -> str:
        return f"<{type(self).__name__} {self.state_abbrev} tier={self.tier}>"


def _record_active_on(record, as_of: dt.date) -> bool:
    """Return True when ``record`` is in effect on ``as_of``.

    Mirrors :func:`opensalestax.data.sst_parser.active_only` but is
    inlined as a per-record predicate so the boundary-parser
    generator can short-circuit before doing the more expensive
    ZIP-range expansion + per-state cross-border check.

    A record is active when:

    - ``effective_from <= as_of``, AND
    - ``effective_to`` is None (open-ended) OR ``as_of <= effective_to``.

    Records lacking an ``effective_from`` (defensively) are treated
    as active so a malformed row isn't silently dropped twice.
    """
    eff_from = getattr(record, "effective_from", None)
    eff_to = getattr(record, "effective_to", None)
    if eff_from is not None and eff_from > as_of:
        return False
    return not (eff_to is not None and eff_to < as_of)


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
