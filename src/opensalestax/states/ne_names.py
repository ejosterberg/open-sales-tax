# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Nebraska city tax authorities.

Verified by ZIP probe + rate cross-check against NE DOR's
"Local Sales and Use Tax Rates" publication (2026-Q1).
"""

from __future__ import annotations

NE_CITY_NAMES: dict[str, str] = {
    "03950": "Bellevue",
    "28000": "Lincoln",
    "37000": "Omaha",
}


def city_name(code: str) -> str | None:
    """Return the friendly NE city name for an SST code, or None."""
    return NE_CITY_NAMES.get(code)


__all__ = ["NE_CITY_NAMES", "city_name"]
