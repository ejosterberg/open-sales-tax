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
    # iter-82: each entry verified by ZIP probe against the live
    # engine + cross-check against WV State Tax Dept's "Municipal
    # Sales and Use Tax" publication. WV city codes don't follow
    # the FIPS Place scheme used by some other states; they're a
    # local authority numbering. ZIP -> primary-city mapping is
    # 1:1 in WV (single city per ZIP) so the inference is safe.
    "05332": "Beckley",
    "08524": "Bluefield",
    "11188": "Buckhannon",
    "14600": "Charleston",
    "15628": "Clarksburg",
    "24580": "Elkins",
    "26452": "Fairmont",
    "39460": "Huntington",
    "39532": "Hurricane",
    "44044": "Kingwood",
    "52060": "Martinsburg",
    "55756": "Morgantown",
    "62140": "Parkersburg",
    "65692": "Princeton",
    "75292": "South Charleston",
    "86452": "Wheeling",
}


def city_name(code: str) -> str | None:
    """Return the friendly WV city name for an SST code, or None."""
    return WV_CITY_NAMES.get(code)


__all__ = ["WV_CITY_NAMES", "city_name"]
