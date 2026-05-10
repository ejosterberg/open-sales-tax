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
}


def city_name(code: str) -> str | None:
    """Return the friendly UT city name for an SST code, or None."""
    return UT_CITY_NAMES.get(code)


__all__ = ["UT_CITY_NAMES", "city_name"]
