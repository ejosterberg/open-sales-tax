# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for North Dakota city tax authorities.

Verified by ZIP probe + rate cross-check against ND Office of
State Tax Commissioner's "Local Sales and Use Tax Rates"
publication (2026-Q1).
"""

from __future__ import annotations

ND_CITY_NAMES: dict[str, str] = {
    "07200": "Bismarck",
    "19620": "Dickinson",  # ZIP 58601 (verified by probe; FIPS Place 3819620)
    "25700": "Fargo",
    "32060": "Grand Forks",
    "53380": "Minot",  # ZIP 58701 (verified by probe; FIPS Place 3853380)
    # iter-86 addition: Valley City via probe + FIPS Place
    "81180": "Valley City",  # ZIP 58072 (Barnes Co; FIPS Place 3881180)
    "86220": "Williston",  # ZIP 58801 (verified by probe; FIPS Place 3886220)
    # iter-181 additions (9, 2026-05-15): probed common ND ZIPs and
    # picked up the curated names for 9 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match (38-NNNNN pattern).
    "03540": "Ashley",  # ZIP 58413 (McIntosh Co; FIPS Place 3803540)
    "05420": "Belfield",  # ZIP 58621 (Stark Co; FIPS Place 3805420)
    "19420": "Devils Lake",  # ZIP 58301 (Ramsey Co; FIPS Place 3819420)
    "40580": "Jamestown",  # ZIP 58401 (Stutsman Co; FIPS Place 3840580)
    "47100": "Lisbon",  # ZIP 58054 (Ransom Co; FIPS Place 3847100)
    "49820": "Stanley",  # ZIP 58756 (Mountrail Co; FIPS Place 3849820)
    "75380": "Tioga",  # ZIP 58784 (Williams Co; FIPS Place 3875380)
    "82660": "Wahpeton",  # ZIP 58075 (Richland Co; FIPS Place 3882660)
    "87020": "Linton",  # ZIP 58495 (Emmons Co; FIPS Place 3887020)
    # daily-audit 2026-08-15 additions (3): the three ND cities whose
    # 2026-07-01 local-tax changes the audit examined were all still
    # rendering as `ND-city-NNNNN` placeholders in the live engine.
    # Codes verified against the ND Office of State Tax Commissioner's
    # "North Dakota FIPS Codes" table (fips-codes-1-1-2026.pdf), which
    # publishes the FIPS Place code alongside the ND local code.
    "20340": "Drayton",  # ZIP 58225 (Pembina Co; ND local code 157)
    "58740": "Oakes",  # ZIP 58474 (Dickey Co; ND local code 146)
    "71500": "Scranton",  # ZIP 58653 (Bowman Co; ND local code 190)
}


def city_name(code: str) -> str | None:
    """Return the friendly ND city name for an SST code, or None."""
    return ND_CITY_NAMES.get(code)


__all__ = ["ND_CITY_NAMES", "city_name"]
