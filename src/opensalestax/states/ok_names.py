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
    # iter-182 additions (21, 2026-05-15): probed common OK ZIPs and
    # picked up the curated names for 21 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match (40-NNNNN pattern).
    "00200": "Ada",  # ZIP 74820 (Pontotoc Co; FIPS Place 4000200)
    "01800": "Alva",  # ZIP 73717 (Woods Co; FIPS Place 4001800)
    "06600": "Blackwell",  # ZIP 74631 (Kay Co; FIPS Place 4006600)
    "06700": "Blanchard",  # ZIP 73010 (McClain Co; FIPS Place 4006700)
    "07300": "Boise City",  # ZIP 73933 (Cimarron Co; FIPS Place 4007300)
    "12900": "Catoosa",  # ZIP 74015 (Rogers Co; FIPS Place 4012900)
    "14200": "Choctaw",  # ZIP 73020 (Oklahoma Co; FIPS Place 4014200)
    "21900": "Duncan",  # ZIP 73533 (Stephens Co; FIPS Place 4021900)
    "30200": "Guymon",  # ZIP 73939 (Texas Co; FIPS Place 4030200)
    "35000": "Hobart",  # ZIP 73651 (Kiowa Co; FIPS Place 4035000)
    "44800": "McAlester",  # ZIP 74501 (Pittsburg Co; FIPS Place 4044800)
    "48350": "Midwest City",  # ZIPs 73110/73130 (Oklahoma Co; FIPS Place 4048350)
    "50050": "Muskogee",  # ZIP 74403 (Muskogee Co; FIPS Place 4050050)
    "54100": "Okmulgee",  # ZIP 74446 (Okmulgee Co; FIPS Place 4054100)
    "54200": "Okemah",  # ZIP 74859 (Okfuskee Co; FIPS Place 4054200)
    "56650": "Owasso",  # ZIP 74055 (Tulsa/Rogers Co; FIPS Place 4056650)
    "61150": "Purcell",  # ZIP 73080 (McClain Co; FIPS Place 4061150)
    "70250": "Stigler",  # ZIP 74462 (Haskell Co; FIPS Place 4070250)
    "71000": "Stroud",  # ZIP 74079 (Lincoln Co; FIPS Place 4071000)
    "74400": "Tecumseh",  # ZIP 74878 (Pottawatomie Co; FIPS Place 4074400)
    "77550": "Vinita",  # ZIP 74301 (Craig Co; FIPS Place 4077550)
}


def city_name(code: str) -> str | None:
    """Return the friendly OK city name for an SST code, or None."""
    return OK_CITY_NAMES.get(code)


__all__ = ["OK_CITY_NAMES", "city_name"]
