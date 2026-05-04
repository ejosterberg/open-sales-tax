# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Texas sales tax rate + boundary data (top-50-city coverage).

Source: Texas Comptroller of Public Accounts "City Sales and Use Tax
Rates" + "Local Sales and Use Tax Rates" publications, plus the
Sales Tax Rate Locator at https://comptroller.texas.gov/taxes/sales/.
Each city's combined rate cross-checked against Avalara's per-city
rate pages (https://www.avalara.com/taxrates/en/state-rates/texas/)
and TaxJar's Texas city pages on **2026-05-04**.

Architecture: Texas's combined rate has up to four modeled layers:

1. **State portion: 6.25%** (Tex. Tax Code section 151.051) -- the
   ``Texas`` state authority.
2. **County portion** (Tex. Tax Code Chapter 323) -- many Texas
   counties impose **NO** county-level sales tax; the rare ones that
   do (e.g. El Paso County 0.5%) are seeded individually. Counties
   listed in :data:`TX_COUNTY_RATE_PCT` are only those touched by a
   covered city; counties with 0% rate ARE included for parallelism
   with the AZ / MO / SC / VA pattern (the engine sums 0% authorities
   to no effect but keeps the audit trail).
3. **Transit / Metropolitan Transit Authority (MTA) district**
   (Tex. Tax Code Chapter 451) -- the major metro transit agencies
   (Houston METRO, Dallas DART, Austin Capital Metro, San Antonio
   VIA+ATD, Fort Worth FWTA, El Paso Sun Metro, Corpus Christi RTA)
   are modeled as :data:`TX_TRANSIT_DISTRICTS` and bound to cities
   that fall inside the agency's service area. Cities that opted out
   of transit (Arlington being the famous case) get None and absorb
   any remaining local-cap room into their city rate or special
   districts.
4. **City portion** (Tex. Tax Code Chapter 321) -- the city
   authority encodes the **total municipal portion** (city sales tax
   + EDC 4A/4B + crime control + street maintenance + municipal
   development district, etc.) collapsed into a single number. This
   is the cleanest shape for our purposes -- the Comptroller's
   per-city rate has a single 1.0%-2.0% local-option slot that is
   apportioned among these special-purpose taxes by city ordinance.

**Local cap (Tex. Tax Code section 321.101(f)):** the combined
local rate (county + transit + city + districts) is capped at
**2.0%**, making the maximum combined Texas rate **8.25%**. Almost
every major Texas city maxes out at 8.25%. The notable exception in
this seed is **Arlington** at 8.0% -- Arlington opted out of DART
and its local stack (city 1.0% + crime control 0.5% + parks 0.25%)
sums to 1.75%, leaving 0.25% of cap room unused.

**Sourcing model -- IMPORTANT:** Texas uses **origin-based sourcing**
for in-state sellers (the rate is determined by the seller's
location, not the buyer's, per Tex. Tax Code section 321.203). The
ZIP-based boundary table here is a **delivery-address approximation**
that produces the correct rate for a buyer at that ZIP buying from
a seller at the same ZIP -- which is the dominant case for
brick-and-mortar retail and direct-to-consumer e-commerce delivered
in-state. A future ratchet should expose the seller-vs-buyer
distinction so the API caller can pick the right rule.

Cities seeded (top 50 by 2020 census population, minus Atascocita
which is a CDP without a single clean municipal rate):

Houston, San Antonio, Dallas, Austin, Fort Worth, El Paso, Arlington,
Corpus Christi, Plano, Lubbock, Laredo, Garland, Irving, Frisco,
Amarillo, Grand Prairie, McKinney, Brownsville, Killeen, Mesquite,
Pasadena, Denton, McAllen, Carrollton, Midland, Round Rock, Lewisville,
Pearland, Abilene, Beaumont, Allen, College Station, Tyler, Wichita
Falls, Sugar Land, Edinburg, League City, Mission, Conroe, Bryan,
Longview, Pharr, Baytown, Missouri City, Temple, New Braunfels, Cedar
Park, Flower Mound, Rowlett.

49 cities (Atascocita CDP intentionally omitted; see above).

ZIPs not in :data:`TX_CITIES` fall back to state-only at 6.25% via
the Census ZCTA load. This is a *significant* under-collection for
suburban / unincorporated Texas, but it's correct for any address
that is genuinely outside an incorporated city's jurisdiction (most
of rural Texas). A future ratchet should add per-county boundary
seeds for the few counties that impose county-level sales tax.

Disclaimer: this module is calculation infrastructure, not tax
advice. Origin sourcing, single-purpose districts (TIF, MUD, etc.),
and the local-cap interaction can produce surprising results at
specific addresses. Verify against the Comptroller's Sales Tax
Rate Locator before relying on these rates for compliance.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective since 1990-07-01, when H.B. 11 (71st Leg.,
# 6th C.S.) raised the state portion from 6.0% to 6.25% to fund
# public-school finance reform. Stable since.
TX_STATE_RATE_PCT = Decimal("6.250")
TX_STATE_EFFECTIVE_FROM = dt.date(1990, 7, 1)

# Per-county local-tax portion (NOT including the 6.25% state rate).
# Most Texas counties impose NO county-level sales tax; entries here
# are only the counties touched by a covered city. Per Tex. Tax Code
# Chapter 323, counties may impose up to 0.5% (with voter approval)
# but most large-population counties leave the local-cap room for
# cities and transit districts.
#
# Counties with 0.000% are kept for audit parallelism with the
# AZ/MO/SC/VA pattern; the engine sums them to no effect.
TX_COUNTY_RATE_PCT: dict[str, Decimal] = {
    # --- Counties with NO county sales tax (most of Texas) ---
    "Harris County": Decimal("0.000"),
    "Dallas County": Decimal("0.000"),
    "Tarrant County": Decimal("0.000"),
    "Travis County": Decimal("0.000"),
    "Bexar County": Decimal("0.000"),
    "Collin County": Decimal("0.000"),
    "Denton County": Decimal("0.000"),
    "Hidalgo County": Decimal("0.000"),
    "Williamson County": Decimal("0.000"),
    "Lubbock County": Decimal("0.000"),
    "Webb County": Decimal("0.000"),
    "Cameron County": Decimal("0.000"),
    "Bell County": Decimal("0.000"),
    "Nueces County": Decimal("0.000"),
    "Brazoria County": Decimal("0.000"),
    "Fort Bend County": Decimal("0.000"),
    "Galveston County": Decimal("0.000"),
    "Montgomery County": Decimal("0.000"),
    "Brazos County": Decimal("0.000"),
    "Comal County": Decimal("0.000"),
    "Smith County": Decimal("0.000"),
    "Wichita County": Decimal("0.000"),
    "Gregg County": Decimal("0.000"),
    "Potter County": Decimal("0.000"),
    "Randall County": Decimal("0.000"),
    "Midland County": Decimal("0.000"),
    "Taylor County": Decimal("0.000"),
    "Jefferson County": Decimal("0.000"),
    "Ellis County": Decimal("0.000"),
    # --- Counties with a county sales tax ---
    # El Paso County imposes a 0.5% county sales-tax-for-property-tax-
    # relief portion (per Tex. Tax Code section 323.105) so the El
    # Paso city stack lands at the 8.25% cap.
    "El Paso County": Decimal("0.500"),
}

# Transit / Metropolitan Transit Authority districts (Tex. Tax Code
# Chapter 451). Each district is modeled as a ``district`` authority
# under the state and bound to the cities in its service area via the
# second tuple element in TX_CITIES.
#
# Rates are the published agency portion of the local sales tax; for
# San Antonio the 0.625% is the combined VIA Metropolitan Transit
# Authority (0.5%) + Advanced Transportation District (0.125%) which
# always co-occur in VIA's service area.
TX_TRANSIT_DISTRICTS: dict[str, Decimal] = {
    "Houston MTA (METRO)": Decimal("1.000"),
    "Dallas MTA (DART)": Decimal("1.000"),
    "Austin MTA (Capital Metro)": Decimal("1.000"),
    "San Antonio MTA (VIA + ATD)": Decimal("0.625"),
    "Fort Worth MTA (Trinity Metro)": Decimal("0.500"),
    "El Paso MTA (Sun Metro)": Decimal("0.500"),
    "Corpus Christi MTA (RTA)": Decimal("0.500"),
}

# Per-city seed. Tuple shape:
#   (county_name, transit_district_name_or_None, city_total_rate_pct, [zip5s])
#
# - county_name -- the primary county the city sits in. Cities that
#   straddle multiple counties (Houston spans Harris/Fort Bend/
#   Montgomery; Dallas spans Dallas/Collin/Denton/Rockwall/Kaufman)
#   are encoded under the dominant county. Boundary ZIPs from the
#   secondary counties are intentionally NOT included to keep the
#   rate math clean.
# - transit_district_name -- the MTA district (key in
#   TX_TRANSIT_DISTRICTS) the city is bound to, or None if the city
#   is outside any MTA. Arlington famously opted out of DART so it
#   gets None.
# - city_total_rate_pct -- the **combined** municipal portion (city
#   sales tax + EDC 4A/4B + crime control + street maintenance +
#   MDD, etc.). Derived to make state + county + transit + city =
#   the published combined rate at the city centroid.
# - zips -- the primary delivery ZIPs for each city. Not exhaustive
#   (Houston alone has ~80 ZIPs); covers the population centroids
#   that consumers most often query.
#
# Combined rate formula at any covered ZIP:
#     state 6.250 + county[county_name] + transit[district or 0]
#   + city_total_rate_pct
TX_CITIES: dict[str, tuple[str, str | None, Decimal, tuple[str, ...]]] = {
    # =================================================================
    # Houston METRO area (METRO 1.0% transit, no county sales tax)
    # =================================================================
    "Houston": (
        "Harris County",
        "Houston MTA (METRO)",
        Decimal("1.000"),
        # Houston proper -- city-limit ZIPs in Harris County (Houston
        # straddles Harris/Fort Bend/Montgomery; Fort Bend / Montgomery
        # ZIPs intentionally excluded). Combined: 6.25 + 0 + 1.0 + 1.0
        # = 8.25%.
        (
            "77002", "77003", "77004", "77005", "77006", "77007", "77008",
            "77009", "77010", "77011", "77012", "77013", "77014", "77016",
            "77017", "77018", "77019", "77020", "77021", "77022", "77023",
            "77025", "77026", "77027", "77028", "77029", "77030", "77031",
            "77033", "77034", "77035", "77036", "77039", "77040", "77041",
            "77042", "77043", "77045", "77046", "77047", "77048", "77051",
            "77054", "77055", "77056", "77057", "77058", "77059", "77061",
            "77062", "77063", "77074", "77075", "77076", "77077", "77078",
            "77079", "77080", "77081", "77082", "77084", "77085", "77086",
            "77087", "77088", "77089", "77091", "77092", "77093", "77096",
            "77098", "77099",
        ),
    ),
    "Pasadena": (
        # Pasadena is in Harris County and part of the METRO service
        # area. 6.25 + 0 + 1.0 + 1.0 = 8.25%.
        "Harris County",
        "Houston MTA (METRO)",
        Decimal("1.000"),
        ("77502", "77503", "77504", "77505", "77506", "77507"),
    ),
    "Baytown": (
        # Baytown is in Harris/Chambers counties; we model the Harris
        # portion. Baytown is OUTSIDE the METRO service area (METRO
        # boundary ends well west of Baytown), so transit = None and
        # the city absorbs the full 2.0% local cap.
        # 6.25 + 0 + 0 + 2.0 = 8.25%.
        "Harris County",
        None,
        Decimal("2.000"),
        ("77520", "77521", "77522", "77523"),
    ),
    # =================================================================
    # Dallas / Fort Worth Metroplex (DART 1.0% / FWTA 0.5%)
    # =================================================================
    "Dallas": (
        "Dallas County",
        "Dallas MTA (DART)",
        Decimal("1.000"),
        # Dallas city limits in Dallas County. ZIPs that straddle into
        # Collin/Denton/Rockwall/Kaufman are excluded.
        (
            "75201", "75202", "75203", "75204", "75205", "75206", "75207",
            "75208", "75209", "75210", "75211", "75212", "75214", "75215",
            "75216", "75217", "75218", "75219", "75220", "75223", "75224",
            "75225", "75226", "75227", "75228", "75229", "75230", "75231",
            "75232", "75233", "75235", "75236", "75237", "75238", "75240",
            "75241", "75243", "75244", "75246", "75247", "75248", "75249",
            "75251", "75252",
        ),
    ),
    "Plano": (
        # Plano is a DART member (one of the original 1983 charter
        # cities). Plano is in Collin County (mostly) and Denton.
        # 6.25 + 0 + 1.0 + 1.0 = 8.25%.
        "Collin County",
        "Dallas MTA (DART)",
        Decimal("1.000"),
        ("75023", "75024", "75025", "75074", "75075", "75093", "75094"),
    ),
    "Garland": (
        "Dallas County",
        "Dallas MTA (DART)",
        Decimal("1.000"),
        ("75040", "75041", "75042", "75043", "75044"),
    ),
    "Irving": (
        "Dallas County",
        "Dallas MTA (DART)",
        Decimal("1.000"),
        ("75038", "75039", "75060", "75061", "75062", "75063"),
    ),
    "Carrollton": (
        # Carrollton is a DART member. Spans Dallas / Denton / Collin
        # counties; we model the Dallas portion (the bulk of the city).
        "Dallas County",
        "Dallas MTA (DART)",
        Decimal("1.000"),
        ("75006", "75007", "75010", "75234", "75287"),
    ),
    "Rowlett": (
        # Rowlett is a DART member. In Dallas/Rockwall counties; model
        # Dallas portion.
        "Dallas County",
        "Dallas MTA (DART)",
        Decimal("1.000"),
        ("75088", "75089"),
    ),
    "Mesquite": (
        # Mesquite is NOT a DART member (it opted not to join). The
        # local cap is filled with city + crime control + street maint
        # totaling 2.0%. 6.25 + 0 + 0 + 2.0 = 8.25%.
        "Dallas County",
        None,
        Decimal("2.000"),
        ("75149", "75150", "75180", "75181", "75182"),
    ),
    "Grand Prairie": (
        # Grand Prairie is NOT a DART/FWTA member. Spans Dallas /
        # Tarrant / Ellis counties; model the Dallas portion.
        "Dallas County",
        None,
        Decimal("2.000"),
        ("75050", "75051", "75052", "75054"),
    ),
    "Frisco": (
        # Frisco is NOT a DART member. In Collin (mostly) and Denton.
        # 6.25 + 0 + 0 + 2.0 = 8.25%.
        "Collin County",
        None,
        Decimal("2.000"),
        ("75033", "75034", "75035", "75036", "75068"),
    ),
    "McKinney": (
        # McKinney is NOT a DART member. In Collin County.
        "Collin County",
        None,
        Decimal("2.000"),
        ("75069", "75070", "75071", "75072"),
    ),
    "Allen": (
        # Allen is NOT a DART member. In Collin County.
        "Collin County",
        None,
        Decimal("2.000"),
        ("75002", "75013"),
    ),
    "Lewisville": (
        # Lewisville is a DART member. In Denton County.
        "Denton County",
        "Dallas MTA (DART)",
        Decimal("1.000"),
        ("75056", "75057", "75067", "75077"),
    ),
    "Flower Mound": (
        # Flower Mound is NOT a DART member. In Denton/Tarrant.
        "Denton County",
        None,
        Decimal("2.000"),
        ("75022", "75028"),
    ),
    "Denton": (
        # Denton city is NOT a DART member. In Denton County.
        "Denton County",
        None,
        Decimal("2.000"),
        ("76201", "76205", "76207", "76208", "76209", "76210"),
    ),
    "Fort Worth": (
        # Fort Worth is the anchor of FWTA / Trinity Metro (0.5%
        # transit). City rate fills remaining cap with crime control
        # 0.5% + city 1.0% = 1.5% city + 0.5% transit = 2.0% local.
        "Tarrant County",
        "Fort Worth MTA (Trinity Metro)",
        Decimal("1.500"),
        (
            "76102", "76103", "76104", "76105", "76106", "76107", "76108",
            "76109", "76110", "76111", "76112", "76114", "76115", "76116",
            "76117", "76118", "76119", "76120", "76123", "76126", "76131",
            "76132", "76133", "76134", "76135", "76137", "76140", "76148",
            "76164", "76177", "76179", "76244",
        ),
    ),
    "Arlington": (
        # Arlington is the famous DART/FWTA opt-out -- no transit
        # district. The city stack (city 1.0% + crime control 0.5% +
        # parks/street maint 0.25%) sums to 1.75%, leaving 0.25% of
        # the local cap unused. Combined: 6.25 + 0 + 0 + 1.75 = 8.00%.
        # This is the only major Texas city in this seed below 8.25%.
        "Tarrant County",
        None,
        Decimal("1.750"),
        ("76001", "76002", "76010", "76011", "76012", "76013", "76014",
         "76015", "76016", "76017", "76018"),
    ),
    # =================================================================
    # Austin (Capital Metro 1.0% transit)
    # =================================================================
    "Austin": (
        "Travis County",
        "Austin MTA (Capital Metro)",
        Decimal("1.000"),
        # Austin city limits in Travis County. ZIPs straddling
        # Williamson / Hays counties intentionally excluded.
        (
            "78701", "78702", "78703", "78704", "78705", "78712", "78717",
            "78721", "78722", "78723", "78724", "78725", "78726", "78727",
            "78728", "78729", "78730", "78731", "78732", "78733", "78734",
            "78735", "78736", "78737", "78738", "78739", "78741", "78742",
            "78744", "78745", "78746", "78747", "78748", "78749", "78750",
            "78751", "78752", "78753", "78754", "78756", "78757", "78758",
            "78759",
        ),
    ),
    "Round Rock": (
        # Round Rock is NOT in Capital Metro. In Williamson County.
        # 6.25 + 0 + 0 + 2.0 = 8.25%.
        "Williamson County",
        None,
        Decimal("2.000"),
        ("78664", "78665", "78681"),
    ),
    "Cedar Park": (
        # Cedar Park is NOT in Capital Metro. In Williamson County.
        "Williamson County",
        None,
        Decimal("2.000"),
        ("78613",),
    ),
    # =================================================================
    # San Antonio (VIA 0.5% + ATD 0.125% = 0.625% combined transit)
    # =================================================================
    "San Antonio": (
        # San Antonio combined: state 6.25 + city portion (1.125% city
        # + 0.25% ED corp + 0.25% pre-K = 1.625%) + transit 0.625%
        # (VIA 0.5 + ATD 0.125). Total = 8.5%? No -- the local cap is
        # 2.0% so the published combined is 8.25%. The actual stack
        # used by the Comptroller is city 1.125 + transit 0.625 +
        # ATD-already-in-transit + remaining 0.25% of cap split among
        # city special purposes. Net: combined 8.25%, modeled as
        # state 6.25 + city 1.375 + transit 0.625 = 8.25.
        "Bexar County",
        "San Antonio MTA (VIA + ATD)",
        Decimal("1.375"),
        (
            "78201", "78202", "78203", "78204", "78205", "78207", "78208",
            "78209", "78210", "78211", "78212", "78213", "78214", "78215",
            "78216", "78217", "78218", "78219", "78220", "78221", "78222",
            "78223", "78224", "78225", "78226", "78227", "78228", "78229",
            "78230", "78231", "78232", "78233", "78237", "78238", "78239",
            "78240", "78242", "78244", "78245", "78247", "78248", "78249",
            "78250", "78251", "78252", "78253", "78254", "78255", "78258",
            "78259", "78260", "78261",
        ),
    ),
    "New Braunfels": (
        # New Braunfels is in Comal/Guadalupe; outside VIA service area.
        "Comal County",
        None,
        Decimal("2.000"),
        ("78130", "78132"),
    ),
    # =================================================================
    # El Paso (Sun Metro 0.5% transit + 0.5% county tax)
    # =================================================================
    "El Paso": (
        # El Paso stack: state 6.25 + county 0.5 + transit 0.5 + city
        # 1.0 = 8.25%. El Paso County is one of the few TX counties
        # imposing a county sales tax (0.5% per Tex. Tax Code 323.105).
        "El Paso County",
        "El Paso MTA (Sun Metro)",
        Decimal("1.000"),
        (
            "79901", "79902", "79903", "79904", "79905", "79906", "79907",
            "79908", "79912", "79915", "79922", "79924", "79925", "79927",
            "79928", "79932", "79934", "79935", "79936", "79938",
        ),
    ),
    # =================================================================
    # Corpus Christi (RTA 0.5% transit) + Coastal Bend
    # =================================================================
    "Corpus Christi": (
        # Corpus Christi combined: state 6.25 + city 1.5 (city 1.0 +
        # crime control 0.125 + street maint 0.125 + business/industry
        # 0.25) + transit 0.5 = 8.25%.
        "Nueces County",
        "Corpus Christi MTA (RTA)",
        Decimal("1.500"),
        (
            "78401", "78402", "78404", "78405", "78406", "78407", "78408",
            "78409", "78410", "78411", "78412", "78413", "78414", "78415",
            "78416", "78417", "78418", "78419",
        ),
    ),
    # =================================================================
    # Rio Grande Valley (no MTA -- city absorbs full local cap)
    # =================================================================
    "Laredo": (
        "Webb County",
        None,
        Decimal("2.000"),
        ("78040", "78041", "78043", "78045", "78046"),
    ),
    "Brownsville": (
        "Cameron County",
        None,
        Decimal("2.000"),
        ("78520", "78521", "78526"),
    ),
    "McAllen": (
        "Hidalgo County",
        None,
        Decimal("2.000"),
        ("78501", "78503", "78504", "78539"),
    ),
    "Edinburg": (
        "Hidalgo County",
        None,
        Decimal("2.000"),
        ("78539", "78540", "78541", "78542"),
    ),
    "Mission": (
        "Hidalgo County",
        None,
        Decimal("2.000"),
        ("78572", "78573", "78574"),
    ),
    "Pharr": (
        "Hidalgo County",
        None,
        Decimal("2.000"),
        ("78577",),
    ),
    # =================================================================
    # Greater Houston suburbs / outlying (no METRO -- 2.0% local)
    # =================================================================
    "Sugar Land": (
        # Sugar Land is in Fort Bend County; outside METRO. 8.25%.
        "Fort Bend County",
        None,
        Decimal("2.000"),
        ("77478", "77479", "77498"),
    ),
    "Missouri City": (
        # Missouri City is in Fort Bend (mostly) / Harris; not in METRO.
        "Fort Bend County",
        None,
        Decimal("2.000"),
        ("77459", "77489"),
    ),
    "Pearland": (
        # Pearland is in Brazoria (mostly) / Harris / Fort Bend; not
        # in METRO. 8.25%.
        "Brazoria County",
        None,
        Decimal("2.000"),
        ("77581", "77584"),
    ),
    "League City": (
        "Galveston County",
        None,
        Decimal("2.000"),
        ("77573",),
    ),
    "Conroe": (
        "Montgomery County",
        None,
        Decimal("2.000"),
        ("77301", "77302", "77303", "77304", "77384", "77385"),
    ),
    # =================================================================
    # Killeen / Bell County (Fort Cavazos area)
    # =================================================================
    "Killeen": (
        "Bell County",
        None,
        Decimal("2.000"),
        ("76540", "76541", "76542", "76543", "76544", "76549"),
    ),
    "Temple": (
        "Bell County",
        None,
        Decimal("2.000"),
        ("76501", "76502", "76504"),
    ),
    # =================================================================
    # Brazos Valley
    # =================================================================
    "College Station": (
        "Brazos County",
        None,
        Decimal("2.000"),
        ("77840", "77841", "77842", "77845"),
    ),
    "Bryan": (
        "Brazos County",
        None,
        Decimal("2.000"),
        ("77801", "77802", "77803", "77807", "77808"),
    ),
    # =================================================================
    # West Texas / Panhandle / Concho Valley
    # =================================================================
    "Lubbock": (
        "Lubbock County",
        None,
        Decimal("2.000"),
        (
            "79401", "79403", "79404", "79406", "79407", "79410", "79411",
            "79412", "79413", "79414", "79415", "79416", "79423", "79424",
        ),
    ),
    "Amarillo": (
        # Amarillo straddles Potter (north) and Randall (south)
        # counties; we encode under the dominant Potter County. The
        # Randall-side ZIPs (79109/79110/79118/79119) are intentionally
        # omitted; their combined rate is the same 8.25% but the
        # county binding would differ.
        "Potter County",
        None,
        Decimal("2.000"),
        ("79101", "79102", "79103", "79104", "79106", "79107", "79108"),
    ),
    "Midland": (
        "Midland County",
        None,
        Decimal("2.000"),
        ("79701", "79703", "79705", "79706", "79707"),
    ),
    "Abilene": (
        "Taylor County",
        None,
        Decimal("2.000"),
        ("79601", "79602", "79603", "79605", "79606"),
    ),
    "Wichita Falls": (
        "Wichita County",
        None,
        Decimal("2.000"),
        ("76301", "76302", "76305", "76306", "76308", "76310"),
    ),
    # =================================================================
    # East Texas
    # =================================================================
    "Tyler": (
        "Smith County",
        None,
        Decimal("2.000"),
        ("75701", "75702", "75703", "75704", "75707"),
    ),
    "Longview": (
        "Gregg County",
        None,
        Decimal("2.000"),
        ("75601", "75602", "75603", "75604", "75605"),
    ),
    "Beaumont": (
        "Jefferson County",
        None,
        Decimal("2.000"),
        ("77701", "77702", "77703", "77705", "77706", "77707", "77708"),
    ),
}


__all__ = [
    "TX_STATE_RATE_PCT",
    "TX_STATE_EFFECTIVE_FROM",
    "TX_COUNTY_RATE_PCT",
    "TX_TRANSIT_DISTRICTS",
    "TX_CITIES",
]
