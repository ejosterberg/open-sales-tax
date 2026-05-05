# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Nebraska city tax authorities.

Verified by ZIP probe + rate cross-check against NE DOR's
"Local Sales and Use Tax Rates" publication (2026-Q1) and
FIPS Place codes from the U.S. Census Bureau (2020).

The 5-digit codes here are FIPS Place codes (the "Place" half
of the standard state-FIPS / place-FIPS pair, e.g. Norfolk =
31-34615). The SST quarterly NER<...>.csv file uses these
codes verbatim in jurisdiction-type 01 (city/local) rows.
"""

from __future__ import annotations

NE_CITY_NAMES: dict[str, str] = {
    "01990": "Fremont",
    "03390": "Beatrice",
    "03950": "Bellevue",
    "10110": "Columbus",
    "18580": "Gering",
    "19595": "Grand Island",
    "20260": "Gretna",
    "21415": "Hastings",
    "25055": "Kearney",
    "26385": "La Vista",
    "28000": "Lincoln",
    "29925": "McCook",
    "34615": "Norfolk",
    "35000": "North Platte",
    "37000": "Omaha",
    "38295": "Papillion",
    "40605": "Ralston",
}


def city_name(code: str) -> str | None:
    """Return the friendly NE city name for an SST code, or None."""
    return NE_CITY_NAMES.get(code)


__all__ = ["NE_CITY_NAMES", "city_name"]
