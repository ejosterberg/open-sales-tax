# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Friendly names for Tennessee tax authorities.

The TN SST file references city / district jurisdictions by
opaque numeric codes (e.g. 48000 / 91951). Receipts and the TN
DOR's "Local Option Sales Tax" publications use human-readable
names (Memphis, Nashville, etc.). Tenn. Code Ann. section
67-6-705 governs the merchant's collection / remittance and
broadly aligns with the receipt-disclosure expectation.

This minimum verified set covers the four metro centres that
publish the most-used jurisdiction codes; cities not listed
fall back to the placeholder "TN-city-<code>" so codes that
need verification surface visibly without misnaming them.

Sources:
- TN DOR Local Option Sales Tax publication (2026-Q1)
- TN DOR IMPROVE Act / Transit District Sales Tax publication
  for the 91950-91954 series (effective 2025-02-01)
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Cities (key = SST jurisdiction_code from rate-file col3 for type-1 rows)
# ---------------------------------------------------------------------------
TN_CITY_NAMES: dict[str, str] = {
    "14000": "Chattanooga",
    "40000": "Knoxville",
    "48000": "Memphis",
    "52006": "Nashville (Metro)",
}


# ---------------------------------------------------------------------------
# Special districts (key = SST jurisdiction_code for type-79 rows)
# Per the IMPROVE Act (PC 181 of 2017), participating counties may
# levy a 0.5% transit-improvement sales tax. The 91950-91954 codes
# went live 2025-02-01.
# ---------------------------------------------------------------------------
TN_DISTRICT_NAMES: dict[str, str] = {
    "91951": "Nashville-Davidson IMPROVE Act Transit Sales Tax",
}


def city_name(code: str) -> str | None:
    """Return the friendly TN city name for an SST code, or None."""
    return TN_CITY_NAMES.get(code)


def district_name(code: str) -> str | None:
    """Return the friendly TN special-district name, or None."""
    return TN_DISTRICT_NAMES.get(code)


__all__ = [
    "TN_CITY_NAMES",
    "TN_DISTRICT_NAMES",
    "city_name",
    "district_name",
]
