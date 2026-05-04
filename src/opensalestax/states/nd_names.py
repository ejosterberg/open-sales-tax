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
    "25700": "Fargo",
    "32060": "Grand Forks",
}


def city_name(code: str) -> str | None:
    """Return the friendly ND city name for an SST code, or None."""
    return ND_CITY_NAMES.get(code)


__all__ = ["ND_CITY_NAMES", "city_name"]
