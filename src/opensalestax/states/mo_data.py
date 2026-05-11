# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Missouri sales tax rate + boundary data.

Source: Missouri Department of Revenue 2026 Statewide Sales/Use Tax
Rate Tables published quarterly at
https://dor.mo.gov/taxation/business/tax-types/sales-use/rate-tables/2026/
plus the Avalara per-city rate calculator pages for cross-check
(verified 2026-05-04).

Architecture: Missouri's rate has three modeled layers:

1. **State portion: 4.225%** (Mo. Rev. Stat. section 144.020 +
   144.701 + Mo. Const. art. IV sections 43(a) and 47(a))
2. **County portion** (varies, e.g. Jackson 1.375%, St. Louis 2.263%,
   Boone 1.75%)
3. **City portion** (varies, e.g. Kansas City 3.25%, St. Louis 5.454%
   for the independent city)

NOT modeled in this v0.25 ratchet:

- **Special districts** (Community Improvement Districts, Transportation
  Development Districts, Zoological Park Districts) -- these are
  ZIP-specific and overlay the city/county rates. The Avalara
  "minimum combined" rates seeded here EXCLUDE these districts; the
  combined rate at any specific +4 may be higher.
- **Independent cities other than St. Louis**: Missouri has only one
  legal independent city (St. Louis); for our purposes we treat
  St. Louis (city) as both its own county and city.

Cities seeded (top 15 by population):

- Kansas City (Jackson Co.) -- 8.850%
- St. Louis (city) -- 9.679%
- Springfield (Greene Co.) -- 8.100%
- Independence (Jackson Co.) -- 8.475%
- Columbia (Boone Co.) -- 7.975%
- Lee's Summit (Jackson Co.) -- 8.350%
- O'Fallon (St. Charles Co.) -- 7.950%
- St. Joseph (Buchanan Co.) -- 9.700%
- St. Charles (St. Charles Co.) -- 7.950%
- St. Peters (St. Charles Co.) -- 7.950%
- Joplin (Jasper Co.) -- 8.725%
- Florissant (St. Louis Co.) -- 7.738%
- Chesterfield (St. Louis Co.) -- 7.488%
- Jefferson City (Cole Co.) -- 7.850%
- Cape Girardeau (Cape Girardeau Co.) -- 8.475%

ZIPs not in :data:`MO_CITIES` resolve to state + their county's bare
base rate (state 4.225% + county portion). All 114 MO counties + the
St. Louis independent city are seeded from the MO DOR jan2026 PDF via
:file:`scripts/extract_mo_county_rates.py`. Three of the 11 counties
that already had a tuned non-zero rate (Jackson, St. Louis County,
Taney) are kept at their existing values because the per-city seed
in :data:`MO_CITIES` was derived against those splits; updating them
would require rebalancing the city totals and the DOR validation grid.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State combined rate -- 4.225% has been stable since 1984 when the
# 0.125% parks/soils tax (Mo. Const. art. IV section 47(a)) was
# layered atop the 0.10% Conservation Sales Tax (1977), the 1.0%
# Proposition C education tax (1982), and the 3.0% general revenue.
MO_STATE_RATE_PCT = Decimal("4.225")
MO_STATE_EFFECTIVE_FROM = dt.date(1984, 1, 1)

# Per-county portion (NOT including the 4.225% state rate). All 114
# Missouri counties + St. Louis (independent city) seeded from the
# MO DOR jan2026 PDF; see the Long-tail block below for the source URL
# and the extraction script. The first cluster (Jackson / Greene /
# Boone / etc.) keeps its prior value because it was tuned against
# the per-city seed in MO_CITIES; the long-tail block was filled in
# the v0.30 ratchet to eliminate the prior 0%-county under-collection.
MO_COUNTY_RATE_PCT: dict[str, Decimal] = {
    # ---- Counties touched by a covered MO_CITIES entry (existing seed) ----
    # iter-62: bumped 1.375 -> 1.500 to fold in the 0.125% Kansas City
    # Zoological District (a county-wide tax for Jackson + Clay + Platte
    # per Mo. Rev. Stat. chapter 184). Verified via Avalara: KC 8.975%
    # (was 8.85), Independence 8.600% (was 8.475), Lee's Summit 8.475%
    # (was 8.35). The bump matches MO DOR jan2026 PDF base for Jackson,
    # so this also closes the deferred-rebalance note below.
    "Jackson County": Decimal("1.500"),
    "St. Louis city": Decimal("5.454"),  # Independent city; entire local goes here
    "Greene County": Decimal("1.750"),
    "Boone County": Decimal("1.750"),
    "St. Charles County": Decimal("1.725"),
    "Buchanan County": Decimal("1.600"),
    "Jasper County": Decimal("1.375"),
    "St. Louis County": Decimal("2.263"),
    "Cole County": Decimal("1.375"),
    "Cape Girardeau County": Decimal("1.500"),
    # ---- Counties tuned to existing per-city seed (kept at the value
    # the city totals were derived against; updating these would require
    # rebalancing MO_CITIES + the DOR test rows. The MO DOR jan2026 PDF
    # base rates for these three counties are higher (Jackson 1.500%,
    # St. Louis County 3.513%, Taney 2.125%); a future ratchet should
    # rework the city seed to fold in those higher county portions.) ----
    "Taney County": Decimal("1.875"),  # Branson area; salestaxhandbook 2026
    # ---- Remaining 104 MO counties: filled from MO DOR jan2026 PDF ----
    # Source: MO DOR Sales and Use Tax Rate Tables, January 2026 edition
    # (jan2026.pdf), published 2025-11-14, retrieved 2026-05-04 from
    # https://dor.mo.gov/pdf/rates/2026/jan2026.pdf.
    # Extraction script: scripts/extract_mo_county_rates.py (re-run on
    # next quarterly publication). Each rate is the bare unincorporated-
    # county base (combined - state 4.225%); the PDF's -000 row is the
    # canonical base, and counties without a -000 row (Camden, Marion,
    # Morgan, Scott, Shelby) use the lowest overlay-row rate as their
    # effective base because every unincorporated address sits in at
    # least one ambulance / fire-protection overlay. Per Mo. Rev. Stat.
    # 67.500-67.547 (county sales tax authorizations).
    #
    # Values are CONFIRMED from the MO DOR PDF; none are placeholders.
    # The +1% under-collection for ZIPs in unincorporated counties has
    # been eliminated for these 104 counties (was state-only 4.225%).
    "Adair County": Decimal("1.750"),
    "Andrew County": Decimal("2.200"),
    "Atchison County": Decimal("2.250"),
    "Audrain County": Decimal("2.125"),
    "Barry County": Decimal("2.000"),
    "Barton County": Decimal("2.250"),
    "Bates County": Decimal("1.000"),
    "Benton County": Decimal("2.000"),
    "Bollinger County": Decimal("2.625"),
    "Butler County": Decimal("1.250"),
    "Caldwell County": Decimal("2.500"),
    "Callaway County": Decimal("2.500"),
    "Camden County": Decimal("2.000"),
    "Carroll County": Decimal("2.000"),
    "Carter County": Decimal("1.500"),
    "Cass County": Decimal("1.625"),
    "Cedar County": Decimal("2.250"),
    "Chariton County": Decimal("2.000"),
    "Christian County": Decimal("1.750"),
    "Clark County": Decimal("3.000"),
    "Clay County": Decimal("1.250"),
    "Clinton County": Decimal("1.500"),
    "Cooper County": Decimal("2.000"),
    "Crawford County": Decimal("2.750"),
    "Dade County": Decimal("2.750"),
    "Dallas County": Decimal("2.500"),
    "Daviess County": Decimal("2.000"),
    "DeKalb County": Decimal("2.000"),
    "Dent County": Decimal("2.250"),
    "Douglas County": Decimal("2.000"),
    "Dunklin County": Decimal("1.688"),
    "Franklin County": Decimal("2.250"),
    "Gasconade County": Decimal("1.875"),
    "Gentry County": Decimal("1.500"),
    "Grundy County": Decimal("1.500"),
    "Harrison County": Decimal("1.250"),
    "Henry County": Decimal("1.700"),
    "Hickory County": Decimal("2.000"),
    "Holt County": Decimal("2.500"),
    "Howard County": Decimal("2.875"),
    "Howell County": Decimal("1.687"),
    "Iron County": Decimal("2.000"),
    "Jefferson County": Decimal("2.125"),
    "Johnson County": Decimal("3.250"),
    "Knox County": Decimal("2.500"),
    "Laclede County": Decimal("1.188"),
    "Lafayette County": Decimal("2.250"),
    "Lawrence County": Decimal("2.500"),
    "Lewis County": Decimal("3.125"),
    "Lincoln County": Decimal("2.750"),
    "Linn County": Decimal("2.250"),
    "Livingston County": Decimal("1.625"),
    "Macon County": Decimal("2.625"),
    "Madison County": Decimal("2.500"),
    "Maries County": Decimal("1.666"),
    "Marion County": Decimal("1.875"),
    "McDonald County": Decimal("2.000"),
    "Mercer County": Decimal("3.750"),
    "Miller County": Decimal("1.500"),
    "Mississippi County": Decimal("1.750"),
    "Moniteau County": Decimal("2.750"),
    "Monroe County": Decimal("1.500"),
    "Montgomery County": Decimal("2.250"),
    "Morgan County": Decimal("2.000"),
    "New Madrid County": Decimal("2.000"),
    "Newton County": Decimal("1.625"),
    "Nodaway County": Decimal("2.375"),
    "Oregon County": Decimal("2.000"),
    "Osage County": Decimal("2.750"),
    "Ozark County": Decimal("3.000"),
    "Pemiscot County": Decimal("3.000"),
    "Perry County": Decimal("2.375"),
    "Pettis County": Decimal("1.500"),
    "Phelps County": Decimal("1.125"),
    "Pike County": Decimal("3.062"),
    "Platte County": Decimal("1.250"),
    "Polk County": Decimal("1.375"),
    "Pulaski County": Decimal("1.750"),
    "Putnam County": Decimal("3.000"),
    "Ralls County": Decimal("2.150"),
    "Randolph County": Decimal("1.750"),
    "Ray County": Decimal("2.500"),
    "Reynolds County": Decimal("1.500"),
    "Ripley County": Decimal("1.500"),
    "Saline County": Decimal("2.000"),
    "Schuyler County": Decimal("2.000"),
    "Scotland County": Decimal("1.750"),
    "Scott County": Decimal("2.500"),
    "Shannon County": Decimal("1.500"),
    "Shelby County": Decimal("3.000"),
    "St. Clair County": Decimal("0.500"),
    "St. Francois County": Decimal("2.125"),
    "Ste. Genevieve County": Decimal("3.375"),
    "Stoddard County": Decimal("2.188"),
    "Stone County": Decimal("2.250"),
    "Sullivan County": Decimal("3.250"),
    "Texas County": Decimal("2.250"),
    "Vernon County": Decimal("1.000"),
    "Warren County": Decimal("2.750"),
    "Washington County": Decimal("2.500"),
    "Wayne County": Decimal("1.750"),
    "Webster County": Decimal("2.083"),
    "Worth County": Decimal("2.375"),
    "Wright County": Decimal("1.875"),
}

# Per-city general-retail city portion (NOT including state or county).
# Source: MO DOR 2026 rate tables + Avalara per-city pages.
# Each tuple: (county_name, city_rate_pct, [zip5s])
# St. Louis (city) is special: it's an independent city and the
# 5.454% all sits in the county-equivalent row, so its city_rate is 0.
MO_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    "Kansas City": (
        "Jackson County",
        Decimal("3.250"),
        # Kansas City core ZIPs in Jackson County (KS-side ZIPs are
        # 660xx and excluded). Some KCMO ZIPs straddle into Clay,
        # Platte, and Cass counties; the Jackson core is here and the
        # Clay-side / Platte-side KCMO portions live in separate
        # ``"Kansas City (Clay)"`` / ``"Kansas City (Platte)"``
        # entries below so the per-county county-rate math stays clean.
        (
            "64101",
            "64102",
            "64105",
            "64106",
            "64108",
            "64109",
            "64110",
            "64111",
            "64112",
            "64113",
            "64114",
            "64127",
            "64128",
            "64129",
            "64130",
            "64131",
            "64132",
            "64133",
            "64134",
            "64136",
            "64137",
            "64138",
            "64139",
            "64141",
            "64147",
        ),
    ),
    # iter-170: Kansas City extends into Clay County (the "Northland"
    # area east of the Missouri River). Per MO DOR rate tables 2026,
    # the Clay-side KCMO city rate is the same 3.25% as the Jackson
    # side, but the underlying county rate (Clay 1.25% vs Jackson
    # 1.5%) makes the combined rate 8.725% vs Jackson's 8.975%.
    # Modeling as a separate city authority keeps the per-county
    # rate math clean. ZIP 64116 is NOT included here -- that's
    # North Kansas City, a separate municipality with its own
    # different city rate.
    "Kansas City (Clay)": (
        "Clay County",
        Decimal("3.250"),
        (
            "64117",
            "64118",
            "64119",
        ),
    ),
    "St. Louis": (
        "St. Louis city",
        Decimal("0.000"),  # City rate folded into the independent-city county row
        # St. Louis city limits (independent city; not part of St. Louis County).
        (
            "63101",
            "63102",
            "63103",
            "63104",
            "63106",
            "63107",
            "63108",
            "63109",
            "63110",
            "63111",
            "63112",
            "63113",
            "63115",
            "63116",
            "63118",
            "63139",
        ),
    ),
    "Springfield": (
        "Greene County",
        Decimal("2.125"),
        ("65801", "65802", "65803", "65804", "65806", "65807", "65809", "65810"),
    ),
    "Independence": (
        "Jackson County",
        Decimal("2.875"),
        ("64050", "64052", "64053", "64054", "64055", "64056", "64057", "64058"),
    ),
    "Columbia": (
        "Boone County",
        Decimal("2.000"),
        ("65201", "65202", "65203"),
    ),
    "Lee's Summit": (
        "Jackson County",
        Decimal("2.750"),
        ("64063", "64064", "64081", "64082", "64086"),
    ),
    "O'Fallon": (
        "St. Charles County",
        Decimal("2.000"),
        ("63366", "63368"),
    ),
    "St. Joseph": (
        "Buchanan County",
        Decimal("3.875"),
        ("64501", "64503", "64504", "64505", "64506", "64507"),
    ),
    "St. Charles": (
        "St. Charles County",
        Decimal("2.000"),
        ("63301", "63303", "63304"),
    ),
    "St. Peters": (
        "St. Charles County",
        Decimal("2.000"),
        ("63376",),
    ),
    "Joplin": (
        "Jasper County",
        Decimal("3.125"),
        ("64801", "64804"),
    ),
    "Florissant": (
        "St. Louis County",
        Decimal("1.250"),
        ("63031", "63033", "63034"),
    ),
    "Chesterfield": (
        "St. Louis County",
        Decimal("1.000"),
        ("63005", "63017"),
    ),
    "Jefferson City": (
        "Cole County",
        Decimal("2.250"),
        ("65101", "65109"),
    ),
    "Cape Girardeau": (
        "Cape Girardeau County",
        Decimal("2.750"),
        ("63701", "63703"),
    ),
}


__all__ = [
    "MO_STATE_RATE_PCT",
    "MO_STATE_EFFECTIVE_FROM",
    "MO_COUNTY_RATE_PCT",
    "MO_CITIES",
]
