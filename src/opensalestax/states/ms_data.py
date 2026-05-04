# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Mississippi sales tax rate + boundary data (city-level coverage).

Source: Mississippi Department of Revenue published rate schedules
plus city-specific authorizing acts (Tupelo Water Procurement
Facility Tax, Jackson Special Sales Tax). Cross-checked against
Avalara and SalesTaxHandbook on 2026-05-04.

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

ZIPs not in any covered city's tuple fall back to state-only via
the Census ZCTA load (correct outcome: 7% statewide).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective since 1992-07-01 (Laws 1992, ch. 484 raised
# the general rate from 6% to 7%).
MS_STATE_RATE_PCT = Decimal("7.000")
MS_STATE_EFFECTIVE_FROM = dt.date(1992, 7, 1)

# Per-county local-tax portion (NOT including the 7% state rate).
# Mississippi has no general county-level sales tax; this dict is
# kept for parallelism with the AZ/MO/SC/VA pattern. Counties listed
# here are only those touched by a covered city.
MS_COUNTY_RATE_PCT: dict[str, Decimal] = {
    "Hinds County": Decimal("0.000"),
    "Lee County": Decimal("0.000"),
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
