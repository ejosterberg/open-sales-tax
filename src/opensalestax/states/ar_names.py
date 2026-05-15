# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Arkansas city tax authorities.

Verified by ZIP probe + rate cross-check against AR DFA's
"Sales and Use Tax Rates" publication (2026-Q2).
"""

from __future__ import annotations

AR_CITY_NAMES: dict[str, str] = {
    "05320": "Bentonville",  # ZIP 72712 (verified by probe; FIPS Place 0505320)
    # iter-89 additions (5): Camden / Harrison / Magnolia / Osceola
    # / Stuttgart via probe + FIPS Place last-5-digit match
    "10720": "Camden",  # ZIP 71701 (Ouachita Co; FIPS Place 0510720)
    "15190": "Conway",  # ZIP 72033 (verified by probe; FIPS Place 0515190)
    "23290": "Fayetteville",
    "24550": "Fort Smith",
    "30460": "Harrison",  # ZIP 72601 (Boone Co; FIPS Place 0530460)
    "33400": "Hot Springs",  # ZIP 71901 (verified by probe; FIPS Place 0533400)
    "34750": "North Little Rock",  # ZIP 72076 (verified by probe; FIPS Place 0534750)
    "35710": "Jonesboro",
    "41000": "Little Rock",
    "41720": "Lowell",  # ZIP 72745 (verified by probe; FIPS Place 0541720)
    "43460": "Magnolia",  # ZIP 71753 (Columbia Co; FIPS Place 0543460)
    "52580": "Osceola",  # ZIP 72370 (Mississippi Co; FIPS Place 0552580)
    "55310": "Pine Bluff",  # ZIP 71601 (verified by probe; FIPS Place 0555310)
    "60410": "Rogers",  # FIPS Place 0560410 (Rogers AR)
    "63800": "Sherwood",  # ZIP 72120 (verified by probe; FIPS Place 0563800)
    "66080": "Springdale",  # ZIP 72765 (verified by probe; FIPS Place 0566080)
    "67490": "Stuttgart",  # ZIP 72160 (Arkansas Co; FIPS Place 0567490)
    # iter-178 additions (9, 2026-05-15): probed common AR ZIPs and
    # picked up the curated names for 9 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match.
    "01870": "Arkadelphia",  # ZIP 71923 (Clark Co; FIPS Place 0501870)
    "04840": "Bella Vista",  # ZIPs 72714/72715 (Benton Co; FIPS Place 0504840)
    "05290": "Benton",  # ZIP 72015 (Saline Co; FIPS Place 0505290)
    "12340": "Cave Springs",  # ZIP 72718 (Benton Co; FIPS Place 0512340)
    "33190": "Hope",  # ZIP 71801 (Hempstead Co; FIPS Place 0533190)
    "63020": "Searcy",  # ZIP 72143 (White Co; FIPS Place 0563020)
    "68810": "Texarkana",  # ZIP 71854 (Miller Co; FIPS Place 0568810)
    "71480": "Van Buren",  # ZIP 72956 (Crawford Co; FIPS Place 0571480)
    "74540": "West Memphis",  # ZIP 72301 (Crittenden Co; FIPS Place 0574540)
}


def city_name(code: str) -> str | None:
    """Return the friendly AR city name for an SST code, or None."""
    return AR_CITY_NAMES.get(code)


__all__ = ["AR_CITY_NAMES", "city_name"]
