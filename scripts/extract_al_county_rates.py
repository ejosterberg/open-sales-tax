# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Extract Alabama per-county base sales tax rates from the ALDOR
machine-readable rate file.

Source
------
The Alabama Department of Revenue publishes a comma-delimited CSV of
all state-administered local sales/use/lodging/rental tax rates at::

    https://www.revenue.alabama.gov/wp-content/uploads/2024/03/taxrates.csv

The file is updated monthly. It contains both current and historical
rows; current rows have an empty "Inactive Date" column. Schema (per
the ALDOR data dictionary):

    Locality Code      -- ALDOR's 4-digit jurisdiction code
    Locality Name      -- "AUTAUGA COUNTY", "BIRMINGHAM", etc.
    County Number      -- numeric county index (1-67)
    TaxType            -- ST=sales, SU=consumer use, CU=county-collected
                          use, RT=rental, LL=lodgings
    Rate Type          -- GENER=general retail, AUTO, FARM, GROC, MACH,
                          AMUSE, VEND, WDFEE, ALCOH, REST, etc.
    Administered       -- AVENU, SELF, STATE, RDS (collector)
    Active Date        -- YYYYMMDD
    Inactive Date      -- YYYYMMDD (empty = currently active)
    Rate               -- percentage as decimal string ("2.0000" = 2.000%)
    Indicator          -- AC=active, RC=rate change, NT=not taxable
    PJ                 -- police jurisdiction flag (Y/N or empty)
    County Code        -- linkage code
    PJ_Rate            -- PJ-only rate

For the AL_COUNTY_RATE_PCT dict in src/opensalestax/states/al_data.py
we want **the county-portion sales tax rate that applies inside city
limits** (the convention established by the v0.33 covered-city seeds:
Lauderdale 1.0% = the CL Florence rate, not the unincorporated 1.5%).

Selection rules:

1. Filter to TaxType=ST (sales tax), RateType=GENER (general retail),
   Inactive Date empty (currently active).
2. Exclude UNABATED rows (those are abatement-program reductions for
   specific industrial properties, not the prevailing rate).
3. Exclude JEFFERSON COUNTY EDUCATION (special 0.0% education line).
4. Exclude COUNTY LINE (a town named "County Line", not a county-line
   designation).
5. For each county, group all rows whose Locality Name starts with
   "<COUNTY> COUNTY" and pick:
     - the row whose name is exactly "<COUNTY> COUNTY" (the base rate)
       UNLESS a "<COUNTY> COUNTY CL" row exists county-wide (suffix
       "CL" with no city name following = the CL rate that applies
       inside ALL the county's cities; e.g. "CALHOUN COUNTY - CL",
       "CHAMBERS COUNTY CL", "RUSSELL COUNTY CL", "TALLADEGA COUNTY
       CL", "TUSCALOOSA COUNTY CL"). In that case, prefer the CL rate
       because it matches the inside-city convention used by the
       v0.33 seeds.
     - For counties where the only differentiator is a single named
       city (e.g. "MARION COUNTY CL WINFIELD", "ELMORE COUNTY CL
       PRATTVILLE", "CULLMAN COUNTY CL & PJ ARAB"), use the BASE
       "<COUNTY> COUNTY" rate (the named-city CL is a deduction that
       only applies to that one city, not county-wide).

Usage::

    curl -sLO https://www.revenue.alabama.gov/wp-content/uploads/2024/03/taxrates.csv
    python scripts/extract_al_county_rates.py taxrates.csv

Re-run against any future ALDOR publication; the file URL is stable
and the file is regenerated monthly. Emit the new dict into
``src/opensalestax/states/al_data.py``.
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

# County names that get a "CL" suffix without a city name -- these CL
# rates apply inside ALL incorporated cities in the county. For these
# counties we prefer the CL rate over the base (unincorporated) rate
# because it matches the v0.33 inside-city convention.
COUNTYWIDE_CL_NAMES = {
    "CALHOUN COUNTY - CL",
    "CHAMBERS COUNTY CL",
    "CHILTON COUNTY CL 4 CITIES",
    "MARSHALL COUNTY CL 4 CITIES",
    "RUSSELL COUNTY CL",
    "TALLADEGA COUNTY CL",
    "TUSCALOOSA COUNTY CL",
}

# Friendly-name overrides where the ALDOR uppercase -> title-case
# default doesn't match :data:`opensalestax.data.county_names.COUNTY_NAMES`
# canonical spelling for AL.
NAME_MAP: dict[str, str] = {
    "DEKALB": "DeKalb County",
    "ST CLAIR": "St. Clair County",
}


def normalize_county(aldor_county_word: str) -> str:
    """Convert an uppercase ALDOR county word ("AUTAUGA") to the
    canonical friendly name ("Autauga County")."""
    n = aldor_county_word.strip().upper()
    if n in NAME_MAP:
        return NAME_MAP[n]
    return f"{n.title()} County"


def parse(file_path: Path) -> dict[str, Decimal]:
    """Return county_friendly_name -> Decimal county-portion percentage."""
    # Stage 1: collect base rate (LOCALITY exactly "<COUNTY> COUNTY")
    # and county-wide CL rate (LOCALITY in COUNTYWIDE_CL_NAMES) per
    # county.
    base_rates: dict[str, Decimal] = {}
    cl_rates: dict[str, Decimal] = {}

    with file_path.open(newline="") as f:
        reader = csv.reader(f)
        next(reader)  # header
        for row in reader:
            (
                _code,
                name,
                _county_no,
                tax_type,
                rate_type,
                _admin,
                _active,
                inactive,
                rate_str,
                _indicator,
                _pj,
                _county_code,
                _pj_rate,
            ) = row
            if tax_type != "ST" or rate_type != "GENER":
                continue
            if inactive:
                continue
            if "UNABATED" in name:
                continue
            if name == "JEFFERSON COUNTY EDUCATION":
                continue
            if name == "COUNTY LINE":
                continue

            rate = Decimal(rate_str).quantize(Decimal("0.001"))

            # Base rate row: name is exactly "<COUNTY> COUNTY"
            if " COUNTY" in name and name.endswith(" COUNTY"):
                county_word = name.removesuffix(" COUNTY")
                base_rates[county_word] = rate
                continue

            # County-wide CL row: matches our COUNTYWIDE_CL_NAMES set
            if name in COUNTYWIDE_CL_NAMES:
                # Strip everything after the first " COUNTY" to get the
                # county word.
                head = name.split(" COUNTY", 1)[0]
                county_word = head
                cl_rates[county_word] = rate
                continue

    # Stage 1b: a separate pass picks up counties that ALDOR doesn't
    # publish as a plain "<COUNTY> COUNTY" base row at all -- instead
    # the only currently-active rows are per-city CL rows or
    # "UNINCORP AREAS"/"EXC CL <CITY>" variants. Examples:
    #   * Madison County only has "MADISON COUNTY COUNTY-WIDE TAX"
    #   * Morgan County only has "MORGAN COUNTY UNINCORP AREAS" + CLs
    #   * Pike County only has "PIKE COUNTY CL TROY" + "PIKE COUNTY
    #     EXC CL TROY"
    # For these we infer the inside-city rate by preferring (in
    # order):
    #   1. an explicit "<COUNTY> COUNTY-WIDE TAX" row
    #   2. the lowest "<COUNTY> COUNTY CL <CITY>" rate (the rate
    #      inside any city)
    #   3. the "<COUNTY> COUNTY UNINCORP AREAS" rate
    fallback_rates: dict[str, Decimal] = {}
    countywide_rates: dict[str, Decimal] = {}
    cl_city_rates: dict[str, list[Decimal]] = {}

    with file_path.open(newline="") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            (
                _code, name, _county_no, tax_type, rate_type,
                _admin, _active, inactive, rate_str, *_rest,
            ) = row
            if tax_type != "ST" or rate_type != "GENER":
                continue
            if inactive:
                continue
            if "UNABATED" in name or name == "JEFFERSON COUNTY EDUCATION":
                continue
            if name == "COUNTY LINE":
                continue
            if " COUNTY" not in name:
                continue
            head = name.split(" COUNTY", 1)[0]
            tail = name.split(" COUNTY", 1)[1].strip()
            if not tail:
                continue  # already captured as base
            rate = Decimal(rate_str).quantize(Decimal("0.001"))
            if tail == "COUNTY-WIDE TAX":
                countywide_rates[head] = rate
            elif tail == "UNINCORP AREAS":
                fallback_rates.setdefault(head, rate)
            elif tail.startswith("CL ") and tail != "CL 4 CITIES":
                # "CL <CITYNAME>" -- inside that city
                cl_city_rates.setdefault(head, []).append(rate)

    # Stage 2: pick the final rate per county. Prefer county-wide CL
    # over base, because CL matches the inside-city convention.
    out: dict[str, Decimal] = {}
    for county_word, base in base_rates.items():
        chosen = cl_rates.get(county_word, base)
        out[normalize_county(county_word)] = chosen

    # Pick up CL-only counties.
    for county_word, cl in cl_rates.items():
        friendly = normalize_county(county_word)
        if friendly not in out:
            out[friendly] = cl

    # Pick up "no base row" counties via fallback chain.
    for county_word in set(countywide_rates) | set(cl_city_rates) | set(fallback_rates):
        friendly = normalize_county(county_word)
        if friendly in out:
            continue
        if county_word in countywide_rates:
            out[friendly] = countywide_rates[county_word]
        elif county_word in cl_city_rates:
            # Use the lowest "inside any city" rate -- inside-city
            # convention matches v0.33 seeds.
            out[friendly] = min(cl_city_rates[county_word])
        elif county_word in fallback_rates:
            out[friendly] = fallback_rates[county_word]

    return dict(sorted(out.items()))


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    path = Path(sys.argv[1])
    rates = parse(path)
    print(f"# Extracted {len(rates)} AL county sales tax rates from {path.name}")
    for county, rate in rates.items():
        print(f'    "{county}": Decimal("{rate}"),')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
