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

logger = logging.getLogger(__name__)

# Column counts from specs/research/sst-file-format.md
RATES_COLUMNS = 9
BOUNDARY_COLUMNS = 89

# Sentinel for "no end date" -- SST uses 29991231 to mean indefinite
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
    """One parsed `z`-type row from an SST boundary CSV.

    Phase 1 only consumes ``z`` (ZIP-range) records. ``4`` (FIPS+9-digit-ZIP)
    records are parsed but yielded with ``record_type="4"`` and only the
    common columns populated; tier-2 modules can ignore them. Phase 4 will
    grow this dataclass to cover FIPS+9-digit-ZIP details.
    """

    record_type: str  # 'z' or '4'
    effective_from: dt.date
    effective_to: dt.date | None
    zip5_low: str
    zip5_high: str
    state_fips: str
    county_fips: str | None
    raw_columns: tuple[str, ...]
    """All 89 columns retained for state-specific column extraction."""


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
                general_rate=Decimal(cols[3]),
                food_rate=Decimal(cols[4]),
                drug_rate=Decimal(cols[5]),
                residential_utility_rate=Decimal(cols[6]),
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
        if len(cols) != BOUNDARY_COLUMNS:
            logger.warning(
                "boundary row %d has %d columns, expected %d; skipping",
                line_num,
                len(cols),
                BOUNDARY_COLUMNS,
            )
            continue

        record_type = cols[0]
        if record_type not in {"z", "4"}:
            logger.warning(
                "boundary row %d has unknown record type %r; skipping",
                line_num,
                record_type,
            )
            continue

        try:
            zip5_low = cols[17] or ""
            zip5_high = cols[19] or zip5_low
            yield SstBoundaryRecord(
                record_type=record_type,
                effective_from=_parse_date(cols[1]),
                effective_to=_parse_end_date(cols[2]),
                zip5_low=zip5_low,
                zip5_high=zip5_high,
                state_fips=cols[22],
                county_fips=cols[24] or None,
                raw_columns=tuple(cols),
            )
        except ValueError as exc:
            logger.warning("boundary row %d failed to parse: %s; skipping", line_num, exc)
            continue


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


def _parse_date(raw: str) -> dt.date:
    """Parse a YYYYMMDD string to a date."""
    if len(raw) != 8 or not raw.isdigit():
        raise ValueError(f"invalid date {raw!r}")
    return dt.date(int(raw[:4]), int(raw[4:6]), int(raw[6:]))


def _parse_end_date(raw: str) -> dt.date | None:
    """Parse a YYYYMMDD string; treat the SST 29991231 sentinel as None (open-ended)."""
    if raw == NO_END_DATE:
        return None
    return _parse_date(raw)
