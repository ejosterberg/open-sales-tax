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

# ---------------------------------------------------------------------------
# Counties (key = SST/FIPS county code, e.g. "053" for Hennepin)
# ---------------------------------------------------------------------------
MN_COUNTY_NAMES: dict[str, str] = {
    "001": "Aitkin County",
    "003": "Anoka County",
    "005": "Becker County",
    "007": "Beltrami County",
    "009": "Benton County",
    "011": "Big Stone County",
    "013": "Blue Earth County",
    "015": "Brown County",
    "017": "Carlton County",
    "019": "Carver County",
    "021": "Cass County",
    "023": "Chippewa County",
    "025": "Chisago County",
    "027": "Clay County",
    "029": "Clearwater County",
    "031": "Cook County",
    "033": "Cottonwood County",
    "035": "Crow Wing County",
    "037": "Dakota County",
    "039": "Dodge County",
    "041": "Douglas County",
    "043": "Faribault County",
    "045": "Fillmore County",
    "047": "Freeborn County",
    "049": "Goodhue County",
    "051": "Grant County",
    "053": "Hennepin County",
    "055": "Houston County",
    "057": "Hubbard County",
    "059": "Isanti County",
    "061": "Itasca County",
    "063": "Jackson County",
    "065": "Kanabec County",
    "067": "Kandiyohi County",
    "069": "Kittson County",
    "071": "Koochiching County",
    "073": "Lac qui Parle County",
    "075": "Lake County",
    "077": "Lake of the Woods County",
    "079": "Le Sueur County",
    "081": "Lincoln County",
    "083": "Lyon County",
    "085": "McLeod County",
    "087": "Mahnomen County",
    "089": "Marshall County",
    "091": "Martin County",
    "093": "Meeker County",
    "095": "Mille Lacs County",
    "097": "Morrison County",
    "099": "Mower County",
    "101": "Murray County",
    "103": "Nicollet County",
    "105": "Nobles County",
    "107": "Norman County",
    "109": "Olmsted County",
    "111": "Otter Tail County",
    "113": "Pennington County",
    "115": "Pine County",
    "117": "Pipestone County",
    "119": "Polk County",
    "121": "Pope County",
    "123": "Ramsey County",
    "125": "Red Lake County",
    "127": "Redwood County",
    "129": "Renville County",
    "131": "Rice County",
    "133": "Rock County",
    "135": "Roseau County",
    "137": "St. Louis County",
    "139": "Scott County",
    "141": "Sherburne County",
    "143": "Sibley County",
    "145": "Stearns County",
    "147": "Steele County",
    "149": "Stevens County",
    "151": "Swift County",
    "153": "Todd County",
    "155": "Traverse County",
    "157": "Wabasha County",
    "159": "Wadena County",
    "161": "Waseca County",
    "163": "Washington County",
    "165": "Watonwan County",
    "167": "Wilkin County",
    "169": "Winona County",
    "171": "Wright County",
    "173": "Yellow Medicine County",
}

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


def county_name(code: str) -> str | None:
    """Return the friendly county name for a 3-digit FIPS code, or None."""
    return MN_COUNTY_NAMES.get(code)


def city_name(code: str) -> str | None:
    """Return the friendly city name for an SST city code, or None."""
    return MN_CITY_NAMES.get(code)


def district_name(code: str) -> str | None:
    """Return the friendly special-district name for an SST code, or None."""
    return MN_DISTRICT_NAMES.get(code)


__all__ = [
    "MN_CITY_NAMES",
    "MN_COUNTY_NAMES",
    "MN_DISTRICT_NAMES",
    "city_name",
    "county_name",
    "district_name",
]
