# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Arizona TPT (Transaction Privilege Tax) rate + boundary data.

Source: AZ DOR's monthly "All Business Classifications Tax Rate Table"
CSV, business code 017 RETAIL. URL pattern:

  https://azdor.gov/sites/default/files/document/
    TPT_RATETABLE_ALL_<MMDDYYYY>.csv

May 2026 file (effective 2026-05-01) used to seed the data below.
County rates published in the CSV INCLUDE the 5.6% state portion;
the per-county portion is derived as ``combined - 5.6``.

This module ships an MVP coverage scope:

- All 15 AZ counties with their per-county TPT portion
- 48 AZ cities with per-city rates and their primary ZIPs (top-20 by
  population plus the next ~28 from the same DOR CSV; verified
  2026-05-04 against TPT_RATETABLE_ALL_05012026.csv)

ZIPs not in the city list fall back to state + county (or state-only
where the county isn't covered by an explicit city). A future ratchet
should expand city coverage and ingest the CSV directly so monthly DOR
updates auto-flow.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective since the last AZ TPT base-rate change (2013-06-01).
AZ_STATE_RATE_PCT = Decimal("5.600")
AZ_STATE_EFFECTIVE_FROM = dt.date(2013, 6, 1)

# Per-county TPT portion (NOT including the 5.6% state rate).
# Source: AZ DOR May 2026 CSV, business code 017, county-level rows.
AZ_COUNTY_RATE_PCT: dict[str, Decimal] = {
    "Apache County": Decimal("0.500"),
    "Cochise County": Decimal("0.500"),
    "Coconino County": Decimal("1.300"),
    "Gila County": Decimal("1.000"),
    "Graham County": Decimal("1.000"),
    "Greenlee County": Decimal("0.500"),
    "La Paz County": Decimal("1.000"),
    "Maricopa County": Decimal("0.700"),
    "Mohave County": Decimal("0.000"),
    "Navajo County": Decimal("0.830"),
    "Pima County": Decimal("0.500"),
    "Pinal County": Decimal("1.100"),
    "Santa Cruz County": Decimal("1.000"),
    "Yavapai County": Decimal("0.750"),
    "Yuma County": Decimal("1.112"),
}

# Per-city RETAIL rate (city portion only). Source: AZ DOR May 2026 CSV.
# Each tuple: (county_name, city_rate_pct, [zip5s])
# ZIPs are the primary delivery ZIPs for each city; not exhaustive but
# covers the population centroids that consumers most often query.
AZ_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    "Phoenix": (
        "Maricopa County",
        Decimal("2.800"),
        # Phoenix proper (excluding Glendale/Tempe/Mesa/Scottsdale interior ZIPs)
        (
            "85003",
            "85004",
            "85006",
            "85007",
            "85008",
            "85009",
            "85012",
            "85013",
            "85014",
            "85015",
            "85016",
            "85017",
            "85018",
            "85019",
            "85020",
            "85021",
            "85022",
            "85023",
            "85024",
            "85027",
            "85028",
            "85029",
            "85031",
            "85032",
            "85033",
            "85034",
            "85035",
            "85037",
            "85040",
            "85041",
            "85042",
            "85043",
            "85044",
            "85045",
            "85048",
            "85050",
            "85051",
            "85053",
            "85054",
            "85083",
            "85085",
            "85086",
            "85087",
            # iter-192: Laveen (USPS place name) is inside Phoenix
            # city limits; was returning state-only 6.30% pre-fix.
            "85339",
        ),
    ),
    "Tucson": (
        "Pima County",
        Decimal("2.600"),
        # iter-191: removed 85737 (Oro Valley primary) and 85742
        # (Marana primary) -- both are separate Pima Co cities with
        # their own city tax rates; binding them to Tucson was a
        # mis-attribution. They now bind to Oro Valley / Marana
        # below.
        (
            "85701",
            "85705",
            "85706",
            "85710",
            "85711",
            "85712",
            "85713",
            "85714",
            "85715",
            "85716",
            "85718",
            "85719",
            "85730",
            "85735",
            "85741",
            "85745",
            "85746",
            "85747",
            "85748",
            "85749",
            "85750",
            "85756",
            "85757",
        ),
    ),
    "Mesa": (
        "Maricopa County",
        Decimal("2.000"),
        (
            "85201",
            "85202",
            "85203",
            "85204",
            "85205",
            "85206",
            "85207",
            "85208",
            "85209",
            "85210",
            "85212",
            "85213",
            "85215",
        ),
    ),
    "Chandler": (
        "Maricopa County",
        Decimal("1.500"),
        ("85224", "85225", "85226", "85248", "85249", "85286"),
    ),
    "Scottsdale": (
        "Maricopa County",
        Decimal("1.700"),
        ("85250", "85251", "85254", "85255", "85257", "85258", "85259", "85260", "85262", "85266"),
    ),
    "Glendale": (
        "Maricopa County",
        Decimal("2.900"),
        ("85301", "85302", "85303", "85304", "85305", "85306", "85307", "85308", "85310"),
    ),
    "Gilbert": (
        "Maricopa County",
        Decimal("2.000"),
        ("85233", "85234", "85295", "85296", "85297", "85298"),
    ),
    "Tempe": (
        "Maricopa County",
        Decimal("1.800"),
        ("85281", "85282", "85283", "85284"),
    ),
    "Peoria": (
        "Maricopa County",
        Decimal("1.800"),
        ("85345", "85381", "85382", "85383", "85385"),
    ),
    "Surprise": (
        "Maricopa County",
        Decimal("2.800"),
        ("85374", "85378", "85379", "85387", "85388"),
    ),
    "Avondale": (
        "Maricopa County",
        Decimal("2.500"),
        ("85323", "85392"),
    ),
    "Goodyear": (
        "Maricopa County",
        Decimal("2.500"),
        ("85338", "85395"),
    ),
    "Buckeye": (
        "Maricopa County",
        Decimal("3.000"),
        ("85326", "85396"),
    ),
    "Yuma": (
        "Yuma County",
        Decimal("1.700"),
        ("85364", "85365", "85367"),
    ),
    "Flagstaff": (
        "Coconino County",
        Decimal("2.486"),
        ("86001", "86004", "86005"),
    ),
    "Casa Grande": (
        "Pinal County",
        Decimal("2.000"),
        ("85122", "85194"),
    ),
    "Lake Havasu City": (
        "Mohave County",
        Decimal("2.000"),
        ("86403", "86404", "86406"),
    ),
    "Marana": (
        "Pima County",
        # iter-191: expanded ZIPs (added 85742, 85743) -- both were
        # previously mis-bound to Tucson / no-city respectively.
        Decimal("2.500"),
        ("85653", "85658", "85742", "85743"),
    ),
    "Oro Valley": (
        # iter-191 added: Oro Valley is a separate Pima Co town with
        # 2.5% city tax. ZIPs 85737/85755 were mis-bound to Tucson
        # (85737) or no-city (85755) pre-fix. Combined post-fix:
        # state 5.6 + Pima 0.5 + Oro Valley 2.5 = 8.6%.
        "Pima County",
        Decimal("2.500"),
        ("85737", "85755"),
    ),
    "Prescott": (
        "Yavapai County",
        Decimal("2.950"),
        ("86301", "86303", "86305"),
    ),
    "Prescott Valley": (
        "Yavapai County",
        Decimal("2.830"),
        ("86314", "86315"),
    ),
    # --- 2026-05-04 expansion: next ~28 cities from the same source
    # (TPT_RATETABLE_ALL_05012026.csv, BusinessCode 017 RETAIL).
    # County + ZIP mappings cross-checked against USPS / Wikipedia city
    # pages on 2026-05-04. Sun City and Anthem are CDPs without their
    # own TPT codes in the CSV and are intentionally omitted.
    # --- Maricopa County (additional Phoenix-metro cities) ---
    "Wickenburg": (
        "Maricopa County",
        Decimal("2.200"),
        ("85390",),
    ),
    "Tolleson": (
        # iter-152: raised 2.500 → 2.800 per SalesTaxHandbook (Tolleson
        # city tax 2.8% in 2026; under-collect 0.3% pre-fix).
        "Maricopa County",
        Decimal("2.800"),
        ("85353",),
    ),
    "Litchfield Park": (
        # iter-152: raised 2.800 → 3.000 per SalesTaxHandbook (Litchfield
        # Park city tax 3.0% in 2026; under-collect 0.2% pre-fix).
        "Maricopa County",
        Decimal("3.000"),
        ("85340",),
    ),
    "El Mirage": (
        "Maricopa County",
        Decimal("3.000"),
        ("85335",),
    ),
    "Carefree": (
        "Maricopa County",
        Decimal("3.000"),
        ("85377",),
    ),
    "Queen Creek": (
        "Maricopa County",
        Decimal("2.250"),
        ("85140", "85142", "85143"),
    ),
    # --- Pinal County ---
    "Apache Junction": (
        "Pinal County",
        Decimal("2.400"),
        ("85119", "85120"),
    ),
    "Maricopa": (
        # The CITY of Maricopa (TPT code MP) sits in PINAL County, not
        # Maricopa County. Distinct entity from Maricopa County itself.
        "Pinal County",
        Decimal("2.500"),
        ("85138", "85139"),
    ),
    "Eloy": (
        "Pinal County",
        Decimal("3.000"),
        ("85131",),
    ),
    "Florence": (
        "Pinal County",
        Decimal("2.000"),
        ("85132",),
    ),
    "Coolidge": (
        "Pinal County",
        Decimal("3.000"),
        ("85128",),
    ),
    # --- Mohave County ---
    "Bullhead City": (
        "Mohave County",
        Decimal("2.000"),
        ("86429", "86430", "86442"),
    ),
    "Kingman": (
        "Mohave County",
        Decimal("2.500"),
        ("86401", "86409"),
    ),
    # --- Cochise County (newly online via Sierra Vista) ---
    "Sierra Vista": (
        "Cochise County",
        Decimal("1.950"),
        ("85635", "85650"),
    ),
    # iter-193: 3 more Cochise Co cities -- all incorporated towns
    # missing from AZ_CITIES. Each had been returning state-only 6.10%
    # pre-fix. Verified rates against Avalara per-city pages.
    "Tombstone": (
        "Cochise County",
        Decimal("3.500"),  # combined 9.6% (state 5.6 + Cochise 0.5 + city 3.5)
        ("85638",),
    ),
    "Willcox": (
        "Cochise County",
        Decimal("3.000"),  # combined 9.1% (state 5.6 + Cochise 0.5 + city 3.0)
        ("85643",),
    ),
    "Huachuca City": (
        "Cochise County",
        Decimal("1.900"),  # combined 8.0% (state 5.6 + Cochise 0.5 + city 1.9)
        ("85616",),
    ),
    # --- Pima County (additional, beyond Tucson + Marana) ---
    "Sahuarita": (
        # iter-150: raised 2.000 → 5.000 in 2024 (city tax 2% became
        # 5% special tax per SalesTaxHandbook). Engine had been
        # under-collecting 3.0% for 85629.
        "Pima County",
        Decimal("5.000"),
        ("85629",),
    ),
    # --- Yuma County (additional, beyond Yuma) ---
    "San Luis": (
        "Yuma County",
        Decimal("4.000"),
        ("85349",),
    ),
    # --- Santa Cruz County (newly online via Nogales) ---
    "Nogales": (
        "Santa Cruz County",
        Decimal("2.000"),
        ("85621",),
    ),
    # --- Gila County (newly online via Globe + Payson) ---
    "Globe": (
        "Gila County",
        Decimal("3.300"),
        ("85501",),
    ),
    "Payson": (
        "Gila County",
        Decimal("3.880"),
        ("85541",),
    ),
    # --- Coconino County (additional, beyond Flagstaff) ---
    "Page": (
        "Coconino County",
        Decimal("3.000"),
        ("86040",),
    ),
    "Williams": (
        "Coconino County",
        Decimal("3.500"),
        ("86046",),
    ),
    # --- Navajo County (newly online via Show Low + others) ---
    "Show Low": (
        "Navajo County",
        Decimal("2.000"),
        ("85901",),
    ),
    "Snowflake": (
        "Navajo County",
        Decimal("3.000"),
        ("85937",),
    ),
    "Holbrook": (
        "Navajo County",
        Decimal("3.000"),
        ("86025",),
    ),
    "Winslow": (
        "Navajo County",
        Decimal("3.000"),
        ("86047",),
    ),
    # --- Yavapai County (additional, beyond Prescott + Prescott Valley) ---
    "Camp Verde": (
        "Yavapai County",
        Decimal("3.650"),
        ("86322",),
    ),
    "Cottonwood": (
        "Yavapai County",
        Decimal("3.500"),
        ("86326",),
    ),
    "Sedona": (
        # Sedona straddles the Yavapai/Coconino county line; the larger
        # share (uptown + west Sedona, ZIP 86336) sits in Yavapai. The
        # 86351 ZIP (Village of Oak Creek, just south of Sedona proper)
        # is also in Yavapai.
        "Yavapai County",
        Decimal("3.500"),
        ("86336", "86351"),
    ),
    # --- iter-151: more AZ city additions ---
    "Sun City": (
        # CDP in Maricopa Co; state 5.6 + Maricopa 0.7 + city 3.0 = 9.3
        # per SalesTaxHandbook.
        "Maricopa County",
        Decimal("3.000"),
        ("85351", "85372", "85373", "85375"),
    ),
    "Vail": (
        # ZIP 85641 in Pima Co; state 5.6 + Pima 0.5 + city 2.6 = 8.7.
        "Pima County",
        Decimal("2.600"),
        ("85641",),
    ),
    "Bisbee": (
        # state 5.6 + Cochise 0.5 + city 3.5 = 9.6.
        "Cochise County",
        Decimal("3.500"),
        ("85603",),
    ),
    # --- iter-152: more Maricopa Co cities + Apache Co additions ---
    "Cave Creek": (
        # ZIP 85327 was returning 0% (missing-binding bug, 3rd this
        # session after CA Mariposa 95338 + FL Paxton 32538).
        # state 5.6 + Maricopa 0.7 + city 3.0 = 9.3.
        "Maricopa County",
        Decimal("3.000"),
        ("85327", "85331"),
    ),
    "Fountain Hills": (
        # state 5.6 + Maricopa 0.7 + city 2.9 = 9.2.
        "Maricopa County",
        Decimal("2.900"),
        ("85268", "85269"),
    ),
    "Paradise Valley": (
        # state 5.6 + Maricopa 0.7 + city 2.8 = 9.1.
        "Maricopa County",
        Decimal("2.800"),
        ("85253",),
    ),
    "Youngtown": (
        # state 5.6 + Maricopa 0.7 + city 3.0 = 9.3.
        "Maricopa County",
        Decimal("3.000"),
        ("85363",),
    ),
    "Eagar": (
        # state 5.6 + Apache 0.5 + city 3.0 = 9.1.
        "Apache County",
        Decimal("3.000"),
        ("85925",),
    ),
    "Springerville": (
        # state 5.6 + Apache 0.5 + city 3.0 = 9.1.
        "Apache County",
        Decimal("3.000"),
        ("85938",),
    ),
    # --- iter-153: La Paz Co (Parker + Quartzsite) ---
    "Parker": (
        # state 5.6 + La Paz 1.0 + city 4.0 = 10.6.
        # Includes 2% city tax + 2% special added Oct 2025.
        "La Paz County",
        Decimal("4.000"),
        ("85344",),
    ),
    "Quartzsite": (
        # state 5.6 + La Paz 1.0 + city 2.5 = 9.1.
        "La Paz County",
        Decimal("2.500"),
        ("85346",),
    ),
}


__all__ = [
    "AZ_STATE_RATE_PCT",
    "AZ_STATE_EFFECTIVE_FROM",
    "AZ_COUNTY_RATE_PCT",
    "AZ_CITIES",
]
