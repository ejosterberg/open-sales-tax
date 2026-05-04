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
    "51300": "Olympia (combined local)",
    "57745": "Renton (combined local)",
    "63000": "Seattle (combined local)",
    "67000": "Spokane (combined local)",
    "70000": "Tacoma (combined local)",
    "74060": "Vancouver (combined local)",
}


def city_name(code: str) -> str | None:
    """Return the friendly WA city name for an SST code, or None."""
    return WA_CITY_NAMES.get(code)


__all__ = ["WA_CITY_NAMES", "city_name"]
