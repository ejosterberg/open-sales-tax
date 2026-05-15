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
    # iter-187 additions (6, 2026-05-15): each verified by ZIP probe
    # against the live engine + zip-codes.com city lookup. Per the
    # docstring above, WV ZIP -> primary-city is 1:1 so the
    # placeholder code -> city inference is safe when the ZIP itself
    # binds to a unique non-shared authority code.
    "04876": "Berkeley Springs",  # ZIP 25411 (Morgan Co)
    "14610": "Charles Town",  # ZIP 25414 (Jefferson Co)
    "27028": "Fayetteville",  # ZIP 25840 (Fayette Co)
    "35284": "Harpers Ferry",  # ZIP 25425 (Jefferson Co)
    "54484": "Milton",  # ZIP 25541 (Cabell Co)
    "73468": "Shepherdstown",  # ZIP 25443 (Jefferson Co)
}


def city_name(code: str) -> str | None:
    """Return the friendly WV city name for an SST code, or None."""
    return WV_CITY_NAMES.get(code)


__all__ = ["WV_CITY_NAMES", "city_name"]
