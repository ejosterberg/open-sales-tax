# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Oklahoma city tax authorities.

Verified by ZIP probe + rate cross-check against OK DOR's
"Sales and Use Tax Rate Charts" publication (2026-Q2).
"""

from __future__ import annotations

OK_CITY_NAMES: dict[str, str] = {
    "52500": "Norman",
    "55000": "Oklahoma City",
    "75000": "Tulsa",
}


def city_name(code: str) -> str | None:
    """Return the friendly OK city name for an SST code, or None."""
    return OK_CITY_NAMES.get(code)


__all__ = ["OK_CITY_NAMES", "city_name"]
