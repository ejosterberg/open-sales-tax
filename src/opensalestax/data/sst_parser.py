# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Parse SST quarterly CSV files into raw row dicts.

This is the *generic* parser. State modules consume the raw rows
yielded here and build :class:`~opensalestax.states.protocol.RateRow`
or :class:`~opensalestax.states.protocol.BoundaryRow` records from
them. Per the format research in
``specs/research/sst-file-format.md``, the layout is fixed but
column meanings vary slightly across states (especially the
jurisdiction-type code in column 2 of the rates file).

This parser:

- Splits each line by comma
- Validates the row has the expected number of columns (9 for
  rates, 89 for boundaries)
- Skips empty lines and rows that don't parse
- Logs (via the standard logging module) but does not raise on
  individual bad rows -- one corrupt row in a 40k-row file
  shouldn't prevent the rest from loading
"""

from __future__ import annotations

import datetime as dt
import logging
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

logger = logging.getLogger(__name__)

# Column counts from specs/research/sst-file-format.md
RATES_COLUMNS = 9
BOUNDARY_COLUMNS = 89

# Sentinels for "no end date". States have shipped at least two:
# - 29991231 (used by MN -- year 2999)
# - 99991231 (used by WI -- year 9999, the more common ISO sentinel)
NO_END_DATE_SENTINELS = frozenset({"29991231", "99991231"})

# Backwards-compatible alias for the original sentinel
NO_END_DATE = "29991231"


@dataclass(frozen=True, slots=True)
class SstRateRecord:
    """One parsed row from an SST rates CSV.

    Field meanings per the empirical layout in
    ``specs/research/sst-file-format.md``. Column 2 ``jurisdiction_type``
    is state-specific; state modules interpret it in their own
    ``parse_rates``.
    """

    state_fips: str
    jurisdiction_type: str
    jurisdiction_code: str
    general_rate: Decimal
    food_rate: Decimal
    drug_rate: Decimal
    residential_utility_rate: Decimal
    effective_from: dt.date
    effective_to: dt.date | None  # None for the SST 29991231 sentinel


@dataclass(frozen=True, slots=True)
class SstBoundaryRecord:
    """One parsed `z`- or `4`-type row from an SST boundary CSV.

    Both record types share the state/county/city columns. ``4``
    records additionally carry ZIP+4 ranges (zip4_low/high) for
    address-precision matching; ``z`` records cover the full ZIP5
    with no +4 narrowing. Both record types may also carry a
    special-district binding (intra_state_class + jurisdiction
    code/type), which the rate file's type-63 rows match against
    via ``district_code``.

    Column reference (1-indexed; SST publishes the layout in their
    Boundary File Format Specification, validated against MN/WI
    2026Q2 + cross-checked against the MN DOR sales-tax-rate
    calculator):

    - col18 zip5_low / col19 zip4_low / col20 zip5_high /
      col21 zip4_high  -> address range
    - col23 state FIPS / col25 county FIPS / col26 city code
    - col30 intra-state class ('ST' = special district, 'IN' =
      municipal/intra-state, blank = no extra binding)
    - col31 SST jurisdiction code (matches col3 in the rate file)
    - col32 SST jurisdiction type (matches col2 in the rate file)
    """

    record_type: str  # 'z' (zip-wide), '4' (zip+4 range), or 'a' (address-level)
    effective_from: dt.date
    effective_to: dt.date | None
    zip5_low: str
    zip5_high: str
    zip4_low: str | None
    zip4_high: str | None
    state_fips: str
    county_fips: str | None
    city_code: str | None
    """SST city/local jurisdiction code from col26. Maps to the
    ``jurisdiction_code`` of a type-01 (city) rate row."""

    intra_state_class: str | None
    """col30: 'ST' = special district, 'IN' = intra-state /
    municipal, blank = no extra binding."""

    district_code: str | None
    """col31: SST jurisdiction code for a special district.
    Maps to the ``jurisdiction_code`` of a non-state rate row
    whose ``jurisdiction_type`` equals ``district_type``."""

    district_type: str | None
    """col32: SST jurisdiction-type code (matches type-63 etc.)."""

    raw_columns: tuple[str, ...]
    """All 89+ columns retained for state-specific column extraction."""


def parse_rates_csv(lines: Iterable[str]) -> Iterator[SstRateRecord]:
    """Parse SST rates-file lines into :class:`SstRateRecord` instances.

    Lines that fail to parse are logged at WARNING and skipped --
    one bad row shouldn't sink the whole file load.
    """
    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        cols = stripped.split(",")
        if len(cols) != RATES_COLUMNS:
            logger.warning(
                "rates row %d has %d columns, expected %d; skipping",
                line_num,
                len(cols),
                RATES_COLUMNS,
            )
            continue

        try:
            yield SstRateRecord(
                state_fips=cols[0],
                jurisdiction_type=cols[1],
                jurisdiction_code=cols[2],
                # general_rate must parse strictly: a blank value is the
                # SST file's signal that a row is a special-purpose stub
                # (CID/TDD-style local-improvement districts on KS, etc.)
                # that should NOT contribute to the general retail rate
                # stack. v0.54.x briefly relaxed this to Decimal(0) and
                # silently broke KS Lawrence/Salina/Wichita post-reload --
                # see specs/security/audit-2026-05-04.md for the regression
                # writeup. The 18 VT type-02 legacy rows the relaxation
                # was meant to preserve are an acceptable loss; their
                # boundaries are absent from the live grid anyway.
                general_rate=Decimal(cols[3]),
                # food/drug/residential-utility rate columns are still
                # tolerated as blank since those columns are routinely
                # empty on rows with a valid general_rate (the "rate"
                # for a category that just falls through to general).
                food_rate=_decimal_or_zero(cols[4]),
                drug_rate=_decimal_or_zero(cols[5]),
                residential_utility_rate=_decimal_or_zero(cols[6]),
                effective_from=_parse_date(cols[7]),
                effective_to=_parse_end_date(cols[8]),
            )
        except (ValueError, InvalidOperation) as exc:
            logger.warning("rates row %d failed to parse: %s; skipping", line_num, exc)
            continue


def parse_boundary_csv(lines: Iterable[str]) -> Iterator[SstBoundaryRecord]:
    """Parse SST boundary-file lines into :class:`SstBoundaryRecord` instances."""
    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped:
            continue

        cols = stripped.split(",")
        # Tolerate trailing columns: newer SST quarterlies (SD 2026Q2,
        # WA 2026Q2) ship 90-column rows; older schema is 89. Reject
        # only when the row is too SHORT to safely index core fields.
        if len(cols) < BOUNDARY_COLUMNS:
            logger.warning(
                "boundary row %d has %d columns, expected at least %d; skipping",
                line_num,
                len(cols),
                BOUNDARY_COLUMNS,
            )
            continue

        # SST publishes record-type codes in either case ("z" / "Z",
        # "4", "a" / "A"). Normalize to lowercase so downstream
        # consumers can compare without worrying about file-by-file
        # casing.
        record_type = cols[0].lower()
        if record_type not in {"z", "4", "a"}:
            logger.warning(
                "boundary row %d has unknown record type %r; skipping",
                line_num,
                cols[0],
            )
            continue

        try:
            if record_type == "a":
                # Address-level rows (used by VT) carry a single ZIP+4
                # at cols 15/16 instead of the col-17..21 range used
                # by 'z'/'4' rows. We collapse 'a' rows to a zip5-wide
                # binding (zip4 omitted) so a million per-street rows
                # don't bloat the boundaries table; the loose lookup
                # only needs to know "this ZIP is in this city".
                zip5_low = cols[15] or ""
                zip5_high = zip5_low
                zip4_low_padded: str = ""
                zip4_high_padded: str = ""
            else:
                zip5_low = cols[17] or ""
                zip5_high = cols[19] or zip5_low
                zip4_low_raw = cols[18] or ""
                zip4_high_raw = cols[20] or zip4_low_raw
                # Zero-pad +4 ranges to 4 chars so downstream string
                # comparison ("0001" <= "1015" <= "0007") behaves
                # numerically. The SST file publishes "1" instead of
                # "0001" when the leading digits are zero; without
                # padding, "1015" lexicographically falls between "1"
                # and "7", spuriously matching every range that starts
                # at "1" (e.g. OK 73072-1015 was matched against Norman
                # ranges 1..7, 1..9 and McClain ranges 1..11).
                zip4_low_padded = (
                    zip4_low_raw.zfill(4) if record_type == "4" and zip4_low_raw else zip4_low_raw
                )
                zip4_high_padded = (
                    zip4_high_raw.zfill(4)
                    if record_type == "4" and zip4_high_raw
                    else zip4_high_raw
                )
            common: dict[str, Any] = {
                "record_type": record_type,
                "effective_from": _parse_date(cols[1]),
                "effective_to": _parse_end_date(cols[2]),
                "zip5_low": zip5_low,
                "zip5_high": zip5_high,
                # ZIP+4 fields populated only on type-4 rows; 'z' and
                # 'a' rows leave them None so the engine's "no +4
                # range" branch matches (treat as zip-wide).
                "zip4_low": (zip4_low_padded or None) if record_type == "4" else None,
                "zip4_high": (zip4_high_padded or None) if record_type == "4" else None,
                "state_fips": cols[22],
                # 'a' rows in VT leave county_fips blank; the city
                # code (col 25) is the binding we care about.
                "county_fips": cols[24] or None,
                "city_code": cols[25] or None,
                "raw_columns": tuple(cols),
            }
        except ValueError as exc:
            logger.warning("boundary row %d failed to parse: %s; skipping", line_num, exc)
            continue

        # Each boundary row can bind the ZIP to MULTIPLE special
        # districts in repeating triplets starting at col30
        # (intra_state_class, jurisdiction_code, jurisdiction_type).
        # MN ZIP 55417, e.g., is bound to Hennepin County Transit
        # (80004) at col30-32, Metro Area Transportation (80008) at
        # col36-38, and Metro Area Tax for Housing (80009) at
        # col39-41. We yield one SstBoundaryRecord per non-blank
        # triplet so each district produces its own boundary; if
        # the row has no district triplets we still yield a single
        # record so state/county/city bindings are emitted.
        #
        # Skip triplets whose type is "45" (state) -- those are
        # location-reference codes (e.g. WA's L1704 / L1708 alternate
        # location IDs that all point at the state row, not real
        # districts). Treating them as districts double-counts the
        # state rate per code (WA Bellevue would otherwise return
        # 29.3% from 5 phantom L-code "districts" at 3.8% each on
        # top of the real state + city).
        triplets: list[tuple[str | None, str | None, str | None]] = []
        for start in range(29, len(cols) - 2, 3):
            cls = cols[start] or None
            code = cols[start + 1] or None
            type_ = cols[start + 2] or None
            if not (cls or code or type_):
                continue
            if type_ == "45":
                continue
            triplets.append((cls, code, type_))

        if not triplets:
            yield SstBoundaryRecord(
                **common,
                intra_state_class=None,
                district_code=None,
                district_type=None,
            )
            continue

        for cls, code, type_ in triplets:
            yield SstBoundaryRecord(
                **common,
                intra_state_class=cls,
                district_code=code,
                district_type=type_,
            )


def active_only(
    records: Iterable[SstRateRecord | SstBoundaryRecord],
    as_of: dt.date | None = None,
) -> Iterator[SstRateRecord | SstBoundaryRecord]:
    """Filter to records active on ``as_of`` (default: today)."""
    target = as_of or dt.date.today()
    for record in records:
        if record.effective_from > target:
            continue
        if record.effective_to is not None and record.effective_to < target:
            continue
        yield record


def _decimal_or_zero(raw: str) -> Decimal:
    """Parse a rate string; return Decimal(0) for blanks.

    SST rate files occasionally leave food/drug/utility rate
    columns blank on legacy district rows (e.g. VT type-02 rows
    that pre-date the SST food-and-food-ingredients category
    breakout). Without this helper, ``Decimal('')`` raises
    ``InvalidOperation`` and the row is dropped entirely -- which
    silently loses the row's general_rate too.
    """
    if not raw:
        return Decimal("0")
    return Decimal(raw)


def _parse_date(raw: str) -> dt.date:
    """Parse a YYYYMMDD string to a date."""
    if len(raw) != 8 or not raw.isdigit():
        raise ValueError(f"invalid date {raw!r}")
    return dt.date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))


def _parse_end_date(raw: str) -> dt.date | None:
    """Parse a YYYYMMDD string; treat any open-ended sentinel as None."""
    if raw in NO_END_DATE_SENTINELS:
        return None
    return _parse_date(raw)
