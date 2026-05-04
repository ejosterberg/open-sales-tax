# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Virginia sales tax rate + boundary data (regional + top-12-city coverage).

Source: Virginia Department of Taxation rate-by-locality chart at
www.tax.virginia.gov/retail-sales-and-use-tax (verified 2026-05-04
against Avalara per-city pages for the 12 cities seeded here).

Architecture: Virginia's combined rate has three layers:

1. **State portion: 4.3%** (Va. Code section 58.1-603) -- the
   ``Virginia`` state authority.
2. **Mandatory local: 1%** (Va. Code sections 58.1-605, 58.1-606)
   -- imposed in every Virginia locality so it functions as a
   statewide floor. The existing module folds this into the state
   authority at **5.3%** so ZIPs outside the 12 covered cities
   land at the correct combined rate.
3. **Regional add-on: +0.7%** in Hampton Roads / Northern Virginia
   / Central Virginia regions; **+1.0%** in the Historic Triangle
   (James City / Williamsburg / York). Modeled as ``district``
   authorities that sit under the state.

Per-city ``city`` authorities are emitted at **0% rate** -- the
city authority is purely a friendly anchor for the per-ZIP
boundary lookup. The combined rate at any covered ZIP is:
state 5.3% + (district 0.7% if regional, else 0%) + city 0%.

Combined rates by city (2026-05-04):

- Hampton Roads (+0.7%) -> 6.0%: Virginia Beach, Norfolk,
  Chesapeake, Newport News, Hampton, Portsmouth, Suffolk
- Northern Virginia (+0.7%) -> 6.0%: Arlington, Alexandria
- Central Virginia (+0.7%) -> 6.0%: Richmond
- No regional add-on -> 5.3%: Roanoke, Lynchburg

ZIPs not in any covered city's tuple fall back to state-only at
5.3% via the Census ZCTA load. This is correct everywhere outside
the regional-add-on regions and Historic Triangle. A future ratchet
should iterate Census ZCTA->locality data so every VA ZIP in a
regional-add-on locality (not just the 12 cities here) picks up
the +0.7% / +1.0% district binding.

Note: The Historic Triangle (James City County, Williamsburg, York
County) +1.0% region is documented but NOT seeded in v0.25 -- none
of the top-12 cities are in the Triangle. Seeding it is a one-line
addition once a maintainer adds Williamsburg / York / James City to
:data:`VA_CITIES`.
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
# element (district_name, or None if no regional add-on applies).
VA_DISTRICT_RATE_PCT: dict[str, Decimal] = {
    "Hampton Roads Region": Decimal("0.700"),
    "Northern Virginia Region": Decimal("0.700"),
    "Central Virginia Region": Decimal("0.700"),
    # Historic Triangle (+1.0%) -- documented; not seeded in v0.25.
    # "Historic Triangle Region": Decimal("1.000"),
}

# Per-city seed. Tuple shape:
#   (locality_name, district_name_or_None, [zip5s])
# - locality_name is what shows up as the parent_authority_name on
#   the city RateRow. Independent cities are named directly; for
#   counties (Arlington / Fairfax / etc.) the county name is used.
# - district_name None means "no regional add-on" (locality is
#   outside Hampton Roads / Northern VA / Central VA / Historic
#   Triangle). Combined rate at those ZIPs is 5.3% via state.
# - The zips are the primary delivery ZIPs for each city's centroid.
VA_CITIES: dict[str, tuple[str | None, tuple[str, ...]]] = {
    # ---- Hampton Roads (+0.7% -> 6.0%) ----
    "Virginia Beach": (
        "Hampton Roads Region",
        ("23451", "23452", "23453", "23454", "23455", "23456",
         "23457", "23459", "23460", "23461", "23462", "23464"),
    ),
    "Norfolk": (
        "Hampton Roads Region",
        ("23502", "23503", "23504", "23505", "23507", "23508",
         "23509", "23510", "23511", "23513", "23517", "23518"),
    ),
    "Chesapeake": (
        "Hampton Roads Region",
        ("23320", "23321", "23322", "23323", "23324", "23325"),
    ),
    "Newport News": (
        "Hampton Roads Region",
        ("23601", "23602", "23603", "23605", "23606", "23607",
         "23608"),
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
        ("22201", "22202", "22203", "22204", "22205", "22206",
         "22207", "22209", "22213", "22214"),
    ),
    "Alexandria": (
        "Northern Virginia Region",
        ("22301", "22302", "22304", "22305", "22311", "22312",
         "22314"),
    ),
    # ---- Central Virginia (+0.7% -> 6.0%) ----
    "Richmond": (
        "Central Virginia Region",
        ("23218", "23219", "23220", "23221", "23222", "23223",
         "23224", "23225", "23226", "23227", "23230", "23231",
         "23234", "23235"),
    ),
    # ---- No regional add-on (-> 5.3%) ----
    "Roanoke": (
        None,
        ("24011", "24012", "24013", "24014", "24015", "24016",
         "24017", "24018", "24019"),
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
    "VA_CITIES",
]
