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
    "48000": "Madison",
    "51575": "Middleton",
    "53000": "Milwaukee",
    "55750": "Neenah",
    "56375": "New Berlin",
    "58800": "Oak Creek",
    "60500": "Oshkosh",
    "64100": "Portage",
    "66000": "Racine",
    "67200": "Rhinelander",
    "77200": "Stevens Point",
    "77675": "Stoughton",
    "77875": "Sturgeon Bay",
    "78650": "Superior",
    "84250": "Waukesha",
    "84475": "Wausau",
    "85300": "West Allis",
    "87200": "Whitewater",
}


def city_name(code: str) -> str | None:
    """Return the friendly WI city name for an SST code, or None."""
    return WI_CITY_NAMES.get(code)


__all__ = ["WI_CITY_NAMES", "city_name"]
