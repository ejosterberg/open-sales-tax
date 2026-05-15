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
    # iter-84 additions (4): Brentwood / Cleveland / Franklin /
    # Winchester via probe + FIPS Place last-5-digit match
    "08280": "Brentwood",  # ZIP 37027 (Williamson Co; FIPS 4708280)
    "14000": "Chattanooga",
    "15160": "Clarksville",
    "15400": "Cleveland",  # ZIP 37311 (Bradley Co; FIPS 4715400)
    "27740": "Franklin",  # ZIP 37064 (Williamson Co; FIPS 4727740)
    "40000": "Knoxville",
    "48000": "Memphis",
    "51560": "Murfreesboro",
    "52006": "Nashville (Metro)",
    "81080": "Winchester",  # ZIP 37398 (Franklin Co; FIPS 4781080)
    # iter-177 additions (14, 2026-05-15): probed common TN ZIPs and
    # picked up the curated names for 14 more cities verified by
    # ZIP probe + FIPS Place last-5-digit match. Covers Nashville
    # suburbs (Hendersonville/La Vergne/Lebanon/Smyrna/Springfield),
    # Memphis suburbs (Bartlett/Germantown), and major secondary
    # cities (Columbia/Jackson/Cookeville/Crossville/Sparta/
    # Livingston/Mountain City).
    "03440": "Bartlett",  # ZIP 38133 (Shelby Co; FIPS 4703440)
    "16540": "Columbia",  # ZIP 38401 (Maury Co; FIPS 4716540) -- also
    # the authority that 37174 (Spring Hill) currently binds to
    "16920": "Cookeville",  # ZIP 38501 (Putnam Co; FIPS 4716920)
    "18540": "Crossville",  # ZIP 38555 (Cumberland Co; FIPS 4718540)
    "28960": "Germantown",  # ZIPs 38138/38139 (Shelby Co; FIPS 4728960)
    "33280": "Hendersonville",  # ZIP 37075 (Sumner Co; FIPS 4733280)
    "37640": "Jackson",  # ZIPs 38301/38305 (Madison Co; FIPS 4737640)
    "41200": "La Vergne",  # ZIP 37086 (Rutherford Co; FIPS 4741200)
    "41520": "Lebanon",  # ZIPs 37087/37090 (Wilson Co; FIPS 4741520)
    "43140": "Livingston",  # ZIP 38570 (Overton Co; FIPS 4743140)
    "50400": "Mountain City",  # ZIP 37683 (Johnson Co; FIPS 4750400)
    "69420": "Smyrna",  # ZIP 37167 (Rutherford Co; FIPS 4769420)
    "70180": "Sparta",  # ZIP 38583 (White Co; FIPS 4770180)
    "70500": "Springfield",  # ZIP 37172 (Robertson Co; FIPS 4770500)
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
