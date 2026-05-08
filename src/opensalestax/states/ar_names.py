# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Arkansas city tax authorities.

Verified by ZIP probe + rate cross-check against AR DFA's
"Sales and Use Tax Rates" publication (2026-Q2).
"""

from __future__ import annotations

AR_CITY_NAMES: dict[str, str] = {
    "05320": "Bentonville",  # ZIP 72712 (verified by probe; FIPS Place 0505320)
    "15190": "Conway",  # ZIP 72033 (verified by probe; FIPS Place 0515190)
    "23290": "Fayetteville",
    "24550": "Fort Smith",
    "33400": "Hot Springs",  # ZIP 71901 (verified by probe; FIPS Place 0533400)
    "34750": "North Little Rock",  # ZIP 72076 (verified by probe; FIPS Place 0534750)
    "35710": "Jonesboro",
    "41000": "Little Rock",
    "41720": "Lowell",  # ZIP 72745 (verified by probe; FIPS Place 0541720)
    "55310": "Pine Bluff",  # ZIP 71601 (verified by probe; FIPS Place 0555310)
    "60410": "Rogers",  # FIPS Place 0560410 (Rogers AR)
    "63800": "Sherwood",  # ZIP 72120 (verified by probe; FIPS Place 0563800)
    "66080": "Springdale",  # ZIP 72765 (verified by probe; FIPS Place 0566080)
}


def city_name(code: str) -> str | None:
    """Return the friendly AR city name for an SST code, or None."""
    return AR_CITY_NAMES.get(code)


__all__ = ["AR_CITY_NAMES", "city_name"]
