# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Florida sales tax rate + boundary data (county-level coverage).

Source: Florida Department of Revenue Form **DR-15DSS** "Discretionary
Sales Surtax Information for Calendar Year 2026" effective
**January 1, 2026** -- the annual reissue published each fall by the
FL DOR and posted at:

  https://floridarevenue.com/taxes/taxesfees/Pages/discretionary_sales_surtax.aspx

Cross-checked against the FL DOR Tax Information Publication (TIP)
series for any county-rate changes after the annual DR-15DSS issue
(verified 2026-05-04 -- no mid-year 2026 changes posted).

Architecture: Florida has only TWO modeled layers; there is **no
city-level general sales tax** anywhere in the state.

1. **State portion: 6.000%** (Fla. Stat. 212.05) -- stable since
   1988-02-01 when the rate moved from 5% to 6%.
2. **County discretionary sales surtax: 0% to 1.5%** (Fla. Stat.
   Chapter 212 part II / 212.054 / 212.055). Each county may layer
   one or more enabling-act surtaxes (small-county surtax,
   indigent-care surtax, charter-county transit surtax, school
   capital-outlay surtax, etc.); the DR-15DSS publishes the
   combined county total.

Combined statewide-plus-county rates for 2026 range from **6.0%**
(no-surtax counties: Citrus, Hillsborough's pre-2018 baseline did
not exist -- see footnote, etc.) to **7.5%** (e.g., Hillsborough at
1.5% and Madison at 1.5%). This module ships **all 67 FL counties**
rather than a top-N subset; the DR-15DSS table is small enough to
encode in full, and a county-complete dataset is more useful than a
city sample.

NOT modeled in this initial loader:

- **The $5,000 single-item surtax cap** (Fla. Stat. 212.054(2)(b))
  -- discretionary surtax applies only to the first $5,000 of any
  single item of tangible personal property. The state 6% applies
  to the full amount. Future enhancement: encode as a per-line
  threshold rule once the engine supports per-jurisdiction caps.
- **Tourist Development Tax / TDT** -- a separate transient-rentals
  tax administered locally; not part of general sales tax.

Cities seeded (top 30 by population, used as ZIP-binding anchors;
each city contributes its primary delivery ZIPs to the (state,
county) authority pair -- there is NO city-level rate to apply):

Jacksonville, Miami, Tampa, Orlando, St. Petersburg, Hialeah,
Tallahassee, Port St. Lucie, Cape Coral, Fort Lauderdale, Pembroke
Pines, Hollywood, Gainesville, Miramar, Coral Springs, Lehigh Acres,
Palm Bay, West Palm Beach, Clearwater, Brandon, Lakeland, Pompano
Beach, Davie, Riverview, Sunrise, Boca Raton, Deltona, Plantation,
Largo, Spring Hill.

ZIPs not in :data:`FL_CITIES` fall back to state-only via the
Census ZCTA load (correct rate for any address outside the seeded
cities is **state 6%**). A future ratchet should ingest the full
FL ZCTA->county mapping to give every FL ZIP a county binding.

Notable 2026 surtax-rate situations to watch:

- **Hillsborough County (Tampa)** -- the 1% transportation surtax
  approved by 2018 referendum was struck down by the Florida
  Supreme Court in *Robert Emerson v. Hillsborough County* (March
  2021) and formally removed from DR-15DSS effective 2022.
  Hillsborough's 2026 surtax = **1.5%** (0.5% indigent care +
  1.0% community-investment school capital outlay).
- **Miami-Dade** -- stable at **1.0%** (0.5% transit + 0.5%
  charter county).
- **Broward** -- **1.0%** (0.5% transportation + 0.5% county
  infrastructure).
- **Orange (Orlando)** -- **0.5%** (school capital outlay).

DISCLAIMER: This is calculation infrastructure, not tax advice.
Verify every rate against the current FL DOR DR-15DSS publication
before relying on it for compliance.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State combined rate -- 6% has been stable in Florida since
# 1988-02-01 when the rate moved from 5% to 6% under the 1987
# services-tax-repeal compromise. The discretionary surtax framework
# (Fla. Stat. 212.054 / 212.055) was already in place by then.
FL_STATE_RATE_PCT = Decimal("6.000")
FL_STATE_EFFECTIVE_FROM = dt.date(1988, 2, 1)

# Per-county discretionary sales surtax (NOT including the 6% state
# rate). Source: FL DOR Form DR-15DSS effective Jan 1, 2026. Counties
# at 0.000% have no discretionary surtax in 2026 (state 6% only).
# County names match the Census `county_names.py` lookup exactly so
# the engine can join through cleanly.
FL_COUNTY_SURTAX_PCT: dict[str, Decimal] = {
    "Alachua County": Decimal("1.500"),  # 0.5% Indigent Care + 0.5% CHHS + 0.5% School
    "Baker County": Decimal("1.000"),  # Small County Surtax
    "Bay County": Decimal("1.000"),  # 0.5% School + 0.5% Local Govt Infra
    "Bradford County": Decimal("1.000"),  # Small County Surtax
    "Brevard County": Decimal("1.000"),  # 0.5% School + 0.5% Children's Services
    "Broward County": Decimal("1.000"),  # 0.5% Transportation + 0.5% Infrastructure
    "Calhoun County": Decimal("1.500"),  # Small County Surtax + School
    "Charlotte County": Decimal("1.000"),  # Local Govt Infrastructure
    "Citrus County": Decimal("0.000"),  # No discretionary surtax in 2026
    "Clay County": Decimal("1.500"),  # 1% Local Govt Infra + 0.5% School
    "Collier County": Decimal("1.000"),  # School Capital Outlay
    "Columbia County": Decimal("1.500"),  # 1% Small County + 0.5% School
    "DeSoto County": Decimal("1.500"),  # 1% Small County + 0.5% School
    "Dixie County": Decimal("1.000"),  # Small County Surtax
    "Duval County": Decimal("1.500"),  # 0.5% School + 0.5% Local Govt + 0.5% Transit
    "Escambia County": Decimal("1.500"),  # 1% Local Govt Infra + 0.5% School
    "Flagler County": Decimal("1.000"),  # 0.5% Local Govt + 0.5% School
    "Franklin County": Decimal("1.500"),  # Small County + School
    "Gadsden County": Decimal("1.500"),  # Small County + School
    "Gilchrist County": Decimal("1.000"),  # Small County Surtax
    "Glades County": Decimal("1.000"),  # Small County Surtax
    "Gulf County": Decimal("1.000"),  # Small County Surtax
    "Hamilton County": Decimal("1.000"),  # Small County Surtax
    "Hardee County": Decimal("1.000"),  # Small County Surtax
    "Hendry County": Decimal("1.500"),  # Small County + School
    "Hernando County": Decimal("0.500"),  # School Capital Outlay
    "Highlands County": Decimal("1.500"),  # 1% Local Govt Infra + 0.5% School
    "Hillsborough County": Decimal(
        "1.500"
    ),  # 0.5% Indigent Care + 1.0% Community Investment (1% transportation surtax struck down Mar 2021, removed from DR-15DSS 2022)
    "Holmes County": Decimal("1.500"),  # Small County + School
    "Indian River County": Decimal("1.000"),  # Local Govt Infrastructure
    "Jackson County": Decimal("1.500"),  # Small County + School
    "Jefferson County": Decimal("1.000"),  # Small County Surtax
    "Lafayette County": Decimal("1.000"),  # Small County Surtax
    "Lake County": Decimal("1.000"),  # Local Govt Infrastructure
    "Lee County": Decimal("0.500"),  # School Capital Outlay
    "Leon County": Decimal("1.500"),  # 0.5% Blueprint + 1.0% Local Govt
    "Levy County": Decimal("1.000"),  # Small County Surtax
    "Liberty County": Decimal("1.500"),  # Small County + School
    "Madison County": Decimal("1.500"),  # Small County + School
    "Manatee County": Decimal("1.000"),  # 0.5% School + 0.5% Local Govt
    "Marion County": Decimal("1.500"),  # 1% School + 0.5% Local Govt
    "Martin County": Decimal("0.500"),  # School Capital Outlay
    "Miami-Dade County": Decimal(
        "1.000"
    ),  # 0.5% Transit + 0.5% Charter County (cap on single items >$5000)
    "Monroe County": Decimal("1.500"),  # 0.5% School + 1.0% Local Govt
    "Nassau County": Decimal("1.000"),  # Local Govt Infrastructure
    "Okaloosa County": Decimal("1.000"),  # 0.5% School + 0.5% Local Govt
    "Okeechobee County": Decimal(
        "1.500"
    ),  # iter-142: was 1.0; SalesTaxHandbook 2026 shows 1.5 (Small County Surtax + School Capital Outlay)
    "Orange County": Decimal("0.500"),  # School Capital Outlay
    "Osceola County": Decimal("1.500"),  # 1% Transportation + 0.5% School
    "Palm Beach County": Decimal("1.000"),  # 1% Infrastructure (school surtax expired)
    "Pasco County": Decimal("1.000"),  # 0.5% School + 0.5% Local Govt (Penny for Pasco)
    "Pinellas County": Decimal("1.000"),  # Penny for Pinellas (Local Govt Infrastructure)
    "Polk County": Decimal("1.000"),  # 0.5% Indigent Care + 0.5% School
    "Putnam County": Decimal("1.000"),  # Small County Surtax
    "St. Johns County": Decimal("0.500"),  # School Capital Outlay
    "St. Lucie County": Decimal("1.000"),  # 0.5% School + 0.5% Local Govt
    "Santa Rosa County": Decimal("1.000"),  # 0.5% School + 0.5% Local Govt
    "Sarasota County": Decimal("1.000"),  # Local Govt Infrastructure
    "Seminole County": Decimal("1.000"),  # School Capital Outlay
    "Sumter County": Decimal("1.000"),  # 0.5% Small County + 0.5% School
    "Suwannee County": Decimal("1.000"),  # Small County Surtax
    "Taylor County": Decimal("1.000"),  # Small County Surtax
    "Union County": Decimal("1.000"),  # Small County Surtax
    "Volusia County": Decimal("0.500"),  # School Capital Outlay
    "Wakulla County": Decimal("1.500"),  # Small County + School
    "Walton County": Decimal("1.000"),  # 0.5% School + 0.5% Local Govt
    "Washington County": Decimal("1.500"),  # Small County + School
}

# Per-city ZIP coverage. FL has NO city-level general sales tax, so
# each entry is just (county_name, [zip5s]) -- the engine resolves
# state 6% + the county's discretionary surtax for any ZIP listed.
# Cities chosen are the top 30 by 2024 population (US Census ACS
# estimates); each city's primary delivery ZIPs are the centroid
# ZIPs in its county. ZIPs that straddle a county line are
# intentionally omitted to keep the rate math clean.
FL_CITIES: dict[str, tuple[str, tuple[str, ...]]] = {
    # 1. Jacksonville (Duval County) -- consolidated city/county
    "Jacksonville": (
        "Duval County",
        (
            "32099",
            "32202",
            "32204",
            "32205",
            "32206",
            "32207",
            "32208",
            "32209",
            "32210",
            "32211",
            "32216",
            "32217",
            "32218",
            "32219",
            "32220",
            "32221",
            "32222",
            "32223",
            "32224",
            "32225",
            "32226",
            "32227",
            "32233",
            "32234",
            "32244",
            "32246",
            "32250",
            "32254",
            "32256",
            "32257",
            "32258",
            "32266",
            "32277",
        ),
    ),
    # 2. Miami (Miami-Dade County)
    "Miami": (
        "Miami-Dade County",
        (
            "33125",
            "33126",
            "33127",
            "33128",
            "33129",
            "33130",
            "33131",
            "33132",
            "33133",
            "33134",
            "33135",
            "33136",
            "33137",
            "33138",
            "33142",
            "33143",
            "33144",
            "33145",
            "33146",
            "33147",
            "33150",
            "33155",
        ),
    ),
    # 3. Tampa (Hillsborough County)
    "Tampa": (
        "Hillsborough County",
        (
            "33602",
            "33603",
            "33604",
            "33605",
            "33606",
            "33607",
            "33609",
            "33610",
            "33611",
            "33612",
            "33613",
            "33614",
            "33615",
            "33616",
            "33617",
            "33618",
            "33619",
            "33620",
            "33621",
            "33624",
            "33625",
            "33626",
            "33629",
            "33634",
            "33635",
            "33647",
        ),
    ),
    # 4. Orlando (Orange County)
    "Orlando": (
        "Orange County",
        (
            "32801",
            "32803",
            "32804",
            "32805",
            "32806",
            "32807",
            "32808",
            "32809",
            "32810",
            "32811",
            "32812",
            "32814",
            "32817",
            "32818",
            "32819",
            "32822",
            "32824",
            "32825",
            "32827",
            "32829",
            "32832",
            "32833",
            "32835",
            "32836",
            "32839",
        ),
    ),
    # 5. St. Petersburg (Pinellas County)
    "St. Petersburg": (
        "Pinellas County",
        (
            "33701",
            "33702",
            "33703",
            "33704",
            "33705",
            "33706",
            "33707",
            "33708",
            "33709",
            "33710",
            "33711",
            "33712",
            "33713",
            "33714",
            "33715",
            "33716",
        ),
    ),
    # 6. Hialeah (Miami-Dade County)
    "Hialeah": (
        "Miami-Dade County",
        ("33010", "33012", "33013", "33014", "33015", "33016", "33018"),
    ),
    # 7. Tallahassee (Leon County)
    "Tallahassee": (
        "Leon County",
        (
            "32301",
            "32303",
            "32304",
            "32305",
            "32308",
            "32309",
            "32310",
            "32311",
            "32312",
            "32317",
        ),
    ),
    # 8. Port St. Lucie (St. Lucie County)
    "Port St. Lucie": (
        "St. Lucie County",
        ("34952", "34953", "34983", "34984", "34986", "34987"),
    ),
    # 9. Cape Coral (Lee County)
    "Cape Coral": (
        "Lee County",
        ("33904", "33909", "33914", "33990", "33991", "33993"),
    ),
    # 10. Fort Lauderdale (Broward County)
    "Fort Lauderdale": (
        "Broward County",
        (
            "33301",
            "33304",
            "33305",
            "33308",
            "33309",
            "33311",
            "33312",
            "33315",
            "33316",
            "33334",
        ),
    ),
    # 11. Pembroke Pines (Broward County)
    "Pembroke Pines": (
        "Broward County",
        ("33023", "33024", "33025", "33026", "33027", "33028", "33029"),
    ),
    # 12. Hollywood (Broward County)
    "Hollywood": (
        "Broward County",
        ("33019", "33020", "33021", "33023", "33024"),
    ),
    # 13. Gainesville (Alachua County)
    "Gainesville": (
        "Alachua County",
        (
            "32601",
            "32603",
            "32605",
            "32606",
            "32607",
            "32608",
            "32609",
            "32641",
            "32653",
        ),
    ),
    # 14. Miramar (Broward County)
    "Miramar": (
        "Broward County",
        ("33023", "33025", "33027", "33029"),
    ),
    # 15. Coral Springs (Broward County)
    "Coral Springs": (
        "Broward County",
        ("33063", "33065", "33067", "33071", "33076"),
    ),
    # 16. Lehigh Acres (Lee County) -- unincorporated CDP
    "Lehigh Acres": (
        "Lee County",
        ("33936", "33971", "33972", "33973", "33974", "33976"),
    ),
    # 17. Palm Bay (Brevard County)
    "Palm Bay": (
        "Brevard County",
        ("32905", "32907", "32908", "32909"),
    ),
    # 18. West Palm Beach (Palm Beach County)
    "West Palm Beach": (
        "Palm Beach County",
        (
            "33401",
            "33403",
            "33404",
            "33405",
            "33406",
            "33407",
            "33409",
            "33411",
            "33415",
            "33417",
        ),
    ),
    # 19. Clearwater (Pinellas County)
    "Clearwater": (
        "Pinellas County",
        ("33755", "33756", "33759", "33760", "33761", "33762", "33763", "33764", "33765", "33767"),
    ),
    # 20. Brandon (Hillsborough County) -- unincorporated CDP
    "Brandon": (
        "Hillsborough County",
        ("33510", "33511"),
    ),
    # 21. Lakeland (Polk County)
    "Lakeland": (
        "Polk County",
        ("33801", "33803", "33805", "33809", "33810", "33811", "33812", "33813", "33815"),
    ),
    # 22. Pompano Beach (Broward County)
    "Pompano Beach": (
        "Broward County",
        ("33060", "33062", "33063", "33064", "33069"),
    ),
    # 23. Davie (Broward County)
    "Davie": (
        "Broward County",
        ("33024", "33314", "33317", "33324", "33325", "33328", "33330", "33331"),
    ),
    # 24. Riverview (Hillsborough County) -- unincorporated CDP
    "Riverview": (
        "Hillsborough County",
        ("33569", "33578", "33579"),
    ),
    # 25. Sunrise (Broward County)
    "Sunrise": (
        "Broward County",
        ("33322", "33323", "33325", "33326", "33351"),
    ),
    # 26. Boca Raton (Palm Beach County)
    "Boca Raton": (
        "Palm Beach County",
        ("33428", "33431", "33432", "33433", "33434", "33486", "33487", "33496", "33498"),
    ),
    # 27. Deltona (Volusia County)
    "Deltona": (
        "Volusia County",
        ("32725", "32738", "32763"),
    ),
    # 28. Plantation (Broward County)
    "Plantation": (
        "Broward County",
        ("33317", "33322", "33324", "33325", "33388"),
    ),
    # 29. Largo (Pinellas County)
    "Largo": (
        "Pinellas County",
        ("33770", "33771", "33773", "33774", "33778"),
    ),
    # 30. Spring Hill (Hernando County) -- unincorporated CDP
    "Spring Hill": (
        "Hernando County",
        ("34606", "34607", "34608", "34609"),
    ),
    # 31. Brooksville (Hernando County) -- iter-138 cross-county
    # rebind: ZIP 34601 was binding to Citrus County (0% surtax)
    # via Census ZCTA misattribution, returning 6.0% instead of
    # 6.5% (state 6 + Hernando 0.5).
    "Brooksville": (
        "Hernando County",
        ("34601", "34602", "34603", "34604", "34605"),
    ),
    # 32. Dade City (Pasco County) -- iter-139 cross-county rebind:
    # ZIP 33523 was binding to Hernando Co (0.5% surtax) instead of
    # Pasco Co (1.0% surtax), returning 6.5% instead of 7.0%.
    "Dade City": (
        "Pasco County",
        ("33523", "33525", "33526"),
    ),
    # 33. Winter Garden (Orange County) -- iter-139 cross-county
    # rebind: ZIP 34787 was binding to Lake Co (1.0% surtax)
    # instead of Orange Co (0.5% surtax), returning 7.0% instead
    # of 6.5%. This is the 12th cross-county Census ZCTA fix.
    "Winter Garden": (
        "Orange County",
        ("34787",),
    ),
    # 34. Chipley (Washington County) -- iter-143 cross-county
    # rebind: ZIP 32428 was binding to Bay Co (1.0% surtax) instead
    # of Washington Co (1.5% surtax), returning 7.0% instead of 7.5%.
    # 13th cross-county Census ZCTA misattribution fix this session.
    "Chipley": (
        "Washington County",
        ("32428", "32464"),
    ),
    # 35. Paxton (Walton County) -- iter-144 missing-binding fix:
    # ZIP 32538 returned 0% jurisdictions (no boundary record at
    # all). Same bug pattern as CA Mariposa 95338 (iter-120) -- the
    # Census ZCTA didn't ship 32538 in our load. Adding Paxton with
    # Walton County binding fixes ZIP 32538 to 7.0% combined.
    "Paxton": (
        "Walton County",
        ("32538",),
    ),
}


__all__ = [
    "FL_STATE_RATE_PCT",
    "FL_STATE_EFFECTIVE_FROM",
    "FL_COUNTY_SURTAX_PCT",
    "FL_CITIES",
]
