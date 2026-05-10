# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""ZIP-Code-Tabulation-Area (ZCTA) -> state boundary loader.

Phase 6 ratchet: 23 of the 52 jurisdictions are "self-seeded" --
their state modules know their statewide rate but ship no SST
quarterly file (CA, TX, NY, FL, PA, IL, MD, MA, AZ, CT, DC, SC,
VA, CO, ID, LA, MO, MS, ME, AL, HI, NM, PR). Without ZIP->state
boundary rows, the engine returned "no jurisdictions found" for
every ZIP in those 23 states.

This module bridges that gap by loading the **2020 Census
ZCTA->County relationship file** (free, public-domain, ~46k
rows) into ZIP -> state boundaries:

  https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/
    tab20_zcta520_county20_natl.txt

Each row maps a ZCTA (5-digit ZIP) to a county GEOID (5 digits;
first 2 are state FIPS). The loader collapses the rows by ZCTA
and emits one BoundaryRow per (ZIP, state) pair, deduplicated
across counties so the boundaries table doesn't blow up.

This loader does NOT add county-level boundaries -- per-county
modeling for these states waits on the SubJurisdiction Protocol
work (see specs/decisions/04-colorado-home-rule.md and 05-
louisiana-parishes.md). State-level coverage alone unblocks the
demo, the connectors, and any caller that just needs the
statewide rate at a real US ZIP.
"""

from __future__ import annotations

import logging
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path

import httpx

from opensalestax.data.sst import default_data_dir
from opensalestax.data.state_fips import FIPS_TO_ABBREV

logger = logging.getLogger(__name__)


# Census 2020 ZCTA->County national relationship file. ~3 MB; cached
# locally after first download. Pin to 2020 because it's the latest
# decennial-tied file and Census promises long-term URL stability.
ZCTA_COUNTY_URL = (
    "https://www2.census.gov/geo/docs/maps-data/data/rel2020/zcta520/"
    "tab20_zcta520_county20_natl.txt"
)
ZCTA_COUNTY_FILENAME = "tab20_zcta520_county20_natl.txt"

# Pipe-delimited header layout (taken from the file itself, 2026-05-04
# verification). Columns 1-indexed for readability; we 0-index in code.
_COL_GEOID_ZCTA = 1  # the 5-digit ZCTA / ZIP code
_COL_GEOID_COUNTY = 9  # full 5-digit county GEOID (state FIPS + 3 digits)


@dataclass(frozen=True, slots=True)
class ZctaStateRow:
    """One ZIP-to-state binding derived from the Census ZCTA file."""

    zip5: str
    state_abbrev: str


@dataclass(frozen=True, slots=True)
class ZctaCountyRow:
    """One ZIP-to-county binding derived from the Census ZCTA file.

    ``county_fips`` is the 3-digit county FIPS suffix (the last three
    digits of the 5-digit county GEOID -- e.g. ``"086"`` for Miami-Dade,
    ``"037"`` for Los Angeles, ``"013"`` for Maricopa). The 2-digit
    state FIPS prefix is implicit in ``state_abbrev``.

    A single ZIP can intersect multiple counties; the parser yields one
    row per (ZIP, state, county) triple, deduplicated within the file.
    """

    zip5: str
    state_abbrev: str
    county_fips: str


def download_zcta_county_file(
    dest_dir: Path | None = None,
    *,
    timeout: float = 60.0,
) -> Path:
    """Download (and cache) the Census ZCTA->County relationship file."""
    target_dir = dest_dir or default_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / ZCTA_COUNTY_FILENAME
    if target_path.exists():
        return target_path
    with httpx.Client(timeout=timeout, follow_redirects=True) as client:
        response = client.get(ZCTA_COUNTY_URL)
        response.raise_for_status()
        target_path.write_bytes(response.content)
    return target_path


def parse_zcta_state_rows(
    source_file: Path,
    *,
    abbrev_filter: Iterable[str] | None = None,
) -> Iterator[ZctaStateRow]:
    """Parse the Census ZCTA->county file into deduped ZIP->state rows.

    Census publishes one row per (ZCTA, county) intersection -- a
    single ZIP that crosses 3 counties shows up 3 times. We collapse
    to one row per (ZIP, state) since the per-county detail isn't
    consumed at this layer (waits on SubJurisdiction work).

    ``abbrev_filter`` lets a caller restrict to a subset of states
    (e.g. just the self-seeded modules); when None, every state in
    ``FIPS_TO_ABBREV`` is emitted.

    iter-68 supplement: yields rows from
    :data:`opensalestax.data.usps_po_box_zips.USPS_PO_BOX_ZIPS` AFTER
    the Census file. PO-box-only ZIPs (e.g. Springfield MA 01101) are
    not in Census ZCTA because they have no physical delivery
    boundary, so without this supplement the engine returned 0% on
    those ZIPs in flat-rate states.
    """
    from opensalestax.data.usps_po_box_zips import USPS_PO_BOX_ZIPS

    keep: set[str] | None = None
    if abbrev_filter is not None:
        keep = {a.upper() for a in abbrev_filter}

    seen: set[tuple[str, str]] = set()
    with source_file.open(encoding="utf-8-sig") as fp:
        header_skipped = False
        for raw in fp:
            line = raw.rstrip("\r\n")
            if not line:
                continue
            if not header_skipped:
                header_skipped = True
                continue
            cols = line.split("|")
            if len(cols) <= _COL_GEOID_COUNTY:
                continue
            zip5 = cols[_COL_GEOID_ZCTA].strip()
            county_geoid = cols[_COL_GEOID_COUNTY].strip()
            if not zip5 or not county_geoid or len(county_geoid) < 2:
                continue
            state_fips = county_geoid[:2]
            abbrev = FIPS_TO_ABBREV.get(state_fips)
            if abbrev is None:
                continue
            if keep is not None and abbrev not in keep:
                continue
            key = (zip5, abbrev)
            if key in seen:
                continue
            seen.add(key)
            yield ZctaStateRow(zip5=zip5, state_abbrev=abbrev)

    # Append USPS PO-box-only ZIPs the Census file doesn't cover.
    for zip5, abbrev in USPS_PO_BOX_ZIPS.items():
        if keep is not None and abbrev not in keep:
            continue
        key = (zip5, abbrev)
        if key in seen:
            continue
        seen.add(key)
        yield ZctaStateRow(zip5=zip5, state_abbrev=abbrev)


def parse_zcta_county_rows(
    source_file: Path,
    *,
    abbrev_filter: Iterable[str] | None = None,
) -> Iterator[ZctaCountyRow]:
    """Parse the Census ZCTA->county file into deduped (ZIP, state, county) rows.

    Unlike :func:`parse_zcta_state_rows` (which collapses to one row
    per ZIP+state), this preserves the per-county breakdown so a state
    module can emit a county-level boundary for every ZIP in the
    state, regardless of whether the city is in any hand-curated seed
    list. ZIPs that cross county lines yield one row per (ZIP, state,
    county) triple.

    ``abbrev_filter`` lets a caller restrict to a subset of states
    (e.g. just ``{"FL", "AZ", "CA"}``); when None, every state in
    ``FIPS_TO_ABBREV`` is emitted.
    """
    keep: set[str] | None = None
    if abbrev_filter is not None:
        keep = {a.upper() for a in abbrev_filter}

    seen: set[tuple[str, str, str]] = set()
    with source_file.open(encoding="utf-8-sig") as fp:
        header_skipped = False
        for raw in fp:
            line = raw.rstrip("\r\n")
            if not line:
                continue
            if not header_skipped:
                header_skipped = True
                continue
            cols = line.split("|")
            if len(cols) <= _COL_GEOID_COUNTY:
                continue
            zip5 = cols[_COL_GEOID_ZCTA].strip()
            county_geoid = cols[_COL_GEOID_COUNTY].strip()
            if not zip5 or not county_geoid or len(county_geoid) != 5:
                continue
            if not county_geoid.isdigit():
                continue
            state_fips = county_geoid[:2]
            county_fips = county_geoid[2:]
            abbrev = FIPS_TO_ABBREV.get(state_fips)
            if abbrev is None:
                continue
            if keep is not None and abbrev not in keep:
                continue
            key = (zip5, abbrev, county_fips)
            if key in seen:
                continue
            seen.add(key)
            yield ZctaCountyRow(zip5=zip5, state_abbrev=abbrev, county_fips=county_fips)


def default_zcta_dir() -> Path:
    """Cache directory for the ZCTA file. Honors ``OPENSALESTAX_DATA_DIR``."""
    override = os.environ.get("OPENSALESTAX_DATA_DIR")
    if override:
        return Path(override)
    return default_data_dir()


__all__ = [
    "ZCTA_COUNTY_FILENAME",
    "ZCTA_COUNTY_URL",
    "ZctaCountyRow",
    "ZctaStateRow",
    "default_zcta_dir",
    "download_zcta_county_file",
    "parse_zcta_county_rows",
    "parse_zcta_state_rows",
]
