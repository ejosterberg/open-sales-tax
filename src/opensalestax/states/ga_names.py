# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Georgia city tax authorities.

GA's local sales tax is overwhelmingly county-administered (LOST
+ SPLOST + ELOST + TSPLOST), but a small number of cities
publish their own city-rate code in the SST file. Atlanta's
1.9% MOST (Municipal Option Sales Tax) is the largest.

Verified against GA DOR's "Local Tax Rates Special Districts &
Other" rate publication.
"""

from __future__ import annotations

GA_CITY_NAMES: dict[str, str] = {
    "04000": "Atlanta",
}

# Special districts published in the GA SST file. Verified by ZIP probe
# against GA DOR's "Local Tax Rates Special Districts & Other" rate
# publication: 00060 covers ~93 ZIPs in Fulton County @ 0.75% (TSPLOST),
# 00044 covers ~54 ZIPs in DeKalb County @ 1.0% (MARTA), 00031 covers
# ~20 ZIPs in Fayette County @ 0.0% (placeholder/locator code).
GA_DISTRICT_NAMES: dict[str, str] = {
    "00031": "Fayette County District",
    "00044": "DeKalb County MARTA",
    "00060": "Fulton County TSPLOST",
}


def city_name(code: str) -> str | None:
    """Return the friendly GA city name for an SST code, or None."""
    return GA_CITY_NAMES.get(code)


def district_name(code: str) -> str | None:
    """Return the friendly GA special-district name for an SST code, or None."""
    return GA_DISTRICT_NAMES.get(code)


__all__ = ["GA_CITY_NAMES", "GA_DISTRICT_NAMES", "city_name", "district_name"]
