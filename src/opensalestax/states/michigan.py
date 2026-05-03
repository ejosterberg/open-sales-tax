# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Michigan state module (tier 1, SST member).

MI is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The statewide general sales/use tax
rate is **6.0%** per **MCL section 205.52(1)** (the General Sales
Tax Act, Public Act 167 of 1933 as amended). The 6% rate has been
in effect since 1994, when Proposal A raised it from 4% to 6% and
constitutionalized that level under Article IX section 8 of the
Michigan Constitution; further increases require a 3/4 supermajority
of both legislative chambers.

## NOTABLE DIFFERENCE FROM PEER STATES: NO LOCAL SALES TAX

Michigan is one of a small number of US states that **levies NO
general local sales tax**. The 6% state rate is the entire combined
sales-tax rate at every Michigan address -- there are no county,
city, township, or special-district general sales taxes layered on
top.

Article IX section 8 of the Michigan Constitution caps the state
sales tax at 6% and (combined with the legislative architecture of
the General Sales Tax Act in MCL Chapter 205) preempts local
general sales taxes entirely. A handful of narrow industry-
specific local taxes do exist:

- Accommodations / lodging excise taxes (e.g., Wayne County
  hotel/motel tax for the Detroit area, the Michigan Convention
  Facility Development Act tax)
- Stadium and convention-facility development taxes in select
  counties under specific enabling acts
- City utility-users taxes (very narrow; not a general sales tax)
- Detroit's various municipal levies under its city charter

These are NOT general sales taxes -- they are narrow industry-
specific levies that do not apply to general retail transactions
and are not modeled by this module. General retail sales in
Michigan always tax at exactly 6.0%.

This is a notable contrast with peer SST member states (e.g. WI's
counties typically add 0.5%; MN's metro adds transit districts)
and mirrors Indiana's no-local-tax landscape (Ind. Code Title 6,
Article 2.5). The SST rate file for Michigan effectively ships a
single state-level row, and the ``_JURISDICTION_TYPE`` dict below
maps only the state-type code.

## SST jurisdiction-type code mapping

Michigan's SST rate file has only state-level entries (no
counties, cities, or districts to map). The dict accepts only
the canonical state-type code ``"45"`` so that any unexpected
non-state row in a future quarterly file is silently dropped
rather than miscategorized -- an over-collection or under-
collection bug in this module would be more harmful than a
gap in coverage that surfaces during review.

## Taxability matrix (per MCL Chapter 205, General Sales Tax Act)

- **General tangible personal property** -- TAXABLE at 6% per
  MCL section 205.52 (imposition) and section 205.51(1)(d)
  (definition of "sale at retail"). The 6% rate is set by
  section 205.52(1).
- **Clothing** -- TAXABLE. Michigan has **no general clothing
  exemption** in the General Sales Tax Act; clothing and footwear
  are ordinary tangible personal property and tax at the full 6%.
  Michigan has NO back-to-school holiday for clothing.
- **Groceries (food and food ingredients)** -- EXEMPT per **MCL
  section 205.54g(1)(a)**. The exemption covers "food or food
  ingredients" for human consumption, tracking the SST common
  definition. Items expressly excluded from "food and food
  ingredients" -- prepared food, candy, alcoholic beverages,
  dietary supplements, soft drinks, tobacco -- remain TAXABLE at
  6%. (Note: section 205.54g(2) defines "prepared food" by
  reference to the SST uniform definitions.)
- **Prescription drugs** -- EXEMPT per **MCL section 205.94d(1)**
  (the Use Tax Act companion is at MCL section 205.94d; the Sales
  Tax Act mirror is in MCL section 205.54a(1)(g) for sales of drugs
  for human use sold pursuant to a prescription). The exemption
  covers prescription drugs for human use, plus insulin (whether or
  not sold by prescription), oxygen and other items required by a
  written prescription. Over-the-counter drugs are NOT exempt.
- **Prepared food** -- TAXABLE at 6% per MCL section 205.52
  (general imposition); "prepared food" is expressly excluded from
  the food-and-food-ingredients exemption in section 205.54g(2).
- **Digital goods (specified digital products)** -- **NOT TAXABLE**
  in Michigan. This is a notable peer-state difference: Michigan
  has NOT amended the General Sales Tax Act or the Use Tax Act to
  reach electronically-delivered digital products. The Michigan
  Department of Treasury's longstanding administrative position --
  most recently affirmed in **Revenue Administrative Bulletin
  (RAB) 2023-22** (Sales of Computer Software and Digital Products)
  and predecessors RAB 1999-5 and RAB 2015-20 -- is that the sales
  and use taxes apply only to sales of TANGIBLE personal property,
  and electronically-delivered digital goods (downloaded software,
  music/video/ebook downloads, streaming subscriptions, cloud
  software, SaaS) are NOT tangible personal property and are NOT
  subject to tax. The Michigan Supreme Court's decision in *Auto-
  Owners Insurance Co. v. Department of Treasury*, 313 Mich. App.
  56 (2015), aff'd 500 Mich. 921 (2016), confirmed that prewritten
  computer software delivered electronically (without transfer of
  any tangible medium) is not subject to Michigan use tax. Tangible
  prewritten software (delivered on disk, USB, etc.) IS taxable;
  the distinction turns on the medium of delivery.

  This differs from peer SST states that have legislated a digital-
  goods sales tax (IA's section 423.5A effective 2019; IN's section
  6-2.5-4-16.4 effective 2018; WI's section 77.52(1)(d) effective
  2010) and from the SST common definitions, which Michigan has
  adopted for OTHER purposes (food, prepared food, drugs) but NOT
  for the digital-products imposition. A future Michigan Legislature
  could amend the Act to reach digital products; as of 2026-05-03
  the position remains "not taxable." This rule is encoded as
  ``is_taxable=False`` and the notes call out the RAB and Auto-
  Owners decision so a future maintainer can re-verify.

## Sales-tax holidays

**NONE.** Michigan has never enacted a sales-tax holiday.
Confirmed 2026-05-03 against the Michigan Department of Treasury's
published guidance and a search of the General Sales Tax Act for
any periodic exemption window -- there is no back-to-school
holiday, no disaster-prep holiday, no Energy Star holiday, and
no other recurring exemption period in Michigan law. The
``holidays_for(year)`` method returns an empty iterator for every
year (mirroring DC, ID, and IN).

## Loading

Michigan's rate data loads from the SST quarterly rate file via
the inherited ``SstStateModule.parse_rates`` machinery. Because
the file ships only the state-level row, the resulting
``RateRow`` stream is a single record with
``authority_type='state'``, ``rate_pct=Decimal('6.000')``, and no
parent. Boundary loading inherits the generic ``z``-record ZIP5
walker but is effectively a no-op for Michigan (no sub-state
authorities to bind ZIPs to); the engine answers every Michigan
ZIP with the single state authority + 6% rate.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Michigan Department of Treasury guidance before relying on these
rules in production. Michigan's digital-goods position in
particular is administrative (RAB) rather than statutory and
could shift if the Legislature amends the General Sales Tax Act.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Michigan has NO general local sales tax. The SST rate file contains
# only state-level rows, so we map only the canonical state code. Any
# unexpected non-state row in a future quarterly file is silently
# dropped by the inherited parser (rather than miscategorized as
# something that does not exist in MI's general-sales-tax landscape).
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
}

# Michigan taxability matrix per MCL Chapter 205 (General Sales Tax Act).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Michigan at the 6% state rate. "
            "The General Sales Tax Act (MCL Chapter 205) contains no "
            "general clothing exemption; clothing and footwear are "
            "ordinary tangible personal property under MCL section "
            "205.51(1)(d) and tax at the rate set by MCL section "
            "205.52(1). Michigan has NO annual back-to-school sales-"
            "tax holiday. Calculation only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients for human consumption are "
            "EXEMPT in Michigan per MCL section 205.54g(1)(a). The "
            "exemption tracks the Streamlined Sales Tax Project's "
            "uniform definition of 'food and food ingredients'. Items "
            "expressly excluded from the exemption (prepared food, "
            "candy, alcoholic beverages, dietary supplements, soft "
            "drinks, tobacco) remain TAXABLE at the 6% state rate. "
            "Prepared food (restaurant meals, hot deli items, ready-"
            "to-eat foods) is excluded from the exemption -- see the "
            "'prepared_food' rule. The OpenSalesTax engine maps the "
            "'groceries' category to SNAP-eligible food and food "
            "ingredients; callers selling candy, soft drinks, or "
            "supplements to Michigan customers should categorize "
            "those line items as 'general' (or 'prepared_food' for "
            "hot/ready items) rather than 'groceries' so the correct "
            "6% rate is applied. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs for human use are EXEMPT in Michigan "
            "per MCL section 205.54a(1)(g) (Sales Tax Act) and the "
            "parallel Use Tax Act provision at MCL section 205.94d. "
            "The exemption covers drugs sold pursuant to a "
            "prescription, plus insulin (with or without prescription), "
            "oxygen, and other items required by a written "
            "prescription. Over-the-counter (non-prescription) drugs "
            "are NOT covered by this exemption and remain taxable at "
            "the general 6% rate. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-eat "
            "deli items) is TAXABLE in Michigan at the 6% state rate "
            "per MCL section 205.52 (general imposition). 'Prepared "
            "food' is expressly excluded from the food-and-food-"
            "ingredients exemption in MCL section 205.54g(2), which "
            "incorporates the SST uniform definition of prepared food. "
            "Michigan has NO general local sales tax, so the combined "
            "rate on prepared food is exactly 6%; narrow industry-"
            "specific local accommodations or convention-facility "
            "taxes (e.g., Wayne County / Detroit) are NOT modeled by "
            "this module. Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=False,
        notes=(
            "Specified digital products are NOT TAXABLE in Michigan -- "
            "a notable peer-state difference. The General Sales Tax "
            "Act and Use Tax Act apply only to sales of TANGIBLE "
            "personal property, and the Michigan Department of "
            "Treasury's longstanding position (Revenue Administrative "
            "Bulletin 2023-22, prior RAB 2015-20 and RAB 1999-5) is "
            "that electronically-delivered digital goods -- downloaded "
            "software, music / video / ebook downloads, streaming "
            "subscriptions, cloud software, and SaaS -- are NOT "
            "tangible personal property and are NOT subject to "
            "Michigan sales or use tax. The Michigan Supreme Court's "
            "decision in Auto-Owners Insurance Co. v. Department of "
            "Treasury, 313 Mich. App. 56 (2015), aff'd 500 Mich. 921 "
            "(2016), confirmed that prewritten computer software "
            "delivered electronically (no tangible medium) is not "
            "subject to Michigan use tax. EXCEPTION: prewritten "
            "computer software delivered on a TANGIBLE medium (disk, "
            "USB drive, etc.) IS taxable as tangible personal "
            "property -- callers shipping physical software media to "
            "Michigan should categorize those line items as 'general' "
            "rather than 'digital_goods' so the correct 6% rate is "
            "applied. This differs from peer SST states that have "
            "legislated digital-goods taxation (IA section 423.5A "
            "effective 2019; IN section 6-2.5-4-16.4 effective 2018; "
            "WI section 77.52(1)(d) effective 2010). A future "
            "Michigan Legislature could amend the Act; this rule "
            "should be re-verified against the current RAB at every "
            "data refresh. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Michigan "
            "at the 6% state rate per MCL section 205.52(1) "
            "(imposition) and MCL section 205.51(1)(d) (definition of "
            "'sale at retail'). The 6% rate has been in effect since "
            "Proposal A of 1994, which raised the rate from 4% to 6% "
            "and constitutionalized that level under Article IX "
            "section 8 of the Michigan Constitution (further "
            "increases require a 3/4 supermajority of both legislative "
            "chambers). Michigan levies NO general local sales tax -- "
            "the 6% state rate is the entire combined rate everywhere "
            "in the state. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
}


class Michigan(SstStateModule):
    """Michigan state module (tier 1, SST member; state-only -- no general locals).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS), the jurisdiction-type
    code mapping (which restricts the inherited SST parser to
    state-level rows since MI has no sub-state general sales taxes),
    and the taxability matrix. Rate parsing, boundary parsing,
    special cases, and the empty-holidays default are all inherited.
    """

    state_abbrev: str = "MI"
    state_name: str = "Michigan"
    state_fips: str = "26"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.michigan`` registers
# Michigan under "MI" in the state registry.
_PROTOCOL_CHECK: StateModule = Michigan()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# state's general rate. Michigan's RateRow emits
# ``rate_pct=Decimal("6.000")`` from the SST file; the constant below
# is purely documentary so future readers can grep the codebase for
# the rate.
MICHIGAN_GENERAL_RATE_PCT: Decimal = Decimal("6.000")

MICHIGAN = register(Michigan())
