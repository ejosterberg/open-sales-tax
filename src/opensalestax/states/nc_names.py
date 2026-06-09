# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for North Carolina special-district tax authorities.

NC's local tax stack is dominated by Article 39 (county base) +
Article 42 (county additional) + Article 46 (county transit).
The 99XXX type-79 codes encode the per-county Article 43 or 46
public transportation tax (0.50% in the active counties).

Authoritative source (verified by deep-research iter-221):
NCDOR's "North Carolina Information for Streamlined Sales Tax
Participants" page at
https://www.ncdor.gov/taxes-forms/sales-and-use-tax/other-sales-and-use-tax-resources/streamlined-sales-tax-information/north-carolina-information-streamlined-sales-taxr-participants

NCDOR lists exactly four ACTIVE 99XXX Public Transportation Tax
codes: 99063 Durham, 99119 Mecklenburg, 99135 Orange, 99183 Wake.

iter-221 fix (2026-05-19): the iter-83 hand-curated table had
99055 mislabelled as "Durham County" (duplicating 99063). Under
the standard FIPS-pattern heuristic (99XXX -> FIPS 37XXX),
99055 maps to FIPS 37055 = Dare County. NCDOR does NOT list 99055
in its current active codes; Dare County's combined rate is 6.75%
state+county with no transit asterisk and salestaxhandbook
confirms "None of the cities or local governments within Dare
County collect additional local sales taxes." The 99055 binding
in the SST file may be a stale entry, a pre-emptive entry for
Dare County's Nov 3 2026 ballot referendum on a 0.25% Article 46
Parks-and-Recreation tax, or an undocumented levy. Either way,
the previous "Durham" label was definitively wrong; the entry is
removed below until NCDOR documents it.

Label terminology: per NCDOR's published name, the four active
codes use "Public Transportation Tax" (not "...Sales Tax" --
iter-221 minor wording fix).
"""

from __future__ import annotations

NC_DISTRICT_NAMES: dict[str, str] = {
    "99063": "Durham County Public Transportation Tax",
    "99119": "Mecklenburg County Public Transportation Tax",
    "99135": "Orange County Public Transportation Tax",
    "99183": "Wake County Public Transportation Tax",
    # 99055: REMOVED in iter-221. NCDOR does not list this code
    # in its current SST participants page. SST file binds it to
    # 279xx (Outer Banks / Dare County). Investigate before
    # re-adding -- likely either stale or pre-Nov-2026-ballot.
}


def district_name(code: str) -> str | None:
    """Return the friendly NC district name for an SST code, or None."""
    return NC_DISTRICT_NAMES.get(code)


__all__ = ["NC_DISTRICT_NAMES", "district_name"]
