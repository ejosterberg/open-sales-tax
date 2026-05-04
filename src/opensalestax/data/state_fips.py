# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""USPS state abbreviation <-> FIPS code mapping.

Single source of truth for code-vs-abbrev conversion. Used by
the ZCTA boundary loader (which maps Census ZCTA->county GEOID
to the OpenSalesTax state catalog) and any other component that
needs to bridge between Census/IRS FIPS codes and the API's USPS
abbreviations.

Source: NIST FIPS PUB 5-2 (the canonical state-numeric-code list,
published 1987 and unchanged since). Includes 50 states + DC + 5
US territories.
"""

from __future__ import annotations

# 2-digit FIPS code -> USPS 2-letter state abbreviation
FIPS_TO_ABBREV: dict[str, str] = {
    "01": "AL",
    "02": "AK",
    "04": "AZ",
    "05": "AR",
    "06": "CA",
    "08": "CO",
    "09": "CT",
    "10": "DE",
    "11": "DC",
    "12": "FL",
    "13": "GA",
    "15": "HI",
    "16": "ID",
    "17": "IL",
    "18": "IN",
    "19": "IA",
    "20": "KS",
    "21": "KY",
    "22": "LA",
    "23": "ME",
    "24": "MD",
    "25": "MA",
    "26": "MI",
    "27": "MN",
    "28": "MS",
    "29": "MO",
    "30": "MT",
    "31": "NE",
    "32": "NV",
    "33": "NH",
    "34": "NJ",
    "35": "NM",
    "36": "NY",
    "37": "NC",
    "38": "ND",
    "39": "OH",
    "40": "OK",
    "41": "OR",
    "42": "PA",
    "44": "RI",
    "45": "SC",
    "46": "SD",
    "47": "TN",
    "48": "TX",
    "49": "UT",
    "50": "VT",
    "51": "VA",
    "53": "WA",
    "54": "WV",
    "55": "WI",
    "56": "WY",
    # Territories included for completeness; only PR is in the v1 catalog
    "60": "AS",
    "66": "GU",
    "69": "MP",
    "72": "PR",
    "78": "VI",
}

# Reverse lookup
ABBREV_TO_FIPS: dict[str, str] = {abbrev: fips for fips, abbrev in FIPS_TO_ABBREV.items()}


__all__ = ["ABBREV_TO_FIPS", "FIPS_TO_ABBREV"]
