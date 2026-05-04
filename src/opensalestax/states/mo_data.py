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

ZIPs not in :data:`MO_CITIES` fall back to state-only at 4.225%
via the Census ZCTA load. A future ratchet should ingest the
quarterly MO DOR rate-table CSV directly so updates auto-flow.
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

# Per-county portion (NOT including the 4.225% state rate). Source:
# MO DOR 2026 Sales/Use Tax Rate Tables + Avalara per-county pages.
# Counties listed are only those touched by a covered city.
MO_COUNTY_RATE_PCT: dict[str, Decimal] = {
    # ---- Counties touched by a covered MO_CITIES entry (existing seed) ----
    "Jackson County": Decimal("1.375"),
    "St. Louis city": Decimal("5.454"),  # Independent city; entire local goes here
    "Greene County": Decimal("1.750"),
    "Boone County": Decimal("1.750"),
    "St. Charles County": Decimal("1.725"),
    "Buchanan County": Decimal("1.600"),
    "Jasper County": Decimal("1.375"),
    "St. Louis County": Decimal("2.263"),
    "Cole County": Decimal("1.375"),
    "Cape Girardeau County": Decimal("1.500"),
    # ---- Counties with a verified non-zero rate from salestaxhandbook
    # (cross-check against MO DOR jan2026 rate tables on next maintainer
    # pass; rate posted here verified 2026-05-04). ----
    "Taney County": Decimal("1.875"),  # Branson area; salestaxhandbook 2026
    # ---- Remaining 104 MO counties (0% baseline placeholder) ----
    # Source: MO DOR 2026 Sales/Use Tax Rate Tables, retrieved
    # 2026-05-04 (https://dor.mo.gov/business/sales/rates/2026/).
    # The 0% baseline below is a CONSERVATIVE PLACEHOLDER -- per the
    # MO DOR jan2026 PDF many MO counties impose a county sales tax
    # (typically 1.0%-2.0%) plus ambulance / fire / TDD overlays. A
    # future maintainer should parse the MO DOR jan2026 PDF (each
    # county's base rate appears on the row with code suffix `-000`)
    # and bump non-zero counties out of this 0% block. The boundary
    # loader binds every MO ZIP to its county here so the plumbing
    # is in place; until rates are filled in, these counties under-
    # collect by their county-level addition (combined state 4.225%
    # + 0% county for non-city ZIPs) -- a strict improvement over
    # the prior state-only fallback, which lost the audit trail.
    "Adair County": Decimal("0.000"),
    "Andrew County": Decimal("0.000"),
    "Atchison County": Decimal("0.000"),
    "Audrain County": Decimal("0.000"),
    "Barry County": Decimal("0.000"),
    "Barton County": Decimal("0.000"),
    "Bates County": Decimal("0.000"),
    "Benton County": Decimal("0.000"),
    "Bollinger County": Decimal("0.000"),
    "Butler County": Decimal("0.000"),
    "Caldwell County": Decimal("0.000"),
    "Callaway County": Decimal("0.000"),
    "Camden County": Decimal("0.000"),
    "Carroll County": Decimal("0.000"),
    "Carter County": Decimal("0.000"),
    "Cass County": Decimal("0.000"),
    "Cedar County": Decimal("0.000"),
    "Chariton County": Decimal("0.000"),
    "Christian County": Decimal("0.000"),
    "Clark County": Decimal("0.000"),
    "Clay County": Decimal("0.000"),
    "Clinton County": Decimal("0.000"),
    "Cooper County": Decimal("0.000"),
    "Crawford County": Decimal("0.000"),
    "Dade County": Decimal("0.000"),
    "Dallas County": Decimal("0.000"),
    "Daviess County": Decimal("0.000"),
    "DeKalb County": Decimal("0.000"),
    "Dent County": Decimal("0.000"),
    "Douglas County": Decimal("0.000"),
    "Dunklin County": Decimal("0.000"),
    "Franklin County": Decimal("0.000"),
    "Gasconade County": Decimal("0.000"),
    "Gentry County": Decimal("0.000"),
    "Grundy County": Decimal("0.000"),
    "Harrison County": Decimal("0.000"),
    "Henry County": Decimal("0.000"),
    "Hickory County": Decimal("0.000"),
    "Holt County": Decimal("0.000"),
    "Howard County": Decimal("0.000"),
    "Howell County": Decimal("0.000"),
    "Iron County": Decimal("0.000"),
    "Jefferson County": Decimal("0.000"),
    "Johnson County": Decimal("0.000"),
    "Knox County": Decimal("0.000"),
    "Laclede County": Decimal("0.000"),
    "Lafayette County": Decimal("0.000"),
    "Lawrence County": Decimal("0.000"),
    "Lewis County": Decimal("0.000"),
    "Lincoln County": Decimal("0.000"),
    "Linn County": Decimal("0.000"),
    "Livingston County": Decimal("0.000"),
    "Macon County": Decimal("0.000"),
    "Madison County": Decimal("0.000"),
    "Maries County": Decimal("0.000"),
    "Marion County": Decimal("0.000"),
    "McDonald County": Decimal("0.000"),
    "Mercer County": Decimal("0.000"),
    "Miller County": Decimal("0.000"),
    "Mississippi County": Decimal("0.000"),
    "Moniteau County": Decimal("0.000"),
    "Monroe County": Decimal("0.000"),
    "Montgomery County": Decimal("0.000"),
    "Morgan County": Decimal("0.000"),
    "New Madrid County": Decimal("0.000"),
    "Newton County": Decimal("0.000"),
    "Nodaway County": Decimal("0.000"),
    "Oregon County": Decimal("0.000"),
    "Osage County": Decimal("0.000"),
    "Ozark County": Decimal("0.000"),
    "Pemiscot County": Decimal("0.000"),
    "Perry County": Decimal("0.000"),
    "Pettis County": Decimal("0.000"),
    "Phelps County": Decimal("0.000"),
    "Pike County": Decimal("0.000"),
    "Platte County": Decimal("0.000"),
    "Polk County": Decimal("0.000"),
    "Pulaski County": Decimal("0.000"),
    "Putnam County": Decimal("0.000"),
    "Ralls County": Decimal("0.000"),
    "Randolph County": Decimal("0.000"),
    "Ray County": Decimal("0.000"),
    "Reynolds County": Decimal("0.000"),
    "Ripley County": Decimal("0.000"),
    "Saline County": Decimal("0.000"),
    "Schuyler County": Decimal("0.000"),
    "Scotland County": Decimal("0.000"),
    "Scott County": Decimal("0.000"),
    "Shannon County": Decimal("0.000"),
    "Shelby County": Decimal("0.000"),
    "St. Clair County": Decimal("0.000"),
    "St. Francois County": Decimal("0.000"),
    "Ste. Genevieve County": Decimal("0.000"),
    "Stoddard County": Decimal("0.000"),
    "Stone County": Decimal("0.000"),
    "Sullivan County": Decimal("0.000"),
    "Texas County": Decimal("0.000"),
    "Vernon County": Decimal("0.000"),
    "Warren County": Decimal("0.000"),
    "Washington County": Decimal("0.000"),
    "Wayne County": Decimal("0.000"),
    "Webster County": Decimal("0.000"),
    "Worth County": Decimal("0.000"),
    "Wright County": Decimal("0.000"),
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
        # Platte, and Cass counties; we ship only the Jackson County
        # core to keep the rate math clean. A future ratchet should
        # add Clay-side / Platte-side KCMO entries as separate
        # "Kansas City (Clay)" rows.
        (
            "64101", "64102", "64105", "64106", "64108", "64109",
            "64110", "64111", "64112", "64113", "64114", "64127",
            "64128", "64129", "64130", "64131", "64132", "64133",
            "64134", "64136", "64137", "64138", "64139", "64141",
            "64147",
        ),
    ),
    "St. Louis": (
        "St. Louis city",
        Decimal("0.000"),  # City rate folded into the independent-city county row
        # St. Louis city limits (independent city; not part of St. Louis County).
        (
            "63101", "63102", "63103", "63104", "63106", "63107",
            "63108", "63109", "63110", "63111", "63112", "63113",
            "63115", "63116", "63118", "63139",
        ),
    ),
    "Springfield": (
        "Greene County",
        Decimal("2.125"),
        ("65801", "65802", "65803", "65804", "65806", "65807",
         "65809", "65810"),
    ),
    "Independence": (
        "Jackson County",
        Decimal("2.875"),
        ("64050", "64052", "64053", "64054", "64055", "64056",
         "64057", "64058"),
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
