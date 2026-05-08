# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Washington city tax authorities.

WA's "city" code in the SST file is actually the COMBINED local
rate (city + county + Sound Transit / RTA / Cultural Access /
TBD where applicable) -- so the friendly name is just the city
the code is most commonly associated with. Verified by ZIP probe
+ rate cross-check against WA DOR's "Local Sales & Use Tax Rates
and Changes" publication (2026-Q2). The 5-digit codes are FIPS
Place codes (the "Place" half of the standard state-FIPS /
place-FIPS pair, e.g. Vancouver = 53-74060).
"""

from __future__ import annotations

WA_CITY_NAMES: dict[str, str] = {
    "05210": "Bellevue (combined local)",
    "05280": "Bellingham (combined local)",
    "22640": "Everett (combined local)",
    "23515": "Federal Way (combined local)",
    "35275": "Kennewick (combined local)",  # ZIP 99336 (verified by probe; FIPS 5335275)
    "35415": "Kent (combined local)",  # ZIP 98035 (verified by probe; FIPS 5335415)
    "38038": "Lakewood (combined local)",  # ZIP 98493 (verified by probe; FIPS 5338038)
    "50360": "Oak Harbor (combined local)",  # ZIP 98277 (verified by probe; FIPS 5350360)
    "51300": "Olympia (combined local)",
    "57745": "Renton (combined local)",
    "63000": "Seattle (combined local)",
    "67000": "Spokane (combined local)",
    "67167": "Spokane Valley (combined local)",  # ZIP 99211 (verified by probe; FIPS 5367167)
    "70000": "Tacoma (combined local)",
    "74060": "Vancouver (combined local)",
    "77105": "Wenatchee (combined local)",  # ZIP 98801 (verified by probe; FIPS 5377105)
    "80010": "Yakima (combined local)",  # ZIP 98907 (verified by probe; FIPS 5380010)
}


def city_name(code: str) -> str | None:
    """Return the friendly WA city name for an SST code, or None."""
    return WA_CITY_NAMES.get(code)


__all__ = ["WA_CITY_NAMES", "city_name"]
