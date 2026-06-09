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
#
# Source of truth (iter-220, 2026-05-19): MN DOR's "Tax Type Codes (Sales
# Tax Lines)" spreadsheet at https://www.revenue.state.mn.us/media/document/58036
# (file tax-type-codes.xlsx, last updated 2026-05-26). This is the per-state
# cross-reference that MN DOR publishes under SST Governing Board's
# Rate-and-Boundary File spec. Each 80xxx code in the SST rate/boundary
# files maps deterministically to one entry in that xlsx; the names here
# mirror MN DOR's "Description" column verbatim.
#
# iter-83 had several wrong mappings (e.g. 80001 mislabelled as "Cook
# County Transportation Sales Tax" when the SST file binds 80001 only to
# 553+563 ZIP prefixes — St. Cloud area). See specs/findings/
# mn-transit-district-cross-county-leak.md for the diagnostic journey.
# Re-derived from the authoritative xlsx in iter-220 with deep-research
# verification.
# ---------------------------------------------------------------------------
MN_DISTRICT_NAMES: dict[str, str] = {
    # County-level local-option taxes (iter-220 corrections)
    "80001": "St. Cloud Area Sales and Use Tax",  # 0.5%, eff. 2003-01-01
    "80003": "Cook County Transit Sales and Use Tax",  # 0.5%, eff. 2017-01-01
    "80004": "Hennepin County Transit Sales and Use Tax",  # 0.5%, eff. 2017-10-01
    "80005": "Garrison Kathio West Mille Lacs Sanitary Sewer District",  # 1.0%, eff. 2018-01-01
    "80006": "Carlton County Sales and Use Tax",  # 0.5%, eff. 2023-04-01
    "80008": "Metro Area Transportation Sales and Use Tax",  # 0.75%, eff. 2023-10-01
    "80009": "Metro Area Sales and Use Tax for Housing",  # 0.25%, eff. 2023-10-01
    "80011": "Beltrami County Sales and Use Tax",  # 0.625%, eff. 2024-07-01
    "80012": "Stearns County Sales and Use Tax",  # 0.375%, eff. 2025-04-01
    "80013": "Winona County Sales and Use Tax",  # 0.25%, eff. 2025-04-01
    "80054": "Meeker County Transit Sales and Use Tax",  # 0.5%, eff. 2026-07-01
    # Statewide gross-receipts / fee taxes
    "80007": "Cannabis Gross Receipts Tax",  # 15%, eff. 2025-07-01 (was 10% from 2023)
    "80010": "Retail Delivery Fee",  # variable, eff. 2024-07-01
    "80014": "Liquor Gross Receipts Tax",  # 2.5%
    "80015": "Variable Rate Purchases",  # variable
    "80016": "Interstate Motor Carrier",  # variable
    "80035": "Car Rental Tax",  # 9.2%
    "80036": "Car Rental Fee",  # 5.0%
    "80045": "Prepaid Wireless E911/TAM/988 Fee",  # $0.96/transaction, eff. 2025-07-01
    # City-specific food/beverage/liquor/entertainment taxes
    "80017": "Rochester Lodging Tax",  # 7.0%, eff. 2014-01-01
    "80018": "St. Cloud Liquor Tax",  # 1.0%, eff. 1987-02-01
    "80019": "St. Cloud Food Tax",  # 1.0%, eff. 1987-02-01
    "80020": "Mankato Entertainment Tax",  # 0.5%, eff. 2009-04-01
    "80021": "Mankato Food and Beverage Tax",  # 0.5%, eff. 2009-04-01
    "80022": "Mankato Lodging Tax",  # 3.0%, eff. 2021-10-01
    "80023": "St. Paul Lodging Tax (less than 50 rooms)",  # 3.0%, eff. 2004-04-01
    "80024": "St. Paul Lodging Tax (50 or more rooms)",  # 7.0%, eff. 2019-10-01
    "80025": "Minneapolis Downtown Liquor Tax",  # 3.0%, eff. 1987-02-01
    "80026": "Minneapolis Lodging Tax",  # 3.0%, eff. 2019-10-01
    "80027": "Minneapolis Downtown Restaurant Tax",  # 3.0%, eff. 1987-02-01
    "80028": "Minneapolis Entertainment Tax",  # 3.0%, eff. 1969-10-01
    "80029": "Marshall Food and Beverage Tax",  # 1.5%, eff. 2013-07-01
    "80030": "Detroit Lakes Food and Beverage Tax",  # 1.0%, eff. 2013-07-01
    "80031": "Giants Ridge Food and Beverage Tax",  # 1.0%, eff. 2011-07-01
    "80032": "Giants Ridge Lodging Tax",  # 2.0%, eff. 2011-07-01
    "80033": "Giants Ridge Admissions and Recreation Tax",  # 2.0%, eff. 2011-07-01
    "80034": "Proctor Food and Beverage Tax",  # 1.0%, eff. 2014-04-01
    "80037": "North Mankato Food and Beverage Tax",  # 0.5%, eff. 2020-04-01
    "80038": "Lake County Lodging Tax",  # 4.0%, eff. 2020-10-01
    "80039": "Two Harbors Lodging Tax",  # 1.0%, eff. 2020-10-01
    "80040": "Lake of the Woods County Lodging Tax",  # 3.0%, eff. 2021-01-01
    "80041": "Woodbury Lodging Tax",  # 3.0%, eff. 2023-04-01
    "80042": "Ortonville Lodging Tax",  # 3.0%, eff. 2024-04-01
    "80043": "Plymouth Lodging Tax",  # 3.0%, eff. 2024-07-01
    "80044": "Grand Rapids Lodging Tax",  # 3.0%, eff. 2025-01-01
    "80047": "Lake Vermilion Area Lodging Tax",  # 3.0%, eff. 2025-10-01
    "80048": "Faribault Lodging Tax",  # 3.0%, eff. 2026-01-01
    "80049": "Richfield Lodging Tax",  # 3.0%, eff. 2026-01-01
    "80050": "Marshall Lodging Tax",  # 4.5%, eff. 2026-04-01
    "80051": "Chisago Lakes Area Lodging Tax",  # 3.0%, eff. 2026-07-01
    "80052": "Fairmont Lodging Tax",  # 3.0%, eff. 2026-07-01
    "80053": "Waseca Lodging Tax",  # 3.0%, eff. 2026-07-01
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
