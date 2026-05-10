# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""USPS PO-box-only ZIP -> state supplement for the Census ZCTA file.

The Census Bureau's ZCTA->county relationship file
(:func:`opensalestax.data.zcta_loader.parse_zcta_state_rows`) covers
ZIPs that have physical USPS delivery (street addresses), which is
the vast majority of US ZIPs. But USPS also issues "PO-box-only"
ZIPs that have NO physical delivery -- they exist only as the
remittance address for a business or as a sorting code for a
high-volume PO-box facility. Census doesn't track these because
they have no geographic boundary.

The consequence pre-iter-68 was that any GET ``/v1/calculate`` for
a PO-box-only ZIP in a flat-rate state (MA / NJ / RI / CT / KY /
MD / IN / MI) returned ``combined_rate_pct: 0`` -- the engine had
no boundary binding for that ZIP at all. Springfield MA 01101
returned 0% sales tax instead of the MA flat 6.25%. Same shape
hit Newark 07101, Trenton 08601, Providence 02901, Hartford
06101, etc.

This module is a hand-curated supplement: each entry below was
empirically discovered by probing the live engine (via /loop
audit iters), confirmed against USPS's own ZIP look-up
(usps.com/zip4) for the city/state mapping, and added so that
the next ZCTA reload binds it state-only. Future PO-box ZIPs can
be added as they're discovered -- the table only needs to grow.

For SST member states (NJ, RI), the SST quarterly file is the
primary boundary source; this supplement still helps because the
SST file also misses PO-box ZIPs (uses Census-derived data
upstream). For self-seeded flat-rate states (MA, MD, CT), the
ZCTA loader is the ONLY source of state bindings, so this
supplement is essential.

Note: only flat-rate states are listed here. For states with
local sales tax overlays (NY / CA / TX / etc.), a PO-box ZIP can
land in any of N counties / cities; without geographic data the
correct local rate cannot be determined, so falling back to
state-only would silently undercollect. Those states are out of
scope for this supplement; their PO-box ZIPs will continue to
return 0 (with the SubJurisdiction Protocol work being the
proper long-term fix).
"""

from __future__ import annotations

# Map of ZIP5 (string, zero-padded) -> state abbrev. Keep alphabetical
# by ZIP for diff-friendly maintenance.
USPS_PO_BOX_ZIPS: dict[str, str] = {
    # Massachusetts -- Springfield + Boston + Worcester PO-box ZIPs
    # (USPS Bulletin / usps.com look-up)
    "01101": "MA",
    "01102": "MA",
    "01115": "MA",
    "01199": "MA",
    "01601": "MA",  # Worcester PO box
    "01613": "MA",  # Worcester PO box
    "01655": "MA",  # Worcester unique-ZIP business
    "02101": "MA",  # Boston PO box
    "02201": "MA",  # Boston Government Center
    "02266": "MA",  # Boston PO box
    # Rhode Island -- Providence PO-box ZIPs
    "02901": "RI",
    "02902": "RI",
    # Connecticut -- Hartford + New Haven PO-box ZIPs
    "06101": "CT",
    "06102": "CT",
    "06141": "CT",
    "06501": "CT",  # New Haven PO box
    # New Jersey -- Newark / Jersey City / Paterson / Camden / Trenton
    "07101": "NJ",
    "07188": "NJ",  # Newark unique-ZIP
    "07303": "NJ",  # Jersey City PO box
    "07399": "NJ",  # Jersey City unique-ZIP
    "07509": "NJ",  # Paterson PO box
    "07599": "NJ",  # Paterson unique-ZIP
    "08101": "NJ",  # Camden PO box
    "08163": "NJ",  # Camden unique-ZIP
    "08601": "NJ",  # Trenton PO box
    # Maryland -- Baltimore PO-box ZIPs
    "21263": "MD",  # Baltimore PO box
    "21275": "MD",  # Baltimore PO box
}


__all__ = ["USPS_PO_BOX_ZIPS"]
