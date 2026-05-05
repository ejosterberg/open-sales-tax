# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""New York sales tax rate + boundary data (statewide + top-30 cities).

Source: New York State Department of Taxation and Finance,
Publication 718 "New York State Sales and Use Tax Rates by
Jurisdiction" (effective March 1, 2024 with subsequent quarterly
Pub 718-S updates), retrieved 2026-05-04 from
https://www.tax.ny.gov/pdf/publications/sales/pub718.pdf and
cross-checked against NY DTF Publication 718-A (rate-locator
tables) plus Avalara's per-city pages for NYC, Buffalo, and
Yonkers as a sanity check.

Architecture: New York's combined rate has up to four layers:

1. **State portion: 4.0%** (N.Y. Tax Law section 1105) -- the
   ``New York`` state authority.
2. **County portion** (varies, e.g. Erie 4.75%, Onondaga 4.0%,
   Westchester 3.0%, NYC's five "boroughs" each map to a county
   that shares the city's combined rate).
3. **Metropolitan Commuter Transportation District (MCTD):
   +0.375%** -- a regional surcharge collected by NY DTF on
   behalf of the MTA in 12 downstate counties (NYC's five plus
   Nassau, Suffolk, Westchester, Rockland, Dutchess, Orange,
   Putnam). Modeled as a ``district`` authority that sits under
   the state.
4. **City portion** (only a handful of NY cities impose their
   own sales tax: New York City 4.5%, Yonkers 1.5%, New Rochelle
   1.0%, Mount Vernon 1.0%, White Plains 1.0%; most "cities" in
   NY have NO city sales tax and use only the county rate).

NYC special case: the five boroughs of New York City are
themselves counties (Bronx County, Kings County [Brooklyn], New
York County [Manhattan], Queens County, Richmond County [Staten
Island]). All five share the same combined rate (8.875%) because
the city tax (4.5%) and MCTD (0.375%) are uniform across the
city. To keep the rate math clean we ship ONE city entry "New
York City" with county "New York County" (Manhattan); the ZIP
list covers all five boroughs. Borough-specific identification
is a future enhancement.

Cities seeded (top 30 by population; combined rates verified
against NY DTF Pub 718 on 2026-05-04):

- New York City (all 5 boroughs) -- 8.875%
- Buffalo (Erie Co.) -- 8.750%
- Yonkers (Westchester Co.) -- 8.875%
- Rochester (Monroe Co.) -- 8.000%
- Syracuse (Onondaga Co.) -- 8.000%
- Albany (Albany Co.) -- 8.000%
- New Rochelle (Westchester Co.) -- 8.375%
- Mount Vernon (Westchester Co.) -- 8.375%
- Schenectady (Schenectady Co.) -- 8.000%
- Utica (Oneida Co.) -- 8.750%
- White Plains (Westchester Co.) -- 8.375%
- Hempstead (Nassau Co.) -- 8.625%
- Troy (Rensselaer Co.) -- 8.000%
- Niagara Falls (Niagara Co.) -- 8.000%
- Binghamton (Broome Co.) -- 8.000%
- Freeport (Nassau Co.) -- 8.625%
- Long Beach (Nassau Co.) -- 8.625%
- Spring Valley (Rockland Co.) -- 8.375%
- Rome (Oneida Co.) -- 8.750%
- Levittown (Nassau Co.) -- 8.625%
- Valley Stream (Nassau Co.) -- 8.625%
- Brentwood (Suffolk Co.) -- 8.625%
- West Babylon (Suffolk Co.) -- 8.625%
- North Hempstead (Nassau Co.) -- 8.625%
- Cheektowaga (Erie Co.) -- 8.750%
- Tonawanda (Erie Co.) -- 8.750%
- Irondequoit (Monroe Co.) -- 8.000%
- Ramapo (Rockland Co.) -- 8.375%
- Greece (Monroe Co.) -- 8.000%
- Brookhaven (Suffolk Co.) -- 8.625%

ZIPs not in :data:`NY_CITIES` fall back to state-only at 4.0%
via the Census ZCTA load. This is an under-collection for any
upstate ZIP that should pick up its county's local rate; a
future ratchet should iterate Census ZCTA->county data for all
62 NY counties to pick up the county portion (and the MCTD
surcharge in the 12 MCTD counties) for every NY ZIP, not just
the 30 cities seeded here. Special-purpose districts (Hudson
Yards, etc.) and city-specific TPT-style overlays are NOT
modeled in v0.26.

NOT modeled in v0.26:

- The N.Y. Tax Law section 1115(a)(30) clothing-and-footwear
  state-portion exemption for items <$110 (the existing
  ``threshold_semantic="below_exempt"`` taxability rule in
  :mod:`new_york` already encodes this at the state level; the
  MCTD and per-locality re-imposition behavior described in
  NY DTF Publication 718-C lands when the threshold-rule engine
  expands to per-authority overrides).
- NYC borough-specific identification (all five boroughs share
  the 8.875% combined rate so the engine answer is correct;
  receipt-line borough labels are a future enhancement).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State combined rate -- 4.0% has been stable since June 1, 2005 when
# the temporary 0.25% increase added in 2003 expired and the rate
# returned to 4.0% (N.Y. Tax Law section 1105).
NY_STATE_RATE_PCT = Decimal("4.000")
NY_STATE_EFFECTIVE_FROM = dt.date(2005, 6, 1)

# Metropolitan Commuter Transportation District surcharge: 0.375%
# (N.Y. Tax Law section 1109). Collected by NY DTF on behalf of the
# MTA in the 12 MCTD counties. Modeled as a single district authority
# named "Metropolitan Commuter Transportation District".
NY_MCTD_RATE = Decimal("0.375")
NY_MCTD_DISTRICT_NAME = "Metropolitan Commuter Transportation District"

# The 12 counties where MCTD applies. Source: NY DTF Pub 718.
NY_MCTD_COUNTIES: frozenset[str] = frozenset(
    {
        # NYC's five boroughs (each its own county)
        "Bronx County",
        "Kings County",  # Brooklyn
        "New York County",  # Manhattan
        "Queens County",
        "Richmond County",  # Staten Island
        # Long Island
        "Nassau County",
        "Suffolk County",
        # Lower Hudson Valley
        "Westchester County",
        "Rockland County",
        # Mid-Hudson Valley
        "Dutchess County",
        "Orange County",
        "Putnam County",
    }
)

# Per-county portion (NOT including the 4% state rate or the 0.375%
# MCTD surcharge). Source: NY DTF Publication 718 (effective March 1,
# 2025), retrieved 2026-05-04 from
# https://www.tax.ny.gov/pdf/publications/sales/pub718.pdf.
#
# Coverage extended in this ratchet to ALL 62 NY counties (previously
# 14) so the ZIP_COUNTY-driven boundary loader can resolve every NY
# ZIP -- not just the ones in the top-30 city seed -- to the correct
# county portion plus the MCTD 0.375% surcharge in the 12 MCTD
# counties.
#
# Per-county rate derivation: combined Pub 718 rate minus the 4.0%
# state rate, minus the 0.375% MCTD surcharge for MCTD counties. For
# the four Westchester cities that file their own returns (Mount
# Vernon, New Rochelle, White Plains, Yonkers), the city rate is
# encoded as the city authority on top of a 3.0% Westchester county
# rate -- this preserves the existing combined-rate math for the four
# city ZIPs (e.g., Yonkers 4 + 3 + 0.375 MCTD + 1.5 city = 8.875%)
# but means non-city Westchester ZIPs under-collect by 1.0% relative
# to Pub 718 (8.375% combined) until a future ratchet expands the
# city/county model to handle Westchester's "instead-of" allocation.
NY_COUNTY_RATE_PCT: dict[str, Decimal] = {
    # ---- Counties with covered cities (existing seed; preserved) ----
    # NYC's five boroughs all use 0% county portion -- the local tax
    # is collected as the city portion (NYC 4.5%) plus MCTD 0.375%.
    # We use New York County (Manhattan) as the canonical county for
    # the consolidated "New York City" entry; the other four boroughs
    # share the same combined rate via the city entry.
    "Bronx County": Decimal("0.000"),
    "Kings County": Decimal("0.000"),
    "New York County": Decimal("0.000"),
    "Queens County": Decimal("0.000"),
    "Richmond County": Decimal("0.000"),
    # Upstate / non-NYC counties touched by covered cities
    "Erie County": Decimal("4.750"),
    "Monroe County": Decimal("4.000"),
    "Onondaga County": Decimal("4.000"),
    "Albany County": Decimal("4.000"),
    "Westchester County": Decimal("3.000"),  # cities Yonkers, NR, Mt. V, WP add city tax
    "Schenectady County": Decimal("4.000"),
    "Oneida County": Decimal("4.750"),
    "Nassau County": Decimal("4.250"),
    "Rensselaer County": Decimal("4.000"),
    "Niagara County": Decimal("4.000"),
    "Broome County": Decimal("4.000"),
    "Rockland County": Decimal("4.000"),
    "Suffolk County": Decimal("4.250"),
    # ---- Remaining 43 counties from NY DTF Pub 718 (March 1, 2025) ----
    # All combined rates verified against Pub 718; per-county rate is
    # combined - 4% state - 0.375% MCTD (for MCTD counties only).
    "Allegany County": Decimal("4.500"),  # combined 8.5%
    "Cattaraugus County": Decimal("4.000"),  # combined 8% (Olean/Salamanca city codes share rate)
    "Cayuga County": Decimal("4.000"),  # combined 8% (Auburn city code shares rate)
    "Chautauqua County": Decimal("4.000"),  # combined 8%
    "Chemung County": Decimal("4.000"),  # combined 8%
    "Chenango County": Decimal("4.000"),  # combined 8% (Norwich city code shares rate)
    "Clinton County": Decimal("4.000"),  # combined 8%
    "Columbia County": Decimal("4.000"),  # combined 8%
    "Cortland County": Decimal("4.000"),  # combined 8%
    "Delaware County": Decimal("4.000"),  # combined 8%
    "Dutchess County": Decimal("3.750"),  # combined 8.125% (MCTD); 8.125 - 4 - 0.375 = 3.75
    "Essex County": Decimal("4.000"),  # combined 8%
    "Franklin County": Decimal("4.000"),  # combined 8%
    "Fulton County": Decimal("4.000"),  # combined 8%
    "Genesee County": Decimal("4.000"),  # combined 8%
    "Greene County": Decimal("4.000"),  # combined 8%
    "Hamilton County": Decimal("4.000"),  # combined 8%
    "Herkimer County": Decimal("4.250"),  # combined 8.25%
    "Jefferson County": Decimal("4.000"),  # combined 8%
    "Lewis County": Decimal("4.000"),  # combined 8%
    "Livingston County": Decimal("4.000"),  # combined 8%
    "Madison County": Decimal("4.000"),  # combined 8% (Oneida city code shares rate)
    "Montgomery County": Decimal("4.000"),  # combined 8%
    "Ontario County": Decimal("3.500"),  # combined 7.5%
    "Orange County": Decimal("3.750"),  # combined 8.125% (MCTD); 8.125 - 4 - 0.375 = 3.75
    "Orleans County": Decimal("4.000"),  # combined 8%
    "Oswego County": Decimal("4.000"),  # combined 8% (Oswego city code shares rate)
    "Otsego County": Decimal("4.000"),  # combined 8%
    "Putnam County": Decimal("4.000"),  # combined 8.375% (MCTD); 8.375 - 4 - 0.375 = 4
    "St. Lawrence County": Decimal("4.000"),  # combined 8% (Ogdensburg city code shares rate)
    "Saratoga County": Decimal("3.000"),  # combined 7% (Saratoga Springs city code shares rate)
    "Schoharie County": Decimal("4.000"),  # combined 8%
    "Schuyler County": Decimal("4.000"),  # combined 8%
    "Seneca County": Decimal("4.000"),  # combined 8%
    "Steuben County": Decimal("4.000"),  # combined 8%
    "Sullivan County": Decimal("4.000"),  # combined 8%
    "Tioga County": Decimal("4.000"),  # combined 8%
    "Tompkins County": Decimal("4.000"),  # combined 8% (Ithaca city code shares rate)
    "Ulster County": Decimal("4.000"),  # combined 8%
    "Warren County": Decimal("3.000"),  # combined 7% (Glens Falls city code shares rate)
    "Washington County": Decimal("3.000"),  # combined 7%
    "Wayne County": Decimal("4.000"),  # combined 8%
    "Wyoming County": Decimal("4.000"),  # combined 8%
    "Yates County": Decimal("4.000"),  # combined 8%
}

# Per-city seed. Tuple shape:
#   (county_name, city_rate_pct, [zip5s])
# - county_name is what shows up as the parent_authority_name on
#   the city RateRow and the county BoundaryRow target.
# - city_rate_pct is the city portion ONLY (not including state,
#   county, or MCTD). For most NY "cities" this is 0%; only NYC
#   (4.5%), Yonkers (1.5%), and the three small Westchester cities
#   (1.0% each) impose their own sales tax.
# - The zips are the primary delivery ZIPs for each city's
#   centroid. NYC's tuple covers all five boroughs.
NY_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    # ---- New York City -- 8.875% (4 + 4.5 + 0.375 MCTD; 0% county) ----
    # All 5 boroughs share the combined rate. The county is shown as
    # New York County (Manhattan) for the consolidated entry; ZIPs
    # cover Manhattan (100xx, 101xx, 102xx), Bronx (104xx),
    # Brooklyn (112xx), Queens (110xx, 111xx, 113xx, 114xx, 116xx),
    # and Staten Island (103xx).
    "New York City": (
        "New York County",
        Decimal("4.500"),
        (
            # Manhattan (New York County) -- 100xx, 101xx, 102xx
            "10001",
            "10002",
            "10003",
            "10004",
            "10005",
            "10006",
            "10007",
            "10009",
            "10010",
            "10011",
            "10012",
            "10013",
            "10014",
            "10016",
            "10017",
            "10018",
            "10019",
            "10020",
            "10021",
            "10022",
            "10023",
            "10024",
            "10025",
            "10026",
            "10027",
            "10028",
            "10029",
            "10030",
            "10031",
            "10032",
            "10033",
            "10034",
            "10035",
            "10036",
            "10037",
            "10038",
            "10039",
            "10040",
            "10044",
            "10065",
            "10075",
            "10128",
            "10280",
            "10282",
            # Bronx (Bronx County) -- 104xx
            "10451",
            "10452",
            "10453",
            "10454",
            "10455",
            "10456",
            "10457",
            "10458",
            "10459",
            "10460",
            "10461",
            "10462",
            "10463",
            "10464",
            "10465",
            "10466",
            "10467",
            "10468",
            "10469",
            "10470",
            "10471",
            "10472",
            "10473",
            "10474",
            "10475",
            # Staten Island (Richmond County) -- 103xx
            "10301",
            "10302",
            "10303",
            "10304",
            "10305",
            "10306",
            "10307",
            "10308",
            "10309",
            "10310",
            "10311",
            "10312",
            "10314",
            # Brooklyn (Kings County) -- 112xx
            "11201",
            "11203",
            "11204",
            "11205",
            "11206",
            "11207",
            "11208",
            "11209",
            "11210",
            "11211",
            "11212",
            "11213",
            "11214",
            "11215",
            "11216",
            "11217",
            "11218",
            "11219",
            "11220",
            "11221",
            "11222",
            "11223",
            "11224",
            "11225",
            "11226",
            "11228",
            "11229",
            "11230",
            "11231",
            "11232",
            "11233",
            "11234",
            "11235",
            "11236",
            "11237",
            "11238",
            "11239",
            "11249",
            # Queens (Queens County) -- 110xx, 111xx, 113xx, 114xx, 116xx
            "11004",
            "11005",
            "11101",
            "11102",
            "11103",
            "11104",
            "11105",
            "11106",
            "11354",
            "11355",
            "11356",
            "11357",
            "11358",
            "11360",
            "11361",
            "11362",
            "11363",
            "11364",
            "11365",
            "11366",
            "11367",
            "11368",
            "11369",
            "11370",
            "11371",
            "11372",
            "11373",
            "11374",
            "11375",
            "11377",
            "11378",
            "11379",
            "11385",
            "11411",
            "11412",
            "11413",
            "11414",
            "11415",
            "11416",
            "11417",
            "11418",
            "11419",
            "11420",
            "11421",
            "11422",
            "11423",
            "11426",
            "11427",
            "11428",
            "11429",
            "11432",
            "11433",
            "11434",
            "11435",
            "11436",
            "11691",
            "11692",
            "11693",
            "11694",
            "11697",
        ),
    ),
    # ---- Buffalo -- 8.750% (4 + 4.75 Erie; no MCTD, no city tax) ----
    "Buffalo": (
        "Erie County",
        Decimal("0.000"),
        (
            "14201",
            "14202",
            "14203",
            "14204",
            "14206",
            "14207",
            "14208",
            "14209",
            "14210",
            "14211",
            "14212",
            "14213",
            "14214",
            "14215",
            "14216",
            "14217",
            "14218",
            "14219",
            "14220",
            "14222",
        ),
    ),
    # ---- Rochester -- 8.000% (4 + 4 Monroe; no MCTD, no city tax) ----
    "Rochester": (
        "Monroe County",
        Decimal("0.000"),
        (
            "14604",
            "14605",
            "14606",
            "14607",
            "14608",
            "14609",
            "14610",
            "14611",
            "14612",
            "14613",
            "14614",
            "14615",
            "14616",
            "14617",
            "14618",
            "14619",
            "14620",
            "14621",
            "14623",
            "14624",
            "14625",
        ),
    ),
    # ---- Yonkers -- 8.875% (4 + 3 Westchester + 0.375 MCTD + 1.5 city) ----
    "Yonkers": (
        "Westchester County",
        Decimal("1.500"),
        ("10701", "10702", "10703", "10704", "10705", "10706", "10707", "10710"),
    ),
    # ---- Syracuse -- 8.000% (4 + 4 Onondaga; no MCTD, no city tax) ----
    "Syracuse": (
        "Onondaga County",
        Decimal("0.000"),
        (
            "13202",
            "13203",
            "13204",
            "13205",
            "13206",
            "13207",
            "13208",
            "13210",
            "13219",
            "13224",
        ),
    ),
    # ---- Albany -- 8.000% (4 + 4 Albany; no MCTD, no city tax) ----
    "Albany": (
        "Albany County",
        Decimal("0.000"),
        ("12202", "12203", "12204", "12205", "12206", "12207", "12208", "12209", "12210"),
    ),
    # ---- New Rochelle -- 8.375% (4 + 3 Westchester + 0.375 MCTD + 1 city) ----
    "New Rochelle": (
        "Westchester County",
        Decimal("1.000"),
        ("10801", "10804", "10805"),
    ),
    # ---- Mount Vernon -- 8.375% (4 + 3 Westchester + 0.375 MCTD + 1 city) ----
    "Mount Vernon": (
        "Westchester County",
        Decimal("1.000"),
        ("10550", "10552", "10553"),
    ),
    # ---- Schenectady -- 8.000% (4 + 4 Schenectady; no MCTD, no city tax) ----
    "Schenectady": (
        "Schenectady County",
        Decimal("0.000"),
        ("12302", "12303", "12304", "12305", "12306", "12307", "12308", "12309"),
    ),
    # ---- Utica -- 8.750% (4 + 4.75 Oneida; no MCTD, no city tax) ----
    "Utica": (
        "Oneida County",
        Decimal("0.000"),
        ("13501", "13502", "13503"),
    ),
    # ---- White Plains -- 8.375% (4 + 3 Westchester + 0.375 MCTD + 1 city) ----
    "White Plains": (
        "Westchester County",
        Decimal("1.000"),
        ("10601", "10603", "10604", "10605", "10606", "10607"),
    ),
    # ---- Hempstead -- 8.625% (4 + 4.25 Nassau + 0.375 MCTD; no city tax) ----
    # The Town/Village of Hempstead has no separate city sales tax;
    # combined rate is the Nassau County total.
    "Hempstead": (
        "Nassau County",
        Decimal("0.000"),
        ("11549", "11550", "11551", "11552", "11553", "11554", "11556"),
    ),
    # ---- Troy -- 8.000% (4 + 4 Rensselaer; no MCTD, no city tax) ----
    "Troy": (
        "Rensselaer County",
        Decimal("0.000"),
        ("12180", "12181", "12182"),
    ),
    # ---- Niagara Falls -- 8.000% (4 + 4 Niagara; no MCTD, no city tax) ----
    "Niagara Falls": (
        "Niagara County",
        Decimal("0.000"),
        ("14301", "14302", "14303", "14304", "14305"),
    ),
    # ---- Binghamton -- 8.000% (4 + 4 Broome; no MCTD, no city tax) ----
    "Binghamton": (
        "Broome County",
        Decimal("0.000"),
        ("13901", "13902", "13903", "13904", "13905"),
    ),
    # ---- Freeport -- 8.625% (4 + 4.25 Nassau + 0.375 MCTD; no city tax) ----
    "Freeport": (
        "Nassau County",
        Decimal("0.000"),
        ("11520",),
    ),
    # ---- Long Beach -- 8.625% (4 + 4.25 Nassau + 0.375 MCTD; no city tax) ----
    "Long Beach": (
        "Nassau County",
        Decimal("0.000"),
        ("11561",),
    ),
    # ---- Spring Valley -- 8.375% (4 + 4 Rockland + 0.375 MCTD; no city tax) ----
    "Spring Valley": (
        "Rockland County",
        Decimal("0.000"),
        ("10977",),
    ),
    # ---- Rome -- 8.750% (4 + 4.75 Oneida; no MCTD, no city tax) ----
    "Rome": (
        "Oneida County",
        Decimal("0.000"),
        ("13440", "13441", "13442"),
    ),
    # ---- Levittown -- 8.625% (4 + 4.25 Nassau + 0.375 MCTD; no city tax) ----
    "Levittown": (
        "Nassau County",
        Decimal("0.000"),
        ("11756",),
    ),
    # ---- Valley Stream -- 8.625% (4 + 4.25 Nassau + 0.375 MCTD) ----
    "Valley Stream": (
        "Nassau County",
        Decimal("0.000"),
        ("11580", "11581", "11582"),
    ),
    # ---- Brentwood -- 8.625% (4 + 4.25 Suffolk + 0.375 MCTD; no city tax) ----
    "Brentwood": (
        "Suffolk County",
        Decimal("0.000"),
        ("11717",),
    ),
    # ---- West Babylon -- 8.625% (4 + 4.25 Suffolk + 0.375 MCTD) ----
    "West Babylon": (
        "Suffolk County",
        Decimal("0.000"),
        ("11704",),
    ),
    # ---- North Hempstead -- 8.625% (4 + 4.25 Nassau + 0.375 MCTD) ----
    # Town of North Hempstead -- no separate city sales tax.
    "North Hempstead": (
        "Nassau County",
        Decimal("0.000"),
        ("11030", "11040", "11042", "11050", "11576"),
    ),
    # ---- Cheektowaga -- 8.750% (4 + 4.75 Erie; no MCTD, no city tax) ----
    "Cheektowaga": (
        "Erie County",
        Decimal("0.000"),
        ("14225", "14227"),
    ),
    # ---- Tonawanda -- 8.750% (4 + 4.75 Erie; no MCTD, no city tax) ----
    "Tonawanda": (
        "Erie County",
        Decimal("0.000"),
        ("14150", "14223"),
    ),
    # ---- Irondequoit -- 8.000% (4 + 4 Monroe; no MCTD, no city tax) ----
    "Irondequoit": (
        "Monroe County",
        Decimal("0.000"),
        ("14617", "14622"),
    ),
    # ---- Ramapo -- 8.375% (4 + 4 Rockland + 0.375 MCTD; no city tax) ----
    "Ramapo": (
        "Rockland County",
        Decimal("0.000"),
        ("10952", "10901"),
    ),
    # ---- Greece -- 8.000% (4 + 4 Monroe; no MCTD, no city tax) ----
    "Greece": (
        "Monroe County",
        Decimal("0.000"),
        ("14615", "14626"),
    ),
    # ---- Brookhaven -- 8.625% (4 + 4.25 Suffolk + 0.375 MCTD) ----
    # Town of Brookhaven covers many ZIPs across central Suffolk;
    # we seed the most common centroid ZIPs.
    "Brookhaven": (
        "Suffolk County",
        Decimal("0.000"),
        ("11719", "11720", "11772", "11776", "11779", "11790"),
    ),
}


__all__ = [
    "NY_STATE_RATE_PCT",
    "NY_STATE_EFFECTIVE_FROM",
    "NY_MCTD_RATE",
    "NY_MCTD_DISTRICT_NAME",
    "NY_MCTD_COUNTIES",
    "NY_COUNTY_RATE_PCT",
    "NY_CITIES",
]
