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
    # iter-203 additions (11, 2026-05-19): same pattern as iter-187.
    # ZIP 25430 (placeholder code 66988) skipped -- 66988 also binds
    # to ZIP 25438, so the city attribution is ambiguous and cannot
    # be safely inferred from a single ZIP probe.
    "10180": "Bridgeport",  # ZIP 26330 (Harrison Co)
    "22564": "Dunbar",  # ZIP 25064 (Kanawha Co)
    "55588": "Moorefield",  # ZIP 26836 (Hardy Co)
    "59068": "Nitro",  # ZIP 25143 (Kanawha Co)
    "60028": "Oak Hill",  # ZIP 25901 (Fayette Co)
    "62956": "Petersburg",  # ZIP 26847 (Grant Co)
    "68596": "Ripley",  # ZIP 25271 (Jackson Co)
    "71212": "Saint Albans",  # ZIP 25177 (Kanawha Co)
    "79708": "Terra Alta",  # ZIP 26764 (Preston Co)
    "84580": "Wardensville",  # ZIP 26851 (Hardy Co)
    "85972": "Weston",  # ZIP 26452 (Lewis Co)
}


def city_name(code: str) -> str | None:
    """Return the friendly WV city name for an SST code, or None."""
    return WV_CITY_NAMES.get(code)


__all__ = ["WV_CITY_NAMES", "city_name"]
