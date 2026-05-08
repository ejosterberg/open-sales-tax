# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Kansas city tax authorities.

Verified by ZIP probe + rate cross-check against KS DOR's
"Jurisdiction Sales Tax Rates" publication (2026-Q1).
"""

from __future__ import annotations

KS_CITY_NAMES: dict[str, str] = {
    "36000": "Kansas City",
    "38900": "Lawrence",  # ZIP 66044 (verified by probe; FIPS Place 2038900)
    "44250": "Manhattan",  # ZIP 66502 (verified by probe; FIPS Place 2044250)
    "52575": "Olathe",
    "53775": "Overland Park",
    "62700": "Salina",  # ZIP 67401 (verified by probe; FIPS Place 2062700)
    "71000": "Topeka",
    "79000": "Wichita",
}


def city_name(code: str) -> str | None:
    """Return the friendly KS city name for an SST code, or None."""
    return KS_CITY_NAMES.get(code)


__all__ = ["KS_CITY_NAMES", "city_name"]
