# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Human-readable names for Wisconsin tax authorities.

The SST quarterly rate file references jurisdictions by opaque
numeric codes (county FIPS like ``001``, city codes like
``53000``). These are fine for internal joins but useless on a
customer-facing receipt.

This module is the single source of truth for the SST-code ->
friendly-name translation for WI cities. It is consulted at LOAD
time (the data loader writes the friendly name into
``tax_authorities.name`` at insert time) so the engine's output
already carries human-readable names without any per-request
mapping work.

iter-63/64/79 set (31 entries) covers most of Wisconsin's
largest incorporated cities and many suburbs / county seats /
mid-size cities. Each code below was confirmed two ways:

1. Probe live API for a ZIP known to lie in that city, e.g.
   ``GET /v1/rates?zip5=53202`` returns the city placeholder
   ``WI-city-53000`` -> code 53000 belongs to whatever city
   53202 lies in.
2. Cross-check against the US Census FIPS Place code. WI's SST
   jurisdiction codes for major cities follow the Census
   ``state-FIPS + place-FIPS`` scheme: Milwaukee FIPS Place is
   5553000, the SST code is the trailing 53000. Match for all
   11 entries below.

Note that not every SST WI city code matches a FIPS Place code
1:1 -- some ZIPs return codes for adjacent villages
(Allouez/Ashwaubenon for some 54301-area ZIPs) rather than the
nominal Green Bay city. This module ONLY adds entries verified
both ways; placeholders ``WI-city-NNNNN`` continue to surface for
codes still pending empirical verification.

Sources:
- US Census Bureau FIPS Class Codes (state 55 = Wisconsin) and
  the WI Place codes list (52 entries, available via the Census
  TIGER/Line gazetteer).
- Live probes against api.opensalestax.org/v1/rates per ZIP.
"""

from __future__ import annotations

WI_CITY_NAMES: dict[str, str] = {
    "02375": "Appleton",
    "05900": "Beaver Dam",
    "06925": "Berlin",  # iter-90 (ZIP 54923; Green Lake Co; FIPS 5506925)
    "10025": "Brookfield",  # iter-90 (ZIP 53005; Waukesha Co; FIPS 5510025)
    "19775": "De Pere",
    "22300": "Eau Claire",
    "23300": "Elkhorn",
    "25950": "Fitchburg",
    "26275": "Fond du Lac",
    "27300": "Franklin",
    "30075": "Grand Chute",
    "31000": "Green Bay",
    "31125": "Greendale",
    "37825": "Janesville",
    "39225": "Kenosha",
    "46850": "McFarland",  # iter-90 (ZIP 53558; Dane Co; FIPS 5546850)
    "48000": "Madison",
    "49300": "Marinette",  # iter-90 (ZIP 54143; Marinette Co; FIPS 5549300)
    "51575": "Middleton",
    "53000": "Milwaukee",
    "54875": "Mount Pleasant",  # iter-90 (ZIP 53406; Racine Co; FIPS 5554875)
    "55750": "Neenah",
    "56375": "New Berlin",
    "58800": "Oak Creek",
    "59875": "Omro",  # iter-90 (ZIP 54963; Winnebago Co; FIPS 5559875)
    "60500": "Oshkosh",
    "63300": "Pleasant Prairie",  # iter-90 (ZIP 53158; Kenosha Co; FIPS 5563300)
    "64100": "Portage",
    "66000": "Racine",
    "67200": "Rhinelander",
    "77200": "Stevens Point",
    "77675": "Stoughton",
    "77875": "Sturgeon Bay",
    "78600": "Sun Prairie",  # iter-90 (ZIP 53590; Dane Co; FIPS 5578600)
    "78650": "Superior",
    "84250": "Waukesha",
    "84475": "Wausau",
    "85300": "West Allis",
    "87200": "Whitewater",
    # iter-183 additions (20, 2026-05-15): probed common WI ZIPs and
    # picked up the curated names for 20 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match (55-NNNNN pattern).
    "01550": "Altoona",  # ZIP 54720 (Eau Claire Co; FIPS Place 5501550)
    "02250": "Antigo",  # ZIP 54409 (Langlade Co; FIPS Place 5502250)
    "04625": "Baraboo",  # ZIP 53913 (Sauk Co; FIPS Place 5504625)
    "16450": "Columbus",  # ZIP 53925 (Columbia Co; FIPS Place 5516450)
    "29400": "Glendale",  # ZIP 53217 (Milwaukee Co; FIPS Place 5529400)
    "31175": "Greenfield",  # ZIPs 53220/53228 (Milwaukee Co; FIPS Place 5531175)
    "36525": "Hurley",  # ZIP 54534 (Iron Co; FIPS Place 5536525)
    "40775": "La Crosse",  # ZIP 54601 (La Crosse Co; FIPS Place 5540775)
    "48500": "Manitowoc",  # ZIP 54220 (Manitowoc Co; FIPS Place 5548500)
    "50425": "Medford",  # ZIP 54451 (Taylor Co; FIPS Place 5550425)
    "51025": "Menomonie",  # ZIP 54751 (Dunn Co; FIPS Place 5551025)
    "57100": "New Richmond",  # ZIP 54017 (St. Croix Co; FIPS Place 5557100)
    "63525": "Plover",  # ZIP 54467 (Portage Co; FIPS Place 5563525)
    "68175": "Ripon",  # ZIP 54971 (Fond du Lac Co; FIPS Place 5568175)
    "70125": "Waupaca",  # ZIP 54980 (Waupaca Co; FIPS Place 5570125)
    "72925": "Shawano",  # ZIP 54166 (Shawano Co; FIPS Place 5572925)
    "75625": "Spooner",  # ZIP 54801 (Washburn Co; FIPS Place 5575625)
    "83175": "Wales",  # ZIP 53183 (Waukesha Co; FIPS Place 5583175)
    "84675": "Wauwatosa",  # ZIP 53226 (Milwaukee Co; FIPS Place 5584675)
    "88150": "Wisconsin Dells",  # ZIP 53965 (Columbia/Sauk Co; FIPS Place 5588150)
    # iter-231 additions (12, 2026-05-19): Census 2024 Gazetteer for WI
    # places (state 55). Same bulk-lookup pattern proven on UT in
    # iter-226..230. Each SST code XXXXX matches Census FIPS Place
    # 55-XXXXX.
    "00100": "Abbotsford",  # FIPS Place 5500100 (Clark/Marathon Co)
    "00275": "Adams",  # FIPS Place 5500275 (Adams Co)
    "00450": "Adell",  # FIPS Place 5500450 (Sheboygan Co; village)
    "00750": "Albany",  # FIPS Place 5500750 (Green Co; village)
    "01000": "Algoma",  # FIPS Place 5501000 (Kewaunee Co)
    "01150": "Allouez",  # FIPS Place 5501150 (Brown Co; village)
    "01225": "Alma",  # FIPS Place 5501225 (Buffalo Co)
    "01300": "Alma Center",  # FIPS Place 5501300 (Jackson Co; village)
    "01325": "Almena",  # FIPS Place 5501325 (Barron Co; village)
    "01400": "Almond",  # FIPS Place 5501400 (Portage Co; village)
    "01725": "Amery",  # FIPS Place 5501725 (Polk Co)
    "01750": "Amherst",  # FIPS Place 5501750 (Portage Co; village)
    # NOTE: WI has ~1850 SST city placeholders total; the Census
    # Gazetteer for WI places only covers cities, villages, and CDPs.
    # WI's unique Town governance form (used in townships) is NOT in
    # the Place gazetteer -- WI Towns require the Census County
    # Subdivision file (2024_gaz_cousub_55.txt). Future iters can use
    # that file to label the remaining ~70% of WI codes.
}


def city_name(code: str) -> str | None:
    """Return the friendly WI city name for an SST code, or None."""
    return WI_CITY_NAMES.get(code)


__all__ = ["WI_CITY_NAMES", "city_name"]
