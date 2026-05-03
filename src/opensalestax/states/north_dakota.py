# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""North Dakota state module (tier 1, SST member).

ND is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The statewide general sales/use tax
rate is **5.0%** per **N.D.C.C. section 57-39.2-02.1**, the
imposition statute of the North Dakota Sales Tax (Chapter
57-39.2). The 5% rate has been stable for many years (raised
from 4% to 5% effective 1987-07-01 by the 1987 legislative
assembly's omnibus revenue act).

## North Dakota's local-tax landscape

Unlike Kentucky, Indiana, or Michigan (peer SST members with NO
local sales tax), North Dakota DOES allow local option sales
taxes. Both incorporated cities and counties may impose a
local-option sales / use / gross-receipts tax under:

- **N.D.C.C. chapter 11-09.2** -- county home rule charter
  authority (counties that adopt a home rule charter may impose
  taxes including a sales tax)
- **N.D.C.C. chapter 40-05.1** -- city home rule charter
  authority (home rule cities may impose a city sales tax)
- **N.D.C.C. chapter 40-57.3** -- city sales, use, and
  gross-receipts tax (the more commonly used non-home-rule
  authority that lets ANY incorporated city, by voter approval,
  impose a city sales tax administered by the State Tax
  Commissioner)

Local rates typically range from 0.25% to 3.5%, with most
participating cities at 1%-2.5%. Combined (state + city +
optional county) rates statewide therefore range from **5.0%
(unincorporated areas with no county tax) to roughly 8.5%**
(highest combined rates in some North Dakota cities). Per-
jurisdiction rates flow through the standard SST quarterly file
and are loaded by the inherited :class:`SstStateModule` parser
-- this module does NOT deferred-codify city rates inline.

The default jurisdiction-type code mapping (state ``45`` /
county ``00`` / city ``01`` / district ``63``) is inherited from
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`.
This mapping is empirically validated against MN and WI 2026Q2
files; if a future quarterly capture of a North Dakota SST file
shows different codes for any sub-state authority, override
``jurisdiction_types`` on this subclass at that time.

## SST jurisdiction-type code mapping

ND inherits the default mapping. Counties that have adopted home
rule charters and impose a sales tax appear under ``00``; cities
appear under ``01``. There is no widespread special-district
sales tax in North Dakota, so the ``63`` mapping is reserved
for any future special-district authority that might be added.

## Taxability matrix (per N.D.C.C. chapter 57-39.2)

- **General tangible personal property** -- TAXABLE at 5% per
  **N.D.C.C. section 57-39.2-02.1** (imposition of the state
  sales tax on retail sales of tangible personal property and
  on certain services and digital products) and the
  complementary use tax in N.D.C.C. chapter 57-40.2.
- **Clothing** -- TAXABLE. North Dakota has **no general
  clothing exemption** in chapter 57-39.2; clothing and
  footwear are ordinary tangible personal property and tax at
  the full 5% state rate plus any applicable local rates.
  North Dakota has **no annual back-to-school sales-tax
  holiday** (see "Sales-tax holidays" below).
- **Groceries (food and food ingredients)** -- EXEMPT per
  **N.D.C.C. section 57-39.2-04(46)**, which exempts the gross
  receipts from the sale of "food and food ingredients" for
  human consumption (using the Streamlined Sales Tax Project's
  uniform definition incorporated by reference). Items
  expressly excluded from the "food and food ingredients"
  definition -- candy, dietary supplements, soft drinks,
  alcoholic beverages, tobacco -- remain TAXABLE at the 5%
  state rate. Prepared food (restaurant meals etc.) is also
  excluded from the exemption and remains taxable; see the
  ``prepared_food`` rule.
- **Prescription drugs** -- EXEMPT per **N.D.C.C. section
  57-39.2-04(33)**. The exemption covers drugs sold pursuant
  to a prescription, plus insulin, oxygen, and certain medical
  / durable equipment when prescribed.
- **Prepared food** -- TAXABLE at 5% per the general
  imposition in N.D.C.C. section 57-39.2-02.1; "prepared food"
  is expressly excluded from the food-and-food-ingredients
  exemption in section 57-39.2-04(46) and from the SST common
  definition incorporated by reference.
- **Digital goods (specified digital products)** -- TAXABLE at
  5% per **N.D.C.C. section 57-39.2-02.1(1)(c)**, added by
  **House Bill 1041 of the 66th Legislative Assembly (2019)**.
  The 2019 amendment expressly extended the sales tax to
  "specified digital products" delivered electronically --
  including digital audio works, digital audio-visual works,
  digital books, and similar electronically-transferred
  products -- whether sold with a permanent right of use or
  under a subscription / conditional access model. Prewritten
  ("canned") computer software delivered by any means is also
  taxable as tangible personal property under the longstanding
  definitions in N.D.C.C. section 57-39.2-01.

## Sales-tax holidays

**NONE.** North Dakota has never enacted a recurring sales-tax
holiday. Confirmed 2026-05-03 against the North Dakota Office
of State Tax Commissioner's published guidance and a search of
N.D.C.C. chapter 57-39.2 for any periodic exemption window --
there is no back-to-school holiday, no disaster-prep holiday,
no Energy Star holiday, and no other recurring exemption period
in North Dakota law. The ``holidays_for(year)`` method returns
an empty iterator for every year (mirroring Kentucky, Indiana,
DC, and Idaho).

## Loading

North Dakota's rate data loads from the SST quarterly rate file
via the inherited ``SstStateModule.parse_rates`` machinery. The
file ships state-level + per-city (and the few county home-rule)
rows; the inherited parser converts each into a ``RateRow`` with
the appropriate ``authority_type``. Boundary loading uses the
generic ``z``-record ZIP5 walker.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
North Dakota Office of State Tax Commissioner guidance before
relying on these rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# North Dakota taxability matrix per N.D.C.C. chapter 57-39.2.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in North Dakota at the 5% state "
            "rate (plus any applicable city / county local rates). "
            "N.D.C.C. chapter 57-39.2 contains no general clothing "
            "exemption; clothing and footwear are ordinary tangible "
            "personal property and tax at the rate set by N.D.C.C. "
            "section 57-39.2-02.1. North Dakota has no annual "
            "back-to-school sales-tax holiday. Calculation only -- "
            "not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients for human consumption are "
            "EXEMPT in North Dakota per N.D.C.C. section "
            "57-39.2-04(46), which exempts the gross receipts from "
            "the sale of food and food ingredients (using the "
            "Streamlined Sales Tax Project's uniform definition "
            "incorporated by reference). Items expressly excluded "
            "from 'food and food ingredients' (candy, dietary "
            "supplements, soft drinks, alcoholic beverages, "
            "tobacco) remain TAXABLE at the 5% state rate. "
            "Prepared food (restaurant meals, hot deli items, "
            "ready-to-eat) is also excluded from the exemption and "
            "remains taxable; see the 'prepared_food' rule. The "
            "OpenSalesTax engine maps the 'groceries' category to "
            "SNAP-eligible food and food ingredients; callers "
            "selling candy, soft drinks, or supplements to North "
            "Dakota customers should categorize those line items "
            "as 'general' (or 'prepared_food' for hot/ready items) "
            "rather than 'groceries' so the correct 5% rate is "
            "applied. Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in North Dakota per "
            "N.D.C.C. section 57-39.2-04(33). The exemption covers "
            "drugs sold pursuant to a prescription, plus insulin, "
            "oxygen, and certain medical / durable equipment when "
            "prescribed. Over-the-counter drugs sold without a "
            "prescription are NOT covered by the exemption and tax "
            "at the general 5% state rate. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-"
            "eat deli items) is TAXABLE in North Dakota at the 5% "
            "state rate per N.D.C.C. section 57-39.2-02.1 "
            "(imposition). 'Prepared food' is expressly excluded "
            "from the food-and-food-ingredients exemption in "
            "section 57-39.2-04(46) and from the SST common "
            "definition incorporated by reference. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in North "
            "Dakota at the 5% state rate per N.D.C.C. section "
            "57-39.2-02.1(1)(c), added by House Bill 1041 of the "
            "66th Legislative Assembly (2019). The 2019 amendment "
            "expressly extended the sales tax to digital audio "
            "works, digital audio-visual works, digital books, "
            "and other 'specified digital products' delivered "
            "electronically -- whether transferred with a "
            "permanent right of use or under a subscription / "
            "conditional access model. Prewritten ('canned') "
            "computer software delivered by any means is also "
            "taxable as tangible personal property under the "
            "longstanding definitions in N.D.C.C. section "
            "57-39.2-01. Callers shipping digital goods or SaaS "
            "to North Dakota should verify their specific product "
            "category against current Office of State Tax "
            "Commissioner guidance. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "North Dakota at the 5% state rate per N.D.C.C. "
            "section 57-39.2-02.1 (imposition of the state sales "
            "tax on retail sales of tangible personal property "
            "and on specified digital products), complemented by "
            "the use tax in N.D.C.C. chapter 57-40.2. Local "
            "option sales taxes imposed by cities (under "
            "N.D.C.C. chapter 40-57.3 or home-rule chapter "
            "40-05.1) and home-rule counties (under N.D.C.C. "
            "chapter 11-09.2) layer on top; combined rates "
            "typically range from 5.0% to roughly 8.5% statewide. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}


class NorthDakota(SstStateModule):
    """North Dakota state module (tier 1, SST member).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS) and the taxability
    matrix. Rate parsing, boundary parsing, jurisdiction-type
    code mapping, special cases, and the empty-holidays default
    are all inherited.
    """

    state_abbrev: str = "ND"
    state_name: str = "North Dakota"
    state_fips: str = "38"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.north_dakota``
# registers North Dakota under "ND" in the state registry.
_PROTOCOL_CHECK: StateModule = NorthDakota()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# state-rate value (mirrors KENTUCKY, INDIANA, etc.). North Dakota's
# RateRow emits ``rate_pct=Decimal("5.000")`` from the SST file; the
# constant below is purely documentary so future readers can grep
# the codebase for the rate.
NORTH_DAKOTA_GENERAL_RATE_PCT: Decimal = Decimal("5.000")

NORTH_DAKOTA = register(NorthDakota())
