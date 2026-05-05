# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Pennsylvania sales tax rate + boundary data.

Source: Pennsylvania Department of Revenue published rate schedule
(https://revenue.pa.gov/Pages/Sales-Use-Tax.aspx) and the underlying
statutes:

- **Statewide 6.0%** -- 72 P.S. section 7202(a) (Tax Reform Code of
  1971, sales-and-use tax base rate).
- **Allegheny County +1.0%** local sales tax -- 72 P.S. section 7202
  (a) authorizing-and-rate provisions for Allegheny County (the
  "Regional Asset District" 1% local levy enacted by Allegheny County
  in 1994).
- **City/County of Philadelphia +2.0%** local sales tax -- 72 P.S.
  section 7202(b) (the Philadelphia 2% local sales-and-use tax,
  raised from 1% to 2% effective 2009-10-08; cross-referenced in
  61 Pa. Code section 60.16). Philadelphia City and Philadelphia
  County are coterminous; this 2% functions as both the city tax
  and the county tax.

Cross-checked 2026-05-04 against publicly accessible per-city pages
that list combined Pennsylvania sales-tax rates (Philadelphia 8.0%,
Pittsburgh 7.0%, all other major PA cities 6.0%).

Architecture: Pennsylvania's combined rate has just two modeled
layers:

1. **State portion: 6.0%** (72 P.S. section 7202(a))
2. **County portion** (0% in 65 of 67 counties; 1% in Allegheny;
   2% in Philadelphia)

Per the implementation choice documented in the agent brief, the
Philadelphia 2% is encoded as the **county** rate for Philadelphia
County (since the city and county are coterminous in PA; the City
of Philadelphia *is* Philadelphia County under the 1854 Act of
Consolidation), and Allegheny's 1% is the county rate for Allegheny
County. Every PA city is then emitted with a 0% city rate -- the
city authority is purely a friendly anchor for per-ZIP boundary
lookup. This avoids the "is it a county tax or city tax" question
and matches how PA filers experience it: there is exactly ONE local
sales tax line on a Philadelphia or Pittsburgh receipt, never two.

Cities seeded (top 15 by population):

- Philadelphia (Philadelphia Co.) -- 8.000% (state 6% + county 2%)
- Pittsburgh (Allegheny Co.) -- 7.000% (state 6% + county 1%)
- Allentown (Lehigh Co.) -- 6.000%
- Erie (Erie Co.) -- 6.000%
- Reading (Berks Co.) -- 6.000%
- Scranton (Lackawanna Co.) -- 6.000%
- Bethlehem (Northampton Co.) -- 6.000%
- Lancaster (Lancaster Co.) -- 6.000%
- Harrisburg (Dauphin Co.) -- 6.000%
- York (York Co.) -- 6.000%
- Altoona (Blair Co.) -- 6.000%
- State College (Centre Co.) -- 6.000%
- Wilkes-Barre (Luzerne Co.) -- 6.000%
- Chester (Delaware Co.) -- 6.000%
- Norristown (Montgomery Co.) -- 6.000%

ZIPs not in :data:`PA_CITIES` fall back to state-only at 6.000%
via the Census ZCTA load. This is correct everywhere outside
Allegheny County and Philadelphia County. A future ratchet should
expand to ZIPs in Allegheny County beyond the City of Pittsburgh
proper (e.g., suburban municipalities such as Monroeville, Bethel
Park, McKeesport) so they pick up the +1.0% Allegheny county tax.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State combined rate -- 6.0% has been the PA sales-tax base rate
# since 1968-03-01 (Act of March 4, 1971, P.L. 6, No. 2 -- Tax
# Reform Code of 1971, section 202; the 6% rate itself was set by
# earlier amendments to the prior Selective Sales and Use Tax Act).
PA_STATE_RATE_PCT = Decimal("6.000")
PA_STATE_EFFECTIVE_FROM = dt.date(1968, 3, 1)

# Per-county portion (NOT including the 6.0% state rate). All 67
# Pennsylvania counties are listed for completeness; only Allegheny
# (1.0%) and Philadelphia (2.0%) carry a local tax. The other 65
# counties are explicitly listed at 0.000% so a future maintainer
# adding a ZIP for a no-tax county doesn't have to wonder whether
# the omission is a bug or a deliberate "no local tax" signal.
PA_COUNTY_RATE_PCT: dict[str, Decimal] = {
    "Adams County": Decimal("0.000"),
    "Allegheny County": Decimal("1.000"),
    "Armstrong County": Decimal("0.000"),
    "Beaver County": Decimal("0.000"),
    "Bedford County": Decimal("0.000"),
    "Berks County": Decimal("0.000"),
    "Blair County": Decimal("0.000"),
    "Bradford County": Decimal("0.000"),
    "Bucks County": Decimal("0.000"),
    "Butler County": Decimal("0.000"),
    "Cambria County": Decimal("0.000"),
    "Cameron County": Decimal("0.000"),
    "Carbon County": Decimal("0.000"),
    "Centre County": Decimal("0.000"),
    "Chester County": Decimal("0.000"),
    "Clarion County": Decimal("0.000"),
    "Clearfield County": Decimal("0.000"),
    "Clinton County": Decimal("0.000"),
    "Columbia County": Decimal("0.000"),
    "Crawford County": Decimal("0.000"),
    "Cumberland County": Decimal("0.000"),
    "Dauphin County": Decimal("0.000"),
    "Delaware County": Decimal("0.000"),
    "Elk County": Decimal("0.000"),
    "Erie County": Decimal("0.000"),
    "Fayette County": Decimal("0.000"),
    "Forest County": Decimal("0.000"),
    "Franklin County": Decimal("0.000"),
    "Fulton County": Decimal("0.000"),
    "Greene County": Decimal("0.000"),
    "Huntingdon County": Decimal("0.000"),
    "Indiana County": Decimal("0.000"),
    "Jefferson County": Decimal("0.000"),
    "Juniata County": Decimal("0.000"),
    "Lackawanna County": Decimal("0.000"),
    "Lancaster County": Decimal("0.000"),
    "Lawrence County": Decimal("0.000"),
    "Lebanon County": Decimal("0.000"),
    "Lehigh County": Decimal("0.000"),
    "Luzerne County": Decimal("0.000"),
    "Lycoming County": Decimal("0.000"),
    "McKean County": Decimal("0.000"),
    "Mercer County": Decimal("0.000"),
    "Mifflin County": Decimal("0.000"),
    "Monroe County": Decimal("0.000"),
    "Montgomery County": Decimal("0.000"),
    "Montour County": Decimal("0.000"),
    "Northampton County": Decimal("0.000"),
    "Northumberland County": Decimal("0.000"),
    "Perry County": Decimal("0.000"),
    "Philadelphia County": Decimal("2.000"),
    "Pike County": Decimal("0.000"),
    "Potter County": Decimal("0.000"),
    "Schuylkill County": Decimal("0.000"),
    "Snyder County": Decimal("0.000"),
    "Somerset County": Decimal("0.000"),
    "Sullivan County": Decimal("0.000"),
    "Susquehanna County": Decimal("0.000"),
    "Tioga County": Decimal("0.000"),
    "Union County": Decimal("0.000"),
    "Venango County": Decimal("0.000"),
    "Warren County": Decimal("0.000"),
    "Washington County": Decimal("0.000"),
    "Wayne County": Decimal("0.000"),
    "Westmoreland County": Decimal("0.000"),
    "Wyoming County": Decimal("0.000"),
    "York County": Decimal("0.000"),
}

# Per-city seed (top 15 PA cities by population). Tuple shape:
#   (county_name, city_rate_pct, [zip5s])
#
# city_rate_pct is 0.000 for EVERY PA city -- the local tax (where
# it exists) is encoded as the county rate per the implementation
# choice documented in the module docstring. The city authority is
# emitted purely as a friendly per-ZIP anchor; combined rate at any
# covered ZIP is state 6% + county (0%/1%/2%) + city 0%.
#
# ZIPs are the primary delivery ZIPs for each city's centroid.
PA_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    # ---- Allegheny County (+1.0% -> 7.0%) ----
    "Pittsburgh": (
        "Allegheny County",
        Decimal("0.000"),
        (
            "15201",
            "15203",
            "15206",
            "15208",
            "15210",
            "15211",
            "15212",
            "15213",
            "15214",
            "15215",
            "15217",
            "15219",
            "15220",
            "15222",
            "15224",
            "15226",
            "15232",
            "15233",
        ),
    ),
    # ---- Philadelphia County (+2.0% -> 8.0%) ----
    "Philadelphia": (
        "Philadelphia County",
        Decimal("0.000"),
        (
            "19102",
            "19103",
            "19104",
            "19106",
            "19107",
            "19111",
            "19114",
            "19115",
            "19116",
            "19118",
            "19119",
            "19120",
            "19121",
            "19122",
            "19123",
            "19124",
            "19125",
            "19126",
            "19127",
            "19128",
            "19129",
            "19130",
            "19131",
            "19132",
            "19133",
            "19134",
            "19135",
            "19136",
            "19137",
            "19138",
            "19139",
            "19140",
            "19141",
            "19142",
            "19143",
            "19144",
            "19145",
            "19146",
            "19147",
            "19148",
            "19149",
            "19150",
            "19151",
            "19152",
            "19153",
            "19154",
        ),
    ),
    # ---- No local tax (-> 6.0%) ----
    "Allentown": (
        "Lehigh County",
        Decimal("0.000"),
        ("18101", "18102", "18103", "18104", "18109"),
    ),
    "Erie": (
        "Erie County",
        Decimal("0.000"),
        (
            "16501",
            "16502",
            "16503",
            "16504",
            "16505",
            "16506",
            "16507",
            "16508",
            "16509",
            "16510",
            "16511",
        ),
    ),
    "Reading": (
        "Berks County",
        Decimal("0.000"),
        ("19601", "19602", "19604", "19605", "19606", "19607", "19611"),
    ),
    "Scranton": (
        "Lackawanna County",
        Decimal("0.000"),
        ("18503", "18504", "18505", "18508", "18509", "18510", "18512"),
    ),
    "Bethlehem": (
        "Northampton County",
        Decimal("0.000"),
        # Bethlehem straddles Northampton + Lehigh counties; we ship
        # only the Northampton-side ZIPs here. Both counties are at
        # 0.000% local so the combined rate is identical (6.000%).
        ("18015", "18017", "18018", "18020"),
    ),
    "Lancaster": (
        "Lancaster County",
        Decimal("0.000"),
        ("17602", "17603", "17604"),
    ),
    "Harrisburg": (
        "Dauphin County",
        Decimal("0.000"),
        ("17101", "17102", "17103", "17104", "17109", "17110", "17111", "17112"),
    ),
    "York": (
        "York County",
        Decimal("0.000"),
        ("17401", "17402", "17403", "17404", "17406", "17408"),
    ),
    "Altoona": (
        "Blair County",
        Decimal("0.000"),
        ("16601", "16602", "16603"),
    ),
    "State College": (
        "Centre County",
        Decimal("0.000"),
        ("16801", "16802", "16803"),
    ),
    "Wilkes-Barre": (
        "Luzerne County",
        Decimal("0.000"),
        ("18701", "18702", "18703", "18704", "18705", "18706"),
    ),
    "Chester": (
        "Delaware County",
        Decimal("0.000"),
        ("19013", "19014", "19015"),
    ),
    "Norristown": (
        "Montgomery County",
        Decimal("0.000"),
        ("19401", "19403"),
    ),
}


__all__ = [
    "PA_STATE_RATE_PCT",
    "PA_STATE_EFFECTIVE_FROM",
    "PA_COUNTY_RATE_PCT",
    "PA_CITIES",
]
