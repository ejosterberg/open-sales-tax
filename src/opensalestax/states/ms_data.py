# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Mississippi sales tax rate + boundary data (statewide coverage).

Source: Mississippi Department of Revenue published rate schedules
plus city-specific authorizing acts (Tupelo Water Procurement
Facility Tax, Jackson Special Sales Tax). Cross-checked against
Avalara and SalesTaxHandbook on 2026-05-04. The general-retail
position that no Mississippi county imposes a county-level sales
tax is documented in Miss. Code Ann. section 27-65-241 (which
authorizes ONLY specific municipalities -- Jackson and Tupelo --
to impose a general-retail surcharge by local-and-private act);
no analogous authorization exists for counties.

Mississippi has very few general-retail local sales taxes. The
state's ordinary 7% rate (Miss. Code Ann. section 27-65-17) is
collected statewide; only a handful of municipalities have an
authorizing local-and-private act adding a city-level surcharge
on **general retail** (as distinct from the more common tourism
levies that apply only to hotels, restaurants, or rentals -- those
are NOT modeled here).

Cities seeded:

- **Jackson** (Hinds County) -- 1.0% Special Sales Tax authorized
  by Mississippi Code Ann. section 27-65-241 ("Jackson Capital
  City Convention Center" / infrastructure surcharge)
- **Tupelo** (Lee County) -- 0.25% Water Procurement Facility Tax
  authorized by H.B. 1685, Laws 2008 (Miss. Code Ann. section
  27-65-241 et seq.; codified by local-and-private bill)

Cities documented in the docstring + DOR validation grid but NOT
modeled with a local rate (their general retail combined rate is
the flat 7% statewide):

- **Hattiesburg** (Forrest County) -- has 1% Park & Recreation
  and 2% Convention Commission taxes BUT only on restaurants
  (Hattiesburg Tourism Tax) and hotels/motels; **general retail
  is 7%**. Not modeled because the engine doesn't yet support
  per-category local taxability overrides.
- **Gulfport** (Harrison County) -- general retail 7%; Harrison
  County Tourism Tax (2%) applies only to hotels and prepared
  food.
- **Biloxi** (Harrison County) -- general retail 7%; same
  Harrison County Tourism Tax (hotels/restaurants only).

**Statewide ZIP coverage via Census ZCTA**
(parallels FL/AZ/CA in v0.28 and TX/NY/MO/IL/PA in v0.29).
:meth:`Mississippi.parse_boundaries` iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` and emits state +
county bindings for every MS ZIP. Because no MS county imposes a
general-retail county sales tax (verified per Miss. Code Ann.
section 27-65-241), every county in :data:`MS_COUNTY_RATE_PCT` is
at **0% verified**, so the dollar result is unchanged from the
prior state-only fallback (7% statewide flat) -- but the audit
trail now records WHICH county each MS ZIP physically sits in.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective since 1992-07-01 (Laws 1992, ch. 484 raised
# the general rate from 6% to 7%).
MS_STATE_RATE_PCT = Decimal("7.000")
MS_STATE_EFFECTIVE_FROM = dt.date(1992, 7, 1)

# Per-county local-tax portion (NOT including the 7% state rate).
# All 82 MS counties at 0.000% verified per Miss. Code Ann. section
# 27-65-241 (no general-retail county tax authorization in MS;
# tourism/hotel-restaurant levies in some counties are NOT modeled
# here because the engine doesn't yet support per-category local
# taxability overrides). Cross-checked against MS DOR + Avalara on
# 2026-05-04. Every county is listed so the ZIP_COUNTY-driven
# boundary loader can resolve every MS ZIP to a queryable county.
MS_COUNTY_RATE_PCT: dict[str, Decimal] = {
    "Adams County": Decimal("0.000"),       # verified 0% (no county tax) per Miss. Code Ann. 27-65-241
    "Alcorn County": Decimal("0.000"),      # verified 0% (no county tax)
    "Amite County": Decimal("0.000"),       # verified 0% (no county tax)
    "Attala County": Decimal("0.000"),      # verified 0% (no county tax)
    "Benton County": Decimal("0.000"),      # verified 0% (no county tax)
    "Bolivar County": Decimal("0.000"),     # verified 0% (no county tax)
    "Calhoun County": Decimal("0.000"),     # verified 0% (no county tax)
    "Carroll County": Decimal("0.000"),     # verified 0% (no county tax)
    "Chickasaw County": Decimal("0.000"),   # verified 0% (no county tax)
    "Choctaw County": Decimal("0.000"),     # verified 0% (no county tax)
    "Claiborne County": Decimal("0.000"),   # verified 0% (no county tax)
    "Clarke County": Decimal("0.000"),      # verified 0% (no county tax)
    "Clay County": Decimal("0.000"),        # verified 0% (no county tax)
    "Coahoma County": Decimal("0.000"),     # verified 0% (no county tax)
    "Copiah County": Decimal("0.000"),      # verified 0% (no county tax)
    "Covington County": Decimal("0.000"),   # verified 0% (no county tax)
    "DeSoto County": Decimal("0.000"),      # verified 0% (no county tax)
    "Forrest County": Decimal("0.000"),     # verified 0% (no general-retail county tax; Hattiesburg Tourism Tax is hotel/restaurant only)
    "Franklin County": Decimal("0.000"),    # verified 0% (no county tax)
    "George County": Decimal("0.000"),      # verified 0% (no county tax)
    "Greene County": Decimal("0.000"),      # verified 0% (no county tax)
    "Grenada County": Decimal("0.000"),     # verified 0% (no county tax)
    "Hancock County": Decimal("0.000"),     # verified 0% (no county tax)
    "Harrison County": Decimal("0.000"),    # verified 0% (no general-retail county tax; Harrison County Tourism Tax is hotel/prepared-food only)
    "Hinds County": Decimal("0.000"),       # verified 0% (no county tax; Jackson 1% is a city-level surcharge)
    "Holmes County": Decimal("0.000"),      # verified 0% (no county tax)
    "Humphreys County": Decimal("0.000"),   # verified 0% (no county tax)
    "Issaquena County": Decimal("0.000"),   # verified 0% (no county tax)
    "Itawamba County": Decimal("0.000"),    # verified 0% (no county tax)
    "Jackson County": Decimal("0.000"),     # verified 0% (no county tax)
    "Jasper County": Decimal("0.000"),      # verified 0% (no county tax)
    "Jefferson County": Decimal("0.000"),   # verified 0% (no county tax)
    "Jefferson Davis County": Decimal("0.000"),  # verified 0% (no county tax)
    "Jones County": Decimal("0.000"),       # verified 0% (no county tax)
    "Kemper County": Decimal("0.000"),      # verified 0% (no county tax)
    "Lafayette County": Decimal("0.000"),   # verified 0% (no county tax)
    "Lamar County": Decimal("0.000"),       # verified 0% (no county tax)
    "Lauderdale County": Decimal("0.000"),  # verified 0% (no county tax)
    "Lawrence County": Decimal("0.000"),    # verified 0% (no county tax)
    "Leake County": Decimal("0.000"),       # verified 0% (no county tax)
    "Lee County": Decimal("0.000"),         # verified 0% (no county tax; Tupelo 0.25% is a city-level surcharge)
    "Leflore County": Decimal("0.000"),     # verified 0% (no county tax)
    "Lincoln County": Decimal("0.000"),     # verified 0% (no county tax)
    "Lowndes County": Decimal("0.000"),     # verified 0% (no county tax)
    "Madison County": Decimal("0.000"),     # verified 0% (no county tax)
    "Marion County": Decimal("0.000"),      # verified 0% (no county tax)
    "Marshall County": Decimal("0.000"),    # verified 0% (no county tax)
    "Monroe County": Decimal("0.000"),      # verified 0% (no county tax)
    "Montgomery County": Decimal("0.000"),  # verified 0% (no county tax)
    "Neshoba County": Decimal("0.000"),     # verified 0% (no county tax)
    "Newton County": Decimal("0.000"),      # verified 0% (no county tax)
    "Noxubee County": Decimal("0.000"),     # verified 0% (no county tax)
    "Oktibbeha County": Decimal("0.000"),   # verified 0% (no county tax)
    "Panola County": Decimal("0.000"),      # verified 0% (no county tax)
    "Pearl River County": Decimal("0.000"),  # verified 0% (no county tax)
    "Perry County": Decimal("0.000"),       # verified 0% (no county tax)
    "Pike County": Decimal("0.000"),        # verified 0% (no county tax)
    "Pontotoc County": Decimal("0.000"),    # verified 0% (no county tax)
    "Prentiss County": Decimal("0.000"),    # verified 0% (no county tax)
    "Quitman County": Decimal("0.000"),     # verified 0% (no county tax)
    "Rankin County": Decimal("0.000"),      # verified 0% (no county tax)
    "Scott County": Decimal("0.000"),       # verified 0% (no county tax)
    "Sharkey County": Decimal("0.000"),     # verified 0% (no county tax)
    "Simpson County": Decimal("0.000"),     # verified 0% (no county tax)
    "Smith County": Decimal("0.000"),       # verified 0% (no county tax)
    "Stone County": Decimal("0.000"),       # verified 0% (no county tax)
    "Sunflower County": Decimal("0.000"),   # verified 0% (no county tax)
    "Tallahatchie County": Decimal("0.000"),  # verified 0% (no county tax)
    "Tate County": Decimal("0.000"),        # verified 0% (no county tax)
    "Tippah County": Decimal("0.000"),      # verified 0% (no county tax)
    "Tishomingo County": Decimal("0.000"),  # verified 0% (no county tax)
    "Tunica County": Decimal("0.000"),      # verified 0% (no general-retail county tax; Tunica County tourism levy is hotel/restaurant only)
    "Union County": Decimal("0.000"),       # verified 0% (no county tax)
    "Walthall County": Decimal("0.000"),    # verified 0% (no county tax)
    "Warren County": Decimal("0.000"),      # verified 0% (no county tax)
    "Washington County": Decimal("0.000"),  # verified 0% (no county tax)
    "Wayne County": Decimal("0.000"),       # verified 0% (no county tax)
    "Webster County": Decimal("0.000"),     # verified 0% (no county tax)
    "Wilkinson County": Decimal("0.000"),   # verified 0% (no county tax)
    "Winston County": Decimal("0.000"),     # verified 0% (no county tax)
    "Yalobusha County": Decimal("0.000"),   # verified 0% (no county tax)
    "Yazoo County": Decimal("0.000"),       # verified 0% (no county tax)
}

# Per-city general-retail local rate. Source dates in module docstring.
# Each tuple: (county_name, city_rate_pct, [zip5s])
# Only cities with a non-zero general-retail city rate are listed;
# Hattiesburg/Gulfport/Biloxi are documented above.
MS_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    "Jackson": (
        "Hinds County",
        Decimal("1.000"),
        (
            # Jackson proper -- city-limit ZIPs in Hinds County.
            "39201", "39202", "39203", "39204", "39206", "39209",
            "39211", "39212", "39213", "39216", "39217", "39269",
            "39272",
        ),
    ),
    "Tupelo": (
        "Lee County",
        Decimal("0.250"),
        # Tupelo Water Procurement Facility Tax -- city-limit ZIPs.
        ("38801", "38802", "38804"),
    ),
}


__all__ = [
    "MS_STATE_RATE_PCT",
    "MS_STATE_EFFECTIVE_FROM",
    "MS_COUNTY_RATE_PCT",
    "MS_CITIES",
]
