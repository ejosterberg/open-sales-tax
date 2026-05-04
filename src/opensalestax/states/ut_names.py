# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Utah city tax authorities.

UT's "city" jurisdiction code in the SST file is the city's
local-option additional sales tax. The combined rate at any
address also includes UT's state base + county rates +
Mass Transit (which is loaded separately as the state's "base"
in UT's encoding -- see utah.py for detail).

Verified by ZIP probe + rate cross-check against UT State Tax
Commission's "Tax Rate Charts" publication (2026-Q2).
"""

from __future__ import annotations

UT_CITY_NAMES: dict[str, str] = {
    "62470": "Provo",
    "67000": "Salt Lake City",
}


def city_name(code: str) -> str | None:
    """Return the friendly UT city name for an SST code, or None."""
    return UT_CITY_NAMES.get(code)


__all__ = ["UT_CITY_NAMES", "city_name"]
