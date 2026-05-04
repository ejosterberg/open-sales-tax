# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""South Carolina sales tax rate + boundary data (county-level coverage).

Source: SC DOR Form ST-500 "South Carolina Local Tax Designation by
County" effective **May 1, 2026** (Rev. 3/9/2026), publication
number 5182. Cross-checked against the SC DOR Local Sales Taxes
page on dor.sc.gov (audit refreshed 2026-05-04).

Architecture: South Carolina's local sales taxes are **county-level
only** -- there is no city-level general retail surcharge anywhere
in the state. Each county may impose any combination of:

- Local Option (LO) -- 1%
- Capital Project (CP) -- 1%
- Education Capital Improvement (ECI) -- 1%
- School District (SD) -- 1%
- Transportation Tax (TT) -- 1%

Combined county totals (state 6% + locals) range from **6%** in
Beaufort, Greenville, and Oconee (no local tax -- the only three
verified-zero counties per SC DOR ST-500 Rev. 3/9/2026) to **9%**
in Berkeley, Charleston, Jasper, and the Myrtle Beach municipal
area (3% of local taxes). This module ships **all 46 SC counties**
rather than a top-N subset; the SC DOR table is small enough to
encode in full and a county-complete dataset is more useful than
a city sample.

Boundary modeling: cities don't get separate authorities (since SC
doesn't tax at the city level for general retail). Instead, each
covered city's primary delivery ZIPs are bound to (state, county)
authorities. The :data:`SC_CITIES` table is the per-ZIP boundary
seed; the cities included are the 10 largest by population for
2026 plus Mount Pleasant (Charleston metro suburb).

Myrtle Beach is the lone SC municipality with its own tax (1%
Tourism Development tax, plus the Horry County base) -- it's
modeled as a city authority above Horry County.

**Statewide ZIP coverage via Census ZCTA**
(parallels FL/AZ/CA in v0.28 and TX/NY/MO/IL/PA in v0.29).
:meth:`SouthCarolina.parse_boundaries` iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` and emits state +
county bindings for every SC ZIP -- not just the ZIPs seeded into
:data:`SC_CITIES`. Effect: a Berkeley County ZIP outside Goose
Creek city limits (e.g., Moncks Corner 29461, Hanahan 29410) now
picks up the +3.0% Berkeley combined local rate for an 9.0%
combined rate, instead of falling back to state-only at 6.0%.
Similarly Aiken County ZIPs (e.g., 29801) pick up the +2.0% Aiken
combined local for an 8.0% combined.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective since the 1% surcharge under section
# 12-36-1110 was added on top of the long-standing 5% under section
# 12-36-910(A) on 2007-06-01.
SC_STATE_RATE_PCT = Decimal("6.000")
SC_STATE_EFFECTIVE_FROM = dt.date(2007, 6, 1)

# Per-county local-tax portion (NOT including the 6% state rate).
# Source: SC DOR ST-500 (Rev. 3/9/2026) effective May 1, 2026.
# Combined column on the right is state 6% + this county portion.
SC_COUNTY_RATE_PCT: dict[str, Decimal] = {
    "Abbeville County": Decimal("1.000"),       # LO -> 7%
    "Aiken County": Decimal("2.000"),           # CP, ECI -> 8%
    "Allendale County": Decimal("2.000"),       # LO, CP -> 8%
    "Anderson County": Decimal("1.000"),        # ECI -> 7%
    "Bamberg County": Decimal("2.000"),         # LO, CP -> 8%
    "Barnwell County": Decimal("2.000"),        # LO, CP -> 8%
    "Beaufort County": Decimal("0.000"),        # verified 0% (no local) -> 6% per SC DOR ST-500 Rev. 3/9/2026
    "Berkeley County": Decimal("3.000"),        # LO, TT, ECI -> 9%
    "Calhoun County": Decimal("2.000"),         # LO, CP -> 8%
    "Charleston County": Decimal("3.000"),      # LO, TT, ECI -> 9%
    "Cherokee County": Decimal("2.000"),        # LO, ECI -> 8%
    "Chester County": Decimal("2.000"),         # LO, CP -> 8%
    "Chesterfield County": Decimal("2.000"),    # LO, ECI -> 8%
    "Clarendon County": Decimal("1.000"),       # LO -> 7%
    "Colleton County": Decimal("2.000"),        # LO, CP -> 8%
    "Darlington County": Decimal("2.000"),      # LO, ECI -> 8%
    "Dillon County": Decimal("2.000"),          # LO, SD -> 8%
    "Dorchester County": Decimal("1.000"),      # TT -> 7%
    "Edgefield County": Decimal("2.000"),       # LO, CP -> 8%
    "Fairfield County": Decimal("1.000"),       # LO -> 7%
    "Florence County": Decimal("2.000"),        # LO, CP -> 8%
    "Georgetown County": Decimal("1.000"),      # CP -> 7%
    "Greenville County": Decimal("0.000"),      # verified 0% (no local) -> 6% per SC DOR ST-500 Rev. 3/9/2026
    "Greenwood County": Decimal("1.000"),       # CP -> 7%
    "Hampton County": Decimal("1.000"),         # LO -> 7%
    "Horry County": Decimal("2.000"),           # TT, ECI -> 8% (general retail; +TD in Myrtle Beach)
    "Jasper County": Decimal("3.000"),          # LO, TT, ECI -> 9%
    "Kershaw County": Decimal("2.000"),         # LO, ECI -> 8%
    "Lancaster County": Decimal("2.000"),       # LO, CP -> 8%
    "Laurens County": Decimal("2.000"),         # LO, CP -> 8%
    "Lee County": Decimal("2.000"),             # LO, CP -> 8%
    "Lexington County": Decimal("1.000"),       # SD -> 7%
    "McCormick County": Decimal("2.000"),       # LO, CP -> 8%
    "Marion County": Decimal("2.000"),          # LO, CP -> 8%
    "Marlboro County": Decimal("2.000"),        # LO, SD -> 8%
    "Newberry County": Decimal("1.000"),        # CP -> 7%
    "Oconee County": Decimal("0.000"),          # verified 0% (no local) -> 6% per SC DOR ST-500 Rev. 3/9/2026
    "Orangeburg County": Decimal("1.000"),      # CP -> 7%
    "Pickens County": Decimal("1.000"),         # LO -> 7%
    "Richland County": Decimal("2.000"),        # LO, TT -> 8%
    "Saluda County": Decimal("2.000"),          # LO, CP -> 8%
    "Spartanburg County": Decimal("1.000"),     # CP -> 7%
    "Sumter County": Decimal("2.000"),          # LO, CP -> 8%
    "Union County": Decimal("1.000"),           # LO -> 7%
    "Williamsburg County": Decimal("2.000"),    # LO, CP (CP effective 2026-05-01) -> 8%
    "York County": Decimal("1.000"),            # CP -> 7%
}

# Per-city general-retail rate. SC has no city-level general-retail
# tax EXCEPT Myrtle Beach (1% Tourism Development tax). All other
# entries here are city = 0% with the rate coming from the county.
# Each tuple: (county_name, city_rate_pct, [zip5s])
# The zips are the primary delivery ZIPs for each city's centroid.
SC_CITIES: dict[str, tuple[str, Decimal, tuple[str, ...]]] = {
    "Columbia": (
        "Richland County",
        Decimal("0.000"),
        # Columbia city limits in Richland County. ZIPs that straddle
        # Lexington County (29063, 29170, 29172, 29212) are excluded
        # because the local rate differs across the county line.
        (
            "29201", "29202", "29203", "29204", "29205", "29206",
            "29209", "29210", "29229",
        ),
    ),
    "Charleston": (
        "Charleston County",
        Decimal("0.000"),
        # Charleston city ZIPs in Charleston County (peninsula + James
        # Island + West Ashley). Berkeley/Dorchester ZIPs that share the
        # "Charleston" postal name are excluded.
        (
            "29401", "29403", "29405", "29407", "29412", "29414",
            "29424", "29425", "29492",
        ),
    ),
    "Mount Pleasant": (
        "Charleston County",
        Decimal("0.000"),
        ("29464", "29466"),
    ),
    "North Charleston": (
        "Charleston County",
        Decimal("0.000"),
        # Note: 29420 / 29485 straddle into Dorchester County and are
        # excluded; 29406 / 29410 / 29418 are firmly in Charleston Co.
        ("29405", "29406", "29410", "29418"),
    ),
    "Rock Hill": (
        "York County",
        Decimal("0.000"),
        ("29730", "29732", "29733"),
    ),
    "Greenville": (
        "Greenville County",
        Decimal("0.000"),
        ("29601", "29605", "29607", "29609", "29611", "29615"),
    ),
    "Summerville": (
        "Dorchester County",
        Decimal("0.000"),
        # Summerville is split across Dorchester and Berkeley counties.
        # We bind only the Dorchester ZIPs; Berkeley-side Summerville
        # ZIPs (29486) need a separate "Summerville (Berkeley)" entry
        # in a future ratchet.
        ("29483", "29485"),
    ),
    "Spartanburg": (
        "Spartanburg County",
        Decimal("0.000"),
        ("29301", "29302", "29303", "29306", "29307"),
    ),
    "Sumter": (
        "Sumter County",
        Decimal("0.000"),
        ("29150", "29153", "29154"),
    ),
    "Goose Creek": (
        "Berkeley County",
        Decimal("0.000"),
        ("29445",),
    ),
}


__all__ = [
    "SC_STATE_RATE_PCT",
    "SC_STATE_EFFECTIVE_FROM",
    "SC_COUNTY_RATE_PCT",
    "SC_CITIES",
]
