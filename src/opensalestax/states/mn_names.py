# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Human-readable names for Minnesota tax authorities.

The SST quarterly rate file references jurisdictions by opaque
numeric codes (county FIPS like ``053``, city codes like
``43000``, special-district codes like ``80004``). These are
fine for internal joins but useless on a customer-facing
receipt. The MN DOR's sales-tax-rate calculator at
revenue.state.mn.us/sales-tax-rate-calculator uses friendly
names ("Hennepin County", "Minneapolis", "Hennepin County
Transit"), and Minnesota Statutes 297A.99 requires the same
names on retail receipts.

This module is the single source of truth for the SST-code ->
friendly-name translation. It is consulted at LOAD time (the
data loader writes the friendly name into ``tax_authorities.name``
at insert time) so the engine's output already carries
human-readable names without any per-request mapping work.

Sources:
- MN counties: NIST FIPS PUB 6-4 (Minnesota = state 27;
  county FIPS 001-173 odd, well-documented)
- MN cities + special districts: MN DOR Sales Tax Fact Sheet
  164 ("Local Sales and Use Taxes") and the
  revenue.state.mn.us/local-sales-tax-information rate tables
- Special-district codes (80xxx): MN DOR Local Sales Tax
  Schedule (cross-referenced to the SST jurisdiction codes
  via Fact Sheet 164S addendum and the 2026Q2 SST rate file)

Coverage note: this table is hand-curated to cover the
metropolitan + greater-Minnesota cities that show up in our
test fixtures. Cities not yet listed fall back to the
``MN-city-<code>`` placeholder; PRs welcome.
"""

from __future__ import annotations

# Counties are looked up via the generic
# :mod:`opensalestax.data.county_names` table (Census ZCTA->County
# 2020 source); MN-specific entries here cover only the cities
# and special districts that the SST jurisdiction codes don't
# share with FIPS.

# ---------------------------------------------------------------------------
# Cities (key = SST jurisdiction_code from rate-file col3 for type-01 rows)
#
# Hand-verified against the live engine + MN DOR sales-tax-rate calculator.
# Pre-2026 versions of this module had ~60 entries derived from naming
# patterns alone -- many were wrong (St. Paul code 58000 was mislabelled
# "Sebeka" because the SST jurisdiction codes don't follow FIPS conventions).
# This minimal set is the verified subset; cities not listed fall back to
# the placeholder "MN-city-<code>" so a code surfaces visibly until a
# maintainer cross-checks the friendly name and adds it.
#
# Verification protocol: pick a ZIP+4 that is unambiguously inside the
# city per the city's own GIS, run our engine + the MN DOR calculator at
# revenue.state.mn.us/sales-tax-rate-calculator for the same ZIP+4, and
# confirm both calculators emit the same combined rate AND the city
# component matches in name + percentage.
# ---------------------------------------------------------------------------
MN_CITY_NAMES: dict[str, str] = {
    "06616": "Bloomington",
    "40166": "Maple Grove",
    "43000": "Minneapolis",
    "55852": "Roseville",
    "58000": "St. Paul",
    "69700": "West St. Paul",
    "71428": "Woodbury",
}

# ---------------------------------------------------------------------------
# Special districts (key = SST jurisdiction_code for type-63 rows)
# Cross-checked against MN DOR Fact Sheet 164S and the 2026Q2 rate file.
# ---------------------------------------------------------------------------
MN_DISTRICT_NAMES: dict[str, str] = {
    "80001": "Cook County Transportation Sales Tax",
    "80003": "Beltrami County Transportation Sales Tax",
    "80004": "Hennepin County Transit Sales Tax",
    "80005": "Two Harbors Lodging Tax",
    "80006": "Carlton County Transit Sales Tax",
    "80008": "Metro Area Transportation Sales Tax",
    "80009": "Metro Area Sales and Use Tax for Housing",
    "80011": "St. Louis County Transportation Sales Tax",
    "80012": "Anoka County Transportation Sales Tax",
    "80013": "Washington County Transportation Sales Tax",
}


def city_name(code: str) -> str | None:
    """Return the friendly city name for an SST city code, or None."""
    return MN_CITY_NAMES.get(code)


def district_name(code: str) -> str | None:
    """Return the friendly special-district name for an SST code, or None."""
    return MN_DISTRICT_NAMES.get(code)


__all__ = [
    "MN_CITY_NAMES",
    "MN_DISTRICT_NAMES",
    "city_name",
    "district_name",
]
