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
    # iter-204 additions (8, 2026-05-19): DB-driven probe pattern.
    # Queried tax_authorities for single-ZIP-bound placeholders, then
    # WebFetched zip-codes.com for the primary city. Single-ZIP
    # binding ensures the city attribution is unambiguous. Multi-ZIP
    # placeholders (e.g. 01900 spans 3 counties) are kept aside for a
    # different approach -- they're likely county-level or special-
    # district authorities mislabelled as 'city' by the loader.
    "00772": "Alderson",  # ZIP 24910 (Monroe Co)
    "01996": "Ansted",  # ZIP 25812 (Fayette Co)
    "04276": "Barboursville",  # ZIP 25504 (Cabell Co)
    "10852": "Bruceton Mills",  # ZIP 26525 (Preston Co)
    "13108": "Capon Bridge",  # ZIP 26711 (Hampshire Co)
    "14524": "Chapmanville",  # ZIP 25508 (Logan Co)
    "15076": "Chester",  # ZIP 26034 (Hancock Co)
    "15676": "Clay",  # ZIP 25043 (Clay Co)
    # iter-205 additions (8, 2026-05-19): D-H alphabet sweep continued.
    "20428": "Davis",  # ZIP 26260 (Tucker Co)
    "24364": "Elizabeth",  # ZIP 26143 (Wirt Co)
    "24844": "Ellenboro",  # ZIP 26346 (Ritchie Co)
    "28204": "Follansbee",  # ZIP 26037 (Brooke Co)
    "29044": "Franklin",  # ZIP 26807 (Pendleton Co)
    "32044": "Glenville",  # ZIP 26351 (Gilmer Co)
    "32716": "Grafton",  # ZIP 26354 (Taylor Co)
    "35428": "Harrisville",  # ZIP 26362 (Ritchie Co)
    # iter-206 additions (8, 2026-05-19): H-M alphabet sweep continued.
    "37636": "Hinton",  # ZIP 25951 (Summers Co)
    "39340": "Hundred",  # ZIP 26575 (Wetzel Co)
    "46636": "Lewisburg",  # ZIP 24901 (Greenbrier Co)
    "48148": "Logan",  # ZIP 25601 (Logan Co)
    "50932": "Man",  # ZIP 25635 (Logan Co)
    "51100": "Mannington",  # ZIP 26582 (Marion Co)
    "52228": "Masontown",  # ZIP 26542 (Preston Co)
    "53572": "Middlebourne",  # ZIP 26149 (Tyler Co)
    # iter-207 additions (8, 2026-05-19): M-P alphabet sweep continued.
    "55468": "Montgomery",  # ZIP 25136 (Fayette Co)
    "56020": "Moundsville",  # ZIP 26041 (Marshall Co)
    "58372": "New Cumberland",  # ZIP 26047 (Hancock Co)
    "58684": "New Martinsville",  # ZIP 26155 (Wetzel Co)
    "61636": "Paden City",  # ZIP 26159 (Wetzel Co)
    "62332": "Paw Paw",  # ZIP 25434 (Morgan Co)
    "62764": "Pennsboro",  # ZIP 26415 (Ritchie Co)
    "63892": "Pine Grove",  # ZIP 26419 (Wetzel Co)
    # iter-208 additions (8, 2026-05-19): P-R alphabet sweep continued.
    "63940": "Pineville",  # ZIP 24874 (Wyoming Co)
    "66412": "Quinwood",  # ZIP 25981 (Greenbrier Co)
    "67108": "Ravenswood",  # ZIP 26164 (Jackson Co)
    "67636": "Reedsville",  # ZIP 26547 (Preston Co)
    "68116": "Richwood",  # ZIP 26261 (Nicholas Co)
    "70084": "Romney",  # ZIP 26757 (Hampshire Co)
    "70588": "Rowlesburg",  # ZIP 26425 (Preston Co)
    "70828": "Rupert",  # ZIP 25984 (Greenbrier Co)
}


def city_name(code: str) -> str | None:
    """Return the friendly WV city name for an SST code, or None."""
    return WV_CITY_NAMES.get(code)


__all__ = ["WV_CITY_NAMES", "city_name"]
