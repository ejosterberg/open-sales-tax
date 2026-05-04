# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Washington city tax authorities.

WA's "city" code in the SST file is actually the COMBINED local
rate (city + county + Sound Transit / RTA / Cultural Access /
TBD where applicable) -- so the friendly name is just the city
the code is most commonly associated with. Verified by ZIP probe
+ rate cross-check against WA DOR's "Local Sales & Use Tax Rates
and Changes" publication (2026-Q2).
"""

from __future__ import annotations

WA_CITY_NAMES: dict[str, str] = {
    "05210": "Bellevue (combined local)",
    "63000": "Seattle (combined local)",
    "67000": "Spokane (combined local)",
    "70000": "Tacoma (combined local)",
}


def city_name(code: str) -> str | None:
    """Return the friendly WA city name for an SST code, or None."""
    return WA_CITY_NAMES.get(code)


__all__ = ["WA_CITY_NAMES", "city_name"]
