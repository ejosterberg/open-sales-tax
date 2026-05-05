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
| Maui           | 009  | 0.000%    | (none as of 2025-01-01) | 4.000% |
| Kalawao        | 005  | 0.000%    | (no county tax authority -- DOH-administered) | 4.000% |

Note on Maui: an earlier draft of HI module documentation referenced
a 0.5% Maui County surcharge "effective 2024-01-01" but the latest
Hawaii Department of Taxation Tax Facts 31-1 publication (verified
against the official DOTAX surcharge schedule on 2026-05-04) shows
Maui County at 0.000% as of 2025-01-01. Maui Bill No. 30 (2023) was
authorized but not enacted; this module encodes the actual
effective rate. If Maui later enacts the surcharge, update
``HI_COUNTY_RATE_PCT["Maui County"]`` and the corresponding
``HI_COUNTY_SURCHARGE_EFFECTIVE`` entry.

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
# rate). Source: HRS section 46-16.8 + Hawaii DOTAX Tax Facts 31-1
# (verified 2026-05-04). Combined county GET = 4.0% state +
# this county portion.
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
    # Maui County: 0% as of 2025-01-01 per HI DOTAX Tax Facts 31-1.
    # Maui Bill No. 30 (2023) authorized but did not enact a 0.5%
    # surcharge. Promote to 0.500 + add the effective date here if
    # Maui later enacts the surcharge.
    "Maui County": Decimal("0.000"),  # no county surcharge -> 4.0%
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
    "Maui County": None,  # not yet enacted as of 2025-01-01
}


__all__ = [
    "HI_STATE_RATE_PCT",
    "HI_STATE_EFFECTIVE_FROM",
    "HI_COUNTY_RATE_PCT",
    "HI_COUNTY_SURCHARGE_EFFECTIVE",
]
