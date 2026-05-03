# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Nevada state module (tier 1, SST member).

NV is a Streamlined Sales Tax member (verified 2026-05-03 against
the SST member roster on streamlinedsalestax.org). The minimum
statewide combined rate -- the rate that applies in every Nevada
county before any county-option add-ons -- is **6.85%**.

## RATE COMPOSITION

Nevada's 6.85% statewide-minimum rate is the sum of multiple
state-level statutory layers that all counties impose. The headline
number is published by the Nevada Department of Taxation
(https://tax.nv.gov/) and breaks down as follows:

- **2.00%** -- State Sales Tax under **NRS Chapter 372** (the
  Sales and Use Tax Act of 1955; **NRS section 372.105** sets the
  imposition rate). This is the only portion that the Nevada
  Constitution (Art. 10) requires a 2/3 legislative supermajority
  to amend, because the underlying 1955 act was adopted by
  initiative petition.
- **2.60%** -- Local School Support Tax under **NRS Chapter 374**
  (LSST -- imposed by NRS section 374.110, codified statewide in
  every county to fund K-12 education).
- **2.25%** -- State / City-County Relief Tax components (the
  "City-County Relief Tax" + "Basic City-County Relief Tax")
  imposed in every county under **NRS Chapter 377** and related
  authority -- a state-level revenue-sharing layer that returns
  proceeds to local governments. Combined with the 2.00% state
  and 2.60% LSST, this brings every Nevada county to the 6.85%
  statewide minimum rate.

**Combined statewide minimum: 2.00 + 2.60 + 2.25 = 6.85%.**

The Nevada Department of Taxation publishes a single combined
rate in its quarterly "Sales Tax Map" / rate file (the "general
rate" column in the SST quarterly file). v1 ships the 6.85%
combined headline; the underlying 2 / 2.6 / 2.25 split is
documented here for the maintainer who later wants to model
distributions to the Local School Support Tax fund or the
City-County Relief Tax fund separately. The engine does not need
the split for calculation -- a single combined-rate row is
correct for every NV transaction at the state-level minimum.

## LOCAL JURISDICTIONS -- DEFERRED IN v1

Nevada's 17 counties may add additional county-option taxes (per
NRS Chapters 377A, 377B, and various county-specific enabling
statutes covering transit, infrastructure, public safety, indigent
medical services, and other county-level needs). The county-option
add-ons push combined county rates above the 6.85% statewide
minimum:

- **Clark County** (Las Vegas / Henderson / North Las Vegas /
  Boulder City): adds approximately **1.525%** in county-option
  taxes, for a combined rate of approximately **8.375%** -- the
  highest in Nevada and applicable to the bulk of Nevada's
  transaction volume (Clark County contains roughly 73% of the
  state's population and an even larger share of its taxable
  retail sales, per the Nevada Department of Taxation's quarterly
  collections reports).
- **Washoe County** (Reno / Sparks): adds approximately
  **1.415%** in county-option taxes, for a combined rate of
  approximately **8.265%**.
- Other counties add smaller increments; rural counties typically
  remain at or near the 6.85% statewide minimum.

**v1 ships only the 6.85% statewide-minimum row.** Per-county
add-on rates are NOT modeled in v1; a v1 caller calculating tax
on a Las Vegas or Reno address will UNDER-COLLECT by the county
add-on amount (~1.5%). This follows the same deferred-locals
pattern established by v0.7 for Louisiana parishes (~64 parishes
deferred), v0.6 for South Carolina counties, and v0.7 for
Missouri / Mississippi local-option taxes -- see
``specs/decisions/05-louisiana-parishes.md`` for the trade-off
discussion (Option A: state-only with prominent deferral) that
applies equally here. A future contribution adding the Nevada
county-add-on table would close this gap; the SST quarterly file
for Nevada presumptively ships per-county rate rows that the
inherited :class:`SstStateModule` parser will pick up once the
``jurisdiction_types`` mapping for NV is validated against an
empirical capture of an NV SST file.

Until that follow-up lands, the inherited parser ships only the
state-level row, and Nevada's effective coverage is "statewide
minimum 6.85% only."

## TAXABILITY MATRIX (per NRS Chapter 372)

- **General tangible personal property** -- TAXABLE at 6.85% per
  **NRS section 372.105** (the imposition statute) and the
  definition of "tangible personal property" in **NRS section
  372.085**.
- **Clothing** -- TAXABLE. Nevada has **no clothing exemption**
  in NRS Chapter 372. Clothing and footwear are general tangible
  personal property and tax at the rate set by NRS 372.105.
- **Groceries (food for human consumption)** -- EXEMPT per
  **NRS section 372.284** ("Sale of food for human consumption
  ... is exempted from the taxes imposed by this chapter"). The
  exemption tracks the Streamlined definition of "food and food
  ingredients" -- candy, soft drinks, dietary supplements, and
  prepared food are NOT included in the exemption (those tax at
  the general 6.85% rate). The exemption was added by the people
  in 1979 and is constitutionally entrenched against repeal by
  Art. 10 section 3 of the Nevada Constitution.
- **Prescription drugs** -- EXEMPT per **NRS section 372.283**
  ("Prescription medicines ... is exempted from the taxes
  imposed by this chapter"). The exemption covers drugs and
  medicines prescribed by a licensed practitioner; it also
  reaches insulin, oxygen for medical use, and certain prosthetic
  devices. Over-the-counter (non-prescription) drugs are NOT
  covered by this exemption.
- **Prepared food** -- TAXABLE at 6.85%. Prepared food (restaurant
  meals, hot deli items, ready-to-eat foods) is excluded from the
  food-for-human-consumption exemption in NRS 372.284 and taxes
  at the general rate set by NRS 372.105.
- **Digital goods** -- generally NOT TAXABLE in Nevada for the
  dominant case (downloaded ebooks, streaming subscriptions,
  downloaded software, SaaS, and similar electronically-delivered
  digital products). Nevada's sales-tax base is restricted by
  statute to "tangible personal property" as defined in **NRS
  section 372.085**, which requires the property to be "tangible"
  (i.e. capable of being seen, weighed, measured, felt, or touched,
  or in any other manner perceptible to the senses). The Nevada
  Department of Taxation has consistently taken the position that
  electronically-delivered digital products do not satisfy the
  tangibility requirement and are therefore outside the sales-tax
  base. Prewritten ("canned") computer software delivered on a
  physical medium IS taxable as TPP; prewritten software delivered
  electronically is NOT taxable absent specific legislative
  expansion (no such expansion has been enacted as of the SST
  quarterly capture used to validate this module). This is a
  notable contrast with peer SST states like Iowa (which taxes
  specified digital products under Iowa Code 423.5A) and Indiana
  (which taxes them under Ind. Code 6-2.5-4-16.4).

## SALES TAX HOLIDAYS

Nevada has **ONE annual sales-tax holiday** in current law: the
**Nevada National Guard Sales Tax Holiday**, codified at
**NRS section 372.7282**.

### NEVADA NATIONAL GUARD HOLIDAY -- BUYER-ELIGIBILITY GAP -- NOT MODELED IN v1

Per NRS 372.7282, the holiday exempts ALL sales of tangible
personal property to **active-duty members of the Nevada National
Guard and their immediate families** from sales/use tax during a
3-day window each year, traditionally the **Friday-Saturday-Sunday
closest to Nevada Day (October 31)**. There is no per-item dollar
cap and no item-category restriction; the holiday is defined by
**buyer eligibility** (active Nevada Guard member or family),
which the buyer establishes at point of sale by presenting
qualifying military / dependent identification.

This holiday is **structurally different** from every other state
sales-tax holiday currently modeled by OpenSalesTax. Florida,
Texas, Massachusetts, Maryland, Mississippi, Iowa, Arkansas,
Louisiana, etc. all define their holidays by **item category +
date + per-item cap** -- properties that the engine's
:class:`HolidayWindow` and :class:`opensalestax.db.models.HolidayPeriod`
schema model directly. Nevada's National Guard holiday adds a
dimension (buyer eligibility) that the engine does NOT currently
model: there is no per-buyer exemption-certificate mechanism, no
buyer-class field on the calculation request, and no way for the
engine to know whether a given line item is being purchased by an
eligible National Guard member or by an ineligible general
consumer.

If the engine were to expose this holiday as a date-only,
category-wide :class:`HolidayWindow` (i.e.
``applicable_categories=None``, ``max_amount_per_item=None``), the
calculation engine would zero out tax on **every** Nevada
transaction during the 3-day window for **every** buyer --
regardless of National Guard status. That would be a systematic
under-collection bug for every Nevada retailer's general consumer
base. The conservative, correct behavior is to NOT yield this
holiday from :meth:`Nevada.holidays_for` until the engine grows a
buyer-eligibility model (e.g. an exemption-certificate field on
the calculation request, similar to the Phase 5 exemption-cert
feature reserved in the constitution / current-state roadmap).

**v1 decision:** :meth:`Nevada.holidays_for` returns an empty
iterator for every year. The Nevada National Guard Sales Tax
Holiday is documented here, in :file:`MAINTAINERS.md`, and in
:file:`specs/research/references.md`, but is NOT exposed to the
calculation engine in v1. A future PR -- gated on the engine's
buyer-eligibility / exemption-certificate model landing -- can
re-enable it as a buyer-class-restricted exemption rather than
a category / date-only holiday window.

This decision matches the project's correctness-over-coverage
posture: a missing holiday under-exempts an eligible buyer (which
the buyer can correct via their refund process with the Nevada
Department of Taxation) but a misapplied holiday under-collects
on every non-eligible buyer (which the retailer would have to
make up out of its own funds plus penalties). Under-collection is
the more harmful failure mode.

## LOADING

Nevada's rate data loads from the SST quarterly rate file via the
inherited :class:`SstStateModule.parse_rates` machinery. Until an
empirical capture of an NV SST file confirms the per-county
jurisdiction-type code mapping, the inherited
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (00 county / 01 city / 45 state / 63 district) applies.
The next maintainer holding an NV SST file should validate the
codes empirically and override ``jurisdiction_types`` on this
subclass if any code differs.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current Nevada
Department of Taxation guidance before relying on these rules in
production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Nevada taxability matrix per NRS Chapter 372.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Nevada at the 6.85% statewide "
            "minimum combined rate. NRS Chapter 372 (Nevada Sales and "
            "Use Tax Act) contains no general clothing exemption; "
            "clothing and footwear are general tangible personal "
            "property under NRS section 372.085 and tax at the rate "
            "set by NRS section 372.105. Nevada has no annual back-"
            "to-school clothing holiday. The Nevada National Guard "
            "Sales Tax Holiday (NRS section 372.7282) is a buyer-"
            "eligibility holiday, NOT a category-based holiday, and "
            "is intentionally NOT modeled in v1 (see module docstring "
            "for the deferral rationale). Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food for human consumption is EXEMPT in Nevada per NRS "
            "section 372.284. The exemption tracks the Streamlined "
            "Sales Tax Project's uniform definition of 'food and food "
            "ingredients' and excludes candy, soft drinks, dietary "
            "supplements, and prepared food (those remain taxable at "
            "the 6.85% statewide minimum rate). The grocery exemption "
            "is constitutionally entrenched by Article 10 section 3 "
            "of the Nevada Constitution (added by initiative petition "
            "in 1979); legislative repeal would require a popular "
            "vote. Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription medicines are EXEMPT in Nevada per NRS "
            "section 372.283. The exemption covers drugs and "
            "medicines prescribed by a licensed practitioner, plus "
            "insulin, oxygen for medical use, and certain prosthetic "
            "devices when prescribed. Over-the-counter (non-"
            "prescription) drugs are NOT covered by the exemption "
            "and remain taxable at the 6.85% statewide minimum rate. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, ready-"
            "to-eat foods) is TAXABLE in Nevada at the 6.85% "
            "statewide minimum rate. The food-for-human-consumption "
            "exemption in NRS section 372.284 expressly excludes "
            "prepared food (along with candy, soft drinks, and "
            "dietary supplements); restaurant meals and ready-to-eat "
            "foods tax at the general rate set by NRS section "
            "372.105. Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=False,
        notes=(
            "Digital goods (electronically-delivered ebooks, "
            "streaming subscriptions, downloaded software, SaaS, "
            "digital audio / video) are generally NOT TAXABLE in "
            "Nevada. NRS section 372.085 limits the sales-tax base "
            "to 'tangible personal property' -- property capable of "
            "being seen, weighed, measured, felt, or touched. The "
            "Nevada Department of Taxation's longstanding position "
            "is that electronically-delivered digital products do "
            "NOT satisfy the tangibility requirement and are "
            "therefore outside the sales-tax base. Prewritten "
            "('canned') computer software delivered on a physical "
            "medium IS taxable as TPP under NRS section 372.085; "
            "the same software delivered electronically is NOT "
            "taxable absent specific legislative expansion (no such "
            "expansion has been enacted in NRS Chapter 372 as of "
            "the SST quarterly capture used to validate this "
            "module). Notable contrast with peer SST states like "
            "Iowa (taxes specified digital products under Iowa "
            "Code 423.5A) and Indiana (Ind. Code 6-2.5-4-16.4). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Nevada "
            "at the 6.85% statewide minimum combined rate per NRS "
            "section 372.105 (imposition) and NRS section 372.085 "
            "(definition of tangible personal property). The 6.85% "
            "rate is the sum of three state-level statutory layers: "
            "2.00% State Sales Tax (NRS Chapter 372, the 1955 "
            "Sales and Use Tax Act); 2.60% Local School Support Tax "
            "(NRS Chapter 374, NRS section 374.110); and 2.25% "
            "City-County Relief Tax components (NRS Chapter 377). "
            "Per-county option add-ons (Clark ~1.525% / Washoe "
            "~1.415% / etc.) are NOT modeled in v1 -- a v1 caller "
            "calculating tax on a Clark or Washoe County address "
            "will UNDER-COLLECT by the county add-on amount. See "
            "the module docstring for the deferred-locals "
            "rationale. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
}


class Nevada(SstStateModule):
    """Nevada state module (tier 1, SST member; statewide minimum only).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS) and the taxability matrix.
    Rate parsing, boundary parsing, special cases, and the empty-
    holidays default are all inherited.

    The Nevada National Guard Sales Tax Holiday (NRS 372.7282) is
    intentionally NOT modeled in v1 because it is a buyer-eligibility
    holiday rather than a category-based holiday, and the engine does
    not currently model buyer eligibility. See the module docstring
    for the full deferral rationale.

    Per-county option add-ons (Clark / Washoe / etc.) are similarly
    deferred in v1 -- the inherited parser ships only the 6.85%
    statewide minimum row. See the module docstring's "LOCAL
    JURISDICTIONS -- DEFERRED IN v1" section for details.
    """

    state_abbrev: str = "NV"
    state_name: str = "Nevada"
    state_fips: str = "32"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.nevada`` registers
# Nevada under "NV" in the state registry.
_PROTOCOL_CHECK: StateModule = Nevada()
del _PROTOCOL_CHECK

# Module-level constant for callers / future maintainers. The actual
# rate that flows into the engine comes from the SST quarterly file
# via the inherited parser; this constant is a documentary anchor
# for the headline 6.85% statewide minimum (sum of 2.00% NRS 372 +
# 2.60% NRS 374 LSST + 2.25% NRS 377 City-County Relief Tax).
NEVADA_STATEWIDE_MINIMUM_RATE_PCT: Decimal = Decimal("6.850")

NEVADA = register(Nevada())
