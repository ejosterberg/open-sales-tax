# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Extract Missouri per-county base sales tax rates from MO DOR PDF.

Reads the MO Department of Revenue Sales/Use Tax Rate Tables PDF (which
is published quarterly at https://dor.mo.gov/business/sales/rates/) and
emits a Python dict literal mapping county friendly name -> Decimal
county-portion rate (combined - state 4.225%).

Algorithm
---------

The MO DOR PDF lists every taxing jurisdiction with a 9-character code
``00000-CCC-NNN`` where ``CCC`` is the 3-digit county FIPS suffix and
``NNN`` distinguishes overlay districts.

We pick rows where:

1. The jurisdiction code ends in ``-000`` (the unincorporated-county
   base rate row), AND
2. The first line of the jurisdiction-name cell IS the county name
   (``<X> COUNTY`` or ``ST. LOUIS CITY``). Subsequent lines name any
   countywide overlays (ambulance / library / fire-protection
   districts) that are baked into the base rate -- those overlays
   apply to every address in the unincorporated county and so we
   include them in our county portion. They are NOT separable.

Then ``county_portion = combined_sales_rate - 4.225``. The result is
the rate the engine should add for any non-city ZIP in that county.

Usage::

    python scripts/extract_mo_county_rates.py path/to/jan2026.pdf

Re-run this against any future quarterly MO DOR publication; emit the
new dict into ``src/opensalestax/states/mo_data.py``. The output is
a Python dict literal that can be pasted into ``MO_COUNTY_RATE_PCT``.
"""

from __future__ import annotations

import re
import sys
from decimal import Decimal
from pathlib import Path

import pdfplumber  # type: ignore[import-untyped]

# Maps the MO DOR's UPPERCASE county-name spelling to the friendly name
# used by ``opensalestax.data.county_names.COUNTY_NAMES`` (which is the
# key used in ``MO_COUNTY_RATE_PCT``). MO DOR drops the period in the
# St-prefixed county names; we restore it.
NAME_MAP: dict[str, str] = {
    "DE KALB COUNTY": "DeKalb County",
    "DEKALB COUNTY": "DeKalb County",
    "MCDONALD COUNTY": "McDonald County",
    "STE GENEVIEVE COUNTY": "Ste. Genevieve County",
    "STE. GENEVIEVE COUNTY": "Ste. Genevieve County",
    "ST CHARLES COUNTY": "St. Charles County",
    "ST. CHARLES COUNTY": "St. Charles County",
    "ST CLAIR COUNTY": "St. Clair County",
    "ST. CLAIR COUNTY": "St. Clair County",
    "ST FRANCOIS COUNTY": "St. Francois County",
    "ST. FRANCOIS COUNTY": "St. Francois County",
    "ST LOUIS COUNTY": "St. Louis County",
    "ST. LOUIS COUNTY": "St. Louis County",
    "ST LOUIS CITY": "St. Louis city",
    "ST. LOUIS CITY": "St. Louis city",
    "CITY OF ST LOUIS": "St. Louis city",
    "CITY OF ST. LOUIS": "St. Louis city",
}

STATE_RATE = Decimal("4.225")

# Match any unincorporated-county row (jurisdiction prefix 00000) with
# any -NNN suffix. We prefer ``-000`` (the bare base) when present and
# fall back to the lowest-rate overlay row otherwise -- some counties
# (Camden, Marion, Morgan, Scott, Shelby) have NO -000 row because
# every unincorporated address sits inside at least one ambulance /
# fire-protection overlay, so the lowest overlay row IS the effective
# base for unincorporated addresses.
CODE_RE = re.compile(r"^00000-\d{3}-\d{3}$")
RATE_RE = re.compile(r"^\d+\.\d{4}%$")


def normalize_county(first_line: str) -> str | None:
    """Return the canonical friendly name if ``first_line`` is a county header."""
    n = first_line.strip().rstrip(".").upper()
    n = re.sub(r"\s+", " ", n)
    if n in NAME_MAP:
        return NAME_MAP[n]
    m = re.fullmatch(r"([A-Z]+(?: [A-Z]+)*) COUNTY", n)
    if m:
        county = m.group(1).strip().title()
        return f"{county} County"
    if n == "ST LOUIS CITY" or n == "ST. LOUIS CITY":
        return "St. Louis city"
    return None


def parse(pdf_path: Path) -> dict[str, Decimal]:
    """Return county_friendly_name -> Decimal county-portion percentage."""
    by_county: dict[str, Decimal] = {}
    has_base: dict[str, bool] = {}

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables():
                for row in table:
                    if not row or len(row) < 3:
                        continue
                    name_cell = (row[0] or "").strip()
                    code_cell = (row[1] or "").strip() if len(row) > 1 else ""
                    rate_cell = (row[2] or "").strip() if len(row) > 2 else ""
                    if not name_cell or not code_cell or not rate_cell:
                        continue
                    if not CODE_RE.fullmatch(code_cell):
                        continue
                    if not RATE_RE.fullmatch(rate_cell):
                        continue
                    first_line = name_cell.splitlines()[0]
                    county = normalize_county(first_line)
                    if not county:
                        continue
                    try:
                        combined = Decimal(rate_cell.rstrip("%"))
                    except ValueError:
                        continue
                    # Prefer -000 (true base); otherwise take the lowest
                    # rate across overlay rows. Once a -000 row is seen
                    # for a county, ignore further overlay rows for that
                    # county (the -000 row IS canonical).
                    is_base = code_cell.endswith("-000")
                    if has_base.get(county):
                        continue
                    if is_base:
                        by_county[county] = combined
                        has_base[county] = True
                        continue
                    cur = by_county.get(county)
                    if cur is None or combined < cur:
                        by_county[county] = combined

    out: dict[str, Decimal] = {}
    for county, combined in sorted(by_county.items()):
        county_portion = (combined - STATE_RATE).quantize(Decimal("0.001"))
        if county_portion < 0:
            county_portion = Decimal("0.000")
        out[county] = county_portion
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    pdf = Path(sys.argv[1])
    rates = parse(pdf)
    print(f"# Extracted {len(rates)} MO county base rates from {pdf.name}")
    for county, rate in rates.items():
        print(f'    "{county}": Decimal("{rate}"),')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
