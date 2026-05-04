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


def city_name(code: str) -> str | None:
    """Return the friendly GA city name for an SST code, or None."""
    return GA_CITY_NAMES.get(code)


__all__ = ["GA_CITY_NAMES", "city_name"]
