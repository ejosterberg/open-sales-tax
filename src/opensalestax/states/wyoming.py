# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Wyoming state module (tier 1, SST member).

WY is a Streamlined Sales Tax member (verified 2026-05-03 against
the SST member roster on streamlinedsalestax.org). The statewide
rate is **4.0%** per **Wyo. Stat. Ann. section 39-15-104(a)** (the
imposition statute in the Selective Sales Tax Act of 1937, as
amended). The 4.0% rate has been in continuous effect since
**1994**, when Senate Enrolled Act 31 of the 1993 Wyoming
Legislature raised the rate from 3% to 4% effective July 1, 1993.

## PHASE 7 MILESTONE -- LAST SST MEMBER PROMOTION

**Wyoming is the FINAL Streamlined Sales Tax member to be
promoted from tier 2 to tier 1.** When this module ships, EVERY
SST member state has a fully-maintained tier-1 module with a
state-specific taxability matrix grounded in primary statutory
sources rather than the generic tier-2 default. This completes
**Phase 7** of the OpenSalesTax build (the SST tier-2 -> tier-1
ratchet started in v0.8 with AR/GA/IA/IN, continued through v0.9
KS/KY/MI/NE/NV and v0.10 NC/ND/NJ/OH/OK, and concludes here).

## RATE COMPOSITION -- STATE 4% + COUNTY OPTIONS UP TO ~3%

Wyoming's combined rate structure layers county-level options on
top of the 4% state rate:

- **State rate**: 4.0% per Wyo. Stat. section 39-15-104(a). Applies
  uniformly statewide.
- **General-purpose county sales tax** (the "5th penny"): up to
  **1.0%** per **Wyo. Stat. section 39-15-204(a)(i)**. Counties
  may impose this tax by voter approval; revenues fund general
  county and municipal operations.
- **Specific-purpose county sales tax** (the "6th penny"): up to
  **1.0%** per **Wyo. Stat. section 39-15-204(a)(iii)**. Counties
  may impose this tax by voter approval for a SPECIFIC capital
  project (e.g., a new courthouse, a road improvement, a
  recreation center); the tax sunsets when the funded project
  is paid off.
- **Economic-development / lodging-tax overlays**: counties may
  also impose narrow specific-purpose levies under Wyo. Stat.
  section 39-15-204(a)(iv)-(vii) (lodging tax, county school
  facilities tax, etc.). Lodging tax in particular is a
  separate excise on accommodations (Wyo. Stat. section
  39-15-204(a)(v)) and NOT part of the general sales tax base
  modeled by this engine.

The result: **combined Wyoming sales-tax rates typically range
from 4% to 7%** depending on which county options the local
voters have approved. The current Wyoming Department of Revenue
"Sales, Use and Lodging Tax Rate Chart" (verified 2026-05-03 at
https://revenue.wyo.gov/divisions/excise-tax/excise-tax-publications)
shows most Wyoming counties at 5% (state 4% + 1% general-purpose)
or 6% (state 4% + 1% general-purpose + 1% specific-purpose);
Goshen, Niobrara, and a few others sit at 5%, and a small set of
counties without the 5th-penny option remain at the bare 4%.

WY is an SST member so per-county / per-municipality rates flow
through the standard SST quarterly file. The
:class:`SstStateModule` base class provides the parser; this
subclass only adds the Wyoming-specific taxability matrix.

## SST JURISDICTION-TYPE CODE MAPPING

Per :mod:`specs.research.sst-file-format`, the WY SST rate file
is presumed to use the same jurisdiction-type code mapping that
MN and WI validate empirically at 2026Q2 (codes ``00`` county,
``01`` city, ``45`` state, ``63`` district). The MN/WI codes are
the SST empirical default; if a future quarterly capture of a
Wyoming rate file shows different codes, override
``jurisdiction_types`` on this subclass at that time. Until then
we inherit the
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping.

## TAXABILITY MATRIX (per Wyo. Stat. Title 39, Chapter 15)

- **General tangible personal property** -- TAXABLE at 4% per
  **Wyo. Stat. section 39-15-103(a)(i)** (the imposition
  paragraph) and **section 39-15-104(a)** (the rate-setting
  paragraph). Wyoming's sales-tax base is limited to TANGIBLE
  PERSONAL PROPERTY plus a closed list of enumerated services
  (lodging, communications, admissions, etc.) -- a deliberately
  narrow base by US standards.
- **Clothing** -- TAXABLE year-round at 4%. Wyoming has **no
  general clothing exemption** in chapter 15; clothing and
  footwear are general tangible personal property and tax at the
  rate set by section 39-15-104(a). Wyoming has NO back-to-school
  sales-tax holiday for clothing or any other category (see
  "Sales tax holidays" below).
- **Groceries (food for domestic home consumption)** -- EXEMPT
  per **Wyo. Stat. section 39-15-105(a)(iii)(C)**, effective
  **July 1, 2006** (the exemption was enacted by Senate
  Enrolled Act 64 of the 2006 Wyoming Legislature, taking
  effect at the start of the 2007 fiscal year). The exemption
  covers "food for domestic home consumption" using the
  Streamlined Sales Tax Project's uniform "food and food
  ingredients" definition. Items expressly excluded from the
  exemption (and therefore taxable at the general 4% rate plus
  applicable local options): prepared food, alcoholic
  beverages, tobacco products, candy, soft drinks, and dietary
  supplements.
- **Prescription drugs** -- EXEMPT per **Wyo. Stat. section
  39-15-105(a)(viii)**, which exempts the gross receipts from
  the sale of prescription drugs and certain related items
  (insulin, hypodermic syringes for human use, oxygen and
  oxygen-delivery equipment for human use, and prosthetic
  devices) when dispensed pursuant to a written prescription
  by a licensed practitioner. Over-the-counter
  (non-prescription) drugs are NOT covered by this exemption
  and remain taxable at the general 4% rate plus applicable
  local options.
- **Prepared food** -- TAXABLE at 4% (plus local options) per
  Wyo. Stat. section 39-15-104(a) (general imposition). Wyoming's
  grocery exemption in section 39-15-105(a)(iii)(C) expressly
  excludes prepared food, soft drinks, candy, and dietary
  supplements; restaurant meals, hot deli items, and ready-to-eat
  foods tax at the general rate.
- **Digital goods (specified digital products)** -- **NOT TAXABLE**
  in Wyoming. This is a notable peer-state difference: Wyoming's
  sales-tax base under **Wyo. Stat. section 39-15-103(a)(i)** is
  limited to "the sales price paid for tangible personal property"
  plus a closed list of enumerated services (lodging,
  communications, intrastate transportation, admissions to places
  of amusement, etc.). The Wyoming Legislature has NOT amended
  the Selective Sales Tax Act to extend the base to specified
  digital products as those terms are defined by the Streamlined
  Sales Tax Project. The Wyoming Department of Revenue's
  longstanding administrative position -- consistent with the
  statutory limitation in section 39-15-103 -- is that
  electronically-delivered digital goods (downloaded software,
  music / video / ebook downloads, streaming subscriptions,
  cloud software, and SaaS) are NOT tangible personal property
  and are NOT subject to Wyoming sales or use tax. EXCEPTION:
  prewritten ("canned") computer software delivered on a
  TANGIBLE medium (disk, USB drive, etc.) IS taxable as tangible
  personal property -- callers shipping physical software media
  to Wyoming customers should categorize those line items as
  ``general`` rather than ``digital_goods`` so the correct rate
  is applied. This differs from peer SST states that have
  legislated digital-goods taxation (IA section 423.5A effective
  2019; IN section 6-2.5-4-16.4 effective 2018; WI section
  77.52(1)(d) effective 2010; NJ section 54:32B-3(a) as amended
  by P.L. 2011, c. 49) and aligns Wyoming with MI, NV, and OK
  in the small minority of SST states that have NOT extended
  their sales-tax base to specified digital products. A future
  Wyoming Legislature could amend section 39-15-103; this rule
  should be re-verified against current Department of Revenue
  guidance at every data refresh.

## SALES-TAX HOLIDAYS

**NONE.** Wyoming has **never enacted a sales-tax holiday**.
Verified 2026-05-03 against the Wyoming Department of Revenue's
published guidance (https://revenue.wyo.gov/) and a search of
the Selective Sales Tax Act (Wyo. Stat. Title 39, Chapter 15)
for any periodic exemption window -- there is no back-to-school
holiday, no disaster-prep holiday, no Energy Star holiday, and
no other recurring exemption period in Wyoming law. The
:meth:`Wyoming.holidays_for` method returns an empty iterator
for every year (mirroring the inherited tier-2 default and
peer states MI, ID, IN, KY, NE, NJ, ND).

## LOADING

Wyoming's rate data loads from the SST quarterly rate file via
the inherited :class:`SstStateModule.parse_rates` machinery.
The SST file is expected to ship a single state-level row plus
per-county rows for the general-purpose and specific-purpose
options approved by each county's voters. Boundary loading
inherits the generic ``z``-record ZIP5 walker; Wyoming's
relatively small population and modest ZIP-code count (~150
unique ZIP5 codes statewide) make this a lightweight load
compared to peer states.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Wyoming Department of Revenue guidance before relying on these
rules in production. Wyoming's digital-goods position in
particular is administrative + statutory (the statute limits the
base to TPP) and could shift if the Legislature amends section
39-15-103 to extend the base to specified digital products.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Wyoming taxability matrix per Wyo. Stat. Title 39, Chapter 15
# (Selective Sales Tax Act).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Wyoming year-round at the 4% "
            "state rate (plus any applicable county-level local "
            "options under Wyo. Stat. section 39-15-204). The "
            "Selective Sales Tax Act (Wyo. Stat. Title 39, Chapter "
            "15) contains no general clothing exemption; clothing "
            "and footwear are general tangible personal property "
            "under Wyo. Stat. section 39-15-103(a)(i) and tax at "
            "the rate set by Wyo. Stat. section 39-15-104(a). "
            "Wyoming has NO annual back-to-school sales-tax "
            "holiday and has never enacted a sales-tax holiday of "
            "any kind. Calculation only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food for domestic home consumption is EXEMPT in "
            "Wyoming per Wyo. Stat. section 39-15-105(a)(iii)(C), "
            "effective July 1, 2006 (enacted by Senate Enrolled "
            "Act 64 of the 2006 Wyoming Legislature). The "
            "exemption tracks the Streamlined Sales Tax Project's "
            "uniform definition of 'food and food ingredients' "
            "and applies to both the 4% state rate and any "
            "applicable county-level local options. Items "
            "expressly excluded from the exemption (and therefore "
            "taxable): prepared food, alcoholic beverages, "
            "tobacco products, candy, soft drinks, and dietary "
            "supplements -- those remain taxable at the 4% state "
            "rate plus local options. The OpenSalesTax engine "
            "maps the 'groceries' category to SNAP-eligible food "
            "and food ingredients; callers selling candy, soft "
            "drinks, or supplements to Wyoming customers should "
            "categorize those line items as 'general' (or "
            "'prepared_food' for hot/ready items) rather than "
            "'groceries' so the correct rate is applied. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Wyoming per Wyo. "
            "Stat. section 39-15-105(a)(viii), which exempts the "
            "gross receipts from the sale of prescription drugs "
            "and related items (insulin, hypodermic syringes for "
            "human use, oxygen and oxygen-delivery equipment for "
            "human use, and prosthetic devices) when dispensed "
            "pursuant to a written prescription by a licensed "
            "practitioner. Over-the-counter (non-prescription) "
            "drugs are NOT covered by this exemption and remain "
            "taxable at the general 4% rate plus applicable "
            "local options. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, "
            "ready-to-eat foods) is TAXABLE in Wyoming at the 4% "
            "state rate (plus applicable county-level local "
            "options) per Wyo. Stat. section 39-15-104(a) "
            "(general imposition). The food-for-domestic-home-"
            "consumption exemption in Wyo. Stat. section "
            "39-15-105(a)(iii)(C) expressly excludes prepared "
            "food (along with candy, soft drinks, alcoholic "
            "beverages, tobacco products, and dietary "
            "supplements); restaurant meals and ready-to-eat "
            "foods tax at the rate set by section 39-15-104(a). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=False,
        notes=(
            "Specified digital products are NOT TAXABLE in "
            "Wyoming -- a notable peer-state difference. Wyoming's "
            "sales-tax base under Wyo. Stat. section "
            "39-15-103(a)(i) is limited to 'the sales price paid "
            "for tangible personal property' plus a closed list "
            "of enumerated services (lodging, communications, "
            "intrastate transportation, admissions to places of "
            "amusement, etc.). The Wyoming Legislature has NOT "
            "amended the Selective Sales Tax Act (Wyo. Stat. "
            "Title 39, Chapter 15) to extend the base to "
            "'specified digital products' as those terms are "
            "defined by the Streamlined Sales Tax Project. The "
            "Wyoming Department of Revenue's longstanding "
            "administrative position -- consistent with the "
            "statutory limitation in section 39-15-103 -- is that "
            "electronically-delivered digital goods (downloaded "
            "software, music / video / ebook downloads, streaming "
            "subscriptions, cloud software, and SaaS) are NOT "
            "tangible personal property and are NOT subject to "
            "Wyoming sales or use tax. EXCEPTION: prewritten "
            "('canned') computer software delivered on a TANGIBLE "
            "medium (disk, USB drive, etc.) IS taxable as "
            "tangible personal property under section "
            "39-15-103(a)(i) -- callers shipping physical "
            "software media to Wyoming should categorize those "
            "line items as 'general' rather than 'digital_goods' "
            "so the correct 4%+local rate is applied. This "
            "differs from peer SST states that have legislated "
            "digital-goods taxation (IA section 423.5A effective "
            "2019; IN section 6-2.5-4-16.4 effective 2018; WI "
            "section 77.52(1)(d) effective 2010; NJ section "
            "54:32B-3(a) as amended by P.L. 2011, c. 49) and "
            "aligns Wyoming with MI, NV, and OK in the small "
            "minority of SST states that have NOT extended their "
            "sales-tax base to specified digital products. A "
            "future Wyoming Legislature could amend section "
            "39-15-103; this rule should be re-verified against "
            "current Department of Revenue guidance at every "
            "data refresh. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Wyoming at the 4% state rate per Wyo. Stat. section "
            "39-15-104(a) (the rate-setting paragraph) and Wyo. "
            "Stat. section 39-15-103(a)(i) (the imposition "
            "paragraph). The 4% rate has been in continuous "
            "effect since July 1, 1993 (raised from 3% to 4% by "
            "Senate Enrolled Act 31 of the 1993 Wyoming "
            "Legislature). Counties may impose general-purpose "
            "and specific-purpose local-option sales taxes of up "
            "to 1% each under Wyo. Stat. section 39-15-204(a)(i) "
            "and (a)(iii); combined Wyoming sales-tax rates "
            "typically range from 4% to 7% depending on which "
            "options local voters have approved. Per-county rates "
            "flow through the SST quarterly file via the "
            "inherited parser. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
}


class Wyoming(SstStateModule):
    """Wyoming state module (tier 1, SST member; final SST promotion).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS) and the taxability
    matrix. Rate parsing, boundary parsing, special cases, and the
    empty-holidays default are all inherited.

    Wyoming is the FINAL SST member to be promoted from tier 2 to
    tier 1 (Phase 7 milestone). With this module shipped, every
    SST member state has a fully-maintained taxability matrix
    grounded in primary statutory sources.

    Notable peer-state differences worth flagging for an integrator:

    - **Digital goods are NOT taxable** in WY (joins MI, NV, OK in
      the small minority of SST states that haven't extended the
      sales-tax base to specified digital products). The base is
      statutorily limited to tangible personal property plus a
      closed list of enumerated services per Wyo. Stat. section
      39-15-103(a)(i).
    - **Groceries have been exempt since July 1, 2006** per Wyo.
      Stat. section 39-15-105(a)(iii)(C), enacted by S.E.A. 64 of
      the 2006 Wyoming Legislature.
    - **No sales-tax holidays.** WY has never enacted a sales-tax
      holiday of any kind; ``holidays_for`` returns the empty
      iterator for every year.
    """

    state_abbrev: str = "WY"
    state_name: str = "Wyoming"
    state_fips: str = "56"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Wyoming-specific taxability matrix replaces the default tier-2
    # grocery-only matrix.
    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.wyoming`` registers
# Wyoming under "WY" in the state registry.
_PROTOCOL_CHECK: StateModule = Wyoming()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# state's general rate. Wyoming's RateRow stream emits
# ``rate_pct=Decimal("4.000")`` from the SST file for the state-level
# row; the constant below is purely documentary so future readers can
# grep the codebase for the rate.
WYOMING_STATE_RATE_PCT: Decimal = Decimal("4.000")

WYOMING = register(Wyoming())
