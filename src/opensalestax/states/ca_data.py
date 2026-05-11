# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""California sales tax rate + boundary data (top-50-city CDTFA loader).

Source: California Department of Tax and Fee Administration (CDTFA)
publication "California City and County Sales and Use Tax Rates" --
the rate table effective **April 1, 2026** (Q2 2026), retrieved
2026-05-04 from https://www.cdtfa.ca.gov/taxes-and-fees/rates.htm
and cross-checked against CDTFA Publication 105 ("California City and
County Sales and Use Tax Rates by City") plus Avalara's per-city rate
pages (https://www.avalara.com/taxrates/en/state-rates/california/) on
the same date.

Architecture: California's combined rate has three modeled layers:

1. **State portion: 7.25%** -- the highest statewide rate in the
   United States. Internally CDTFA reports this as state 6.0% +
   uniform county base 1.0% + statewide local 0.25% = 7.25%, but it
   applies uniformly across every California address; we model it as
   a single ``California`` state authority for clarity. (Cal. Rev.
   & Tax Code section 6051 et seq.)
2. **County district portion** -- voter-approved transactions and
   use tax overlays (transportation, transit, hospitals, etc.)
   collected county-wide. Ranges from 0.000% (Kern, Ventura) to
   2.250% (Los Angeles, with LACMTA/Measure M/Measure R/Measure H
   stacked) and 2.000% (Alameda, with BART + Measures B/BB/F/AA/C/W
   stacked).
3. **City district portion** -- city-only transactions and use tax
   overlays. Many California cities add 0.25%-1.75%; a handful go
   higher (Hayward 1.5%, Vallejo 1.875%, Oxnard 2.000%). Plenty of
   cities have NO city portion and ride only the state + county
   stack (Anaheim, Irvine, Fontana, Ontario, Roseville, etc.).

Combined-rate formula at any covered ZIP:

    state 7.250 + CA_COUNTY_RATE_PCT[county] + city_portion

The combined rate ranges from 7.250% (rural counties with no
district overlay -- e.g. Thousand Oaks in Ventura County) up to
10.750% (Hayward in Alameda County) in this seed. Pico Rivera and
Santa Fe Springs (also at 10.750%) are not in the top-50 by
population and are not included here.

**Sourcing model:** California uses a hybrid sourcing rule -- the
**state + uniform 1.25%** portion is sourced to the seller's
location for in-state sales (origin), but the **district tax**
portions (county + city) are sourced to the **delivery address**
(destination) per Cal. Rev. & Tax Code section 7261. The ZIP-based
boundary table here is a **delivery-address approximation** that
produces the correct combined rate for a buyer at that ZIP. For
out-of-state sellers (post-Wayfair), district tax is collected at
the destination rate. A future ratchet should expose the seller-vs-
buyer distinction so the API caller can pick the right rule.

Cities seeded (top 50 by 2020 census population, with East Los
Angeles included as the CDP carrying the LA County rate):

Los Angeles, San Diego, San Jose, San Francisco, Fresno, Sacramento,
Long Beach, Oakland, Bakersfield, Anaheim, Santa Ana, Riverside,
Stockton, Irvine, Chula Vista, Fremont, San Bernardino, Modesto,
Fontana, Oxnard, Moreno Valley, Huntington Beach, Glendale, Santa
Clarita, Garden Grove, Oceanside, Rancho Cucamonga, Santa Rosa,
Ontario, Lancaster, Elk Grove, Palmdale, Corona, Salinas, Pomona,
Hayward, Escondido, Torrance, Sunnyvale, Orange, Fullerton, Pasadena,
Thousand Oaks, Visalia, Roseville, Concord, Simi Valley, East Los
Angeles, Vallejo, Santa Clara.

50 cities total. East Los Angeles is an unincorporated CDP (no city
sales tax of its own) and is included so its ZIPs bind to the LA
County district rate; its city_portion is 0.000%.

ZIPs not in :data:`CA_CITIES` fall back to state-only at 7.25% via
the Census ZCTA load. This is a **significant under-collection** for
suburban / unincorporated California -- the majority of CA's ~1,700
cities and unincorporated areas are not in this seed. A future
ratchet should ingest the CDTFA address-level CSV (the GIS Tax Rate
Areas dataset) to extend coverage statewide.

NOT modeled in v0.27:

- Address-level Tax Rate Area (TRA) precision. CA has ~25,000 TRAs
  encoding the exact district-overlay stack at each parcel; this seed
  uses the city-centroid combined rate which is correct for most
  ZIPs but may be off by 0.25%-1.0% for ZIPs that cross a special
  district boundary (e.g. some San Bernardino ZIPs that touch the
  Apple Valley district).
- Any city outside the top-50 seed. Pico Rivera (10.75%), Santa Fe
  Springs (10.75%), South Gate (10.25%), Compton (10.25%), and many
  other LA County and Alameda County suburbs have their own city
  portions that this seed does not encode.
- The state portion's internal split (state 6.0% + county base 1.0%
  + statewide local 0.25%) -- collapsed into a single 7.25% state
  authority for clarity.

Source-disagreement notes (CDTFA vs Avalara on 2026-05-04):

- **Salinas**: CDTFA Q2 2026 publication shows 9.250%. Avalara
  agrees. Some older third-party sources cite 9.375% (after Measure E
  2024 + Measure G 2016 stacking). Using the CDTFA-published 9.250%.
- **Sunnyvale / Santa Clara**: both at 9.125% per CDTFA (state 7.25
  + Santa Clara County 1.875). Avalara historically listed 9.000%
  before VTA 2016 Measure B took effect; current Avalara matches
  CDTFA at 9.125%.
- **Glendale (LA County)**: not to be confused with Glendale, AZ.
  Combined rate is 10.250%.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State combined rate -- 7.25% has been stable since 2017-01-01 when
# the temporary Proposition 30 0.25% surcharge expired and the rate
# returned to its statutory level (Cal. Rev. & Tax Code section 6051
# et seq.). 2017-01-01 is the canonical "current rate" effective date.
CA_STATE_RATE_PCT = Decimal("7.250")
CA_STATE_EFFECTIVE_FROM = dt.date(2017, 1, 1)

# Per-county district portion (NOT including the 7.25% state rate).
# These are the voter-approved transactions and use tax overlays
# collected uniformly across the entire county. Source: CDTFA Q2 2026
# rate table, retrieved 2026-05-04. Counties listed are only those
# touched by a covered city; counties with 0.000% rate are kept for
# audit parallelism with the AZ/MO/SC/VA/TX pattern (the engine sums
# 0% authorities to no effect but keeps the rate-stack audit trail).
CA_COUNTY_RATE_PCT: dict[str, Decimal] = {
    # ----- Reconciled with CDTFA Q2 2026 (iter-62) -----
    # All values audited 2026-05-09 against CDTFA's Apr 2026 Excel rate
    # file. Counties with explicit "Unincorporated Area" CDTFA rows use
    # those values; others use min(city_combined - state) which is
    # correct when at least one incorporated city in the county has
    # zero city-only district (verified for these counties via the
    # CDTFA city table). Per-city rates in CA_CITIES were rebalanced
    # in the same commit to keep all combined rates matching CDTFA.
    "Alameda County": Decimal("3.000"),  # iter-62: was 2.000 (under-collected by 1%)
    "Contra Costa County": Decimal("1.500"),  # BART + Measures J/X
    "Fresno County": Decimal("0.725"),  # iter-62: was 0.225 (under by 0.5%)
    "Kern County": Decimal("1.000"),  # iter-62: CDTFA Unincorporated Q2 2026 (was 0.000)
    "Los Angeles County": Decimal("2.500"),  # iter-62: was 2.250 (under by 0.25%)
    "Monterey County": Decimal("1.500"),  # iter-62: CDTFA Unincorporated Q2 2026 (was 0.500)
    "Orange County": Decimal("0.500"),  # OCTA Measure M2
    "Placer County": Decimal("0.000"),  # iter-62: was 0.500 (over-collected by 0.5%)
    "Riverside County": Decimal("0.500"),  # Measure A transportation
    "Sacramento County": Decimal("0.500"),  # Measure A transportation
    "San Bernardino County": Decimal("0.500"),  # Measure I transportation
    "San Diego County": Decimal("0.500"),  # SANDAG TransNet
    "San Francisco (City and County)": Decimal("1.375"),  # consolidated; transit + child care
    "San Joaquin County": Decimal("0.500"),  # Measure K transportation
    "Santa Clara County": Decimal("2.500"),  # iter-62: was 1.875 (under by 0.625%)
    "Solano County": Decimal("0.875"),  # iter-62: was 0.125 (under by 0.75%)
    "Sonoma County": Decimal("2.000"),  # iter-62: was 1.250 (under by 0.75%)
    "Stanislaus County": Decimal("0.625"),  # iter-62: was 0.125 (under by 0.5%)
    "Tulare County": Decimal("1.000"),  # iter-62: was 0.500 (under by 0.5%)
    "Ventura County": Decimal("0.000"),
    # ----- Iter-62: 35 additional counties from CDTFA Q2 2026 -----
    # Derived from CDTFA's "California City and County Sales and Use
    # Tax Rates" Excel (effective April 1, 2026, retrieved 2026-05-09
    # from cdtfa.ca.gov/taxes-and-fees/SalesTaxRates04-01-26.xlsx).
    # For counties without an explicit "Unincorporated Area" CDTFA row,
    # the rate is derived as `min(combined_city_rate) - 7.250`, which
    # matches the unincorporated rate when at least one city has no
    # city-only district. Verified against CDTFA's 5 explicit
    # Unincorporated Area entries: Del Norte, Kern, Monterey, Santa
    # Cruz, Yuba (3 of 5 match the min; Santa Cruz + Yuba have a small
    # county-wide tax that doesn't apply to all incorporated cities --
    # accepted as a known under-collect for unincorporated areas in
    # those two specific counties pending a CDTFA TRA-level loader).
    # Pre-fix these counties returned state-only 7.25%; post-fix they
    # return state + county-district correctly for incorporated areas.
    "Amador County": Decimal("0.500"),
    "Butte County": Decimal("1.000"),
    "Calaveras County": Decimal("1.500"),
    "Colusa County": Decimal("1.000"),
    "Del Norte County": Decimal("1.000"),  # CDTFA Unincorporated explicit
    "El Dorado County": Decimal("1.000"),
    "Glenn County": Decimal("1.000"),
    "Humboldt County": Decimal("2.250"),
    "Imperial County": Decimal("0.500"),
    "Inyo County": Decimal("1.500"),
    "Kings County": Decimal("1.000"),
    "Lake County": Decimal("1.500"),
    "Lassen County": Decimal("1.000"),
    "Madera County": Decimal("1.000"),
    "Marin County": Decimal("1.000"),
    "Mendocino County": Decimal("1.625"),
    "Merced County": Decimal("1.000"),
    "Modoc County": Decimal("0.000"),
    "Mono County": Decimal("0.500"),
    "Napa County": Decimal("0.500"),
    "Nevada County": Decimal("1.625"),
    "Plumas County": Decimal("0.000"),
    "San Benito County": Decimal("1.750"),
    "San Luis Obispo County": Decimal("1.000"),
    "San Mateo County": Decimal("2.125"),
    "Santa Barbara County": Decimal("0.500"),
    "Santa Cruz County": Decimal("2.250"),  # CDTFA Unincorporated explicit
    "Shasta County": Decimal("0.000"),
    "Sierra County": Decimal("0.000"),
    "Siskiyou County": Decimal("0.000"),
    "Sutter County": Decimal("0.000"),
    "Tehama County": Decimal("0.000"),
    "Tuolumne County": Decimal("1.500"),
    "Yolo County": Decimal("0.750"),
    "Yuba County": Decimal("1.000"),  # CDTFA Unincorporated explicit
}

# Per-city district portion (city-only overlay; NOT including state
# or county portions). Tuple shape:
#     (county_name, city_rate_pct, [zip5s])
# Combined rate at any covered ZIP:
#     7.250 + CA_COUNTY_RATE_PCT[county] + city_rate_pct
#
# East Los Angeles is an unincorporated CDP -- it has no city sales
# tax of its own but its ZIPs are bound to the LA County district
# rate. Its city_rate_pct is 0.000% and the parent_authority_name
# remains the county.
CA_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    # ----- Los Angeles County -----
    "Los Angeles": (
        "Los Angeles County",
        Decimal("0.000"),  # combined 9.500 = 7.25 + LA County 2.25
        # City of Los Angeles ZIPs (not the broader LA Co. metro). LA
        # has ~100 ZIPs; this is a representative selection of central
        # LA + major neighborhoods at the 9.500% city-centroid rate.
        (
            "90001",
            "90002",
            "90003",
            "90004",
            "90005",
            "90006",
            "90007",
            "90008",
            "90010",
            "90011",
            "90012",
            "90013",
            "90014",
            "90015",
            "90016",
            "90017",
            "90018",
            "90019",
            "90020",
            "90021",
            "90022",
            "90023",
            "90024",
            "90025",
            "90026",
            "90027",
            "90028",
            "90029",
            "90031",
            "90032",
            "90033",
            "90034",
            "90035",
            "90036",
            "90037",
            "90038",
            "90039",
            "90041",
            "90042",
            "90043",
            "90044",
            "90045",
            "90046",
            "90047",
            "90048",
            "90049",
            "90056",
            "90057",
            "90058",
            "90059",
            "90061",
            "90062",
            "90063",
            "90064",
            "90065",
            "90066",
            "90067",
            "90068",
            "90069",
            "90071",
        ),
    ),
    "Long Beach": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.250 = 7.25 + 2.25 + 0.75
        (
            "90802",
            "90803",
            "90804",
            "90805",
            "90806",
            "90807",
            "90808",
            "90810",
            "90813",
            "90814",
            "90815",
        ),
    ),
    "Glendale": (
        # Glendale, CA -- distinct from Glendale, AZ (which is in
        # Maricopa County and modeled separately in az_data).
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500 (state 7.25 + LA 2.5 + city 0.75)
        ("91201", "91202", "91203", "91204", "91205", "91206", "91207", "91208"),
    ),
    "Burbank": (
        # iter-93: added after probe surfaced 9.75% live vs CDTFA
        # 10.5% combined. Burbank levies a 0.75% city sales tax
        # (Measure P, eff 2018-04-01); state 7.25 + LA 2.5 + city
        # 0.75 = 10.500 per SalesTaxHandbook + CDTFA cdtfa95.pdf.
        # ZIP cluster covers downtown Burbank (91501-08) plus
        # PO-box business unique-ZIPs (91510, 91521-27).
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        (
            "91501",
            "91502",
            "91503",
            "91504",
            "91505",
            "91506",
            "91507",
            "91508",
            "91510",
            "91521",
            "91522",
            "91523",
            "91526",
        ),
    ),
    "Walnut Creek": (
        # iter-94: added after probe surfaced 8.75% live vs
        # SalesTaxHandbook 9.25% combined. Walnut Creek levies a
        # 0.5% city sales tax; state 7.25 + Contra Costa 1.5 + city
        # 0.5 = 9.250 per SalesTaxHandbook (CDTFA cdtfa95.pdf
        # confirms 9.25% as the in-city rate).
        "Contra Costa County",
        Decimal("0.500"),  # combined 9.250
        ("94595", "94596", "94597", "94598"),
    ),
    "San Mateo": (
        # iter-94: added after probe surfaced 9.375% live vs
        # SalesTaxHandbook 9.625% combined. San Mateo city levies
        # a 0.25% city sales tax (TVCA / Measure W); state 7.25 +
        # San Mateo Co 2.125 + city 0.25 = 9.625 per
        # SalesTaxHandbook + CDTFA cdtfa95.pdf.
        "San Mateo County",
        Decimal("0.250"),  # combined 9.625
        ("94401", "94402", "94403", "94404"),
    ),
    "El Cerrito": (
        # iter-98: probed 8.75% live vs SalesTaxHandbook 10.75%.
        # El Cerrito stacks Measure G (1%) + Measure E (0.5%) +
        # Measure V (0.5%) = 2.0% city portion. State 7.25 +
        # Contra Costa 1.5 + city 2.0 = 10.750.
        "Contra Costa County",
        Decimal("2.000"),  # combined 10.750
        ("94530",),
    ),
    "Burlingame": (
        # iter-98: probed 9.375% live vs SalesTaxHandbook 9.625%.
        # Burlingame levies a 0.25% city sales tax. State 7.25 +
        # San Mateo Co 2.125 + city 0.25 = 9.625.
        "San Mateo County",
        Decimal("0.250"),  # combined 9.625
        ("94010", "94011"),
    ),
    "Richmond": (
        # iter-99: probed 8.75% live vs SalesTaxHandbook 9.75%.
        # Richmond levies 1% city sales tax. State 7.25 + Contra
        # Costa 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94801", "94802", "94803", "94804", "94805", "94806", "94807", "94808", "94850"),
    ),
    "Antioch": (
        # iter-99: probed 8.75% live vs SalesTaxHandbook 9.75%.
        # Antioch levies 1% city sales tax. State 7.25 + Contra
        # Costa 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94509", "94531"),
    ),
    "Pittsburg": (
        # iter-99: probed 8.75% live vs SalesTaxHandbook 9.75%.
        # Pittsburg levies 1% city sales tax. State 7.25 + Contra
        # Costa 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94565",),
    ),
    "Redwood City": (
        # iter-99: probed 9.375% live vs SalesTaxHandbook 9.875%.
        # Redwood City levies 0.5% city sales tax. State 7.25 +
        # San Mateo Co 2.125 + city 0.5 = 9.875.
        "San Mateo County",
        Decimal("0.500"),  # combined 9.875
        ("94061", "94062", "94063", "94064", "94065"),
    ),
    # iter-100: Marin County (4 cities @ 1% city tax) + San Mateo Co
    # (San Bruno + Pacifica @ 0.5%). All verified via SalesTaxHandbook
    # WebFetch.
    "Mill Valley": (
        "Marin County",
        Decimal("1.000"),  # combined 9.250
        ("94941", "94942"),
    ),
    "Sausalito": (
        "Marin County",
        Decimal("1.000"),  # combined 9.250
        ("94965", "94966"),
    ),
    "Larkspur": (
        "Marin County",
        Decimal("1.000"),  # combined 9.250
        ("94939",),
    ),
    "San Anselmo": (
        "Marin County",
        Decimal("1.000"),  # combined 9.250
        ("94960", "94979"),
    ),
    "San Bruno": (
        "San Mateo County",
        Decimal("0.500"),  # combined 9.875
        ("94066",),
    ),
    "Pacifica": (
        "San Mateo County",
        Decimal("0.500"),  # combined 9.875
        ("94044",),
    ),
    # iter-101: more Bay Area + Placer Co
    "Belmont": (
        # 9.375% live vs SalesTaxHandbook 9.875%. Belmont 0.5% city tax.
        "San Mateo County",
        Decimal("0.500"),  # combined 9.875
        ("94002",),
    ),
    "Rocklin": (
        # 7.25% live vs SalesTaxHandbook 7.75%. Rocklin 0.5% city tax;
        # Placer Co is 0% in our model (per iter-63 reconciliation).
        # state 7.25 + Placer 0 + city 0.5 = 7.75.
        "Placer County",
        Decimal("0.500"),  # combined 7.750
        ("95677", "95765"),
    ),
    # iter-102: more SF Bay Area + Contra Costa
    "San Carlos": (
        # 9.375% live vs SalesTaxHandbook 9.875%. 0.5% city tax.
        "San Mateo County",
        Decimal("0.500"),  # combined 9.875
        ("94070",),
    ),
    "San Ramon": (
        # 8.75% live (94583) vs SalesTaxHandbook 9.75% (94582 main).
        # San Ramon city 1.0% tax. ZIP 94582 (main); 94583 has Dublin
        # overlay (10.25%) per SalesTaxHandbook -- not modeled at the
        # ZIP level here.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94582",),
    ),
    "Folsom": (
        # iter-103: 8.25% live (engine picks El Dorado Co 1.0% for
        # ZIP 95630) vs SalesTaxHandbook 7.75% (Sacramento Co
        # 0.5%, no city tax). Folsom is in Sacramento Co per USPS;
        # adding the city anchor forces the correct county pick.
        # state 7.25 + Sacramento 0.5 + city 0.0 = 7.750.
        "Sacramento County",
        Decimal("0.000"),  # combined 7.750
        ("95630", "95763"),
    ),
    "Palo Alto": (
        # iter-104: 94301/94304/94305/94306 already return 9.75%
        # via Santa Clara County. ZIP 94302 returns 0% (PO-box-
        # only). Adding Palo Alto anchor with all Palo Alto ZIPs
        # ensures consistent Santa Clara binding + closes 94302.
        # state 7.25 + Santa Clara 2.5 + city 0 = 9.750.
        "Santa Clara County",
        Decimal("0.000"),  # combined 9.750
        ("94301", "94302", "94304", "94305", "94306"),
    ),
    "East Palo Alto": (
        # iter-104: 94303 was returning 9.375% (San Mateo Co only,
        # no city tax). SalesTaxHandbook 9.875% with East Palo
        # Alto +0.5% city tax.
        # state 7.25 + San Mateo 2.125 + city 0.5 = 9.875.
        "San Mateo County",
        Decimal("0.500"),  # combined 9.875
        ("94303",),
    ),
    # iter-105: more Marin Co cities (1% city tax pattern)
    "Novato": (
        "Marin County",
        Decimal("1.000"),  # combined 9.250
        ("94945", "94947", "94948", "94949"),
    ),
    "Corte Madera": (
        "Marin County",
        Decimal("1.000"),  # combined 9.250
        ("94925",),
    ),
    # iter-106: more LA Co + La Habra (OC) county-misattribution
    "Culver City": (
        # 9.75% live vs SalesTaxHandbook 10.75% (city +1.0% via Measure CC).
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90230", "90231", "90232", "90233"),
    ),
    "El Segundo": (
        # 9.75% live vs SalesTaxHandbook 10.50% (city +0.75%).
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90245",),
    ),
    "Whittier": (
        # 9.75% live vs SalesTaxHandbook 10.50% (city +0.75%).
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90601", "90602", "90603", "90604", "90605", "90606", "90607", "90608"),
    ),
    "La Habra": (
        # iter-106: 90631 was returning 9.75% with LA County
        # binding -- ZIP 90631 spans OC + LA counties per Census
        # ZCTA, our engine picks LA. La Habra IS in OC per USPS.
        # Anchoring La Habra to Orange County fixes the
        # misattribution + adds 1% city tax.
        # state 7.25 + OC 0.5 + city 1.0 = 8.750.
        "Orange County",
        Decimal("1.000"),  # combined 8.750
        ("90631", "90632", "90633"),
    ),
    # iter-107: more LA Co cities (South Bay)
    "Gardena": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90247", "90248", "90249"),
    ),
    "Lawndale": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90260", "90261"),
    ),
    "Hawthorne": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90250", "90251"),
    ),
    "Cerritos": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500 (Artesia area; 11.0% in
        # Santa Fe Springs subarea not modeled at this scale)
        ("90703",),
    ),
    "Santa Clarita": (
        "Los Angeles County",
        Decimal("0.000"),  # combined 9.500
        ("91350", "91351", "91354", "91355", "91387", "91390"),
    ),
    "Lancaster": (
        "Los Angeles County",
        Decimal("1.500"),  # combined 10.250 (Measure LR)
        ("93534", "93535", "93536"),
    ),
    "Palmdale": (
        "Los Angeles County",
        Decimal("1.500"),  # combined 10.250 (Measure AV)
        ("93550", "93551", "93552"),
    ),
    "Pomona": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.250
        ("91766", "91767", "91768"),
    ),
    "Torrance": (
        "Los Angeles County",
        Decimal("0.500"),  # combined 10.000
        ("90501", "90502", "90503", "90504", "90505"),
    ),
    "Pasadena": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.250
        ("91101", "91103", "91104", "91105", "91106", "91107"),
    ),
    "East Los Angeles": (
        # Unincorporated CDP -- no city sales tax of its own. ZIPs
        # bind to LA County's district rate (combined 9.500%).
        "Los Angeles County",
        Decimal("0.000"),  # combined 9.500 = 7.25 + LA County 2.25
        ("90022", "90023"),
    ),
    # ----- San Diego County -----
    "San Diego": (
        "San Diego County",
        Decimal("0.000"),  # combined 7.750 = 7.25 + 0.50
        (
            "92101",
            "92102",
            "92103",
            "92104",
            "92105",
            "92106",
            "92107",
            "92108",
            "92109",
            "92110",
            "92111",
            "92113",
            "92114",
            "92115",
            "92116",
            "92117",
            "92119",
            "92120",
            "92121",
            "92122",
            "92123",
            "92124",
            "92126",
            "92127",
            "92128",
            "92129",
            "92130",
            "92131",
            "92139",
            "92154",
        ),
    ),
    "Chula Vista": (
        "San Diego County",
        Decimal("1.000"),  # combined 8.750
        ("91910", "91911", "91913", "91914", "91915"),
    ),
    "Oceanside": (
        "San Diego County",
        Decimal("0.500"),  # combined 8.250
        ("92054", "92056", "92057", "92058"),
    ),
    "Escondido": (
        "San Diego County",
        Decimal("1.000"),  # combined 7.750
        ("92025", "92026", "92027", "92029"),
    ),
    # ----- Santa Clara County -----
    "San Jose": (
        "Santa Clara County",
        Decimal("0.250"),  # combined 9.375 = 7.25 + 1.875 + 0.25
        (
            "95110",
            "95111",
            "95112",
            "95113",
            "95116",
            "95117",
            "95118",
            "95119",
            "95120",
            "95121",
            "95122",
            "95123",
            "95124",
            "95125",
            "95126",
            "95127",
            "95128",
            "95129",
            "95130",
            "95131",
            "95132",
            "95133",
            "95134",
            "95135",
            "95136",
            "95138",
            "95139",
            "95148",
        ),
    ),
    "Sunnyvale": (
        "Santa Clara County",
        Decimal("0.000"),  # combined 9.125 = 7.25 + 1.875
        ("94085", "94086", "94087", "94089"),
    ),
    "Santa Clara": (
        "Santa Clara County",
        Decimal("0.000"),  # combined 9.125
        ("95050", "95051", "95054"),
    ),
    # ----- San Francisco (consolidated city + county) -----
    "San Francisco": (
        "San Francisco (City and County)",
        Decimal("0.000"),  # combined 8.625 = 7.25 + 1.375 (no separate city tax)
        (
            "94102",
            "94103",
            "94104",
            "94105",
            "94107",
            "94108",
            "94109",
            "94110",
            "94111",
            "94112",
            "94114",
            "94115",
            "94116",
            "94117",
            "94118",
            "94121",
            "94122",
            "94123",
            "94124",
            "94127",
            "94131",
            "94132",
            "94133",
            "94134",
            "94158",
        ),
    ),
    # ----- Fresno County -----
    "Fresno": (
        "Fresno County",
        Decimal("0.375"),  # combined 8.350 = 7.25 + 0.225 + 0.875
        (
            "93650",
            "93701",
            "93702",
            "93703",
            "93704",
            "93705",
            "93706",
            "93710",
            "93711",
            "93720",
            "93721",
            "93722",
            "93723",
            "93725",
            "93726",
            "93727",
            "93728",
        ),
    ),
    # ----- Sacramento County -----
    "Sacramento": (
        "Sacramento County",
        Decimal("1.000"),  # combined 8.750 = 7.25 + 0.5 + 1.0
        (
            "95811",
            "95814",
            "95815",
            "95816",
            "95817",
            "95818",
            "95819",
            "95820",
            "95821",
            "95822",
            "95823",
            "95824",
            "95825",
            "95826",
            "95827",
            "95828",
            "95829",
            "95831",
            "95832",
            "95833",
            "95834",
            "95835",
            "95838",
        ),
    ),
    "Elk Grove": (
        "Sacramento County",
        Decimal("1.000"),  # combined 8.750
        ("95624", "95757", "95758"),
    ),
    # ----- Alameda County -----
    "Oakland": (
        "Alameda County",
        Decimal("0.500"),  # combined 10.250 = 7.25 + 2.0 + 1.0
        (
            "94601",
            "94602",
            "94603",
            "94605",
            "94606",
            "94607",
            "94608",
            "94609",
            "94610",
            "94611",
            "94612",
            "94613",
            "94618",
            "94619",
            "94621",
        ),
    ),
    "Fremont": (
        "Alameda County",
        Decimal("0.000"),  # combined 10.250
        ("94536", "94538", "94539", "94555"),
    ),
    "Hayward": (
        "Alameda County",
        Decimal("0.500"),  # combined 10.750 -- one of the highest in the US
        ("94541", "94542", "94544", "94545"),
    ),
    # ----- Kern County -----
    "Bakersfield": (
        "Kern County",
        # iter-62: re-attributed -- the 1% that was here is actually the
        # county-wide Kern district tax (per CDTFA Unincorporated). The
        # combined Bakersfield rate stays 8.250%; just split differently
        # between county and city. Bakersfield itself has no city-only
        # sales tax in CDTFA Q2 2026.
        Decimal("0.000"),  # combined 8.250 = 7.25 + Kern 1.0 + 0
        (
            "93301",
            "93304",
            "93305",
            "93306",
            "93307",
            "93308",
            "93309",
            "93311",
            "93312",
            "93313",
            "93314",
        ),
    ),
    # ----- Orange County (combined 7.75% baseline = 7.25 + 0.5 OCTA) -----
    "Anaheim": (
        "Orange County",
        Decimal("0.000"),  # combined 7.750
        ("92801", "92802", "92804", "92805", "92806", "92807", "92808"),
    ),
    "Santa Ana": (
        "Orange County",
        Decimal("1.500"),  # combined 9.250 (Measure X)
        ("92701", "92703", "92704", "92705", "92706", "92707"),
    ),
    "Irvine": (
        "Orange County",
        Decimal("0.000"),  # combined 7.750
        ("92602", "92603", "92604", "92606", "92612", "92614", "92617", "92618", "92620"),
    ),
    "Huntington Beach": (
        "Orange County",
        Decimal("0.000"),  # combined 7.750
        ("92646", "92647", "92648", "92649"),
    ),
    "Garden Grove": (
        "Orange County",
        Decimal("1.000"),  # combined 8.750 (Measure O)
        ("92840", "92841", "92843", "92844", "92845"),
    ),
    "Orange": (
        "Orange County",
        Decimal("0.000"),  # combined 7.750
        ("92865", "92866", "92867", "92868", "92869"),
    ),
    "Fullerton": (
        "Orange County",
        Decimal("0.000"),  # combined 8.750 (Measure S)
        ("92831", "92832", "92833", "92835"),
    ),
    # ----- Riverside County -----
    "Riverside": (
        "Riverside County",
        Decimal("1.000"),  # combined 8.750 (Measure Z)
        ("92501", "92503", "92504", "92505", "92506", "92507", "92508", "92509"),
    ),
    "Moreno Valley": (
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92551", "92553", "92555", "92557"),
    ),
    "Corona": (
        "Riverside County",
        Decimal("1.000"),  # combined 8.750 (Measure X)
        ("92879", "92880", "92881", "92882", "92883"),
    ),
    # ----- San Joaquin County -----
    "Stockton": (
        "San Joaquin County",
        Decimal("1.250"),  # combined 9.000 (Measures A/W stacked)
        (
            "95202",
            "95203",
            "95204",
            "95205",
            "95206",
            "95207",
            "95209",
            "95210",
            "95212",
            "95215",
            "95219",
        ),
    ),
    # ----- San Bernardino County (combined 7.75% baseline) -----
    "San Bernardino": (
        "San Bernardino County",
        Decimal("1.000"),  # combined 8.750 (Measure S)
        ("92401", "92404", "92405", "92407", "92408", "92410", "92411"),
    ),
    "Fontana": (
        "San Bernardino County",
        Decimal("1.000"),  # combined 7.750
        ("92335", "92336", "92337"),
    ),
    "Rancho Cucamonga": (
        "San Bernardino County",
        Decimal("0.000"),  # combined 7.750
        ("91701", "91730", "91737", "91739"),
    ),
    "Ontario": (
        "San Bernardino County",
        Decimal("1.000"),  # combined 7.750
        ("91761", "91762", "91764"),
    ),
    # ----- Stanislaus County -----
    "Modesto": (
        "Stanislaus County",
        Decimal("1.000"),  # combined 8.875 (Measures G/L)
        ("95350", "95351", "95354", "95355", "95356", "95357", "95358"),
    ),
    # ----- Ventura County (county district 0%) -----
    "Oxnard": (
        "Ventura County",
        Decimal("2.000"),  # combined 9.250 (Measures E + O)
        ("93030", "93033", "93035", "93036"),
    ),
    "Thousand Oaks": (
        "Ventura County",
        Decimal("0.000"),  # combined 7.250 (no county or city overlay)
        ("91320", "91360", "91361", "91362"),
    ),
    "Simi Valley": (
        "Ventura County",
        Decimal("0.000"),  # combined 7.250
        ("93063", "93064", "93065"),
    ),
    # ----- Sonoma County -----
    "Santa Rosa": (
        "Sonoma County",
        Decimal("0.750"),  # combined 9.250 (Measure O)
        ("95401", "95403", "95404", "95405", "95407", "95409"),
    ),
    # ----- Monterey County -----
    "Salinas": (
        "Monterey County",
        # iter-62: re-attributed -- 1% of the 1.5% here was the Monterey
        # county-wide TAMC + transportation tax (per CDTFA Unincorporated
        # 1.500%). The remaining 0.5% is Salinas's actual Measure E /
        # Measure G city portion. Combined unchanged at 9.250%.
        Decimal("0.500"),  # combined 9.250 = 7.25 + Monterey 1.5 + Salinas 0.5
        ("93901", "93905", "93906", "93907"),
    ),
    # ----- Tulare County -----
    "Visalia": (
        "Tulare County",
        Decimal("0.250"),  # combined 8.500 (Measure N)
        ("93277", "93291", "93292"),
    ),
    # ----- Placer County -----
    "Roseville": (
        "Placer County",
        Decimal("0.500"),  # combined 7.750
        ("95661", "95678", "95747"),
    ),
    # ----- Contra Costa County -----
    "Concord": (
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750 (Measure V)
        ("94518", "94519", "94520", "94521"),
    ),
    # ----- Solano County -----
    "Vallejo": (
        "Solano County",
        Decimal("1.125"),  # combined 9.250 (Measures B + V stacked)
        ("94589", "94590", "94591", "94592"),
    ),
}


__all__ = [
    "CA_STATE_RATE_PCT",
    "CA_STATE_EFFECTIVE_FROM",
    "CA_COUNTY_RATE_PCT",
    "CA_CITIES",
]
