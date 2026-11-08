# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Ohio special-district tax authorities.

OH has no city sales tax; the local layer is county + transit
authority. This module provides receipt-grade names for the
seven major regional transit-authority sales taxes that the
OH DOR's "Sales and Use Tax Rate Schedule" publishes, plus the
two county-specific COTA LinkUS extensions that took effect
2025-04-01 when voters approved the extension of the Central
Ohio Transit Authority's sales-tax service area into parts of
Delaware and Union counties.

Sources: OH DOR rate publication (2026-Q1), the OH DOR's own
"The Finder" address lookup (tax.ohio.gov), and each transit
authority's own enabling legislation. Code 96000 / 98000
mapping confirmed 2026-11-08 via The Finder which labels an
8.00% Delaware-county address (8700 Lyra Dr, Columbus 43240)
as "Delaware (21) with COTA" with Transit Rate 1.00% (96000),
and the analogous Union-county pattern for 98000.
"""

from __future__ import annotations

# Key: SST jurisdiction_code (col3 in rate-file type-63 rows)
OH_DISTRICT_NAMES: dict[str, str] = {
    "18000": "Greater Cleveland Regional Transit Authority",
    "25000": "Central Ohio Transit Authority (COTA)",
    "31000": "Southwest Ohio Regional Transit Authority (SORTA)",
    "48000": "Toledo Area Regional Transit Authority (TARTA)",
    "50000": "Western Reserve Transit Authority (WRTA)",
    "57000": "Greater Dayton Regional Transit Authority (GDRTA)",
    "77000": "METRO Regional Transit Authority (Akron)",
    # COTA LinkUS extensions, effective 2025-04-01 (Issue 47,
    # Nov 2024 ballot). Each is COTA's Delaware / Union county
    # service-area sales tax; OH DOR Finder labels them "COTA"
    # on the county side of Delaware / Union ZIPs that border
    # Franklin (43017 Dublin, 43035 Lewis Center, 43081/43082
    # Westerville, 43240 Columbus/Polaris on the Delaware side;
    # 43016 Hilliard, 43064 Plain City on the Union side).
    "96000": "Central Ohio Transit Authority (COTA) — Delaware County",
    "98000": "Central Ohio Transit Authority (COTA) — Union County",
}


def district_name(code: str) -> str | None:
    """Return the friendly OH district name for an SST code, or None."""
    return OH_DISTRICT_NAMES.get(code)


__all__ = ["OH_DISTRICT_NAMES", "district_name"]
