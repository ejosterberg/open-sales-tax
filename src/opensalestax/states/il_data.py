# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Illinois sales tax rate + boundary data (top-20-city coverage).

Source: Illinois Department of Revenue (IDOR) "Tax Rate Database" /
"Sales & Use Tax Rates" publications and the IDOR Tax Rate Finder
at https://mytax.illinois.gov/_/. Each city's combined rate
cross-checked against Avalara per-city pages
(https://www.avalara.com/taxrates/en/state-rates/illinois/) on
**2026-05-04**.

Architecture: Illinois's combined general-merchandise rate has up
to four modeled layers:

1. **State portion: 6.25%** (35 ILCS 120/2-10) -- the ``Illinois``
   state authority.
2. **County portion** (35 ILCS 200/, county school facility taxes,
   county public safety taxes, etc.) -- ALL 102 IL counties are now
   seeded from the IDOR machine-readable rate file (extraction
   script: :file:`scripts/extract_il_county_rates.py`). About 75
   counties carry a real county-level tax (typically 0.25%-2.0%);
   the rest are verified-0% and tagged as such inline. The IDOR
   ordmache file ships every Jan 1 / Jul 1 when rates change.
3. **Regional Transportation Authority (RTA) district** (70 ILCS
   3615/4.03) -- a single district authority with a per-county
   rate that varies by county within its six-county service area:

   - **Cook County: 1.00%**
   - **DuPage, Kane, Lake, McHenry, Will counties: 0.75%**

   Modeled here as TWO district authorities -- ``RTA Cook`` and
   ``RTA Collar`` -- bound to cities by their county's RTA tier.
   This mirrors how the engine's ``district`` authority type works
   (one rate per authority).
4. **City / home-rule portion** (Illinois Const. art. VII, sec. 6)
   -- Illinois municipalities with home-rule status (population
   greater than 25,000 or by referendum) may impose their own
   sales tax in 0.25% increments. The city authority encodes the
   **total municipal portion** including any non-home-rule
   municipal-purpose taxes.

Combined rate formula at any covered ZIP:

    state 6.250 + county[county_name] + rta[rta_district or 0]
  + city_total_rate_pct

**IMPORTANT -- Reduced-rate categories not modeled here:** Illinois
imposes a SEPARATE 1% state rate on qualifying food (groceries,
not prepared food), prescription drugs, and medical appliances
(35 ILCS 120/2-10). The local portions still apply at the regular
local rate. The :class:`Illinois.taxability_for` accessor reports
``rate_modifier=1.000`` for those categories; the engine wires the
modifier through (since v0.11.1). The data table here ships the
**general-merchandise** rates only.

**SSAs / TIF districts NOT modeled in v0.x:** Illinois municipalities
may overlay Special Service Areas (SSAs) on specific blocks /
ZIPs / +4 ranges (e.g. the Chicago SSA #1 around the Magnificent
Mile). These overlays bump combined rates above the city baseline
by 0.25%-1.00% in narrow geographies. The seeded city rates here
are the **city-baseline** combined rate; ZIP+4 micro-variation
within an SSA is intentionally out of scope for v1.

Cities seeded (top 20 by 2020 census population):

Chicago, Aurora, Joliet, Naperville, Rockford, Elgin, Springfield,
Peoria, Champaign, Waukegan, Cicero, Bloomington, Arlington Heights,
Evanston, Schaumburg, Decatur, Bolingbrook, Palatine, Skokie,
Des Plaines.

ZIPs not in :data:`IL_CITIES` fall back to state-only at 6.25%
via the Census ZCTA load. This is a *significant* under-collection
for suburban / unincorporated Illinois, but it's correct for any
address that is genuinely outside an incorporated city's
jurisdiction (most of rural Illinois). A future ratchet should
ingest the IDOR Tax Rate Database CSV directly so quarterly
updates auto-flow.

**Rates that disagree across sources (recorded for the next
maintainer to chase):**

- **Naperville (60540)** -- the published combined rate cited by
  Avalara is 7.75% as of 2026-05-04 (state 6.25 + Naperville HR
  0.75 + RTA DuPage 0.75 = 7.75%); the original task brief cited
  7.25% with Naperville HR = 0% and RTA at 1.00%. We use 7.75%
  here because (a) Naperville IS home-rule (population well above
  25,000) and (b) RTA in DuPage is 0.75%, not 1.00%. If the IDOR
  Tax Rate Finder shows a different rate for a specific +4, the
  centroid 0001 +4 will diverge by up to 0.5%.
- **Rockford (61101)** -- task brief cited 6.25% as the baseline
  with a "verify Winnebago has additional 1% LOST". Per IDOR
  Tax Rate Finder + Avalara, Rockford's general-merchandise
  combined is 8.75% (state 6.25 + Winnebago 1.5 + Rockford 1.0 =
  8.75%). The 1% Winnebago tax is the County School Facility
  Sales Tax + a 0.5% public-safety tax, not a LOST. Rockford
  itself has a 1.0% home-rule rate.

Disclaimer: this module is calculation infrastructure, not tax
advice. Single-purpose districts (SSAs, business-improvement
districts, etc.) and the home-rule local-rate landscape can
produce surprising results at specific +4 addresses. Verify
against the IDOR Tax Rate Finder
(https://mytax.illinois.gov/_/) before relying on these rates
for compliance.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective since 1990-01-01 (the 6.25% level set by
# P.A. 86-928 effective 1990-01-01). The state retailers' occupation
# tax base rate has been stable at 6.25% on general merchandise
# since then.
IL_STATE_RATE_PCT = Decimal("6.250")
IL_STATE_EFFECTIVE_FROM = dt.date(1990, 1, 1)

# Per-county local-tax portion (NOT including the 6.25% state rate).
# Source: IDOR Tax Rate Database + Avalara per-county pages, verified
# 2026-05-04. Counties listed are only those touched by a covered
# city; counties with 0% rate ARE included for audit parallelism with
# the AZ/MO/SC/TX/VA pattern.
IL_COUNTY_RATE_PCT: dict[str, Decimal] = {
    # --- Cook (the heavyweight) ---
    "Cook County": Decimal("1.750"),  # Cook County imposes a 1.75% home-rule sales tax
    # --- Collar counties (RTA at 0.75%; most have no county sales tax) ---
    "DuPage County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Kane County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Lake County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "McHenry County": Decimal("0.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Will County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    # --- Downstate counties touched by covered cities ---
    "Winnebago County": Decimal("1.500"),  # School Facility 1% + Public Safety 0.5%
    "Sangamon County": Decimal(
        "1.500"
    ),  # School Facility 1% + Public Safety 0.5% (public-safety +0.5% eff 2026-07-01 per IDOR FY 2026-26-A; raises Springfield to 10.0%)
    "Peoria County": Decimal("1.000"),  # Peoria County School Facility 1%
    "Champaign County": Decimal("1.250"),  # Champaign County 1.25% (county school + public safety)
    "McLean County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Macon County": Decimal("1.500"),  # Macon County School Facility + public safety
    # --- Remaining 90 IL counties: filled from IDOR machine-readable file ---
    # Source: Illinois Department of Revenue "Sales Tax Rates Machine
    # Readable File" (ordmache-current.txt), effective 2026-01-01,
    # retrieved 2026-05-04 from
    # https://tax.illinois.gov/content/dam/soi/en/web/tax/research/taxrates/documents/salestaxrates/ordmache-current.txt
    # Extraction script: scripts/extract_il_county_rates.py (re-run on
    # next IDOR publication, typically Jan 1 / Jul 1 of each year). The
    # IDOR file's combined county-base rate INCLUDES the RTA district
    # for Cook (1.00%) and the collar counties DuPage / Kane / Lake /
    # McHenry / Will (0.75%); the script subtracts state 6.25% AND the
    # RTA portion to recover the bare county-portion this dict holds.
    #
    # Counties marked "verified 0% (no county tax)" actually impose no
    # county-level general-merchandise sales tax per IDOR (the combined
    # rate equals state 6.25% plus the RTA portion if any). Counties
    # without that comment carry a real county school-facility / public-
    # safety / supplementary tax authorized under 35 ILCS 200 et al.
    "Adams County": Decimal("0.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Alexander County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Bond County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Boone County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Brown County": Decimal("1.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Bureau County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Calhoun County": Decimal("1.750"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Carroll County": Decimal("0.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Cass County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Christian County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Clark County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Clay County": Decimal("0.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Clinton County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Coles County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Crawford County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Cumberland County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "De Witt County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "DeKalb County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Douglas County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Edgar County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Edwards County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Effingham County": Decimal("0.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Fayette County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Ford County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Franklin County": Decimal(
        "1.000"
    ),  # public-safety -1.0% eff 2026-07-01 per IDOR FY 2026-26-A; was 2.0% (ordmache 2026-01-01, combined - state - RTA)
    "Fulton County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Gallatin County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Greene County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Grundy County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Hamilton County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Hancock County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Hardin County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Henderson County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Henry County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Iroquois County": Decimal("0.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Jackson County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Jasper County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Jefferson County": Decimal("0.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Jersey County": Decimal("1.750"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Jo Daviess County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Johnson County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Kankakee County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Kendall County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Knox County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "LaSalle County": Decimal("0.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Lawrence County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Lee County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Livingston County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Logan County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Macoupin County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Madison County": Decimal("0.600"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Marion County": Decimal("1.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Marshall County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Mason County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Massac County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "McDonough County": Decimal("1.750"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Menard County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Mercer County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Monroe County": Decimal("1.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Montgomery County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Morgan County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Moultrie County": Decimal("0.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Ogle County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Perry County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Piatt County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Pike County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Pope County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Pulaski County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Putnam County": Decimal("0.000"),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Randolph County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Richland County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Rock Island County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Saline County": Decimal("1.750"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Schuyler County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Scott County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Shelby County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "St. Clair County": Decimal("1.100"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Stark County": Decimal("1.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Stephenson County": Decimal("0.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Tazewell County": Decimal("0.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Union County": Decimal("2.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Vermilion County": Decimal("0.250"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Wabash County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Warren County": Decimal("1.750"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Washington County": Decimal(
        "0.000"
    ),  # verified 0% (no county tax) -- IDOR ordmache 2026-01-01
    "Wayne County": Decimal("0.750"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "White County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Whiteside County": Decimal("1.500"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Williamson County": Decimal("1.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
    "Woodford County": Decimal("2.000"),  # IDOR ordmache 2026-01-01 (combined - state - RTA)
}

# RTA district authorities (70 ILCS 3615/4.03). Modeled as TWO
# authorities because the per-county rate within the RTA service
# area differs (Cook 1.00% / collar counties 0.75%). Each city is
# bound to ONE of these (or None if outside the RTA area).
IL_RTA_DISTRICTS: dict[str, Decimal] = {
    "RTA (Cook County)": Decimal("1.000"),
    "RTA (Collar Counties)": Decimal("0.750"),
}

# Per-city seed. Tuple shape:
#   (county_name, rta_district_name_or_None, city_total_rate_pct, [zip5s])
#
# - county_name -- the primary county the city sits in. Cities that
#   straddle multiple counties (Aurora spans Kane/DuPage/Will/Kendall;
#   Joliet spans Will/Kendall) are encoded under the dominant county.
#   ZIPs are limited to the dominant county to keep rate math clean.
# - rta_district_name -- "RTA (Cook County)" if the city sits in
#   Cook, "RTA (Collar Counties)" if it sits in DuPage / Kane / Lake /
#   McHenry / Will, or None if outside the six-county RTA area.
# - city_total_rate_pct -- the combined municipal portion (city sales
#   tax + home-rule + non-home-rule municipal taxes). Derived to make
#   state + county + RTA + city = the published combined rate at the
#   city centroid.
# - zips -- the primary delivery ZIPs for each city. Not exhaustive;
#   covers the population centroids most often queried.
IL_CITIES: dict[str, tuple[str, str | None, Decimal, tuple[str, ...]]] = {
    # =================================================================
    # Cook County (RTA Cook 1.00%, county 1.75%) -- Chicago + suburbs
    # =================================================================
    "Chicago": (
        # Chicago combined: state 6.25 + Cook 1.75 + Chicago HR 1.25
        # + RTA Cook 1.00 = 10.25%. Tied with Evanston and Skokie for
        # the highest combined general-merchandise rate among major
        # IL cities. (SSA overlays push some Chicago +4 ranges higher
        # but those are not modeled here.)
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.250"),
        # Chicago city-limit ZIPs in Cook County. Chicago has ~80
        # ZIP5s; this seed covers the population centroids most
        # often queried.
        (
            "60601",
            "60602",
            "60603",
            "60604",
            "60605",
            "60606",
            "60607",
            "60608",
            "60609",
            "60610",
            "60611",
            "60612",
            "60613",
            "60614",
            "60615",
            "60616",
            "60617",
            "60618",
            "60619",
            "60620",
            "60621",
            "60622",
            "60623",
            "60624",
            "60625",
            "60626",
            "60628",
            "60629",
            "60630",
            "60631",
            "60632",
            "60633",
            "60634",
            "60636",
            "60637",
            "60638",
            "60639",
            "60640",
            "60641",
            "60642",
            "60643",
            "60644",
            "60645",
            "60646",
            "60647",
            "60649",
            "60651",
            "60652",
            "60653",
            "60654",
            "60655",
            "60656",
            "60657",
            "60659",
            "60660",
            "60661",
        ),
    ),
    "Cicero": (
        # Cicero is in Cook County. Combined: state 6.25 + Cook 1.75
        # + Cicero HR 1.75 + RTA Cook 1.00 = 10.75%. One of the
        # highest combined rates in the state.
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.750"),
        ("60804",),
    ),
    "Evanston": (
        # Evanston is in Cook County. Combined: state 6.25 + Cook
        # 1.75 + Evanston HR 1.25 + RTA Cook 1.00 = 10.25%.
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.250"),
        ("60201", "60202", "60203", "60208"),
    ),
    "Skokie": (
        # Skokie is in Cook County. Combined: state 6.25 + Cook 1.75
        # + Skokie HR 1.25 + RTA Cook 1.00 = 10.25%.
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.250"),
        ("60076", "60077"),
    ),
    "Schaumburg": (
        # Schaumburg is in Cook County. Combined: state 6.25 + Cook
        # 1.75 + Schaumburg HR 1.00 + RTA Cook 1.00 = 10.00%.
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.000"),
        ("60173", "60193", "60194", "60195"),
    ),
    "Arlington Heights": (
        # Arlington Heights is in Cook County (a sliver in Lake;
        # excluded). Combined: state 6.25 + Cook 1.75 + Arlington
        # Heights HR 1.00 + RTA Cook 1.00 = 10.00%.
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.000"),
        ("60004", "60005"),
    ),
    "Palatine": (
        # Palatine is in Cook County. Combined: state 6.25 + Cook
        # 1.75 + Palatine HR 1.00 + RTA Cook 1.00 = 10.00%.
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.000"),
        ("60067", "60074"),
    ),
    "Des Plaines": (
        # Des Plaines is in Cook County. Combined: state 6.25 + Cook
        # 1.75 + Des Plaines HR 1.00 + RTA Cook 1.00 = 10.00%.
        "Cook County",
        "RTA (Cook County)",
        Decimal("1.000"),
        ("60016", "60018"),
    ),
    # =================================================================
    # Collar counties (RTA Collar 0.75%, no county sales tax)
    # =================================================================
    "Aurora": (
        # Aurora's largest portion is in Kane County (small parts in
        # DuPage / Will / Kendall, excluded from the seed). Combined:
        # state 6.25 + Kane 0 + Aurora HR 1.25 + RTA Collar 0.75 =
        # 8.25%.
        "Kane County",
        "RTA (Collar Counties)",
        Decimal("1.250"),
        ("60505", "60506", "60502", "60503", "60504"),
    ),
    "Elgin": (
        # Elgin's main portion is in Kane County (a portion in Cook,
        # excluded). Combined: state 6.25 + Kane 0 + Elgin HR 1.50
        # + RTA Collar 0.75 = 8.50%.
        "Kane County",
        "RTA (Collar Counties)",
        Decimal("1.500"),
        ("60120", "60123", "60124"),
    ),
    "Naperville": (
        # Naperville's main portion is in DuPage County (a portion
        # in Will, excluded). Combined: state 6.25 + DuPage 0 +
        # Naperville HR 0.75 + RTA Collar 0.75 = 7.75%. (Naperville
        # IS home-rule by population but its home-rule sales tax
        # is the modest 0.75% rate.)
        "DuPage County",
        "RTA (Collar Counties)",
        Decimal("0.750"),
        ("60540", "60563", "60564", "60565"),
    ),
    "Joliet": (
        # Joliet's main portion is in Will County (a sliver in
        # Kendall, excluded). Combined: state 6.25 + Will 0 + Joliet
        # HR 1.75 + RTA Collar 0.75 = 8.75%.
        "Will County",
        "RTA (Collar Counties)",
        Decimal("1.750"),
        ("60431", "60432", "60433", "60435", "60436"),
    ),
    "Bolingbrook": (
        # Bolingbrook is in Will County (a portion in DuPage,
        # excluded). Combined: state 6.25 + Will 0 + Bolingbrook HR
        # 1.50 + RTA Collar 0.75 = 8.50%.
        "Will County",
        "RTA (Collar Counties)",
        Decimal("1.500"),
        ("60440", "60490"),
    ),
    "Waukegan": (
        # Waukegan is in Lake County. Combined: state 6.25 + Lake 0
        # + Waukegan HR 1.50 + RTA Collar 0.75 = 8.50%.
        "Lake County",
        "RTA (Collar Counties)",
        Decimal("1.500"),
        ("60085", "60087"),
    ),
    # =================================================================
    # Downstate (no RTA -- city + county absorb local rate)
    # =================================================================
    "Rockford": (
        # Rockford is in Winnebago County. Combined: state 6.25 +
        # Winnebago 1.5 + Rockford HR 1.0 = 8.75%. (Outside the RTA
        # service area.)
        "Winnebago County",
        None,
        Decimal("1.000"),
        ("61101", "61102", "61103", "61104", "61107", "61108", "61109"),
    ),
    "Springfield": (
        # Springfield is in Sangamon County (the IL state capital).
        # Combined: state 6.25 + Sangamon 1.0 + Springfield HR 2.25
        # = 9.50%.
        "Sangamon County",
        None,
        Decimal("2.250"),
        ("62701", "62702", "62703", "62704", "62711"),
    ),
    "Peoria": (
        # Peoria is in Peoria County. Combined: state 6.25 + Peoria
        # Co 1.0 + Peoria HR 1.75 = 9.00%.
        "Peoria County",
        None,
        Decimal("1.750"),
        ("61602", "61603", "61604", "61605", "61606", "61614", "61615"),
    ),
    "Champaign": (
        # Champaign is in Champaign County. Combined: state 6.25 +
        # Champaign Co 1.25 + Champaign HR 1.50 = 9.00%.
        "Champaign County",
        None,
        Decimal("1.500"),
        ("61820", "61821", "61822"),
    ),
    "Bloomington": (
        # Bloomington is in McLean County. Combined per IDOR ordmache
        # 2026-01-01: state 6.25 + McLean 1.00 + Bloomington HR 2.50
        # = 9.75%. (Was 8.75% prior to McLean County's 1% county tax
        # authorization; the IDOR-published combined rate jumped to
        # 9.750% effective 2025-07-01 per the same machine-readable
        # publication. McLean County rate filled from IDOR ordmache;
        # see comment block above IL_COUNTY_RATE_PCT.)
        "McLean County",
        None,
        Decimal("2.500"),
        ("61701", "61704", "61705"),
    ),
    "Decatur": (
        # Decatur is in Macon County. Combined: state 6.25 + Macon
        # 1.5 + Decatur HR 1.50 = 9.25%.
        "Macon County",
        None,
        Decimal("1.500"),
        ("62521", "62522", "62523", "62526"),
    ),
}


__all__ = [
    "IL_STATE_RATE_PCT",
    "IL_STATE_EFFECTIVE_FROM",
    "IL_COUNTY_RATE_PCT",
    "IL_RTA_DISTRICTS",
    "IL_CITIES",
]
