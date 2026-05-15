# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for South Dakota city tax authorities.

Verified by ZIP probe + rate cross-check against SD DOR's
"Municipal Sales Tax" publication (2026-Q1).
"""

from __future__ import annotations

SD_CITY_NAMES: dict[str, str] = {
    "00100": "Aberdeen",
    # iter-85 additions (5): probed + FIPS Place last-5-digit match
    "07580": "Brookings",  # ZIP 57006 (Brookings Co; FIPS Place 4607580)
    "43100": "Mitchell",  # ZIP 57301 (Davison Co; FIPS Place 4643100)
    "49600": "Pierre",  # ZIP 57501 (Hughes Co; FIPS Place 4649600)
    "52980": "Rapid City",
    "59020": "Sioux Falls",
    "69300": "Watertown",  # ZIP 57201 (Codington Co; FIPS Place 4669300)
    "73060": "Yankton",  # ZIP 57078 (Yankton Co; FIPS Place 4673060)
    # iter-180 additions (8, 2026-05-15): probed common SD ZIPs and
    # picked up the curated names for 7 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match (46-NNNNN pattern).
    "06840": "Brandon",  # ZIP 57005 (Minnehaha Co; FIPS Place 4606840)
    "09500": "Canton",  # ZIP 57013 (Lincoln Co; FIPS Place 4609500)
    "15140": "Custer",  # ZIP 57730 (Custer Co; FIPS Place 4615140)
    "30220": "Hot Springs",  # ZIP 57747 (Fall River Co; FIPS Place 4630220)
    "31060": "Huron",  # ZIP 57350 (Beadle Co; FIPS Place 4631060)
    "43180": "Mobridge",  # ZIP 57601 (Walworth Co; FIPS Place 4643180)
    "60020": "Spearfish",  # ZIP 57783 (Lawrence Co; FIPS Place 4660020)
    "66700": "Vermillion",  # ZIP 57069 (Clay Co; FIPS Place 4666700)
}


def city_name(code: str) -> str | None:
    """Return the friendly SD city name for an SST code, or None."""
    return SD_CITY_NAMES.get(code)


__all__ = ["SD_CITY_NAMES", "city_name"]
