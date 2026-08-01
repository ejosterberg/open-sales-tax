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

# Boroughs that levy a borough-WIDE sales tax (collected on every
# transaction in unincorporated borough territory; per ARSSTC and
# borough practice, NOT collected inside any city's incorporated
# limits where a city tax already applies). Used as the
# state-only-fallback rate for ZIPs in the borough that aren't in
# any AK_CITIES coverage set.
#
# Consolidated city-boroughs (Sitka City and Borough, Juneau City
# and Borough, Wrangell City and Borough, Yakutat City and Borough,
# Petersburg Borough, Haines Borough, Skagway Municipality) are NOT
# in this map -- they're modeled as cities in AK_CITIES because the
# borough IS the city; there's no unincorporated territory.
#
# Format: {borough_name: borough_wide_rate_pct}
AK_BOROUGHS: dict[str, Decimal] = {
    "Kenai Peninsula Borough": Decimal("3.000"),
    "Ketchikan Gateway Borough": Decimal("2.500"),
}

# ARSSTC-attested borough ZIPs that Census ZIP_COUNTY does NOT resolve to
# the taxing borough. The borough pass in :mod:`opensalestax.states.alaska`
# is driven by Census ZCTA geography, which is authoritative for *where a
# ZIP is* but not for *who taxes it* -- and for Alaska the taxing authority
# is ARSSTC. Where the two disagree, ARSSTC wins.
#
# Added 2026-08-01 after the daily audit diffed the full ARSSTC
# "Rate Sheet with Zip Codes 7-1-2026" against the live engine:
#
# - 99928 (Ward Cove) and 99950 are absent from ZIP_COUNTY entirely.
# - 99903 and 99918 are present but Census assigns them to Wrangell
#   (AK-275) and Prince of Wales-Hyder (AK-198) respectively, neither of
#   which levies a borough tax -- while ARSSTC bills all four as
#   KETCHIKAN GATEWAY at a 2.5% borough floor.
#
# Without this map 99928 returned the Ketchikan city rate with no borough
# tax, and the other three returned 0.000%.
#
# Format: {borough_name: frozenset of ZIPs}
AK_BOROUGH_ZIPS: dict[str, frozenset[str]] = {
    "Ketchikan Gateway Borough": frozenset({"99903", "99918", "99928", "99950"}),
}

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
    "Chignik": (
        "Lake and Peninsula Borough",
        Decimal("2.000"),
        frozenset({"99564"}),
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
    "Elim": (
        "Nome Census Area",
        Decimal("3.000"),
        frozenset({"99739"}),
    ),
    # Added 2026-08-01: ARSSTC carries EXCURSION INLET as a 4.5%
    # inside-city rate under BOTH the Juneau borough (ZIP 99850) and the
    # Haines borough (ZIP 99827) -- the community straddles the boundary.
    # Only 99850 is claimed here; 99827 already resolves to Haines and
    # sits inside the ARSSTC 4.5-7.0 bracket for that ZIP, so re-pointing
    # it would trade one defensible answer for another.
    "Excursion Inlet": (
        "Juneau City and Borough",
        Decimal("4.500"),
        frozenset({"99850"}),
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
    # 99824 (Douglas) added 2026-08-01: ARSSTC lists it as borough JUNEAU /
    # city JUNEAU at 5.0%, but it was missing from this set so the ZIP
    # returned 0.000%. Douglas is inside the consolidated City and Borough
    # of Juneau.
    "Juneau": (
        "Juneau City and Borough",
        Decimal("5.000"),
        frozenset({"99801", "99802", "99803", "99811", "99812", "99821", "99824"}),
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
    "Mekoryuk": (
        "Bethel Census Area",
        Decimal("4.000"),
        frozenset({"99630"}),
    ),
    "Mountain Village": (
        "Kusilvak Census Area",
        Decimal("3.000"),
        frozenset({"99632"}),
    ),
    # 99928 (Ward Cove) was WRONGLY listed here until 2026-08-01. ARSSTC
    # gives 99928 no city filing code at all -- Ward Cove is unincorporated
    # Ketchikan Gateway Borough territory, so it owes the 2.5% borough tax
    # and NO city tax. Because 99928 is also absent from Census ZIP_COUNTY,
    # the borough pass could not bind it either, so the ZIP returned the
    # 5.5% city rate alone: over-collecting by 3.00pp AND dropping the
    # borough tax it did owe. It is now carried in AK_BOROUGH_ZIPS instead.
    # 99903 / 99918 / 99950 are ARSSTC "KETCHIKAN, I" ZIPs that were
    # missing entirely (engine returned 0.000%); they behave like 99901.
    "Ketchikan": (
        "Ketchikan Gateway Borough",
        Decimal("5.500"),  # ARSSTC peak 5.5%/winter 3.0%; using peak
        frozenset({"99901", "99903", "99918", "99950"}),
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
    "Pelican": (
        "Hoonah-Angoon Census Area",
        Decimal("6.000"),  # ARSSTC peak; winter rate 4.0%
        frozenset({"99832"}),
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
    "Scammon Bay": (
        "Kusilvak Census Area",
        Decimal("6.000"),
        frozenset({"99662"}),
    ),
    "Selawik": (
        "Northwest Arctic Borough",
        Decimal("6.500"),
        frozenset({"99770"}),
    ),
    "Shungnak": (
        "Northwest Arctic Borough",
        Decimal("2.000"),
        frozenset({"99773"}),
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
    # 99836 added 2026-08-01: ARSSTC lists it as borough SITKA at 6.0%
    # (inside-city row); it was missing so the ZIP returned 0.000%.
    "Sitka": (
        "Sitka City and Borough",
        Decimal("6.000"),  # ARSSTC peak 6.0%/winter 5.0%; using peak
        frozenset({"99835", "99836"}),
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
    "Toksook Bay": (
        "Bethel Census Area",
        Decimal("2.000"),
        frozenset({"99637"}),
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
    "White Mountain": (
        "Nome Census Area",
        Decimal("3.000"),
        frozenset({"99784"}),
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
