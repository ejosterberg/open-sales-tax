# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Ohio special-district tax authorities.

OH has no city sales tax; the local layer is county + transit
authority. This module provides receipt-grade names for the
four major regional transit-authority sales taxes that the
OH DOR's "Sales and Use Tax Rate Schedule" publishes.

Sources: OH DOR rate publication (2026-Q1) + each transit
authority's own enabling legislation.
"""

from __future__ import annotations

# Key: SST jurisdiction_code (col3 in rate-file type-63 rows)
OH_DISTRICT_NAMES: dict[str, str] = {
    "18000": "Greater Cleveland Regional Transit Authority",
    "25000": "Central Ohio Transit Authority (COTA)",
    "31000": "Southwest Ohio Regional Transit Authority (SORTA)",
    "48000": "Toledo Area Regional Transit Authority (TARTA)",
}


def district_name(code: str) -> str | None:
    """Return the friendly OH district name for an SST code, or None."""
    return OH_DISTRICT_NAMES.get(code)


__all__ = ["OH_DISTRICT_NAMES", "district_name"]
