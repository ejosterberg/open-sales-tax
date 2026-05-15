# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Utah city tax authorities.

UT's "city" jurisdiction code in the SST file is the city's
local-option additional sales tax. The combined rate at any
address also includes UT's state base + county rates +
Mass Transit (which is loaded separately as the state's "base"
in UT's encoding -- see utah.py for detail).

Verified by ZIP probe + rate cross-check against UT State Tax
Commission's "Tax Rate Charts" publication (2026-Q2).
"""

from __future__ import annotations

UT_CITY_NAMES: dict[str, str] = {
    "45860": "Logan",  # ZIP 84321 (verified by probe; FIPS Place 4945860)
    "53230": "Murray",  # ZIP 84107 (verified by probe; FIPS Place 4953230)
    "57300": "Orem",  # ZIP 84059 (verified by probe; FIPS Place 4957300)
    "58070": "Park City",  # ZIP 84060 (verified by probe; FIPS Place 4958070)
    "62470": "Provo",
    "65330": "St. George",  # ZIP 84771 (verified by probe; FIPS Place 4965330)
    "67000": "Salt Lake City",
    # iter-85 addition: Tooele via probe + FIPS Place
    "76680": "Tooele",  # ZIP 84074 (Tooele Co; FIPS Place 4976680)
    # iter-180 additions (12, 2026-05-15): probed common UT ZIPs and
    # picked up the curated names for 12 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match (49-NNNNN pattern).
    "00540": "Alpine",  # ZIP 84004 (Utah Co; FIPS Place 4900540)
    "11320": "Cedar City",  # ZIP 84720 (Iron Co; FIPS Place 4911320)
    "13850": "Clearfield",  # ZIP 84015 (Davis Co; FIPS Place 4913850)
    "24740": "Farmington",  # ZIP 84025 (Davis Co; FIPS Place 4924740)
    "34200": "Heber City",  # ZIP 84032 (Wasatch Co; FIPS Place 4934200)
    "40360": "Kaysville",  # ZIP 84037 (Davis Co; FIPS Place 4940360)
    "55210": "North Salt Lake",  # ZIP 84054 (Davis Co; FIPS Place 4955210)
    "60930": "Pleasant Grove",  # ZIP 84062 (Utah Co; FIPS Place 4960930)
    "62030": "Price",  # ZIP 84501 (Carbon Co; FIPS Place 4962030)
    "71070": "South Salt Lake",  # ZIPs 84115/84119 (Salt Lake Co; FIPS Place 4971070)
    "71290": "Spanish Fork",  # ZIP 84660 (Utah Co; FIPS Place 4971290)
    "80090": "Vernal",  # ZIP 84078 (Uintah Co; FIPS Place 4980090)
}


def city_name(code: str) -> str | None:
    """Return the friendly UT city name for an SST code, or None."""
    return UT_CITY_NAMES.get(code)


__all__ = ["UT_CITY_NAMES", "city_name"]
