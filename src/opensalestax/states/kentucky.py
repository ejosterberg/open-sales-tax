# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Kentucky state module (tier 1, SST member).

KY is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The statewide general sales/use tax
rate is **6.0%** per **KRS 139.200** (rate set at 6% by H.B.
272 of the 1990 General Assembly when the rate was raised
from 5% to 6%; the 6% rate has been stable since).

## NOTABLE DIFFERENCE FROM PEER STATES: NO LOCAL SALES TAX

Kentucky is one of a small number of US states that **levies NO
local sales tax**. The 6% state rate is the entire combined
sales-tax rate at every Kentucky address -- there are no county,
city, or special-district sales taxes layered on top. Kentucky's
Constitution (section 181) historically restricted local
governments from imposing general sales taxes, and the General
Assembly has never broadly authorized a county-option or
city-option sales tax under KRS Chapter 139.

A handful of related local taxes exist (county-option motor
vehicle rental taxes, transient-room "lodging" taxes, restaurant
meals taxes in select municipalities authorized by individual
local-and-private-laws acts) but those are NOT general sales
taxes -- they are narrow industry-specific levies that do not
apply to general retail transactions and are not modeled by this
module. General retail sales in Kentucky always tax at exactly
6.0%.

This is a notable contrast with peer SST member states (e.g.
WI's counties typically add 0.5%; MN's metro adds transit
districts) and with non-SST 6% states like VA / SC (which
layer mandatory state-administered local rates on top of the
state rate). Kentucky's no-local-tax landscape simplifies the
rate-stack model: the SST rate file for Kentucky effectively
ships a single state-level row, and the ``_JURISDICTION_TYPE``
dict below maps only the state-type code (mirroring Indiana).

## SST jurisdiction-type code mapping

Kentucky's SST rate file has only state-level entries (no
counties, cities, or districts to map). The dict accepts only
the canonical state-type code ``"45"`` so that any unexpected
non-state row in a future quarterly file is silently dropped
rather than miscategorized -- an over-collection or under-
collection bug in this module would be more harmful than a
gap in coverage that surfaces during review (mirrors the
Indiana approach).

## Taxability matrix (per KRS Chapter 139)

- **General tangible personal property** -- TAXABLE at 6% per
  **KRS 139.200** (imposition of the sales tax on retail sales
  of tangible personal property and digital property) and
  **KRS 139.310** (complementary use tax). The definition of
  "tangible personal property" is in KRS 139.010.
- **Clothing** -- TAXABLE. Kentucky has **no general clothing
  exemption** in Chapter 139; clothing and footwear tax at the
  full 6% as ordinary tangible personal property. Kentucky has
  no annual back-to-school sales-tax holiday (see below).
- **Groceries (food and food ingredients)** -- EXEMPT per
  **KRS 139.485**. The exemption covers food and food
  ingredients for human consumption. Items expressly excluded
  from the "food and food ingredients" definition -- candy,
  dietary supplements, soft drinks, alcoholic beverages,
  tobacco -- are TAXABLE at 6%. Prepared food (restaurant
  meals etc.) is also excluded from the exemption and remains
  taxable.
- **Prescription drugs** -- EXEMPT per **KRS 139.472**. The
  exemption covers drugs sold pursuant to a prescription, plus
  insulin and certain medical / durable equipment when
  prescribed.
- **Prepared food** -- TAXABLE at 6% per the general imposition
  in KRS 139.200; "prepared food" is expressly excluded from
  the food-and-food-ingredients exemption in KRS 139.485 and
  from the SST definition incorporated by reference.
- **Digital goods (specified digital products and digital
  property)** -- TAXABLE at 6% per **KRS 139.200(2)**, which
  was substantially expanded by **Senate Bill 6 of the 2018
  Regular Session** (codifying tax on "digital property"
  including digital audio works, digital audio-visual works,
  digital books, and other electronically transferred products)
  and further by **House Bill 8 of the 2022 Regular Session**
  (which significantly expanded sales tax to ~30 additional
  service categories effective January 1, 2023, and also
  refined the digital-property treatment). Prewritten ("canned")
  computer software delivered electronically is taxable as
  tangible personal property under longstanding Department of
  Revenue guidance. SaaS / remotely accessed software was
  brought within the sales-tax base by HB 8 (2022) effective
  January 1, 2023 for many enumerated service categories.

## Sales-tax holidays

**NONE.** Kentucky has never enacted a recurring sales-tax
holiday. Confirmed 2026-05-03 against the Kentucky Department
of Revenue's published guidance and a search of KRS Chapter 139
for any periodic exemption window -- there is no back-to-school
holiday, no disaster-prep holiday, no Energy Star holiday, and
no other recurring exemption period in Kentucky law. The
``holidays_for(year)`` method returns an empty iterator for
every year (mirroring DC, ID, and IN).

## Loading

Kentucky's rate data loads from the SST quarterly rate file via
the inherited ``SstStateModule.parse_rates`` machinery. Because
the file ships only the state-level row, the resulting
``RateRow`` stream is a single record with
``authority_type='state'``, ``rate_pct=Decimal('6.000')``, and
no parent. Boundary loading inherits the generic ``z``-record
ZIP5 walker but is effectively a no-op for Kentucky (no
sub-state authorities to bind ZIPs to); the engine answers
every Kentucky ZIP with the single state authority + 6% rate.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Kentucky DOR guidance before relying on these rules in
production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Kentucky has NO local sales tax. The SST rate file contains only
# state-level rows, so we map only the canonical state code. Any
# unexpected non-state row in a future quarterly file is silently
# dropped by the inherited parser (rather than miscategorized as
# something that does not exist in KY's rate landscape). This
# mirrors the Indiana approach -- both states levy only the state
# rate at every address.
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
}

# Kentucky taxability matrix per KRS Chapter 139.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Kentucky at the 6% state rate. "
            "KRS Chapter 139 contains no general clothing exemption; "
            "clothing and footwear are ordinary tangible personal "
            "property under KRS 139.010 and tax at the rate set by "
            "KRS 139.200. Kentucky has no annual back-to-school "
            "sales-tax holiday. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients for human consumption are "
            "EXEMPT in Kentucky per KRS 139.485. Items expressly "
            "excluded from 'food and food ingredients' (candy, "
            "dietary supplements, soft drinks, alcoholic beverages, "
            "tobacco) remain TAXABLE at the 6% state rate. Prepared "
            "food (restaurant meals, hot deli items, ready-to-eat) "
            "is also excluded from the exemption and remains taxable; "
            "see the 'prepared_food' rule. The OpenSalesTax engine "
            "maps the 'groceries' category to SNAP-eligible food and "
            "food ingredients; callers selling candy, soft drinks, or "
            "supplements to Kentucky customers should categorize "
            "those line items as 'general' (or 'prepared_food' for "
            "hot/ready items) rather than 'groceries' so the correct "
            "6% rate is applied. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Kentucky per KRS "
            "139.472. The exemption covers drugs sold pursuant to a "
            "prescription, plus insulin and certain medical / "
            "durable equipment when prescribed. Over-the-counter "
            "drugs sold without a prescription are NOT covered by "
            "the exemption and tax at the general 6% rate. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-"
            "eat deli items) is TAXABLE in Kentucky at the 6% state "
            "rate per KRS 139.200 (imposition). 'Prepared food' is "
            "expressly excluded from the food-and-food-ingredients "
            "exemption in KRS 139.485. Note: a small number of "
            "Kentucky municipalities have a separate local "
            "restaurant / meals tax authorized by individual "
            "local-and-private-laws acts; those are narrow industry-"
            "specific levies and are NOT modeled by this module "
            "(which applies only the 6% state sales tax). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products / digital property are "
            "TAXABLE in Kentucky at the 6% state rate per KRS "
            "139.200(2), as substantially expanded by Senate Bill 6 "
            "of the 2018 Regular Session (codifying tax on digital "
            "property: digital audio works, digital audio-visual "
            "works, digital books, and other electronically "
            "transferred products) and further refined by House "
            "Bill 8 of the 2022 Regular Session (effective "
            "January 1, 2023, HB 8 significantly expanded the "
            "sales-tax base to roughly 30 additional service "
            "categories and further clarified digital-property "
            "treatment). Prewritten ('canned') computer software "
            "delivered electronically is also taxable as tangible "
            "personal property under longstanding Kentucky DOR "
            "guidance. SaaS / remotely accessed software was "
            "brought within the sales-tax base for many enumerated "
            "service categories by HB 8 (2022) effective "
            "January 1, 2023; the precise list of taxable services "
            "is enumerated in HB 8 and subsequent DOR guidance. "
            "Callers shipping digital goods or SaaS to Kentucky "
            "should verify their specific product category against "
            "current DOR guidance. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Kentucky at the 6% state rate per KRS 139.200 "
            "(imposition of the sales tax on retail sales of "
            "tangible personal property and digital property), "
            "complemented by the use tax in KRS 139.310. The "
            "definition of 'tangible personal property' is in KRS "
            "139.010. Kentucky levies NO local sales tax -- the 6% "
            "state rate is the entire combined rate everywhere in "
            "the state. Calculation only -- not legal or tax advice."
        ),
    ),
}


class Kentucky(SstStateModule):
    """Kentucky state module (tier 1, SST member; state-only -- no locals).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS), the jurisdiction-type
    code mapping (which restricts the inherited SST parser to
    state-level rows since KY has no sub-state sales taxes), and
    the taxability matrix. Rate parsing, boundary parsing, special
    cases, and the empty-holidays default are all inherited.
    """

    state_abbrev: str = "KY"
    state_name: str = "Kentucky"
    state_fips: str = "21"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.kentucky`` registers
# Kentucky under "KY" in the state registry.
_PROTOCOL_CHECK: StateModule = Kentucky()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# instance (mirrors MINNESOTA, WISCONSIN, INDIANA, etc.). Kentucky's
# RateRow emits ``rate_pct=Decimal("6.000")`` from the SST file; the
# constant below is purely documentary so future readers can grep
# the codebase for the rate.
KENTUCKY_GENERAL_RATE_PCT: Decimal = Decimal("6.000")

KENTUCKY = register(Kentucky())
