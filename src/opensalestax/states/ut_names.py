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
    "45860": "Logan",  # ZIP 84321 (verified by probe; FIPS Place 4945860)
    "53230": "Murray",  # ZIP 84107 (verified by probe; FIPS Place 4953230)
    "57300": "Orem",  # ZIP 84059 (verified by probe; FIPS Place 4957300)
    "58070": "Park City",  # ZIP 84060 (verified by probe; FIPS Place 4958070)
    "62470": "Provo",
    "65330": "St. George",  # ZIP 84771 (verified by probe; FIPS Place 4965330)
    "67000": "Salt Lake City",
    # iter-85 addition: Tooele via probe + FIPS Place
    "76680": "Tooele",  # ZIP 84074 (Tooele Co; FIPS Place 4976680)
    # iter-180 additions (12, 2026-05-15): probed common UT ZIPs and
    # picked up the curated names for 12 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match (49-NNNNN pattern).
    "00540": "Alpine",  # ZIP 84004 (Utah Co; FIPS Place 4900540)
    "11320": "Cedar City",  # ZIP 84720 (Iron Co; FIPS Place 4911320)
    "13850": "Clearfield",  # ZIP 84015 (Davis Co; FIPS Place 4913850)
    "24740": "Farmington",  # ZIP 84025 (Davis Co; FIPS Place 4924740)
    "34200": "Heber City",  # ZIP 84032 (Wasatch Co; FIPS Place 4934200)
    "40360": "Kaysville",  # ZIP 84037 (Davis Co; FIPS Place 4940360)
    "55210": "North Salt Lake",  # ZIP 84054 (Davis Co; FIPS Place 4955210)
    "60930": "Pleasant Grove",  # ZIP 84062 (Utah Co; FIPS Place 4960930)
    "62030": "Price",  # ZIP 84501 (Carbon Co; FIPS Place 4962030)
    "71070": "South Salt Lake",  # ZIPs 84115/84119 (Salt Lake Co; FIPS Place 4971070)
    "71290": "Spanish Fork",  # ZIP 84660 (Utah Co; FIPS Place 4971290)
    "80090": "Vernal",  # ZIP 84078 (Uintah Co; FIPS Place 4980090)
    # iter-226 additions (9, 2026-05-19): derived directly from the
    # Census 2024 Gazetteer for UT places (state 49). Each SST code
    # XXXXX matches Census FIPS Place 49-XXXXX:
    "00650": "Alta",  # FIPS Place 4900650 (Salt Lake Co; ZIP 84092 shared w/ Sandy)
    "02740": "Aurora",  # FIPS Place 4902740 (Sevier Co; ZIP 84620)
    "04060": "Beaver",  # FIPS Place 4904060 (Beaver Co; ZIP 84713)
    "05490": "Bicknell",  # FIPS Place 4905490 (Wayne Co; ZIP 84715)
    "05534": "Big Water",  # FIPS Place 4905534 (Kane Co; ZIP 84741)
    "07470": "Boulder",  # FIPS Place 4907470 (Garfield Co; ZIP 84716)
    "08020": "Brian Head",  # FIPS Place 4908020 (Iron Co; ZIP 84719)
    "08787": "Bryce Canyon City",  # FIPS Place 4908787 (Garfield Co; ZIP 84764)
    "11870": "Centerfield",  # FIPS Place 4911870 (Sanpete Co; ZIP 84622)
    # iter-227 additions (15, 2026-05-19): more Census-Gazetteer-verified
    # entries. Continues the FIPS Place 49-XXXXX pattern.
    "01310": "American Fork",  # FIPS Place 4901310 (Utah Co)
    "06370": "Blanding",  # FIPS Place 4906370 (San Juan Co)
    "06700": "Bluff",  # FIPS Place 4906700 (San Juan Co)
    "07690": "Bountiful",  # FIPS Place 4907690 (Davis Co)
    "08460": "Brigham City",  # FIPS Place 4908460 (Box Elder Co)
    "08570": "Brighton",  # FIPS Place 4908570 (Salt Lake Co)
    "11440": "Cedar Hills",  # FIPS Place 4911440 (Utah Co)
    "11980": "Centerville",  # FIPS Place 4911980 (Davis Co)
    "14290": "Clinton",  # FIPS Place 4914290 (Davis Co)
    "20810": "Eagle Mountain",  # FIPS Place 4920810 (Utah Co)
    "23530": "Ephraim",  # FIPS Place 4923530 (Sanpete Co)
    "23640": "Erda",  # FIPS Place 4923640 (Tooele Co)
    "23750": "Escalante",  # FIPS Place 4923750 (Garfield Co)
    "24080": "Eureka",  # FIPS Place 4924080 (Juab Co)
    "24630": "Fairview",  # FIPS Place 4924630 (Sanpete Co)
    # iter-228 additions (25, 2026-05-19): Census Gazetteer F-M sweep.
    "27930": "Garden City",  # FIPS Place 4927930 (Rich Co)
    "31120": "Grantsville",  # FIPS Place 4931120 (Tooele Co)
    "31670": "Green River",  # FIPS Place 4931670 (Emery Co)
    "32660": "Gunnison",  # FIPS Place 4932660 (Sanpete Co)
    "33760": "Hatch",  # FIPS Place 4933760 (Garfield Co)
    "34530": "Helper",  # FIPS Place 4934530 (Carbon Co)
    "35190": "Highland",  # FIPS Place 4935190 (Utah Co)
    "37060": "Huntsville",  # FIPS Place 4937060 (Weber Co)
    "37170": "Hurricane",  # FIPS Place 4937170 (Washington Co)
    "37390": "Hyde Park",  # FIPS Place 4937390 (Cache Co)
    "37500": "Hyrum",  # FIPS Place 4937500 (Cache Co)
    "37690": "Independence",  # FIPS Place 4937690 (Salt Lake Co)
    "38710": "Ivins",  # FIPS Place 4938710 (Washington Co)
    "39920": "Kanab",  # FIPS Place 4939920 (Kane Co)
    "41680": "Koosharem",  # FIPS Place 4941680 (Sevier Co)
    "43440": "La Verkin",  # FIPS Place 4943440 (Washington Co)
    "43660": "Layton",  # FIPS Place 4943660 (Davis Co)
    "44100": "Leeds",  # FIPS Place 4944100 (Washington Co)
    "44320": "Lehi",  # FIPS Place 4944320 (Utah Co)
    "44760": "Lewiston",  # FIPS Place 4944760 (Cache Co)
    "45090": "Lindon",  # FIPS Place 4945090 (Utah Co)
    "45530": "Loa",  # FIPS Place 4945530 (Wayne Co)
    "47730": "Manti",  # FIPS Place 4947730 (Sanpete Co)
    "47840": "Mantua",  # FIPS Place 4947840 (Box Elder Co)
    "47950": "Mapleton",  # FIPS Place 4947950 (Utah Co)
}


def city_name(code: str) -> str | None:
    """Return the friendly UT city name for an SST code, or None."""
    return UT_CITY_NAMES.get(code)


__all__ = ["UT_CITY_NAMES", "city_name"]
