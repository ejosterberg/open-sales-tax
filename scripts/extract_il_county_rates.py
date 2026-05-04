# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Extract Illinois per-county base sales tax rates from the IDOR
machine-readable rate file.

Source
------
Illinois Department of Revenue publishes a machine-readable file of all
sales tax rates by jurisdiction at::

    https://tax.illinois.gov/content/dam/soi/en/web/tax/research/
    taxrates/documents/salestaxrates/ordmache-current.txt

It's a fixed-width text file with one row per jurisdiction. County-level
rows have a code in the form ``XXX-5000-Y`` (the ``5000`` literal marks
a county; ``XXX`` is IDOR's internal county number; ``Y`` is a check
digit). Per the IDOR layout doc the row format is::

    [3]  IDOR county number
    [-]  literal "-"
    [4]  jurisdiction code (5000 for county-base)
    [-]  literal "-"
    [1]  check digit
    [25] jurisdiction name
    [25] county name
    [1]  home-rule flag (Y/N)
    [8]  effective date YYYYMMDD
    [5]  current combined GENERAL MERCHANDISE rate, no decimal point
         (e.g. "06500" -> 6.5000%)
    ...  more fields (use tax, food/drug rate, etc) we ignore

The combined rate at a county-base row is::

    state 6.25% + county-portion + RTA-portion (if county is in RTA)

To recover the bare ``county-portion`` we subtract:

- 6.250% (statewide)
- 1.000% if the county is Cook (Cook County RTA tier)
- 0.750% if the county is DuPage / Kane / Lake / McHenry / Will (collar
  counties — RTA service area)
- 0% otherwise

Per 35 ILCS 120/2-10 (state ROT base rate) and 70 ILCS 3615/4.03 (RTA
authority).

Usage::

    python scripts/extract_il_county_rates.py path/to/ordmache-current.txt

Re-run this against any future IDOR publication; the file URL above is
re-published each Jan 1 and Jul 1 when rates change. Emit the new dict
into ``src/opensalestax/states/il_data.py``.
"""

from __future__ import annotations

import sys
from decimal import Decimal
from pathlib import Path

STATE_RATE = Decimal("6.250")
RTA_COOK = Decimal("1.000")
RTA_COLLAR = Decimal("0.750")

COOK_COUNTIES = {"COOK"}
COLLAR_COUNTIES = {"DUPAGE", "KANE", "LAKE", "MCHENRY", "WILL"}

# Map IDOR's all-uppercase county-name spelling to the friendly name
# used by ``opensalestax.data.county_names.COUNTY_NAMES`` (which is the
# key used in ``IL_COUNTY_RATE_PCT``). Most names are simple title-case
# of the IDOR uppercase; a handful diverge:
NAME_MAP: dict[str, str] = {
    "DEKALB": "DeKalb County",
    "DEWITT": "De Witt County",
    "DE WITT": "De Witt County",
    "DUPAGE": "DuPage County",
    "JO DAVIESS": "Jo Daviess County",
    "JODAVIESS": "Jo Daviess County",
    "LASALLE": "LaSalle County",
    "LA SALLE": "LaSalle County",
    "MCDONOUGH": "McDonough County",
    "MCHENRY": "McHenry County",
    "MCLEAN": "McLean County",
    "ROCK ISLAND": "Rock Island County",
    "ST. CLAIR": "St. Clair County",
    "ST CLAIR": "St. Clair County",
    "SAINT CLAIR": "St. Clair County",
}


def normalize_county(idor_name: str) -> str:
    """Return canonical friendly name for an IDOR uppercase county string."""
    n = idor_name.strip().upper()
    if n in NAME_MAP:
        return NAME_MAP[n]
    # Default: title-case + " County" suffix.
    return f"{n.title()} County"


def parse(file_path: Path) -> dict[str, Decimal]:
    """Return county_friendly_name -> Decimal county-portion percentage."""
    out: dict[str, Decimal] = {}
    text = file_path.read_text()
    for line in text.splitlines():
        if len(line) < 80:
            continue
        # Slice (per IDOR layout doc; verified against ADAMS COUNTY row):
        #   [0:10]   code "XXX-NNNN-C" (10 chars including check digit)
        #   [10:35]  jurisdiction name (25 chars, space-padded)
        #   [35:60]  county name (25 chars, space-padded)
        #   [60:61]  home-rule flag Y/N
        #   [61:69]  effective date YYYYMMDD
        #   [69:74]  current combined GENERAL MERCHANDISE rate (5 digits,
        #            implied 3-decimal-place; "06500" = 6.500%)
        code = line[0:10]
        if code[3] != "-" or code[8] != "-":
            continue
        if code[4:8] != "5000":
            continue
        name = line[10:35].strip()
        county_name = line[35:60].strip()
        if not name.endswith("COUNTY"):
            continue
        date_field = line[61:69]
        rate_field = line[69:74]
        if not date_field.isdigit() or not rate_field.isdigit():
            continue
        # 5-digit rate with implied 3-decimal-place: "06500" -> 6.500%
        combined = Decimal(rate_field) / Decimal(1000)
        canonical = normalize_county(county_name)
        # RTA carve-out:
        county_upper = county_name.strip().upper().replace(".", "")
        if county_upper in COOK_COUNTIES:
            rta = RTA_COOK
        elif county_upper in COLLAR_COUNTIES:
            rta = RTA_COLLAR
        else:
            rta = Decimal("0")
        portion = (combined - STATE_RATE - rta).quantize(Decimal("0.001"))
        if portion < 0:
            portion = Decimal("0.000")
        out[canonical] = portion
    return dict(sorted(out.items()))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    rates = parse(path)
    print(f"# Extracted {len(rates)} IL county base rates from {path.name}")
    for county, rate in rates.items():
        print(f'    "{county}": Decimal("{rate}"),')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
