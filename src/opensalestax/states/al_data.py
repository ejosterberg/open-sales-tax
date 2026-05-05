# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Alabama sales tax rate + boundary data (top-30-city coverage).

Source: Alabama Department of Revenue (ALDOR) "Sales and Use Tax
Rates" page at https://www.revenue.alabama.gov/sales-use/tax-rates/
plus per-city Avalara rate pages and SalesTaxHandbook county pages.
Cross-checked across at least two sources for every covered city
on **2026-05-04**.

Architecture: Alabama's general-retail sales tax has three modeled
layers in this ratchet:

1. **State portion: 4.000%** (Ala. Code section 40-23-2(1))
2. **County portion** (varies by county; e.g. Jefferson 2.000%,
   Madison 0.500%, Mobile 1.000%, Montgomery 2.500%, Tuscaloosa
   3.000%, Shelby 1.000%, Baldwin 3.000%, Houston 1.000%)
3. **City portion** (varies; e.g. Birmingham 4.000%, Mobile 5.000%,
   Montgomery 3.500%, Huntsville 4.500%)

NOT modeled in this ratchet (partial-coverage caveats):

- **Special districts.** Madison City carries a 1.000% Madison Co Sp
  district that bumps the combined Madison rate from 8.000% to
  9.000%; Birmingham has a 1.000% special school district (BSD).
  These are intentionally excluded; the engine will under-collect
  by the special-district portion at those addresses. A future
  ratchet can fold them in once the engine grows per-district
  authority support.
- **The other ~670 Alabama cities.** Alabama is the most fragmented
  local-tax landscape in the United States with roughly 700
  incorporated municipalities, MANY of which self-administer their
  own sales tax under Ala. Code section 11-51-200 et seq. The 30
  cities seeded here represent the top-30 by population; addresses
  in any of the ~670 unseeded cities will pick up state + their
  county portion only and will under-collect by the unseeded
  city's portion (typically 2-5%). The home-rule deferral is
  documented in :mod:`opensalestax.states.alabama` and
  ``specs/decisions/04-colorado-home-rule.md``.
- **Counties not touched by a covered city.** All 67 AL counties
  are seeded in :data:`AL_COUNTY_RATE_PCT` so the
  ZIP_COUNTY-driven boundary loader has a queryable rate for
  every AL ZIP. The 49 non-anchor counties were filled from the
  ALDOR machine-readable rate file in this ratchet (previously
  0.000% placeholders). For counties where ALDOR publishes
  per-jurisdiction variants (CL/PJ/EXC), the **inside-city** rate
  is used (matches the convention used for the 18 anchor counties).
  Addresses in unincorporated areas of those counties may still
  under-collect by 1-3% relative to ALDOR's "EXC <city>" rate;
  this trade-off favours the more common populated-ZIP case.

Cities seeded (top 30 by 2026 population):

- **Birmingham** (Jefferson Co.) -- combined 10.000% (state 4 +
  county 2 + city 4)
- **Huntsville** (Madison Co.) -- combined 9.000% (state 4 + county
  0.5 + city 4.5)
- **Mobile** (Mobile Co.) -- combined 10.000% (state 4 + county 1 +
  city 5)
- **Montgomery** (Montgomery Co.) -- combined 10.000% (state 4 +
  county 2.5 + city 3.5)
- **Tuscaloosa** (Tuscaloosa Co.) -- combined 10.000% (state 4 +
  county 3 + city 3)
- **Hoover** (Jefferson Co.) -- combined 9.500% (state 4 + county 2
  + city 3.5)
- **Auburn** (Lee Co.) -- combined 9.000% (state 4 + county 1 + city 4)
- **Dothan** (Houston Co.) -- combined 9.000% (state 4 + county 1 +
  city 4)
- **Decatur** (Morgan Co.) -- combined 9.000% (state 4 + county 1 +
  city 4)
- **Madison** (Madison Co.) -- combined 8.000% via this loader
  (state 4 + county 0.5 + city 3.5); ALDOR/Avalara show 9.000% with
  the +1.000% Madison Co Sp district which is NOT modeled here
- **Florence** (Lauderdale Co.) -- combined 9.500% (state 4 +
  county 1 + city 4.5)
- **Vestavia Hills** (Jefferson Co.) -- combined 10.000%
- **Phenix City** (Russell Co.) -- combined 9.750% (state 4 +
  county 1 + city 4.75)
- **Prattville** (Autauga Co.) -- combined 9.500% (state 4 + county
  2 + city 3.5)
- **Gadsden** (Etowah Co.) -- combined 10.000% (state 4 + county 1
  + city 5)
- **Alabaster** (Shelby Co.) -- combined 10.000% (state 4 + county
  1 + city 5)
- **Opelika** (Lee Co.) -- combined 9.000% (state 4 + county 1 +
  city 4)
- **Northport** (Tuscaloosa Co.) -- combined 10.000% (state 4 +
  county 3 + city 3)
- **Enterprise** (Coffee Co.) -- combined 9.000% (state 4 + county
  1 + city 4)
- **Daphne** (Baldwin Co.) -- combined 9.500% (state 4 + county 3 +
  city 2.5)
- **Homewood** (Jefferson Co.) -- combined 10.000%
- **Bessemer** (Jefferson Co.) -- combined 10.000%
- **Athens** (Limestone Co.) -- combined 9.000% (state 4 + county 2
  + city 3)
- **Pelham** (Shelby Co.) -- combined 10.000%
- **Anniston** (Calhoun Co.) -- combined 10.000% (state 4 + county
  1 + city 5)
- **Mountain Brook** (Jefferson Co.) -- combined 10.000%
- **Trussville** (Jefferson Co.) -- combined 10.000%
- **Helena** (Shelby Co.) -- combined 10.000%
- **Foley** (Baldwin Co.) -- combined 10.000% (state 4 + county 3 +
  city 3)
- **Selma** (Dallas Co.) -- combined 10.000% (state 4 + county 1.5
  + city 4.5)

Source disagreements found during 2026-05-04 cross-check (both
Avalara and SalesTaxHandbook were consulted; for any disagreement
the Avalara per-city breakdown was treated as authoritative because
it gives the exact components for the city centroid):

- **Mobile County.** SalesTaxHandbook lists 1.500% as the county
  base rate; Avalara's per-city breakdown for Mobile city shows
  county portion of 1.000% (with the city absorbing the 0.500%
  difference). Encoded as 1.000% so combined for Mobile city =
  4 + 1 + 5 = 10.000% (matches Avalara). For unincorporated Mobile
  County addresses (Chickasaw 36611/36671, Prichard 36663) the
  actual county portion is 1.500%, which means non-Mobile-city
  Mobile County ZIPs will under-collect by 0.500% in this ratchet.
- **Madison City** has a +1.000% Madison Co Sp special district
  that brings the Avalara combined rate to 9.000%. We model only
  state 4 + county 0.5 + city 3.5 = 8.000% (the 1.000% special
  district is intentionally out of scope). Validation grid notes
  the gap.

ZIP coverage notes (per the FL/AZ/CA/TX/NY/MO/IL/PA/SC/MS/VA
pattern in v0.28-v0.31): :meth:`Alabama.parse_boundaries` iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` to bind every AL
ZIP to its county. Cross-county-line ZIPs get bound to the
city-anchor county where one is in :data:`AL_CITIES`, otherwise to
the FIPS-sorted-first AL county.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# Statewide 4.0% general rate has been in effect since 1969-12-08
# per Ala. Code section 40-23-2(1) (raised from 3.0% by Act 1969-833).
AL_STATE_RATE_PCT = Decimal("4.000")
AL_STATE_EFFECTIVE_FROM = dt.date(1969, 12, 8)

# Per-county local-tax portion (NOT including the 4.000% state rate).
# All 67 AL counties listed so the ZIP_COUNTY-driven boundary loader
# has a queryable rate for every AL ZIP. Counties touched by a covered
# AL_CITIES entry are at their verified per-city centroid rate (see
# the Source Disagreements section in the module docstring); the
# remaining counties are at the rate published in the ALDOR machine-
# readable rate file.
#
# Sources:
#   * Avalara per-city pages cross-checked against SalesTaxHandbook
#     county pages (verified 2026-05-04) -- used for the city-anchor
#     counties (Autauga, Baldwin, Calhoun, Coffee, Dallas, Etowah,
#     Houston, Jefferson, Lauderdale, Lee, Limestone, Madison,
#     Mobile, Montgomery, Morgan, Russell, Shelby, Tuscaloosa).
#   * ALDOR "Local Sales, Use, Rental & Lodgings Tax Rates Text File"
#     at https://www.revenue.alabama.gov/wp-content/uploads/2024/03/
#     taxrates.csv (retrieved 2026-05-04). Filtered to TaxType=ST
#     (sales tax) RateType=GENER (general retail) currently-active
#     rows. For the long-tail (non-anchor) counties the script
#     scripts/extract_al_county_rates.py emits the dict; for counties
#     where ALDOR publishes a county-wide CL rate (rate inside ALL
#     incorporated cities) we use the CL rate to match the inside-
#     city convention used by the v0.33 city-anchor seeds (e.g.
#     Chambers, Chilton, Marshall, Talladega).
#
# County names match :data:`opensalestax.data.county_names.COUNTY_NAMES`
# exactly. All values represent the county's general-retail sales tax
# portion, NOT including the 4.000% statewide rate or any city tax.
AL_COUNTY_RATE_PCT: dict[str, Decimal] = {
    "Autauga County": Decimal("2.000"),  # Prattville centroid: 4 + 2 + 3.5 = 9.5
    "Baldwin County": Decimal("3.000"),  # Daphne 4+3+2.5=9.5; Foley 4+3+3=10
    "Barbour County": Decimal("1.500"),  # ALDOR taxrates.csv flat county rate
    "Bibb County": Decimal("4.000"),  # ALDOR taxrates.csv flat county rate
    "Blount County": Decimal("3.000"),  # ALDOR taxrates.csv flat county rate
    "Bullock County": Decimal("2.500"),  # ALDOR taxrates.csv flat county rate
    "Butler County": Decimal("1.500"),  # ALDOR taxrates.csv flat county rate
    "Calhoun County": Decimal("1.000"),  # Anniston centroid: 4 + 1 + 5 = 10
    "Chambers County": Decimal("1.000"),  # ALDOR CL rate (inside any city); EXC unincorp = 6.0
    "Cherokee County": Decimal("3.500"),  # ALDOR taxrates.csv flat county rate
    "Chilton County": Decimal("3.000"),  # ALDOR CL 4-cities rate; EXC = 4.0
    "Choctaw County": Decimal("3.000"),  # ALDOR taxrates.csv flat county rate
    "Clarke County": Decimal("1.000"),  # ALDOR taxrates.csv flat county rate
    "Clay County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Cleburne County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Coffee County": Decimal("1.000"),  # Enterprise centroid: 4 + 1 + 4 = 9
    "Colbert County": Decimal("1.500"),  # ALDOR taxrates.csv flat county rate
    "Conecuh County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Coosa County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Covington County": Decimal("2.500"),  # ALDOR taxrates.csv flat county rate
    "Crenshaw County": Decimal("3.500"),  # ALDOR taxrates.csv flat county rate
    "Cullman County": Decimal("4.500"),  # ALDOR base rate; CL+PJ Arab specifically = 3.5
    "Dale County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Dallas County": Decimal("1.500"),  # Selma centroid: 4 + 1.5 + 4.5 = 10
    "DeKalb County": Decimal("1.000"),  # ALDOR taxrates.csv flat county rate
    "Elmore County": Decimal("1.000"),  # ALDOR base rate; CL Prattville specifically = 2.0
    "Escambia County": Decimal("2.000"),  # ALDOR base rate; EXC 5 cities = 5.0, PJ variants 3.5/4.0
    "Etowah County": Decimal("1.000"),  # Gadsden centroid: 4 + 1 + 5 = 10
    "Fayette County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Franklin County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Geneva County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Greene County": Decimal("3.000"),  # ALDOR taxrates.csv flat county rate
    "Hale County": Decimal("3.000"),  # ALDOR taxrates.csv flat county rate
    "Henry County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Houston County": Decimal("1.000"),  # Dothan centroid: 4 + 1 + 4 = 9
    "Jackson County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Jefferson County": Decimal(
        "2.000"
    ),  # Birmingham, Hoover, Vestavia Hills, Homewood, Bessemer, Mountain Brook, Trussville
    "Lamar County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Lauderdale County": Decimal("1.000"),  # Florence centroid: 4 + 1 + 4.5 = 9.5
    "Lawrence County": Decimal("3.000"),  # ALDOR taxrates.csv flat county rate
    "Lee County": Decimal("1.000"),  # Auburn 4+1+4=9; Opelika 4+1+4=9
    "Limestone County": Decimal("2.000"),  # Athens centroid: 4 + 2 + 3 = 9
    "Lowndes County": Decimal("4.000"),  # ALDOR taxrates.csv flat county rate
    "Macon County": Decimal("2.500"),  # ALDOR taxrates.csv flat county rate
    "Madison County": Decimal(
        "0.500"
    ),  # Huntsville 4+0.5+4.5=9; Madison city 4+0.5+3.5=8 (no special district)
    "Marengo County": Decimal("3.000"),  # ALDOR taxrates.csv flat county rate
    "Marion County": Decimal("2.000"),  # ALDOR base rate; CL Winfield specifically = 1.0
    "Marshall County": Decimal("1.000"),  # ALDOR CL 4-cities rate; EXC = 2.0
    "Mobile County": Decimal(
        "1.000"
    ),  # Mobile city centroid: 4 + 1 + 5 = 10 (Avalara). Unincorporated Mobile Co. is 1.5%; under-collect by 0.5% in this ratchet
    "Monroe County": Decimal("3.500"),  # ALDOR taxrates.csv flat county rate
    "Montgomery County": Decimal("2.500"),  # Montgomery centroid: 4 + 2.5 + 3.5 = 10
    "Morgan County": Decimal("1.000"),  # Decatur centroid: 4 + 1 + 4 = 9
    "Perry County": Decimal("3.000"),  # ALDOR taxrates.csv flat county rate
    "Pickens County": Decimal("4.000"),  # ALDOR taxrates.csv flat county rate
    "Pike County": Decimal("2.500"),  # ALDOR CL Troy rate; EXC = 3.5
    "Randolph County": Decimal("2.500"),  # ALDOR taxrates.csv flat county rate
    "Russell County": Decimal("1.000"),  # Phenix City centroid: 4 + 1 + 4.75 = 9.75
    "St. Clair County": Decimal("2.000"),  # ALDOR base rate; CL Pell City specifically = 1.0
    "Shelby County": Decimal("1.000"),  # Alabaster, Pelham, Helena -- all 4 + 1 + 5 = 10
    "Sumter County": Decimal("4.000"),  # ALDOR taxrates.csv flat county rate
    "Talladega County": Decimal("1.000"),  # ALDOR CL rate; PJ = 2.0, base unincorp = 3.0
    "Tallapoosa County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Tuscaloosa County": Decimal("3.000"),  # Tuscaloosa, Northport -- both 4 + 3 + 3 = 10
    "Walker County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
    "Washington County": Decimal("1.000"),  # ALDOR taxrates.csv flat county rate
    "Wilcox County": Decimal("4.500"),  # ALDOR taxrates.csv flat county rate
    "Winston County": Decimal("2.000"),  # ALDOR taxrates.csv flat county rate
}

# Per-city general-retail rate (NOT including state or county).
# Each tuple: (county_name, city_rate_pct, [zip5s]).
# Combined math = state 4.000% + county[county_name] + city_rate_pct.
# ZIPs are the primary delivery codes for the city centroid; ZIPs that
# straddle into a different county are bound back to the city-anchor
# county by parse_boundaries (city-anchor wins over FIPS-sort).
#
# Source: Avalara per-city pages (verified 2026-05-04). Cross-checked
# against SalesTaxHandbook per-county pages.
AL_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    "Birmingham": (
        "Jefferson County",
        Decimal("4.000"),
        # Birmingham city ZIPs in Jefferson County. ZIPs that straddle
        # into Shelby (35216, 35244) or St. Clair (35173) are
        # excluded from the Birmingham seed because the city limits
        # don't extend that far -- those ZIPs anchor to other Jefferson
        # cities (Vestavia Hills, Hoover, Trussville) or aren't covered.
        # 35209 (Homewood) and 35213 (Mountain Brook) are also excluded
        # so each ZIP belongs to at most one city authority and the
        # engine doesn't double-count city tax.
        (
            "35203",
            "35204",
            "35205",
            "35206",
            "35207",
            "35208",
            "35210",
            "35211",
            "35212",
            "35214",
            "35215",
            "35217",
            "35218",
            "35219",
            "35221",
            "35222",
            "35224",
            "35228",
            "35233",
            "35234",
            "35235",
        ),
    ),
    "Huntsville": (
        "Madison County",
        Decimal("4.500"),
        # Huntsville core ZIPs in Madison County. Some Huntsville-named
        # ZIPs cross into Limestone or Morgan; the centroid ZIPs here
        # are firmly in Madison.
        ("35801", "35802", "35803", "35805", "35806", "35808", "35810", "35811", "35816", "35824"),
    ),
    "Mobile": (
        "Mobile County",
        Decimal("5.000"),
        # Mobile city ZIPs in Mobile County. Excludes the Chickasaw
        # (36611, 36671) and Prichard (36663) districts which carry
        # different city portions.
        (
            "36602",
            "36603",
            "36604",
            "36605",
            "36606",
            "36607",
            "36608",
            "36609",
            "36610",
            "36617",
            "36618",
            "36619",
            "36695",
        ),
    ),
    "Montgomery": (
        "Montgomery County",
        Decimal("3.500"),
        (
            "36104",
            "36105",
            "36106",
            "36107",
            "36108",
            "36109",
            "36110",
            "36111",
            "36112",
            "36113",
            "36115",
            "36116",
            "36117",
        ),
    ),
    "Tuscaloosa": (
        "Tuscaloosa County",
        Decimal("3.000"),
        ("35401", "35404", "35405", "35406"),
    ),
    "Hoover": (
        "Jefferson County",
        Decimal("3.500"),
        # Hoover ZIPs primarily in Jefferson Co; 35244 also touches
        # Shelby Co but city-anchor binds it back to Jefferson. 35216
        # is shared with Vestavia Hills postally and is anchored to
        # Vestavia Hills below.
        ("35226", "35244"),
    ),
    "Auburn": (
        "Lee County",
        Decimal("4.000"),
        # 36830 also touches Macon; city-anchor binds to Lee.
        ("36830", "36832"),
    ),
    "Dothan": (
        "Houston County",
        Decimal("4.000"),
        # 36303 also touches Dale and Henry; city-anchor binds to Houston.
        ("36301", "36303", "36305"),
    ),
    "Decatur": (
        "Morgan County",
        Decimal("4.000"),
        ("35601", "35603"),
    ),
    "Madison": (
        "Madison County",
        Decimal("3.500"),
        # NOTE: Madison City carries a +1.000% Madison Co Sp special
        # district that bumps the Avalara combined rate to 9.000%; this
        # loader returns 8.000% (state 4 + county 0.5 + city 3.5). The
        # 1.000% gap is the documented under-collection.
        ("35756", "35757", "35758"),
    ),
    "Florence": (
        "Lauderdale County",
        Decimal("4.500"),
        ("35630", "35633", "35634"),
    ),
    "Vestavia Hills": (
        "Jefferson County",
        Decimal("4.000"),
        # 35216 spans Vestavia Hills, parts of Hoover and Birmingham;
        # anchored here because the bulk of the ZIP is in Vestavia
        # Hills city limits per Avalara. 35243 is Vestavia Hills proper.
        ("35216", "35243"),
    ),
    "Phenix City": (
        "Russell County",
        Decimal("4.750"),
        # 36869 is in Russell; 36867 also touches Lee but Phenix City
        # proper is in Russell.
        ("36867", "36869"),
    ),
    "Prattville": (
        "Autauga County",
        Decimal("3.500"),
        # 36066 straddles Autauga and Elmore; city-anchor binds to Autauga.
        ("36066", "36067"),
    ),
    "Gadsden": (
        "Etowah County",
        Decimal("5.000"),
        # 35903 straddles Cherokee and Etowah; city-anchor binds to Etowah.
        ("35901", "35903", "35904"),
    ),
    "Alabaster": (
        "Shelby County",
        Decimal("5.000"),
        ("35007",),
    ),
    "Opelika": (
        "Lee County",
        Decimal("4.000"),
        # 36801 touches Chambers; city-anchor binds to Lee.
        ("36801", "36804"),
    ),
    "Northport": (
        "Tuscaloosa County",
        Decimal("3.000"),
        ("35473", "35475", "35476"),
    ),
    "Enterprise": (
        "Coffee County",
        Decimal("4.000"),
        # 36330 touches Dale; city-anchor binds to Coffee.
        ("36330",),
    ),
    "Daphne": (
        "Baldwin County",
        Decimal("2.500"),
        ("36526",),
    ),
    "Homewood": (
        "Jefferson County",
        Decimal("4.000"),
        ("35209",),
    ),
    "Bessemer": (
        "Jefferson County",
        Decimal("4.000"),
        ("35020", "35022", "35023"),
    ),
    "Athens": (
        "Limestone County",
        Decimal("3.000"),
        ("35611", "35613"),
    ),
    "Pelham": (
        "Shelby County",
        Decimal("5.000"),
        ("35124",),
    ),
    "Anniston": (
        "Calhoun County",
        Decimal("5.000"),
        # 36207 touches Cleburne; city-anchor binds to Calhoun.
        ("36201", "36206", "36207"),
    ),
    "Mountain Brook": (
        "Jefferson County",
        Decimal("4.000"),
        # 35213 and 35223 are Mountain Brook proper; 35223 is Mountain
        # Brook's primary post office.
        ("35213", "35223"),
    ),
    "Trussville": (
        "Jefferson County",
        Decimal("4.000"),
        # 35173 straddles Jefferson and St. Clair; city-anchor binds
        # to Jefferson.
        ("35173",),
    ),
    "Helena": (
        "Shelby County",
        Decimal("5.000"),
        # 35080 straddles Jefferson and Shelby; city-anchor binds to
        # Shelby.
        ("35080",),
    ),
    "Foley": (
        "Baldwin County",
        Decimal("3.000"),
        ("36535",),
    ),
    "Selma": (
        "Dallas County",
        Decimal("4.500"),
        # 36703 straddles Autauga and Dallas; city-anchor binds to Dallas.
        ("36701", "36703"),
    ),
}


__all__ = [
    "AL_STATE_RATE_PCT",
    "AL_STATE_EFFECTIVE_FROM",
    "AL_COUNTY_RATE_PCT",
    "AL_CITIES",
]
