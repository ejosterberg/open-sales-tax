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
    "Alpine County": Decimal(
        "0.000"
    ),  # iter-162: was missing; ZIP 96120 (Markleeville) returned 0%
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
    "Mariposa County": Decimal("1.000"),  # iter-120: was missing; ZIP 95338 returned 0%
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
    "Trinity County": Decimal("0.000"),  # iter-161: was missing; ZIPs 96041 + 96093 returned 0%
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
        (
            "94801",
            "94802",
            "94803",
            "94804",
            "94805",
            "94806",
            "94807",
            "94808",
            "94850",
        ),
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
    # iter-108: high-profile LA cities
    "Santa Monica": (
        # 9.75% live vs SalesTaxHandbook 10.75% (city +1.0%)
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        (
            "90401",
            "90402",
            "90403",
            "90404",
            "90405",
            "90406",
            "90407",
            "90408",
            "90409",
            "90410",
            "90411",
        ),
    ),
    "West Hollywood": (
        # 9.75% live vs SalesTaxHandbook 10.50% (city +0.75%)
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90069", "90046"),
    ),
    # iter-110: Alhambra + Monterey Park (LA Co +0.75%)
    "Alhambra": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91801", "91802", "91803", "91804", "91896", "91899"),
    ),
    "Monterey Park": (
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91754", "91756"),
    ),
    # iter-111: San Diego Co cities (each +1.0% city tax)
    "National City": (
        "San Diego County",
        Decimal("1.000"),  # combined 8.750
        ("91950", "91951"),
    ),
    "Vista": (
        "San Diego County",
        Decimal("1.000"),  # combined 8.750 (92081/92085 have lower 0.5% rate
        # in some sub-areas not modeled at this scale)
        ("92083", "92084"),
    ),
    "San Marcos": (
        "San Diego County",
        Decimal("1.000"),  # combined 8.750
        ("92069", "92078", "92079", "92096"),
    ),
    # iter-112: Santa Clara Co cities (each +0.25% city tax)
    "Cupertino": (
        "Santa Clara County",
        Decimal("0.250"),  # combined 10.000
        ("95014",),
    ),
    "Milpitas": (
        "Santa Clara County",
        Decimal("0.250"),  # combined 10.000
        ("95035",),
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
        (
            "92602",
            "92603",
            "92604",
            "92606",
            "92612",
            "92614",
            "92617",
            "92618",
            "92620",
        ),
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
        # Fixed iter-109 stale comment: combined is 8.750, not 7.750
        # (state 7.25 + San Bernardino 0.5 + city 1.0 = 8.750).
        # Added ZIP 92376: per SalesTaxHandbook the 92376 ZIP is in
        # the "Fontana tax region" (overlap with Rialto). Rialto
        # proper has its own 92377 ZIP at 7.75%.
        "San Bernardino County",
        Decimal("1.000"),  # combined 8.750
        ("92335", "92336", "92337", "92376"),
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
    "Auburn": (
        # iter-113: 8.25% live (engine picks El Dorado Co 1.0% for
        # ZIP 95603) vs SalesTaxHandbook 7.25% (Placer Co 0.25%
        # + 1% special baked into CA state base, no city tax).
        # Auburn is the seat of Placer Co; cross-county ZCTA
        # misattribution. City anchor forces correct county pick.
        # state 7.25 + Placer 0.0 + city 0.0 = 7.250.
        "Placer County",
        Decimal("0.000"),  # combined 7.250
        ("95603",),
    ),
    "Loomis": (
        # iter-113: 7.25% live (Placer Co 0%, no city) vs
        # SalesTaxHandbook 7.5% (state 6 + Placer 0.25 + Loomis
        # 0.25 + special 1.0 = 7.5%). Loomis levies its own
        # 0.25% city tax on top of Placer base.
        # state 7.25 + Placer 0.0 + city 0.25 = 7.500.
        "Placer County",
        Decimal("0.250"),  # combined 7.500
        ("95650",),
    ),
    # ----- Yolo County -----
    "Davis": (
        # iter-113: 8.125% live (engine binds 95616 to Solano Co
        # 0.875%) vs SalesTaxHandbook 9.25% (Yolo Co + Davis 2.0%
        # city). Davis is in Yolo Co; cross-county ZCTA bug.
        # Engine's Yolo Co rate is 0.75%, so closing the 1.125%
        # gap to 9.25% needs Davis city = 1.25%.
        # state 7.25 + Yolo 0.75 + city 1.25 = 9.250.
        "Yolo County",
        Decimal("1.250"),  # combined 9.250
        ("95616", "95618"),
    ),
    # ----- San Luis Obispo County -----
    "San Luis Obispo": (
        # iter-113: 8.25% live (SLO Co 1.0%) vs SalesTaxHandbook
        # 8.75% (state 6 + SLO Co 0.25 + city 1.5 + special 1.0).
        # Engine's SLO Co 1.0% already absorbs part of city tax;
        # gap to 8.75% closes with city 0.5%.
        # state 7.25 + SLO 1.0 + city 0.5 = 8.750.
        "San Luis Obispo County",
        Decimal("0.500"),  # combined 8.750
        ("93401", "93405", "93406", "93408", "93410"),
    ),
    "Atascadero": (
        # iter-113: same +0.5% city pattern as SLO city; gap to
        # SalesTaxHandbook 8.75%.
        # state 7.25 + SLO 1.0 + city 0.5 = 8.750.
        "San Luis Obispo County",
        Decimal("0.500"),  # combined 8.750
        ("93422",),
    ),
    "Paso Robles": (
        # iter-113: gap to SalesTaxHandbook 8.75%.
        # state 7.25 + SLO 1.0 + city 0.5 = 8.750.
        "San Luis Obispo County",
        Decimal("0.500"),  # combined 8.750
        ("93446", "93447"),
    ),
    "Arroyo Grande": (
        # iter-113: gap to SalesTaxHandbook 8.75%.
        # state 7.25 + SLO 1.0 + city 0.5 = 8.750.
        "San Luis Obispo County",
        Decimal("0.500"),  # combined 8.750
        ("93420", "93421"),
    ),
    "Morro Bay": (
        # iter-113: gap to SalesTaxHandbook 8.75%.
        # state 7.25 + SLO 1.0 + city 0.5 = 8.750.
        "San Luis Obispo County",
        Decimal("0.500"),  # combined 8.750
        ("93442", "93443"),
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
    # ----- Sonoma County -----
    # iter-114: Sonoma Co rate in our model is 2.0% (combined baseline
    # 9.25%). Cities below add their own city portion. Petaluma was
    # binding to Marin Co (1.0%) via Census ZCTA misattribution -- the
    # city anchor forces the correct Sonoma Co bind. Sonoma the city
    # was binding to Napa Co for the same reason; same fix.
    "Petaluma": (
        # state 7.25 + Sonoma 2.0 + city 1.0 = 10.250.
        "Sonoma County",
        Decimal("1.000"),  # combined 10.250
        ("94952", "94954", "94975"),
    ),
    "Sonoma": (
        # state 7.25 + Sonoma 2.0 + city 1.0 = 10.250.
        "Sonoma County",
        Decimal("1.000"),  # combined 10.250
        ("95476",),
    ),
    "Sebastopol": (
        # SalesTaxHandbook 10.5%; state 6 + Sonoma 0.25 + city 1.25 + special 3.
        # In our model: state 7.25 + Sonoma 2.0 + city 1.25 = 10.500.
        "Sonoma County",
        Decimal("1.250"),  # combined 10.500
        ("95472",),
    ),
    "Healdsburg": (
        # state 7.25 + Sonoma 2.0 + city 0.5 = 9.750.
        "Sonoma County",
        Decimal("0.500"),  # combined 9.750
        ("95448",),
    ),
    "Rohnert Park": (
        # state 7.25 + Sonoma 2.0 + city 0.5 = 9.750.
        # NOTE: 94928 has alt 10.25% in Cotati tax region per
        # SalesTaxHandbook; we use the Rohnert Park city rate here.
        "Sonoma County",
        Decimal("0.500"),  # combined 9.750
        ("94928",),
    ),
    "Cotati": (
        # state 7.25 + Sonoma 2.0 + city 1.0 = 10.250.
        "Sonoma County",
        Decimal("1.000"),  # combined 10.250
        ("94931",),
    ),
    # ----- Napa County -----
    # iter-114: Napa Co rate 0.5% in our model. Cities add their city
    # portion; American Canyon + Calistoga's "extra" tax above the
    # baseline rolls into the city portion in our model (SalesTaxHandbook
    # splits it as Special Tax 3% vs Special Tax 1.5%, but the consumer-
    # facing combined rate is what matters for the API).
    "Napa": (
        # state 7.25 + Napa 0.5 + city 1.0 = 8.750.
        "Napa County",
        Decimal("1.000"),  # combined 8.750
        ("94558", "94559", "94581"),
    ),
    "American Canyon": (
        # state 7.25 + Napa 0.5 + city 1.5 = 9.250.
        "Napa County",
        Decimal("1.500"),  # combined 9.250
        ("94503",),
    ),
    "Calistoga": (
        # state 7.25 + Napa 0.5 + city 1.5 = 9.250.
        # In SalesTaxHandbook this 1.5% is "Special Tax 3%" minus the
        # baseline 1.5% already in CA's statewide 7.25; we model it as
        # a city overlay for arithmetic simplicity.
        "Napa County",
        Decimal("1.500"),  # combined 9.250
        ("94515",),
    ),
    # ----- Riverside County (iter-115) -----
    # Riverside Co rate is 0.5% in our model (state+co = 7.75%). All
    # 11 cities below were probing 7.75% before this iter -- a single
    # systemic under-collect pattern. SalesTaxHandbook lists each
    # with a 1.0% (or 1.5%) city tax on top, plus a 1.5% Special Tax
    # district that's already baked into CA's 7.25% state baseline
    # in our model. City portion below closes each gap exactly.
    "Hemet": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92543", "92544", "92545", "92546"),
    ),
    "Temecula": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92590", "92591", "92592", "92593"),
    ),
    "Murrieta": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92562", "92563", "92564"),
    ),
    "Lake Elsinore": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92530", "92531", "92532"),
    ),
    "Menifee": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92584", "92586", "92587"),
    ),
    "Indio": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92201", "92202", "92203"),
    ),
    "Coachella": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92236",),
    ),
    "Palm Desert": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92255", "92260", "92261"),
    ),
    "La Quinta": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92247", "92248", "92253"),
    ),
    "Cathedral City": (
        # state 7.25 + Riverside 0.5 + city 1.5 = 9.250.
        "Riverside County",
        Decimal("1.500"),  # combined 9.250
        ("92234", "92235"),
    ),
    "Palm Springs": (
        # state 7.25 + Riverside 0.5 + city 1.5 = 9.250.
        "Riverside County",
        Decimal("1.500"),  # combined 9.250
        ("92262", "92263", "92264"),
    ),
    # ----- Tulare County (iter-115) -----
    # Tulare Co rate is 1.0% in our model. Porterville layers a
    # 1.0% city tax (most other Tulare Co cities ride the bare
    # county rate at 8.25%).
    "Porterville": (
        # state 7.25 + Tulare 1.0 + city 1.0 = 9.250.
        "Tulare County",
        Decimal("1.000"),  # combined 9.250
        ("93257", "93258"),
    ),
    # ----- More San Diego County (iter-116) -----
    # SD Co rate 0.5% in our model. These 6 add city portions on top.
    # Carlsbad / Encinitas / Santee / Coronado / Poway / Chula Vista
    # were probed and confirmed correct at 7.75% bare-county.
    "El Cajon": (
        # state 7.25 + SD 0.5 + city 0.5 = 8.250.
        "San Diego County",
        Decimal("0.500"),  # combined 8.250
        ("92019", "92020", "92021", "92022"),
    ),
    "La Mesa": (
        # state 7.25 + SD 0.5 + city 0.75 = 8.500.
        "San Diego County",
        Decimal("0.750"),  # combined 8.500
        ("91941", "91942", "91943", "91944"),
    ),
    "Imperial Beach": (
        # state 7.25 + SD 0.5 + city 1.0 = 8.750.
        "San Diego County",
        Decimal("1.000"),  # combined 8.750
        ("91932", "91933"),
    ),
    "Lemon Grove": (
        # state 7.25 + SD 0.5 + city 1.0 = 8.750.
        "San Diego County",
        Decimal("1.000"),  # combined 8.750
        ("91945", "91946"),
    ),
    "Del Mar": (
        # state 7.25 + SD 0.5 + city 1.0 = 8.750.
        "San Diego County",
        Decimal("1.000"),  # combined 8.750
        ("92014",),
    ),
    "Solana Beach": (
        # state 7.25 + SD 0.5 + city 1.0 = 8.750.
        "San Diego County",
        Decimal("1.000"),  # combined 8.750
        ("92075",),
    ),
    # ----- More Orange County (iter-116) -----
    # OC Co rate 0.5% in our model. Most OC suburbs are state+co only;
    # Westminster levies a 1.5% city tax (raised from 1.0% in 2024).
    "Westminster": (
        # state 7.25 + OC 0.5 + city 1.5 = 9.250.
        "Orange County",
        Decimal("1.500"),  # combined 9.250
        ("92683", "92684", "92685"),
    ),
    # ----- More Sacramento County (iter-118) -----
    # Sac Co rate 0.5% in our model. Citrus Heights / Galt are
    # incorporated cities in the county; Rancho Cordova has its own
    # TBID layer. Folsom (iter-103) already added.
    "Rancho Cordova": (
        # state 7.25 + Sac 0.5 + city 1.0 = 8.750.
        "Sacramento County",
        Decimal("1.000"),  # combined 8.750
        ("95670", "95741", "95742"),
    ),
    "Galt": (
        # state 7.25 + Sac 0.5 + city 1.5 = 9.250.
        "Sacramento County",
        Decimal("1.500"),  # combined 9.250
        ("95632",),
    ),
    # ----- More San Bernardino County (iter-118) -----
    # SBd Co rate 0.5% in our model. Highland adds 1.0% city tax.
    "Highland": (
        # state 7.25 + SBd 0.5 + city 1.0 = 8.750.
        "San Bernardino County",
        Decimal("1.000"),  # combined 8.750
        ("92346",),
    ),
    # ----- More Riverside County (iter-118) -----
    # Norco + Calimesa each add 1.0% city tax to the Riverside base.
    "Norco": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92860",),
    ),
    "Calimesa": (
        # state 7.25 + Riverside 0.5 + city 1.0 = 8.750.
        "Riverside County",
        Decimal("1.000"),  # combined 8.750
        ("92320",),
    ),
    # ----- San Joaquin County (iter-119) -----
    # SJ Co rate 0.5% in our model (state+co = 7.75%). Each city
    # adds its own portion. Vallejo (Solano) and Stockton (SJ) had
    # been the only SJ-area cities in the seed.
    "Tracy": (
        # state 7.25 + SJ 0.5 + city 0.5 = 8.250.
        "San Joaquin County",
        Decimal("0.500"),  # combined 8.250
        ("95376", "95377", "95378", "95391"),
    ),
    "Manteca": (
        # state 7.25 + SJ 0.5 + city 1.25 = 9.000.
        "San Joaquin County",
        Decimal("1.250"),  # combined 9.000
        ("95336", "95337"),
    ),
    "Lodi": (
        # state 7.25 + SJ 0.5 + city 1.25 = 9.000.
        # NOTE: 95240/95241 alt 8.25% in some areas with city 0.5%.
        "San Joaquin County",
        Decimal("1.250"),  # combined 9.000
        ("95240", "95242"),
    ),
    # ----- Merced County (iter-119) -----
    # Merced Co engine rate 1.0% (state+co = 8.25%). Atwater and Los
    # Banos each layer 0.5% city tax.
    "Atwater": (
        # state 7.25 + Merced 1.0 + city 0.5 = 8.750.
        "Merced County",
        Decimal("0.500"),  # combined 8.750
        ("95301",),
    ),
    "Los Banos": (
        # state 7.25 + Merced 1.0 + city 0.5 = 8.750.
        "Merced County",
        Decimal("0.500"),  # combined 8.750
        ("93635",),
    ),
    # ----- Fresno County (iter-119) -----
    # Fresno Co engine rate 0.725% (state+co = 7.975%). Each Fresno-Co
    # city below adds its own portion.
    "Clovis": (
        # state 7.25 + Fresno 0.725 + city 1.0 = 8.975.
        "Fresno County",
        Decimal("1.000"),  # combined 8.975
        ("93611", "93612", "93613", "93619"),
    ),
    "Sanger": (
        # state 7.25 + Fresno 0.725 + city 0.75 = 8.725.
        "Fresno County",
        Decimal("0.750"),  # combined 8.725
        ("93657",),
    ),
    "Selma": (
        # state 7.25 + Fresno 0.725 + city 1.0 = 8.975.
        "Fresno County",
        Decimal("1.000"),  # combined 8.975
        ("93662",),
    ),
    "Reedley": (
        # state 7.25 + Fresno 0.725 + city 1.25 = 9.225.
        "Fresno County",
        Decimal("1.250"),  # combined 9.225
        ("93654",),
    ),
    "Kingsburg": (
        # state 7.25 + Fresno 0.725 + city 1.0 = 8.975.
        "Fresno County",
        Decimal("1.000"),  # combined 8.975
        ("93631",),
    ),
    # ----- Tulare County (iter-119) -----
    # Dinuba 93618 was binding to Fresno Co (0.725%) via Census
    # ZCTA misattribution -- Dinuba is in Tulare Co. Same pattern
    # as Auburn/Davis/Petaluma/Sonoma. City anchor + 0.25 city =
    # state 7.25 + Tulare 1.0 + 0.25 = 8.5 (matches SalesTaxHandbook).
    "Dinuba": (
        "Tulare County",
        Decimal("0.250"),  # combined 8.500
        ("93618",),
    ),
    # ----- Mariposa County (iter-120) -----
    # ZIP 95338 was returning 0% jurisdictions because Mariposa Co
    # was absent from CA_COUNTY_RATE_PCT (now added at 1.0%).
    # Mariposa town has no city tax of its own (state 7.25 +
    # Mariposa 1.0 + 0 = 8.25, matches SalesTaxHandbook).
    "Mariposa": (
        "Mariposa County",
        Decimal("0.000"),  # combined 8.250
        ("95338", "95345"),
    ),
    # ----- Stanislaus County (iter-120) -----
    # Stanislaus Co engine rate 0.625% (state+co = 7.875%). Modesto
    # already added; Turlock + Ceres need their own entries.
    # Turlock 95380 was binding to Merced Co (1.0%) via Census ZCTA
    # misattribution -- 7th cross-county case this session. City
    # anchor + 0.75% city = 7.25 + Stanislaus 0.625 + 0.75 = 8.625
    # (matches SalesTaxHandbook).
    "Turlock": (
        "Stanislaus County",
        Decimal("0.750"),  # combined 8.625
        ("95380", "95381", "95382"),
    ),
    "Ceres": (
        # state 7.25 + Stanislaus 0.625 + city 1.0 = 8.875.
        "Stanislaus County",
        Decimal("1.000"),  # combined 8.875
        ("95307",),
    ),
    # ----- Humboldt County (iter-120) -----
    # Humboldt Co engine rate 2.25% (state+co = 9.50%). Eureka and
    # Arcata each layer 0.75% city tax (raised April 2025).
    "Eureka": (
        # state 7.25 + Humboldt 2.25 + city 0.75 = 10.250.
        "Humboldt County",
        Decimal("0.750"),  # combined 10.250
        ("95501", "95502", "95503"),
    ),
    "Arcata": (
        # state 7.25 + Humboldt 2.25 + city 0.75 = 10.250.
        "Humboldt County",
        Decimal("0.750"),  # combined 10.250
        ("95521",),
    ),
    # ----- Butte County (iter-120) -----
    # Butte Co engine rate 1.0% (state+co = 8.25%). Chico/Oroville/
    # Paradise each layer their own city tax.
    "Chico": (
        # state 7.25 + Butte 1.0 + city 1.0 = 9.250.
        "Butte County",
        Decimal("1.000"),  # combined 9.250
        ("95926", "95927", "95928", "95929", "95973", "95976"),
    ),
    "Oroville": (
        # state 7.25 + Butte 1.0 + city 1.0 = 9.250.
        "Butte County",
        Decimal("1.000"),  # combined 9.250
        ("95965", "95966"),
    ),
    "Paradise": (
        # state 7.25 + Butte 1.0 + city 0.5 = 8.750.
        "Butte County",
        Decimal("0.500"),  # combined 8.750
        ("95967", "95969"),
    ),
    # ----- Mendocino County (iter-120) -----
    # Mendocino Co engine rate 1.625% (state+co = 8.875%). Ukiah
    # already correct at 8.875%; Fort Bragg adds 0.375% city.
    "Fort Bragg": (
        # state 7.25 + Mendocino 1.625 + city 0.375 = 9.250.
        "Mendocino County",
        Decimal("0.375"),  # combined 9.250
        ("95437",),
    ),
    # ----- Nevada County (iter-121) -----
    # Nevada Co engine rate 1.625% (state+co = 8.875%). Truckee's
    # Tourism Business Improvement District adds 0.125% above the
    # baseline (Truckee city 1.5% has 1.375% already absorbed in
    # Nevada Co rate which incorporates Grass Valley's 1.375% city).
    "Truckee": (
        # state 7.25 + Nevada 1.625 + city 0.125 = 9.000.
        "Nevada County",
        Decimal("0.125"),  # combined 9.000
        ("96160", "96161", "96162"),
    ),
    # ----- San Benito County (iter-121) -----
    # San Benito Co engine rate 1.75% (state+co = 9.000%). Hollister
    # is the county seat; adds 0.25% city.
    "Hollister": (
        # state 7.25 + SB 1.75 + city 0.25 = 9.250.
        "San Benito County",
        Decimal("0.250"),  # combined 9.250
        ("95023", "95024"),
    ),
    # ----- Santa Cruz County (iter-121) -----
    # Santa Cruz Co engine rate 2.25% (state+co = 9.500%). Watsonville
    # binds to Monterey Co via Census ZCTA misattribution -- 8th
    # cross-county case this session. City anchor + 0.25 city.
    # Scotts Valley is a same-county city-tax overlay.
    "Watsonville": (
        # state 7.25 + Santa Cruz 2.25 + city 0.25 = 9.750.
        "Santa Cruz County",
        Decimal("0.250"),  # combined 9.750
        ("95076", "95077"),
    ),
    "Scotts Valley": (
        # state 7.25 + Santa Cruz 2.25 + city 0.25 = 9.750.
        "Santa Cruz County",
        Decimal("0.250"),  # combined 9.750
        ("95066", "95067"),
    ),
    # ----- More Monterey County (iter-121) -----
    # Monterey Co engine rate 1.5% (state+co = 8.750%). Marina/Seaside/
    # Pacific Grove each layer 0.5% city tax.
    "Marina": (
        # state 7.25 + Monterey 1.5 + city 0.5 = 9.250.
        "Monterey County",
        Decimal("0.500"),  # combined 9.250
        ("93933",),
    ),
    "Seaside": (
        # state 7.25 + Monterey 1.5 + city 0.5 = 9.250.
        "Monterey County",
        Decimal("0.500"),  # combined 9.250
        ("93955",),
    ),
    "Pacific Grove": (
        # state 7.25 + Monterey 1.5 + city 0.5 = 9.250.
        "Monterey County",
        Decimal("0.500"),  # combined 9.250
        ("93950",),
    ),
    # ----- Santa Barbara County (iter-121) -----
    # Santa Barbara Co engine rate 0.5% (state+co = 7.750%). Santa
    # Maria layers 0.5% city tax (SalesTaxHandbook shows city 1.0
    # but 0.5 reaches 8.75% combined which matches).
    "Santa Maria": (
        # state 7.25 + SB Co 0.5 + city 0.5 = 8.250 (live engine).
        # Wait -- engine returned 8.25 pre-iter-121 but SalesTaxHandbook
        # says 8.75. To reach 8.75 from 7.75 baseline (engine SB Co at
        # 0.5%) we need city 1.0. State 7.25 + 0.5 + 1.0 = 8.75.
        "Santa Barbara County",
        Decimal("1.000"),  # combined 8.750
        ("93454", "93455", "93456", "93458"),
    ),
    # ----- More Solano County (iter-122) -----
    # Solano Co engine rate 0.875% (state+co = 8.125%). Each city
    # below adds its own portion. Rio Vista was binding to Sacramento
    # Co via Census ZCTA misattribution -- 9th cross-county case
    # this session.
    "Fairfield": (
        # state 7.25 + Solano 0.875 + city 1.0 = 9.125.
        "Solano County",
        Decimal("1.000"),  # combined 9.125
        ("94533", "94534", "94535"),
    ),
    "Benicia": (
        # state 7.25 + Solano 0.875 + city 1.5 = 9.625.
        "Solano County",
        Decimal("1.500"),  # combined 9.625
        ("94510",),
    ),
    "Suisun City": (
        # state 7.25 + Solano 0.875 + city 1.0 = 9.125.
        "Solano County",
        Decimal("1.000"),  # combined 9.125
        ("94585",),
    ),
    "Dixon": (
        # state 7.25 + Solano 0.875 + city 0.25 = 8.375.
        "Solano County",
        Decimal("0.250"),  # combined 8.375
        ("95620",),
    ),
    "Rio Vista": (
        # state 7.25 + Solano 0.875 + city 1.0 = 9.125. Census ZCTA
        # had bound 94571 to Sacramento Co; city anchor fixes the
        # county pick (9th cross-county case this session).
        "Solano County",
        Decimal("1.000"),  # combined 9.125
        ("94571",),
    ),
    # ----- More Yolo County (iter-122) -----
    # Yolo Co engine rate 0.75% (state+co = 8.000%). West Sacramento
    # adds 1.25 city; Winters 0.25.
    "West Sacramento": (
        # state 7.25 + Yolo 0.75 + city 1.25 = 9.250.
        "Yolo County",
        Decimal("1.250"),  # combined 9.250
        (
            "95605",
            "95691",
        ),
    ),
    "Winters": (
        # state 7.25 + Yolo 0.75 + city 0.25 = 8.250.
        "Yolo County",
        Decimal("0.250"),  # combined 8.250
        ("95694",),
    ),
    # ----- More Contra Costa County (iter-123) -----
    # Contra Costa Co engine rate 1.5% (state+co = 8.75%). Each city
    # below adds its own portion. Concord/Walnut Creek/Antioch/
    # Pittsburg/Richmond/San Ramon already in earlier iters.
    # NOT modeled: San Pablo 94806 -- shares the ZIP with Richmond
    # which already takes the bind; engine picks Richmond's 1.0%
    # city tax instead of San Pablo's 1.5% -> 0.5% under-collection
    # for that ZIP. Mixed-rate-per-ZIP follow-up needed.
    "Brentwood": (
        # state 7.25 + CC 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94513",),
    ),
    "Martinez": (
        # state 7.25 + CC 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94553",),
    ),
    "Pleasant Hill": (
        # state 7.25 + CC 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94523",),
    ),
    "Lafayette": (
        # state 7.25 + CC 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94549",),
    ),
    "Moraga": (
        # state 7.25 + CC 1.5 + city 1.0 = 9.750.
        "Contra Costa County",
        Decimal("1.000"),  # combined 9.750
        ("94556",),
    ),
    "Hercules": (
        # state 7.25 + CC 1.5 + city 1.5 = 10.250.
        "Contra Costa County",
        Decimal("1.500"),  # combined 10.250
        ("94547",),
    ),
    "Pinole": (
        # state 7.25 + CC 1.5 + city 1.5 = 10.250.
        "Contra Costa County",
        Decimal("1.500"),  # combined 10.250
        ("94564",),
    ),
    "Orinda": (
        # state 7.25 + CC 1.5 + city 2.0 = 10.750.
        # SalesTaxHandbook breaks this as city 0.5 + special 4.0 but
        # CA's 7.25 baseline + CC 1.5 already absorbs most of the
        # special; engine city 2.0 reaches the same combined rate.
        "Contra Costa County",
        Decimal("2.000"),  # combined 10.750
        ("94563",),
    ),
    # ----- More Los Angeles County (iter-124) -----
    # LA Co engine rate 2.5% (state+co = 9.75%). The 13 cities below
    # each layer their own city portion. West Covina/Rosemead were
    # probed and confirmed correct at 9.75% (no city tax).
    "Beverly Hills": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90209", "90210", "90211", "90212"),
    ),
    "Downey": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90239", "90240", "90241", "90242"),
    ),
    "Norwalk": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90650", "90651", "90652"),
    ),
    "Bellflower": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90706", "90707"),
    ),
    "Carson": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90745", "90746", "90747", "90749"),
    ),
    "Inglewood": (
        # state 7.25 + LA 2.5 + city 0.5 = 10.250.
        "Los Angeles County",
        Decimal("0.500"),  # combined 10.250
        ("90301", "90302", "90305", "90306", "90307", "90308", "90309", "90310"),
    ),
    "Compton": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90220", "90222", "90223", "90224"),
    ),
    "Lynwood": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90262",),
    ),
    "Paramount": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90723",),
    ),
    "South Gate": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90280",),
    ),
    "Pico Rivera": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90660", "90661", "90662"),
    ),
    "Montebello": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90640",),
    ),
    "El Monte": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91731", "91732", "91733", "91734", "91735"),
    ),
    # ----- More Los Angeles County (iter-125) -----
    # San Gabriel Valley + east-LA-Co suburbs. All 12 below were
    # returning bare 9.75% pre-fix. Walnut + La Mirada were also
    # probed and confirmed correct at 9.75% (no city tax).
    "Arcadia": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91006", "91007", "91066", "91077"),
    ),
    "Baldwin Park": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("91706",),
    ),
    "Covina": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91722", "91723", "91724"),
    ),
    "Glendora": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("91740", "91741", "91740"),
    ),
    "San Gabriel": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91775", "91776", "91778"),
    ),
    "Temple City": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91780",),
    ),
    "Monrovia": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91016", "91017"),
    ),
    "Azusa": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750. Raised Apr 2025.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("91702",),
    ),
    "Duarte": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91010",),
    ),
    "San Dimas": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91773",),
    ),
    "Diamond Bar": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91765",),
    ),
    "Claremont": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91711",),
    ),
    # ----- More Los Angeles County (iter-126) -----
    # Beach Cities + west / southeast LA Co. The 90201-cluster cities
    # (Bell / Bell Gardens / Cudahy) all share ZIP 90201 -- the
    # picker would pick one ambiguously, so they're not modeled here
    # as a known mixed-rate-per-ZIP follow-up.
    "Manhattan Beach": (
        # state 7.25 + LA 2.5 + city 0.5 = 10.250.
        "Los Angeles County",
        Decimal("0.500"),  # combined 10.250
        ("90266", "90267"),
    ),
    "Hermosa Beach": (
        # state 7.25 + LA 2.5 + city 0.5 = 10.250.
        "Los Angeles County",
        Decimal("0.500"),  # combined 10.250
        ("90254",),
    ),
    "Redondo Beach": (
        # state 7.25 + LA 2.5 + city 0.5 = 10.250.
        "Los Angeles County",
        Decimal("0.500"),  # combined 10.250
        ("90277", "90278"),
    ),
    "Malibu": (
        # state 7.25 + LA 2.5 + city 0.5 = 10.250.
        "Los Angeles County",
        Decimal("0.500"),  # combined 10.250
        ("90265",),
    ),
    "La Verne": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91750",),
    ),
    "Sierra Madre": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91024", "91025"),
    ),
    "La Canada Flintridge": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("91011", "91012"),
    ),
    "Huntington Park": (
        # state 7.25 + LA 2.5 + city 1.0 = 10.750.
        "Los Angeles County",
        Decimal("1.000"),  # combined 10.750
        ("90255",),
    ),
    "Maywood": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90270",),
    ),
    "Signal Hill": (
        # state 7.25 + LA 2.5 + city 0.75 = 10.500.
        "Los Angeles County",
        Decimal("0.750"),  # combined 10.500
        ("90755",),
    ),
    # ----- Imperial County (iter-147) -----
    # Imperial Co engine rate 0.5% (state+co = 7.75%). El Centro and
    # Calexico add 0.5 city; Brawley adds 1.0.
    "El Centro": (
        # state 7.25 + Imperial 0.5 + city 0.5 = 8.250.
        "Imperial County",
        Decimal("0.500"),  # combined 8.250
        ("92243", "92244"),
    ),
    "Calexico": (
        # state 7.25 + Imperial 0.5 + city 0.5 = 8.250.
        "Imperial County",
        Decimal("0.500"),  # combined 8.250
        ("92231", "92232"),
    ),
    "Brawley": (
        # state 7.25 + Imperial 0.5 + city 1.0 = 8.750.
        "Imperial County",
        Decimal("1.000"),  # combined 8.750
        ("92227",),
    ),
    # ----- More Kern County (iter-147) -----
    # Kern Co engine rate 1.0% (state+co = 8.25%). Bakersfield/Delano
    # baked into Kern Co rate. Ridgecrest layers 1.0% city tax.
    "Ridgecrest": (
        # state 7.25 + Kern 1.0 + city 1.0 = 9.250.
        "Kern County",
        Decimal("1.000"),  # combined 9.250
        ("93555", "93556"),
    ),
    # ----- Trinity County (iter-161) -----
    # Trinity Co was missing from CA_COUNTY_RATE_PCT, so ZIPs 96041
    # (Hayfork) and 96093 (Weaverville) returned 0% jurisdictions.
    # Same bug pattern as CA Mariposa 95338 (iter-120). Adding
    # Trinity Co at 0.0% + Weaverville + Hayfork city anchors.
    "Weaverville": (
        "Trinity County",
        Decimal("0.000"),  # combined 7.250
        ("96093",),
    ),
    "Hayfork": (
        "Trinity County",
        Decimal("0.000"),  # combined 7.250
        ("96041",),
    ),
    # ----- Alpine County (iter-162) -----
    # Alpine Co (the smallest CA county by population) was missing
    # from CA_COUNTY_RATE_PCT. 5th missing-binding bug this session.
    "Markleeville": (
        "Alpine County",
        Decimal("0.000"),  # combined 7.250
        ("96120",),
    ),
}


__all__ = [
    "CA_STATE_RATE_PCT",
    "CA_STATE_EFFECTIVE_FROM",
    "CA_COUNTY_RATE_PCT",
    "CA_CITIES",
]
