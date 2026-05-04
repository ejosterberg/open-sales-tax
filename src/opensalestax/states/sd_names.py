# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for South Dakota city tax authorities.

Verified by ZIP probe + rate cross-check against SD DOR's
"Municipal Sales Tax" publication (2026-Q1).
"""

from __future__ import annotations

SD_CITY_NAMES: dict[str, str] = {
    "00100": "Aberdeen",
    "52980": "Rapid City",
    "59020": "Sioux Falls",
}


def city_name(code: str) -> str | None:
    """Return the friendly SD city name for an SST code, or None."""
    return SD_CITY_NAMES.get(code)


__all__ = ["SD_CITY_NAMES", "city_name"]
