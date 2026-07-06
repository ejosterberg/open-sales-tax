# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Hawaii GET (General Excise Tax) rate data: state + per-county surcharges.

Source: HRS section 237-13 (state 4.0% general retail rate) and HRS
section 46-16.8 (county surcharge on state tax) plus the Hawaii
Department of Taxation **Tax Facts 31-1** (most recent revision),
which enumerates each county's currently-effective surcharge.

Hawaii is **not** a Streamlined Sales Tax member and has no SST
upstream rate file. This module hand-encodes the 4 inhabited HI
counties' surcharges (Honolulu / Hawaii / Kauai / Maui). A 5th
county FIPS exists for **Kalawao County** (FIPS 005, the former
Hansen's-disease settlement on Molokai administered by the State
Department of Health, ~80 residents); it has not enacted its own
surcharge and is encoded at 0.000% so the boundary loader can
resolve its single ZIP (96742) to a queryable rate.

### Per-county surcharges (HRS section 46-16.8)

| County         | FIPS | Surcharge | Effective    | Combined GET |
|----------------|------|-----------|--------------|--------------|
| Honolulu       | 003  | 0.500%    | 2007-01-01   | 4.500%       |
| Kauai          | 007  | 0.500%    | 2019-01-01   | 4.500%       |
| Hawaii (Big I) | 001  | 0.500%    | 2020-01-01   | 4.500%       |
| Maui           | 009  | 0.500%    | 2024-01-01   | 4.500%       |
| Kalawao        | 005  | 0.000%    | (no county tax authority -- DOH-administered) | 4.000% |

Note on Maui (corrected 2026-07-06 daily audit): the Maui County
0.5% surcharge IS in effect. It was enacted by County Ordinance 5511
(signed 2023-07-19) and took effect **2024-01-01**, running through
**2030-12-31** -- confirmed against the Hawaii Department of Taxation
county-surcharge schedule (https://tax.hawaii.gov/geninfo/countysurcharge/)
and the Maui County Council's "GET surcharge in effect for Maui
County" notice. An earlier revision of this module wrongly recorded
Maui at 0.000% ("Maui Bill No. 30 authorized but did not enact"),
which under-collected 0.5% on every Maui-County transaction from
2024-01-01 onward. The surcharge applies only to activities taxed at
the 4.0% rate (not the 0.5% wholesale or 0.15% insurance rates).

### County rate effective dates

The state portion (4.0%) has been stable since 1965-01-01 (Act 155,
SLH 1965). The per-county surcharges layered on top of the state
portion took effect at the per-county dates above; the
``HI_COUNTY_SURCHARGE_EFFECTIVE`` mapping pins each so an audit
trail can trace why a given county shows a particular combined rate
on a given historical date.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

# State rate effective since the last HI GET base-rate change
# (Act 155, SLH 1965, raised the rate from 3.5% to 4.0% effective
# 1965-01-01; the 4.0% rate has been stable since).
HI_STATE_RATE_PCT = Decimal("4.000")
HI_STATE_EFFECTIVE_FROM = dt.date(1965, 1, 1)

# Per-county GET surcharge portion (NOT including the 4.0% state
# rate). Source: HRS section 46-16.8 + Hawaii DOTAX county-surcharge
# schedule (initial ship verified 2026-05-04; Maui County corrected
# from 0.000% to 0.500% on 2026-07-06). Combined county GET = 4.0%
# state + this county portion.
HI_COUNTY_RATE_PCT: dict[str, Decimal] = {
    "Hawaii County": Decimal("0.500"),  # Big Island; effective 2020-01-01 -> 4.5%
    "Honolulu County": Decimal("0.500"),  # Oahu; effective 2007-01-01 -> 4.5%
    # Kalawao County (FIPS 005) is the former Hansen's-disease
    # settlement on Molokai administered by the State Department of
    # Health -- it has no county government authority to levy a
    # surcharge. Encoded at 0% so the ZCTA-driven boundary loader can
    # resolve its single ZIP (96742) to a queryable state-only rate.
    "Kalawao County": Decimal("0.000"),
    "Kauai County": Decimal("0.500"),  # effective 2019-01-01 -> 4.5%
    # Maui County: 0.5% surcharge in effect since 2024-01-01 (County
    # Ordinance 5511, signed 2023-07-19), running through 2030-12-31.
    # Corrected 2026-07-06 daily audit -- an earlier revision wrongly
    # recorded Maui at 0.000% and under-collected 0.5% from 2024-01-01.
    # Source: HI DOTAX county-surcharge schedule.
    "Maui County": Decimal("0.500"),  # effective 2024-01-01 -> 4.5%
}

# Per-county surcharge effective dates (HRS section 46-16.8). The
# value is the date the surcharge first applied to taxable
# transactions in that county; ``None`` indicates the county has
# not enacted a surcharge as of this module's ship date
# (2026-05-04). Audit trail for the per-county history.
HI_COUNTY_SURCHARGE_EFFECTIVE: dict[str, dt.date | None] = {
    "Hawaii County": dt.date(2020, 1, 1),  # 0.5% -- 2020-01-01
    "Honolulu County": dt.date(2007, 1, 1),  # 0.5% -- 2007-01-01 (longest-running)
    "Kalawao County": None,  # no county tax authority
    "Kauai County": dt.date(2019, 1, 1),  # 0.5% -- 2019-01-01
    "Maui County": dt.date(2024, 1, 1),  # 0.5% -- 2024-01-01 (Ord. 5511)
}


__all__ = [
    "HI_STATE_RATE_PCT",
    "HI_STATE_EFFECTIVE_FROM",
    "HI_COUNTY_RATE_PCT",
    "HI_COUNTY_SURCHARGE_EFFECTIVE",
]
