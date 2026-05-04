# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Rhode Island state module (tier 1, SST member; state-only -- no locals).

RI is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The statewide general sales/use tax rate
is **7.0%** per **R.I. Gen. Laws section 44-18-18** (the imposition
statute in chapter 44-18, Sales and Use Taxes -- Liability and
Computation). The 7.0% rate is one of the two highest single-state
rates in the United States (tied with IN, MS, and TN at 7.0%).

## NOTABLE STRUCTURE: NO LOCAL SALES TAX

Rhode Island is one of a small number of US states that **levies
NO general local sales tax**. The 7.0% state rate is the entire
combined sales-tax rate at every Rhode Island address -- there are
no county, city, town, or special-district sales taxes layered on
top. (Rhode Island has no functioning county-level government for
tax-administration purposes; the state's 39 cities and towns do
not have general sales-tax authority under chapter 44-18.)

This puts RI in the same no-local-tax club as IN (Ind. Code
6-2.5-2-2 at 7.0%), KY (KRS 139.200 at 6.0%), and MI (MCL 205.52
at 6.0%): the combined rate at every RI address equals the state
rate exactly. A handful of related local taxes exist (the 1%
hotel tax under R.I. Gen. Laws section 44-18-36.1 on transient
lodging, and the 1% local meals and beverages tax under section
44-18-18.1 paid by the customer on prepared meals served at
eating and drinking establishments) but those are NOT general
sales taxes -- they are narrow industry-specific levies that do
not apply to general retail transactions and are not modeled by
this module. General retail sales in Rhode Island always tax at
exactly 7.0%.

## SST jurisdiction-type code mapping

Rhode Island's SST rate file has only state-level entries (no
counties, cities, or districts to map). The dict accepts only the
canonical state-type code ``"45"`` so that any unexpected non-
state row in a future quarterly file is silently dropped rather
than miscategorized -- an over-collection or under-collection bug
in this module would be more harmful than a gap in coverage that
surfaces during review. (Same defensive posture as IN.)

## Taxability matrix (per R.I. Gen. Laws Title 44, Chapter 18)

- **General tangible personal property** -- TAXABLE at 7% per
  R.I. Gen. Laws section 44-18-18 (the imposition statute) and
  the definition of "tangible personal property" in R.I. Gen.
  Laws section 44-18-7.
- **Clothing and footwear** -- **EXEMPT, with a $250-per-item
  threshold** per **R.I. Gen. Laws section 44-18-30(27)**. Items
  priced AT OR BELOW $250 per article are fully exempt; for any
  single article priced above $250, the FIRST $250 is exempt and
  only the PORTION ABOVE $250 is taxable at 7%. RI joins the
  broad-exemption club (PA, MA, MN, NJ, VT) but is the only one
  of that group with a per-item threshold above which the excess
  becomes taxable. (NY's $110 threshold makes the ENTIRE article
  taxable once it crosses the cap; RI's structure is exemption-
  up-to-the-cap with only the excess taxed.) The engine encodes
  this via the ``above_excess`` threshold semantic on
  TaxabilityRule, so a $400 wool coat correctly taxes the $150
  above the cap at 7% ($10.50).
- **Groceries (food and food ingredients)** -- EXEMPT per **R.I.
  Gen. Laws section 44-18-30(11)**. The exemption tracks the
  Streamlined Sales Tax Project's uniform definition of "food
  and food ingredients" (codified at R.I. Gen. Laws section
  44-18-7.1 et seq.) and excludes candy, soft drinks, dietary
  supplements, alcoholic beverages, and prepared food (those
  remain taxable).
- **Prescription drugs** -- EXEMPT per **R.I. Gen. Laws section
  44-18-30(28)**. The exemption covers drugs sold pursuant to a
  written prescription by a licensed practitioner; over-the-
  counter (non-prescription) drugs are NOT covered by this
  exemption and remain taxable at the 7% rate.
- **Prepared food** -- TAXABLE at 7% as ordinary tangible personal
  property under R.I. Gen. Laws section 44-18-18; the prepared-
  food category is expressly excluded from the food-and-food-
  ingredients exemption in section 44-18-30(11). Note:
  prepared meals served at eating and drinking establishments
  are ALSO subject to the separate 1% **local meals and
  beverages tax** under R.I. Gen. Laws section 44-18-18.1, which
  is a NON-general-sales-tax levy and is NOT modeled by this
  module (the engine applies only the 7% state rate; the
  additional 1% layer on restaurant transactions must be added
  outside the engine).
- **Digital goods (specified digital products)** -- TAXABLE at
  7% per **R.I. Gen. Laws section 44-18-7.1**, added (and the
  base broadened to include "specified digital products") by
  **section 3 of P.L. 2018, ch. 47, art. 4** (the FY2019 budget
  bill, signed June 22, 2018), effective **October 1, 2018**.
  The provision tracks the SST uniform definition of "specified
  digital product" -- digital audio works, digital audiovisual
  works, and digital books delivered electronically with a
  permanent OR less-than-permanent right of use. Prewritten
  ("canned") computer software delivered by any means is
  separately taxable as TPP under the long-standing definition
  in R.I. Gen. Laws section 44-18-7.

## Sales-tax holidays

**NONE.** Rhode Island has never enacted a recurring sales-tax
holiday. Confirmed 2026-05-03 against the Rhode Island Division
of Taxation's published guidance and a search of chapter 44-18
for any periodic exemption window -- there is no back-to-school
holiday, no disaster-prep holiday, no Energy Star holiday, and
no other recurring exemption period in Rhode Island law. The
``holidays_for(year)`` method returns an empty iterator for
every year (mirroring DC, ID, IN, KY, MI, NE, NJ).

## Loading

Rhode Island's rate data loads from the SST quarterly rate file
via the inherited :class:`SstStateModule.parse_rates` machinery.
Because the file ships only the state-level row, the resulting
:class:`RateRow` stream is a single record with
``authority_type='state'``, ``rate_pct=Decimal('7.000')``, and
no parent. Boundary loading inherits the generic ``z``-record
ZIP5 walker but is effectively a no-op for Rhode Island (no
sub-state authorities to bind ZIPs to); the engine answers
every Rhode Island ZIP with the single state authority + 7%
rate.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Rhode Island Division of Taxation guidance before relying on
these rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Rhode Island has NO local sales tax. The SST rate file contains
# only state-level rows, so we map only the canonical state code.
# Any unexpected non-state row in a future quarterly file is silently
# dropped by the inherited parser (rather than miscategorized as
# something that does not exist in RI's rate landscape).
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
}

# Rhode Island taxability matrix per R.I. Gen. Laws Title 44, Chapter 18.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        taxable_threshold_amount=Decimal("250.00"),
        threshold_semantic="above_excess",
        notes=(
            "Rhode Island: clothing and footwear are EXEMPT up to "
            "$250 per article per R.I. Gen. Laws section 44-18-30(27); "
            "for any single article priced above $250, the first "
            "$250 remains exempt and only the portion above $250 is "
            "taxable at the 7% state rate. RI joins the broad-"
            "clothing-exemption club (PA, MA, MN, NJ, VT) but is the "
            "only one of that group with an excess-above-cap tax "
            "structure (contrast NY $110-per-item, where crossing "
            "the threshold makes the ENTIRE article taxable). The "
            "engine encodes this with the ``above_excess`` threshold "
            "semantic so a $400 wool coat correctly taxes the $150 "
            "above the cap at 7% ($10.50). Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients are EXEMPT in Rhode Island "
            "per R.I. Gen. Laws section 44-18-30(11). The exemption "
            "tracks the Streamlined Sales Tax Project's uniform "
            "definition of 'food and food ingredients' (codified at "
            "R.I. Gen. Laws section 44-18-7.1 et seq.) and excludes "
            "candy, soft drinks, dietary supplements, alcoholic "
            "beverages, and prepared food -- those remain taxable "
            "at the 7% state rate. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Rhode Island per "
            "R.I. Gen. Laws section 44-18-30(28). The exemption "
            "covers drugs sold pursuant to a written prescription "
            "by a licensed practitioner. Over-the-counter (non-"
            "prescription) drugs are NOT covered by the exemption "
            "and remain taxable at the 7% state rate. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, "
            "ready-to-eat foods) is TAXABLE in Rhode Island at the "
            "7% state rate as ordinary tangible personal property "
            "under R.I. Gen. Laws section 44-18-18; the prepared-"
            "food category is expressly excluded from the food-and-"
            "food-ingredients exemption in R.I. Gen. Laws section "
            "44-18-30(11). Note: prepared meals served at eating "
            "and drinking establishments are ALSO subject to a "
            "separate 1% local meals and beverages tax under R.I. "
            "Gen. Laws section 44-18-18.1 -- a non-general-sales-"
            "tax levy that is NOT modeled by this engine (the "
            "engine applies only the 7% state rate; the additional "
            "1% restaurant layer must be added outside the engine). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Rhode Island "
            "at the 7% state rate per R.I. Gen. Laws section "
            "44-18-7.1 (added by section 3 of P.L. 2018, ch. 47, "
            "art. 4 -- the FY2019 budget bill, signed June 22, "
            "2018), effective October 1, 2018. The statute tracks "
            "the SST uniform definition: digital audio works, "
            "digital audiovisual works, and digital books delivered "
            "electronically, whether transferred with a permanent "
            "right of use or with less-than-permanent use. "
            "Prewritten ('canned') computer software delivered by "
            "any means is separately taxable as tangible personal "
            "property under R.I. Gen. Laws section 44-18-7. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Rhode "
            "Island at the 7% state rate per R.I. Gen. Laws section "
            "44-18-18 (the imposition statute) and R.I. Gen. Laws "
            "section 44-18-7 (definition of tangible personal "
            "property). RI's 7% is one of the two highest single-"
            "state rates in the United States (tied with IN, MS, "
            "and TN). Rhode Island levies NO general local sales "
            "tax -- the 7% state rate is the entire combined rate "
            "everywhere in the state (mirrors IN, KY, MI). A "
            "separate 1% hotel tax (section 44-18-36.1) on transient "
            "lodging and a separate 1% local meals and beverages "
            "tax (section 44-18-18.1) on restaurant transactions "
            "are non-general-sales-tax levies that are NOT modeled "
            "by this engine. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
}


class RhodeIsland(SstStateModule):
    """Rhode Island state module (tier 1, SST member; state-only -- no locals).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS), the jurisdiction-type
    code mapping (which restricts the inherited SST parser to
    state-level rows since RI has no sub-state sales taxes), and
    the taxability matrix. Rate parsing, boundary parsing, special
    cases, and the empty-holidays default are all inherited.

    Distinctive features (see module docstring for full statutory
    grounding):

    - **No local sales tax.** The 7% state rate is the entire
      combined rate at every RI address (mirrors IN/KY/MI).
    - **Clothing exempt up to $250 per article** with the excess
      above $250 taxable at 7% per R.I. Gen. Laws section
      44-18-30(27). Encoded via the ``above_excess`` threshold
      semantic so a $400 wool coat correctly taxes the $150
      above the cap at 7% ($10.50).
    - **No state sales-tax holiday.** RI has never enacted a
      recurring holiday; ``holidays_for`` returns empty for every
      year (mirrors DC/ID/IN/KY/MI/NE/NJ).
    """

    state_abbrev: str = "RI"
    state_name: str = "Rhode Island"
    state_fips: str = "44"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.rhode_island``
# registers Rhode Island under "RI" in the state registry.
_PROTOCOL_CHECK: StateModule = RhodeIsland()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# rate (mirrors INDIANA, MINNESOTA, etc.). The actual rate that flows
# into the engine comes from the SST quarterly file via the inherited
# parser; the constant below is documentary so future readers can
# grep the codebase for the rate.
RHODE_ISLAND_GENERAL_RATE_PCT: Decimal = Decimal("7.000")

# Documentary constant: the per-article clothing-exemption cap from
# R.I. Gen. Laws section 44-18-30(27). The engine does not enforce
# this cap in v0.10; documented here so the v0.6 threshold-rules
# feature has a stable named reference.
RHODE_ISLAND_CLOTHING_EXEMPTION_CAP: Decimal = Decimal("250.00")

RHODE_ISLAND = register(RhodeIsland())
