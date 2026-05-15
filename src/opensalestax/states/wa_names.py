# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Washington city tax authorities.

WA's "city" code in the SST file is actually the COMBINED local
rate (city + county + Sound Transit / RTA / Cultural Access /
TBD where applicable) -- so the friendly name is just the city
the code is most commonly associated with. Verified by ZIP probe
+ rate cross-check against WA DOR's "Local Sales & Use Tax Rates
and Changes" publication (2026-Q2). The 5-digit codes are FIPS
Place codes (the "Place" half of the standard state-FIPS /
place-FIPS pair, e.g. Vancouver = 53-74060).
"""

from __future__ import annotations

WA_CITY_NAMES: dict[str, str] = {
    "05210": "Bellevue (combined local)",
    "05280": "Bellingham (combined local)",
    "22640": "Everett (combined local)",
    "23515": "Federal Way (combined local)",
    "35275": "Kennewick (combined local)",  # ZIP 99336 (verified by probe; FIPS 5335275)
    "35415": "Kent (combined local)",  # ZIP 98035 (verified by probe; FIPS 5335415)
    "38038": "Lakewood (combined local)",  # ZIP 98493 (verified by probe; FIPS 5338038)
    "50360": "Oak Harbor (combined local)",  # ZIP 98277 (verified by probe; FIPS 5350360)
    "51300": "Olympia (combined local)",
    "57745": "Renton (combined local)",
    "63000": "Seattle (combined local)",
    # iter-86 addition: Sedro-Woolley via probe + FIPS Place
    "63210": "Sedro-Woolley (combined local)",  # ZIP 98284 (Skagit Co; FIPS 5363210)
    "67000": "Spokane (combined local)",
    "67167": "Spokane Valley (combined local)",  # ZIP 99211 (verified by probe; FIPS 5367167)
    "70000": "Tacoma (combined local)",
    "74060": "Vancouver (combined local)",
    "77105": "Wenatchee (combined local)",  # ZIP 98801 (verified by probe; FIPS 5377105)
    "80010": "Yakima (combined local)",  # ZIP 98907 (verified by probe; FIPS 5380010)
    # iter-176 additions (2026-05-14): 15 more WA cities verified
    # by ZIP probe + FIPS Place cross-check. King / Snohomish /
    # Pierce / Clark / Kittitas / Benton / Jefferson / Clallam
    # coverage expanded so common WA suburbs no longer show as
    # ``WA-city-NNNNN`` placeholders on receipts.
    "08850": "Burien (combined local)",  # ZIP 98166 (King Co; FIPS 5308850)
    "21240": "Ellensburg (combined local)",  # ZIP 98926 (Kittitas Co; FIPS 5321240)
    "33805": "Issaquah (combined local)",  # ZIPs 98027/98029 (King Co; FIPS 5333805)
    "35170": "Kenmore (combined local)",  # ZIP 98028 (King Co; FIPS 5335170)
    "35940": "Kirkland (combined local)",  # ZIP 98033 (King Co; FIPS 5335940)
    "43150": "Maple Valley (combined local)",  # ZIP 98038 (King Co; FIPS 5343150)
    "43955": "Marysville (combined local)",  # ZIP 98270 (Snohomish Co; FIPS 5343955)
    "55855": "Port Townsend (combined local)",  # ZIP 98368 (Jefferson Co; FIPS 5355855)
    "57535": "Redmond (combined local)",  # ZIP 98052 (King Co; FIPS 5357535)
    "58235": "Richland (combined local)",  # ZIP 99352 (Benton Co; FIPS 5358235)
    "61115": "Sammamish (combined local)",  # ZIP 98075 (King Co; FIPS 5361115)
    "63385": "Sequim (combined local)",  # ZIP 98382 (Clallam Co; FIPS 5363385)
    "65170": "Snohomish (combined local)",  # ZIP 98290 (Snohomish Co; FIPS 5365170)
    "76405": "Washougal (combined local)",  # ZIP 98671 (Clark Co; FIPS 5376405)
    "79590": "Woodinville (combined local)",  # ZIP 98072 (King Co; FIPS 5379590)
}


def city_name(code: str) -> str | None:
    """Return the friendly WA city name for an SST code, or None."""
    return WA_CITY_NAMES.get(code)


__all__ = ["WA_CITY_NAMES", "city_name"]
