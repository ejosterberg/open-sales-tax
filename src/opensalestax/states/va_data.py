# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Virginia sales tax rate + boundary data (statewide jurisdiction coverage).

Source: Virginia Department of Taxation "Sales Tax Rates" publication
at https://www.tax.virginia.gov/sales-tax-rates and the underlying
statutes in Va. Code Title 58.1 Chapter 6 (verified 2026-05-04;
cross-checked against VA Tax's per-locality rate tables and
Avalara's per-city rate pages for the seeded cities).

Architecture: Virginia's combined rate has three modeled layers:

1. **State portion: 4.3%** (Va. Code section 58.1-603) -- the
   ``Virginia`` state authority.
2. **Mandatory local: 1%** (Va. Code sections 58.1-605, 58.1-606)
   -- imposed in EVERY Virginia locality so it functions as a
   statewide floor. Folded into the state authority at **5.3%**
   so any VA ZIP lands at the correct combined rate via state
   alone. Because of this fold, :data:`VA_COUNTY_RATE_PCT` is
   uniformly **0%** for every locality -- the local 1% is NOT
   double-counted by being added at the county layer.
3. **Regional add-on (district)**: imposed on top of the 5.3%
   state base in three regions plus the Historic Triangle:

   - **+0.7%** Hampton Roads (HB 2313, 2013) -> 6.0% combined
   - **+0.7%** Northern Virginia (HB 2313, 2013) -> 6.0% combined
   - **+0.7%** Central Virginia (HB 1414, 2020) -> 6.0% combined
   - **+1.0%** Historic Triangle (Va. Code section 58.1-606.1,
     2018) -- stacks ON TOP of Hampton Roads in the three
     overlapping jurisdictions (James City County, York County,
     Williamsburg city) -> 7.0% combined

Per-county (or per-independent-city) ``district`` binding is
authoritative: :data:`VA_COUNTY_DISTRICT` maps each of the 133
VA jurisdictions (95 counties + 38 independent cities) to its
regional district name (or None for localities outside any
regional add-on). The Historic Triangle is encoded as a separate
``district2`` layer for the three overlap jurisdictions.

Per-city ``city`` authorities are emitted at **0% rate** -- the
city authority is purely a friendly anchor for per-ZIP boundary
lookup. The combined rate at any VA ZIP is computed as:
state 5.3% + (district 0.7% if regional, else 0%) + (district2
1.0% if Historic Triangle, else 0%) + city 0%.

**Statewide ZIP coverage via Census ZCTA**
(parallels FL/AZ/CA in v0.28 and TX/NY/MO/IL/PA in v0.29).
:meth:`Virginia.parse_boundaries` iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` and emits state +
county + (district if mapped) bindings for every VA ZIP -- not
just the ZIPs in the top-12 city seed. Effect: every Hampton Roads
suburb in Isle of Wight County (e.g., Smithfield 23430) now picks
up the +0.7% Hampton Roads district binding, and every Loudoun /
Prince William / Fairfax County ZIP in Northern Virginia picks up
the +0.7% NoVA district -- instead of falling back to state-only
at 5.3%.

Cross-checked against Avalara per-city rate pages for the 12
seeded cities and against VA Tax's "Sales Tax Rates" page on
2026-05-04 for the regional-district roll-up. Sources cited
inline below for each non-trivial mapping.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State combined rate (state 4.3% + mandatory local 1%) used for
# every VA ZIP via the existing state authority. Effective 2013-07-01
# when HB 2313 raised the state portion from 4.0% to 4.3% and added
# the regional transportation taxes.
VA_STATE_RATE_PCT = Decimal("5.300")
VA_STATE_EFFECTIVE_FROM = dt.date(2013, 7, 1)

# Regional district add-ons, modeled as ``district`` authorities
# that sit under the Virginia state authority. Each district is
# attached to the cities listed in VA_CITIES via the second tuple
# element (district_name, or None if no regional add-on applies),
# and to counties / independent cities via VA_COUNTY_DISTRICT below.
#
# Historic Triangle is included here as of v0.31; it stacks ON TOP
# of Hampton Roads in the three overlapping jurisdictions (James
# City County, York County, Williamsburg city) per Va. Code section
# 58.1-606.1 (effective 2018-07-01).
VA_DISTRICT_RATE_PCT: dict[str, Decimal] = {
    "Hampton Roads Region": Decimal("0.700"),
    "Northern Virginia Region": Decimal("0.700"),
    "Central Virginia Region": Decimal("0.700"),
    "Historic Triangle Region": Decimal("1.000"),
}

# Per-jurisdiction local-tax portion (NOT including the 5.3% state
# rate). All 133 VA jurisdictions are listed at 0.000% because the
# mandatory 1% local option (Va. Code sections 58.1-605, 58.1-606)
# is already folded into the 5.3% state rate above; adding it here
# would double-count. The county layer exists ONLY to give every VA
# ZIP a county-level authority for binding (which the engine needs
# so that the ZIP_COUNTY-driven boundary loader has somewhere to
# point each ZIP).
#
# Source: VA Tax "Sales Tax Rates" publication (verified 2026-05-04).
# Names match the canonical Census FIPS names in
# :mod:`opensalestax.data.county_names` (independent cities use
# "<Name> city" lowercase suffix per Census convention).
VA_COUNTY_RATE_PCT: dict[str, Decimal] = {
    # ---- 95 counties ----
    "Accomack County": Decimal("0.000"),
    "Albemarle County": Decimal("0.000"),
    "Alleghany County": Decimal("0.000"),
    "Amelia County": Decimal("0.000"),
    "Amherst County": Decimal("0.000"),
    "Appomattox County": Decimal("0.000"),
    "Arlington County": Decimal("0.000"),
    "Augusta County": Decimal("0.000"),
    "Bath County": Decimal("0.000"),
    "Bedford County": Decimal("0.000"),
    "Bland County": Decimal("0.000"),
    "Botetourt County": Decimal("0.000"),
    "Brunswick County": Decimal("0.000"),
    "Buchanan County": Decimal("0.000"),
    "Buckingham County": Decimal("0.000"),
    "Campbell County": Decimal("0.000"),
    "Caroline County": Decimal("0.000"),
    "Carroll County": Decimal("0.000"),
    "Charles City County": Decimal("0.000"),
    "Charlotte County": Decimal("0.000"),
    "Chesterfield County": Decimal("0.000"),
    "Clarke County": Decimal("0.000"),
    "Craig County": Decimal("0.000"),
    "Culpeper County": Decimal("0.000"),
    "Cumberland County": Decimal("0.000"),
    "Dickenson County": Decimal("0.000"),
    "Dinwiddie County": Decimal("0.000"),
    "Essex County": Decimal("0.000"),
    "Fairfax County": Decimal("0.000"),
    "Fauquier County": Decimal("0.000"),
    "Floyd County": Decimal("0.000"),
    "Fluvanna County": Decimal("0.000"),
    "Franklin County": Decimal("0.000"),
    "Frederick County": Decimal("0.000"),
    "Giles County": Decimal("0.000"),
    "Gloucester County": Decimal("0.000"),
    "Goochland County": Decimal("0.000"),
    "Grayson County": Decimal("0.000"),
    "Greene County": Decimal("0.000"),
    "Greensville County": Decimal("0.000"),
    "Halifax County": Decimal("0.000"),
    "Hanover County": Decimal("0.000"),
    "Henrico County": Decimal("0.000"),
    "Henry County": Decimal("0.000"),
    "Highland County": Decimal("0.000"),
    "Isle of Wight County": Decimal("0.000"),
    "James City County": Decimal("0.000"),
    "King and Queen County": Decimal("0.000"),
    "King George County": Decimal("0.000"),
    "King William County": Decimal("0.000"),
    "Lancaster County": Decimal("0.000"),
    "Lee County": Decimal("0.000"),
    "Loudoun County": Decimal("0.000"),
    "Louisa County": Decimal("0.000"),
    "Lunenburg County": Decimal("0.000"),
    "Madison County": Decimal("0.000"),
    "Mathews County": Decimal("0.000"),
    "Mecklenburg County": Decimal("0.000"),
    "Middlesex County": Decimal("0.000"),
    "Montgomery County": Decimal("0.000"),
    "Nelson County": Decimal("0.000"),
    "New Kent County": Decimal("0.000"),
    "Northampton County": Decimal("0.000"),
    "Northumberland County": Decimal("0.000"),
    "Nottoway County": Decimal("0.000"),
    "Orange County": Decimal("0.000"),
    "Page County": Decimal("0.000"),
    "Patrick County": Decimal("0.000"),
    "Pittsylvania County": Decimal("0.000"),
    "Powhatan County": Decimal("0.000"),
    "Prince Edward County": Decimal("0.000"),
    "Prince George County": Decimal("0.000"),
    "Prince William County": Decimal("0.000"),
    "Pulaski County": Decimal("0.000"),
    "Rappahannock County": Decimal("0.000"),
    "Richmond County": Decimal("0.000"),
    "Roanoke County": Decimal("0.000"),
    "Rockbridge County": Decimal("0.000"),
    "Rockingham County": Decimal("0.000"),
    "Russell County": Decimal("0.000"),
    "Scott County": Decimal("0.000"),
    "Shenandoah County": Decimal("0.000"),
    "Smyth County": Decimal("0.000"),
    "Southampton County": Decimal("0.000"),
    "Spotsylvania County": Decimal("0.000"),
    "Stafford County": Decimal("0.000"),
    "Surry County": Decimal("0.000"),
    "Sussex County": Decimal("0.000"),
    "Tazewell County": Decimal("0.000"),
    "Warren County": Decimal("0.000"),
    "Washington County": Decimal("0.000"),
    "Westmoreland County": Decimal("0.000"),
    "Wise County": Decimal("0.000"),
    "Wythe County": Decimal("0.000"),
    "York County": Decimal("0.000"),
    # ---- 38 independent cities (FIPS 510-840) ----
    "Alexandria city": Decimal("0.000"),
    "Bristol city": Decimal("0.000"),
    "Buena Vista city": Decimal("0.000"),
    "Charlottesville city": Decimal("0.000"),
    "Chesapeake city": Decimal("0.000"),
    "Colonial Heights city": Decimal("0.000"),
    "Covington city": Decimal("0.000"),
    "Danville city": Decimal("0.000"),
    "Emporia city": Decimal("0.000"),
    "Fairfax city": Decimal("0.000"),
    "Falls Church city": Decimal("0.000"),
    "Franklin city": Decimal("0.000"),
    "Fredericksburg city": Decimal("0.000"),
    "Galax city": Decimal("0.000"),
    "Hampton city": Decimal("0.000"),
    "Harrisonburg city": Decimal("0.000"),
    "Hopewell city": Decimal("0.000"),
    "Lexington city": Decimal("0.000"),
    "Lynchburg city": Decimal("0.000"),
    "Manassas city": Decimal("0.000"),
    "Manassas Park city": Decimal("0.000"),
    "Martinsville city": Decimal("0.000"),
    "Newport News city": Decimal("0.000"),
    "Norfolk city": Decimal("0.000"),
    "Norton city": Decimal("0.000"),
    "Petersburg city": Decimal("0.000"),
    "Poquoson city": Decimal("0.000"),
    "Portsmouth city": Decimal("0.000"),
    "Radford city": Decimal("0.000"),
    "Richmond city": Decimal("0.000"),
    "Roanoke city": Decimal("0.000"),
    "Salem city": Decimal("0.000"),
    "Staunton city": Decimal("0.000"),
    "Suffolk city": Decimal("0.000"),
    "Virginia Beach city": Decimal("0.000"),
    "Waynesboro city": Decimal("0.000"),
    "Williamsburg city": Decimal("0.000"),
    "Winchester city": Decimal("0.000"),
}

# Per-jurisdiction regional district mapping. None means the
# jurisdiction is outside all four regional add-ons (state 5.3%
# combined). A single district name means the jurisdiction picks
# up that single +0.7% regional add-on (-> 6.0% combined).
#
# Historic Triangle is encoded as a SECOND district layer below
# (VA_HISTORIC_TRIANGLE) since the three Historic Triangle
# jurisdictions (James City County, York County, Williamsburg city)
# also belong to Hampton Roads -- they receive BOTH +0.7% Hampton
# Roads AND +1.0% Historic Triangle for a 7.0% combined rate.
#
# Source: VA Tax "Sales Tax Rates" publication -> "Regional Tax
# Rates" section (verified 2026-05-04). Roll-up of:
# - Hampton Roads (HB 2313, 2013): Va. Code section 58.1-603.1
# - Northern Virginia (HB 2313, 2013): Va. Code section 58.1-603.1
# - Central Virginia (HB 1414, 2020): Va. Code section 58.1-603.2
VA_COUNTY_DISTRICT: dict[str, str | None] = {
    # ---- Hampton Roads Region ----
    # Counties: Isle of Wight, James City, Southampton, York
    # Cities: Chesapeake, Franklin, Hampton, Newport News, Norfolk,
    #         Poquoson, Portsmouth, Suffolk, Virginia Beach, Williamsburg
    "Isle of Wight County": "Hampton Roads Region",
    "James City County": "Hampton Roads Region",
    "Southampton County": "Hampton Roads Region",
    "York County": "Hampton Roads Region",
    "Chesapeake city": "Hampton Roads Region",
    "Franklin city": "Hampton Roads Region",
    "Hampton city": "Hampton Roads Region",
    "Newport News city": "Hampton Roads Region",
    "Norfolk city": "Hampton Roads Region",
    "Poquoson city": "Hampton Roads Region",
    "Portsmouth city": "Hampton Roads Region",
    "Suffolk city": "Hampton Roads Region",
    "Virginia Beach city": "Hampton Roads Region",
    "Williamsburg city": "Hampton Roads Region",
    # ---- Northern Virginia Region ----
    # Counties: Arlington, Fairfax, Loudoun, Prince William
    # Cities: Alexandria, Fairfax, Falls Church, Manassas, Manassas Park
    "Arlington County": "Northern Virginia Region",
    "Fairfax County": "Northern Virginia Region",
    "Loudoun County": "Northern Virginia Region",
    "Prince William County": "Northern Virginia Region",
    "Alexandria city": "Northern Virginia Region",
    "Fairfax city": "Northern Virginia Region",
    "Falls Church city": "Northern Virginia Region",
    "Manassas city": "Northern Virginia Region",
    "Manassas Park city": "Northern Virginia Region",
    # ---- Central Virginia Region ----
    # Counties: Charles City, Chesterfield, Goochland, Hanover,
    #          Henrico, New Kent, Powhatan
    # Cities: Colonial Heights, Hopewell, Petersburg, Richmond
    "Charles City County": "Central Virginia Region",
    "Chesterfield County": "Central Virginia Region",
    "Goochland County": "Central Virginia Region",
    "Hanover County": "Central Virginia Region",
    "Henrico County": "Central Virginia Region",
    "New Kent County": "Central Virginia Region",
    "Powhatan County": "Central Virginia Region",
    "Colonial Heights city": "Central Virginia Region",
    "Hopewell city": "Central Virginia Region",
    "Petersburg city": "Central Virginia Region",
    "Richmond city": "Central Virginia Region",
}

# Historic Triangle Region (Va. Code section 58.1-606.1, effective
# 2018-07-01): a +1.0% regional add-on imposed in James City County,
# York County, and the City of Williamsburg. These three jurisdictions
# ALSO belong to Hampton Roads, so they pick up BOTH Hampton Roads
# (+0.7%) AND Historic Triangle (+1.0%) for a combined rate of:
# state 5.3% + 0.7% + 1.0% = **7.0%**.
VA_HISTORIC_TRIANGLE: frozenset[str] = frozenset(
    {
        "James City County",
        "York County",
        "Williamsburg city",
    }
)

# Per-city seed. Tuple shape:
#   (locality_name, district_name_or_None, [zip5s])
# - locality_name is what shows up as the parent_authority_name on
#   the city RateRow. Independent cities are named directly; for
#   counties (Arlington / Fairfax / etc.) the county name is used.
# - district_name None means "no regional add-on" (locality is
#   outside Hampton Roads / Northern VA / Central VA / Historic
#   Triangle). Combined rate at those ZIPs is 5.3% via state.
# - The zips are the primary delivery ZIPs for each city's centroid.
#
# Note: as of v0.31 the per-county district binding via
# :data:`VA_COUNTY_DISTRICT` covers the entire state via the
# ZIP_COUNTY-driven boundary loader. The per-city seed below is
# preserved as a friendly-anchor layer (so the engine can label a
# Virginia Beach receipt with "Virginia Beach" rather than just
# "Virginia Beach city" the FIPS county-equivalent name).
VA_CITIES: dict[str, tuple[str | None, tuple[str, ...]]] = {
    # ---- Hampton Roads (+0.7% -> 6.0%) ----
    "Virginia Beach": (
        "Hampton Roads Region",
        (
            "23451",
            "23452",
            "23453",
            "23454",
            "23455",
            "23456",
            "23457",
            "23459",
            "23460",
            "23461",
            "23462",
            "23464",
        ),
    ),
    "Norfolk": (
        "Hampton Roads Region",
        (
            "23502",
            "23503",
            "23504",
            "23505",
            "23507",
            "23508",
            "23509",
            "23510",
            "23511",
            "23513",
            "23517",
            "23518",
        ),
    ),
    "Chesapeake": (
        "Hampton Roads Region",
        ("23320", "23321", "23322", "23323", "23324", "23325"),
    ),
    "Newport News": (
        "Hampton Roads Region",
        ("23601", "23602", "23603", "23605", "23606", "23607", "23608"),
    ),
    "Hampton": (
        "Hampton Roads Region",
        ("23661", "23663", "23664", "23665", "23666", "23669"),
    ),
    "Portsmouth": (
        "Hampton Roads Region",
        ("23701", "23702", "23703", "23704", "23707"),
    ),
    "Suffolk": (
        "Hampton Roads Region",
        ("23432", "23433", "23434", "23435", "23436", "23437"),
    ),
    # ---- Northern Virginia (+0.7% -> 6.0%) ----
    "Arlington": (
        "Northern Virginia Region",
        ("22201", "22202", "22203", "22204", "22205", "22206", "22207", "22209", "22213", "22214"),
    ),
    "Alexandria": (
        "Northern Virginia Region",
        ("22301", "22302", "22304", "22305", "22311", "22312", "22314"),
    ),
    # ---- Central Virginia (+0.7% -> 6.0%) ----
    "Richmond": (
        "Central Virginia Region",
        (
            "23218",
            "23219",
            "23220",
            "23221",
            "23222",
            "23223",
            "23224",
            "23225",
            "23226",
            "23227",
            "23230",
            "23231",
            "23234",
            "23235",
        ),
    ),
    # ---- No regional add-on (-> 5.3%) ----
    "Roanoke": (
        None,
        ("24011", "24012", "24013", "24014", "24015", "24016", "24017", "24018", "24019"),
    ),
    "Lynchburg": (
        None,
        ("24501", "24502", "24503", "24504"),
    ),
}


__all__ = [
    "VA_STATE_RATE_PCT",
    "VA_STATE_EFFECTIVE_FROM",
    "VA_DISTRICT_RATE_PCT",
    "VA_COUNTY_RATE_PCT",
    "VA_COUNTY_DISTRICT",
    "VA_HISTORIC_TRIANGLE",
    "VA_CITIES",
]
