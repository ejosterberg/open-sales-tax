# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Indiana state module (tier 1, SST member).

IN is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The statewide general sales/use tax
rate is **7.0%** per **Ind. Code section 6-2.5-2-2(a)** (rate
last increased from 6% to 7% effective April 1, 2008 by P.L.
146-2008, which raised the state rate to fund property-tax
relief). The 7% rate has been stable since.

## NOTABLE DIFFERENCE FROM PEER STATES: NO LOCAL SALES TAX

Indiana is one of a small number of US states that **levies NO
local sales tax**. The 7% state rate is the entire combined
sales-tax rate at every Indiana address -- there are no county,
city, township, or special-district sales taxes layered on top.

A handful of related local taxes exist (county-option innkeeper
taxes on lodging, food-and-beverage taxes in select municipalities
authorized by individual local-and-private-laws acts) but those are
NOT general sales taxes -- they are narrow industry-specific
levies that do not apply to general retail transactions and are
not modeled by this module. General retail sales in Indiana
always tax at exactly 7.0%.

This is a notable contrast with peer SST member states (e.g.
WI's counties typically add 0.5%; MN's metro adds transit
districts) and with non-SST 7% states like MS (which has
isolated tourism / infrastructure local taxes). Indiana's
no-local-tax landscape simplifies the rate-stack model: the
SST rate file for Indiana effectively ships a single state-level
row, and the ``_JURISDICTION_TYPE`` dict below maps only the
state-type code.

## SST jurisdiction-type code mapping

Indiana's SST rate file has only state-level entries (no
counties, cities, or districts to map). The dict accepts only
the canonical state-type code ``"45"`` so that any unexpected
non-state row in a future quarterly file is silently dropped
rather than miscategorized -- an over-collection or under-
collection bug in this module would be more harmful than a
gap in coverage that surfaces during review.

## Taxability matrix (per Ind. Code Title 6, Article 2.5)

- **General tangible personal property** -- TAXABLE at 7% per
  Ind. Code section 6-2.5-2-1 (imposition) and section 6-2.5-2-2
  (rate). Section 6-2.5-1-27 defines tangible personal property.
- **Clothing** -- TAXABLE. Indiana has **no general clothing
  exemption** in Article 2.5; clothing and footwear tax at the
  full 7% as ordinary tangible personal property.
- **Groceries (food and food ingredients)** -- EXEMPT per
  **Ind. Code section 6-2.5-5-20**. The exemption covers food
  and food ingredients for human consumption. Items expressly
  excluded from "food and food ingredients" -- candy, dietary
  supplements, soft drinks, alcoholic beverages, tobacco -- are
  TAXABLE at 7%. Prepared food (restaurant meals etc.) is also
  excluded from the exemption and remains taxable.
- **Prescription drugs** -- EXEMPT per **Ind. Code section
  6-2.5-5-19**. The exemption covers drugs sold pursuant to a
  prescription, plus insulin, oxygen, blood, and certain
  medical/durable equipment when prescribed.
- **Prepared food** -- TAXABLE at 7% per the general imposition
  in section 6-2.5-2-1; "prepared food" is expressly excluded
  from the food-and-food-ingredients exemption in section
  6-2.5-5-20 and from the SST definition incorporated by
  reference.
- **Digital goods (specified digital products)** -- TAXABLE at 7%
  per **Ind. Code section 6-2.5-4-16.4**, which imposes the
  sales/use tax on transferred specified digital products
  (effective July 1, 2018 under H.E.A. 1316-2018). The provision
  tracks the SST definition: digital audio works, digital
  audio-visual works, and digital books transferred
  electronically with a permanent right of use. SaaS / remotely
  accessed software is treated separately under Information
  Bulletin #8 (most recent revision December 2024); the
  Department's longstanding position is that prewritten
  ("canned") software delivered electronically IS taxable but
  remotely accessed software (true SaaS where the customer does
  NOT take possession or control of the software) is NOT
  taxable as tangible personal property. The
  ``digital_goods=is_taxable=True`` rule encodes the dominant
  case (specified digital products with permanent right of use);
  the SaaS distinction is documented in the rule's notes for
  follow-up if/when a sub-category split lands.

## Sales-tax holidays

**NONE.** Indiana has never enacted a recurring sales-tax
holiday. Confirmed 2026-05-03 against the Indiana Department of
Revenue's published guidance and a search of Article 2.5 for
any periodic exemption window -- there is no back-to-school
holiday, no disaster-prep holiday, no Energy Star holiday, and
no other recurring exemption period in Indiana law. The
``holidays_for(year)`` method returns an empty iterator for
every year (mirroring DC and ID).

## Loading

Indiana's rate data loads from the SST quarterly rate file via
the inherited ``SstStateModule.parse_rates`` machinery. Because
the file ships only the state-level row, the resulting
``RateRow`` stream is a single record with
``authority_type='state'``, ``rate_pct=Decimal('7.000')``, and
no parent. Boundary loading inherits the generic ``z``-record
ZIP5 walker but is effectively a no-op for Indiana (no
sub-state authorities to bind ZIPs to); the engine answers
every Indiana ZIP with the single state authority + 7% rate.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Indiana DOR guidance before relying on these rules in
production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Indiana has NO local sales tax. The SST rate file contains only
# state-level rows, so we map only the canonical state code. Any
# unexpected non-state row in a future quarterly file is silently
# dropped by the inherited parser (rather than miscategorized as
# something that does not exist in IN's rate landscape).
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
}

# Indiana taxability matrix per Ind. Code Title 6, Article 2.5.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Indiana at the 7% state rate. "
            "Indiana Code Title 6, Article 2.5 contains no general "
            "clothing exemption; clothing and footwear are ordinary "
            "tangible personal property under Ind. Code section "
            "6-2.5-1-27 and tax at the rate set by section "
            "6-2.5-2-2(a). Indiana has no annual back-to-school "
            "sales-tax holiday. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients for human consumption are "
            "EXEMPT in Indiana per Ind. Code section 6-2.5-5-20. "
            "Items expressly excluded from 'food and food "
            "ingredients' (candy, dietary supplements, soft drinks, "
            "alcoholic beverages, tobacco) remain TAXABLE at the "
            "7% state rate. Prepared food (restaurant meals, hot "
            "deli items, ready-to-eat) is also excluded from the "
            "exemption and remains taxable; see the 'prepared_food' "
            "rule. The OpenSalesTax engine maps the 'groceries' "
            "category to SNAP-eligible food and food ingredients; "
            "callers selling candy, soft drinks, or supplements to "
            "Indiana customers should categorize those line items "
            "as 'general' (or 'prepared_food' for hot/ready items) "
            "rather than 'groceries' so the correct 7% rate is "
            "applied. Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Indiana per Ind. Code "
            "section 6-2.5-5-19. The exemption covers drugs sold "
            "pursuant to a prescription, plus insulin, oxygen, "
            "blood, and certain medical / durable equipment when "
            "prescribed. Over-the-counter drugs sold without a "
            "prescription are NOT covered by the exemption and tax "
            "at the general 7% rate. Calculation only -- not legal "
            "or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-"
            "eat deli items) is TAXABLE in Indiana at the 7% state "
            "rate per Ind. Code section 6-2.5-2-1 (imposition) and "
            "section 6-2.5-2-2(a) (rate). 'Prepared food' is "
            "expressly excluded from the food-and-food-ingredients "
            "exemption in section 6-2.5-5-20. Note: a small number "
            "of Indiana municipalities have a separate local "
            "food-and-beverage tax (e.g. Marion County) authorized "
            "by individual local-and-private-laws acts; those are "
            "narrow industry-specific levies and are NOT modeled "
            "by this module (which applies only the 7% state rate). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Indiana at "
            "the 7% state rate per Ind. Code section 6-2.5-4-16.4 "
            "(effective July 1, 2018 under H.E.A. 1316-2018). The "
            "statute tracks the SST definition: digital audio "
            "works, digital audio-visual works, and digital books "
            "transferred electronically with a PERMANENT RIGHT of "
            "use. Prewritten ('canned') computer software delivered "
            "electronically is also taxable per Indiana DOR "
            "Information Bulletin #8 (most recent revision December "
            "2024). EXCLUDED from the dominant taxable case: "
            "remotely accessed software / true SaaS where the "
            "customer does NOT take possession or control of the "
            "software (Information Bulletin #8 -- not taxable as "
            "tangible personal property), custom computer programs, "
            "and digital media sold without a permanent right of "
            "use (subscription streaming etc., which raises distinct "
            "questions outside the scope of section 6-2.5-4-16.4). "
            "The engine encodes the dominant case as taxable; "
            "callers shipping SaaS or subscription-only digital "
            "media to Indiana should categorize those line items "
            "differently or apply an exemption until a sub-category "
            "split lands. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Indiana at the 7% state rate per Ind. Code section "
            "6-2.5-2-1 (imposition), section 6-2.5-2-2(a) (rate, "
            "raised from 6% to 7% effective April 1, 2008 by P.L. "
            "146-2008), and section 6-2.5-1-27 (definition of "
            "tangible personal property). Indiana levies NO local "
            "sales tax -- the 7% state rate is the entire combined "
            "rate everywhere in the state. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
}


class Indiana(SstStateModule):
    """Indiana state module (tier 1, SST member; state-only -- no locals).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS), the jurisdiction-type
    code mapping (which restricts the inherited SST parser to
    state-level rows since IN has no sub-state sales taxes), and
    the taxability matrix. Rate parsing, boundary parsing, special
    cases, and the empty-holidays default are all inherited.
    """

    state_abbrev: str = "IN"
    state_name: str = "Indiana"
    state_fips: str = "18"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.indiana`` registers
# Indiana under "IN" in the state registry.
_PROTOCOL_CHECK: StateModule = Indiana()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# instance (mirrors MINNESOTA, WISCONSIN, etc.). Indiana's RateRow
# emits ``rate_pct=Decimal("7.000")`` from the SST file; the
# constant below is purely documentary so future readers can grep
# the codebase for the rate.
INDIANA_GENERAL_RATE_PCT: Decimal = Decimal("7.000")

INDIANA = register(Indiana())
