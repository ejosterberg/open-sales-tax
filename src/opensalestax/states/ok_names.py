# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Oklahoma city tax authorities.

Verified by ZIP probe + rate cross-check against OK DOR's
"Sales and Use Tax Rate Charts" publication (2026-Q2) and
FIPS Place codes from the U.S. Census Bureau (2020). The
5-digit codes here are FIPS Place codes (the "Place" half
of the standard state-FIPS / place-FIPS pair, e.g. Yukon
= 40-82950).
"""

from __future__ import annotations

OK_CITY_NAMES: dict[str, str] = {
    "02600": "Ardmore",
    "04450": "Bartlesville",
    "05700": "Bethany",
    "09050": "Broken Arrow",
    # iter-83 additions (3): Durant / Guthrie / Woodward via probe
    # + FIPS Place last-5-digit match
    "22050": "Durant",  # ZIP 74701 (Bryan Co; FIPS Place 4022050)
    "23200": "Edmond",
    "23950": "Enid",
    "29600": "Glenpool",
    "31700": "Guthrie",  # ZIP 73044 (Logan Co; FIPS Place 4031700)
    "37800": "Bixby",
    "41850": "Lawton",
    "49200": "Moore",
    "51150": "Newcastle",
    "52500": "Norman",
    "55000": "Oklahoma City",
    "59850": "Ponca City",
    "65300": "Sand Springs",
    "65400": "Sapulpa",
    "66800": "Shawnee",
    "70300": "Stillwater",
    "75000": "Tulsa",
    "82150": "Woodward",  # ZIP 73801 (Woodward Co; FIPS Place 4082150)
    "82950": "Yukon",
}


def city_name(code: str) -> str | None:
    """Return the friendly OK city name for an SST code, or None."""
    return OK_CITY_NAMES.get(code)


__all__ = ["OK_CITY_NAMES", "city_name"]
