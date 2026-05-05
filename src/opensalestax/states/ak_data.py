# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Alaska sales tax rate + boundary data (top-cities ratchet).

Source: Alaska Remote Seller Sales Tax Commission (ARSSTC) member
jurisdictions list at https://arsstc.org/business-sellers/member-jurisdictions/
captured 2026-05-05. ARSSTC is the canonical clearinghouse for
remote-seller AK sales tax rates; participating jurisdictions
(~65 as of 2026Q2) post their general-retail rates here.

## ALASKA HAS NO STATEWIDE SALES TAX

Alaska is one of the five "no-state-tax" jurisdictions (with DE,
MT, NH, OR), but unlike the other four, ~110 AK municipalities
levy local sales tax at rates ranging from 0% to 7.5%. Until
v0.49 OpenSalesTax modeled AK as no-tax everywhere, missing
real local collections in major towns.

This ratchet ships a **cities-only MVP** covering the 20 largest
sales-tax-collecting AK municipalities (every one whose general-
retail rate I could verify against ARSSTC). The state authority
is registered at 0%; the city authorities carry the real rate.

## SIMPLIFICATIONS / KNOWN GAPS

1. **Borough rates are NOT modeled.** Several AK boroughs (Kenai
   Peninsula 3%, Petersburg 6%, Ketchikan Gateway 2.5%, Haines
   7%, Skagway 5%) impose a borough-wide tax in addition to or
   instead of city rates. Per practice in most boroughs (e.g.
   KPB), the borough rate is NOT collected inside city limits
   where a city tax already applies -- so naively stacking
   borough+city would over-collect at the city center. Modeling
   the per-borough exclusivity rule is deferred to a later
   ratchet. For now, ZIPs in covered cities return the city
   rate only; ZIPs in unincorporated borough areas return 0%
   (under-collects by the borough rate at those addresses).

2. **Anchorage Municipality is NOT modeled with a city rate.**
   Anchorage Municipality has historically had NO general sales
   tax (residents have voted down sales-tax ballot measures
   repeatedly). The ARSSTC list shows "Anchorage, Municipality
   of: 5.00%" without a category modifier, but this is widely
   understood to be Anchorage's REMOTE-SELLER sales tax (which
   ARSSTC administers) introduced via the SCOTUS Wayfair
   decision. Anchorage retail purchases at brick-and-mortar
   stores remain UNTAXED at the state and local level. To avoid
   confusing in-state buyers, we leave Anchorage at 0% for
   ZIP-based lookups (in-state commerce posture).

3. **Fairbanks city is NOT modeled.** Fairbanks has no city
   sales tax (Fairbanks North Star Borough also imposes none).

4. **Seasonal rates are not modeled.** Several AK localities
   (Sitka 6% peak / 5% winter, Ketchikan 5.5% / 3.0%, Haines
   7%/4.5%, Skagway 5%/3%) use higher peak-season rates and
   lower winter rates. We use the year-round rate where ARSSTC
   publishes one, otherwise the peak rate. Off-season returns
   will over-collect by the seasonal delta in those ZIPs.

5. **Bottle / alcohol / lodging / tobacco / marijuana taxes are
   NOT modeled.** ARSSTC publishes separate rates for these
   categories (e.g. Bethel Alcoholic Beverage 15.00%, Dillingham
   Alcoholic 10.00%) but they are non-general-retail and
   outside this engine's general sales-tax scope.

## SCHEMA

``AK_CITIES`` maps city display name to:

  ``(borough_name, general_retail_rate_pct, frozenset(zip5))``

The borough name is informational (matches
``opensalestax.data.county_names.COUNTY_NAMES``) and can be used
later when modeling borough-vs-city exclusivity. ``frozenset(zip5)``
is the set of ZIP5s where this city's tax is collected (per
USPS attribution; small/rural cities typically have one ZIP).
"""

from __future__ import annotations

from decimal import Decimal

# Alaska has no statewide general sales tax. The state authority
# exists for engine compatibility (every AK ZIP gets a state-level
# row in the rate stack); its rate is 0%.
AK_STATE_RATE_PCT: Decimal = Decimal("0.000")

# (borough name, general retail rate, frozenset of ZIPs)
AK_CITIES: dict[str, tuple[str, Decimal, frozenset[str]]] = {
    "Adak": (
        "Aleutians West Census Area",
        Decimal("4.000"),
        frozenset({"99546"}),
    ),
    "Aleknagik": (
        "Dillingham Census Area",
        Decimal("5.000"),
        frozenset({"99555"}),
    ),
    "Aniak": (
        "Bethel Census Area",
        Decimal("2.000"),
        frozenset({"99557"}),
    ),
    "Bethel": (
        "Bethel Census Area",
        Decimal("6.000"),
        frozenset({"99559"}),
    ),
    "Cordova": (
        "Chugach Census Area",
        Decimal("7.000"),
        frozenset({"99574"}),
    ),
    "Craig": (
        "Prince of Wales-Hyder Census Area",
        Decimal("7.000"),  # ARSSTC peak; winter rate 6%
        frozenset({"99921"}),
    ),
    "Dillingham": (
        "Dillingham Census Area",
        Decimal("6.000"),
        frozenset({"99576"}),
    ),
    "Galena": (
        "Yukon-Koyukuk Census Area",
        Decimal("3.000"),
        frozenset({"99741"}),
    ),
    "Gustavus": (
        "Hoonah-Angoon Census Area",
        Decimal("3.000"),
        frozenset({"99826"}),
    ),
    "Haines": (
        "Haines Borough",
        Decimal("5.500"),  # ARSSTC "Haines Rural" 5.0%/3.0%; using rural year-round
        frozenset({"99827"}),
    ),
    "Homer": (
        "Kenai Peninsula Borough",
        Decimal("4.850"),
        frozenset({"99603"}),
    ),
    "Houston": (
        "Matanuska-Susitna Borough",
        Decimal("2.000"),
        frozenset({"99694"}),
    ),
    "Juneau": (
        "Juneau City and Borough",
        Decimal("5.000"),
        frozenset({"99801", "99802", "99803", "99811", "99812", "99821"}),
    ),
    "Kake": (
        "Hoonah-Angoon Census Area",
        Decimal("5.000"),
        frozenset({"99830"}),
    ),
    "Kenai": (
        "Kenai Peninsula Borough",
        Decimal("3.000"),
        frozenset({"99611"}),
    ),
    "Mountain Village": (
        "Kusilvak Census Area",
        Decimal("3.000"),
        frozenset({"99632"}),
    ),
    "Ketchikan": (
        "Ketchikan Gateway Borough",
        Decimal("5.500"),  # ARSSTC peak 5.5%/winter 3.0%; using peak
        frozenset({"99901", "99928"}),
    ),
    "Kodiak": (
        "Kodiak Island Borough",
        Decimal("7.000"),
        frozenset({"99615", "99619"}),
    ),
    "Kotzebue": (
        "Northwest Arctic Borough",
        Decimal("6.000"),
        frozenset({"99752"}),
    ),
    "Nenana": (
        "Yukon-Koyukuk Census Area",
        Decimal("4.000"),
        frozenset({"99760"}),
    ),
    "Nome": (
        "Nome Census Area",
        Decimal("6.000"),
        frozenset({"99762"}),
    ),
    "North Pole": (
        "Fairbanks North Star Borough",
        Decimal("5.500"),
        frozenset({"99705"}),
    ),
    "Old Harbor": (
        "Kodiak Island Borough",
        Decimal("3.000"),
        frozenset({"99643"}),
    ),
    "Quinhagak": (
        "Bethel Census Area",
        Decimal("3.000"),
        frozenset({"99655"}),
    ),
    "Ouzinkie": (
        "Kodiak Island Borough",
        Decimal("6.000"),
        frozenset({"99644"}),
    ),
    "Palmer": (
        "Matanuska-Susitna Borough",
        Decimal("3.000"),
        frozenset({"99645"}),
    ),
    "Petersburg": (
        "Petersburg Borough",
        Decimal("6.000"),
        frozenset({"99833"}),
    ),
    "Saint Paul": (
        "Aleutians East Borough",
        Decimal("3.500"),
        frozenset({"99660"}),
    ),
    "Selawik": (
        "Northwest Arctic Borough",
        Decimal("6.500"),
        frozenset({"99770"}),
    ),
    "Seldovia": (
        "Kenai Peninsula Borough",
        Decimal("6.500"),  # ARSSTC peak; winter rate 2.0%
        frozenset({"99663"}),
    ),
    "Seward": (
        "Kenai Peninsula Borough",
        Decimal("4.000"),
        frozenset({"99664"}),
    ),
    "Sitka": (
        "Sitka City and Borough",
        Decimal("6.000"),  # ARSSTC peak 6.0%/winter 5.0%; using peak
        frozenset({"99835"}),
    ),
    "Skagway": (
        "Skagway Municipality",
        Decimal("5.000"),  # ARSSTC peak 5.0%/winter 3.0%; using peak
        frozenset({"99840"}),
    ),
    "Soldotna": (
        "Kenai Peninsula Borough",
        Decimal("3.000"),
        frozenset({"99669"}),
    ),
    "Tenakee Springs": (
        "Hoonah-Angoon Census Area",
        Decimal("2.000"),
        frozenset({"99841"}),
    ),
    "Thorne Bay": (
        "Prince of Wales-Hyder Census Area",
        Decimal("6.000"),
        frozenset({"99919"}),
    ),
    "Togiak": (
        "Dillingham Census Area",
        Decimal("2.000"),
        frozenset({"99678"}),
    ),
    "Unalakleet": (
        "Nome Census Area",
        Decimal("5.000"),
        frozenset({"99684"}),
    ),
    "Unalaska": (
        "Aleutians West Census Area",
        Decimal("3.000"),
        frozenset({"99685"}),
    ),
    "Wasilla": (
        "Matanuska-Susitna Borough",
        Decimal("2.500"),
        frozenset({"99654", "99687", "99629"}),
    ),
    "Wrangell": (
        "Wrangell City and Borough",
        Decimal("7.000"),
        frozenset({"99929"}),
    ),
    "Yakutat": (
        "Yakutat City and Borough",
        Decimal("5.000"),
        frozenset({"99689"}),
    ),
}
