# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Kansas city tax authorities.

Verified by ZIP probe + rate cross-check against KS DOR's
"Jurisdiction Sales Tax Rates" publication (2026-Q1).
"""

from __future__ import annotations

KS_CITY_NAMES: dict[str, str] = {
    # iter-83 additions (4): Dodge City / Emporia / Hays / Newton --
    # all verified by ZIP probe + FIPS Place last-5-digit match.
    "18250": "Dodge City",  # ZIP 67801 (Ford Co; FIPS Place 2018250)
    "21275": "Emporia",  # ZIP 66801 (Lyon Co; FIPS Place 2021275)
    "31100": "Hays",  # ZIP 67601 (Ellis Co; FIPS Place 2031100)
    "36000": "Kansas City",
    "38900": "Lawrence",  # ZIP 66044 (verified by probe; FIPS Place 2038900)
    "44250": "Manhattan",  # ZIP 66502 (verified by probe; FIPS Place 2044250)
    "50475": "Newton",  # ZIP 67114 (Harvey Co; FIPS Place 2050475)
    "52575": "Olathe",
    "53775": "Overland Park",
    "62700": "Salina",  # ZIP 67401 (verified by probe; FIPS Place 2062700)
    "71000": "Topeka",
    "79000": "Wichita",
    # iter-179 additions (16, 2026-05-15): probed common KS ZIPs in
    # NE-KS / Wyandotte / Johnson Co metro + scattered secondary
    # cities. Each FIPS Place code verified by matching the engine's
    # SST jurisdiction code to the standard 20-NNNNN (KS state FIPS +
    # 5-digit place) pattern.
    "01775": "Andale",  # ZIP 67001 (Sedgwick Co; FIPS Place 2001775)
    "02900": "Atchison",  # ZIP 66002 (Atchison Co; FIPS Place 2002900)
    "07975": "Basehor",  # ZIP 66012 (Leavenworth Co; FIPS Place 2007975)
    "15200": "Concordia",  # ZIP 66901 (Cloud Co; FIPS Place 2015200)
    "17850": "De Soto",  # ZIP 66018 (Johnson Co; FIPS Place 2017850)
    "25425": "Gardner",  # ZIP 66030 (Johnson Co; FIPS Place 2025425)
    "33625": "Hutchinson",  # ZIP 67501 (Reno Co; FIPS Place 2033625)
    "33875": "Independence",  # ZIP 67301 (Montgomery Co; FIPS Place 2033875)
    "39075": "Leawood",  # ZIPs 66206/66224 (Johnson Co; FIPS Place 2039075)
    "39350": "Lenexa",  # ZIPs 66215/66220 (Johnson Co; FIPS Place 2039350)
    "39825": "Liberal",  # ZIP 67901 (Seward Co; FIPS Place 2039825)
    "47225": "Mission",  # ZIP 66202 (Johnson Co; FIPS Place 2047225)
    "53375": "Oskaloosa",  # ZIP 66066 (Jefferson Co; FIPS Place 2053375)
    "53550": "Ottawa",  # ZIP 66067 (Franklin Co; FIPS Place 2053550)
    "54950": "Wamego",  # ZIP 66526 (Pottawatomie Co; FIPS Place 2054950)
    "67625": "Spring Hill",  # ZIP 66083 (Johnson Co; FIPS Place 2067625)
}


def city_name(code: str) -> str | None:
    """Return the friendly KS city name for an SST code, or None."""
    return KS_CITY_NAMES.get(code)


__all__ = ["KS_CITY_NAMES", "city_name"]
