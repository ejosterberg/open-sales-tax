# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for West Virginia city tax authorities.

WV authorizes municipalities to levy a 1% Municipal Sales and
Use Tax (W. Va. Code section 8-13C-4); 60+ WV cities have done
so. Verified by ZIP probe against WV State Tax Department's
"Municipal Sales and Use Tax" publication (2026-Q1).
"""

from __future__ import annotations

WV_CITY_NAMES: dict[str, str] = {
    "14600": "Charleston",
    "39460": "Huntington",
    "55756": "Morgantown",
}


def city_name(code: str) -> str | None:
    """Return the friendly WV city name for an SST code, or None."""
    return WV_CITY_NAMES.get(code)


__all__ = ["WV_CITY_NAMES", "city_name"]
