# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""North Carolina state module (tier 1, SST member).

NC is a Streamlined Sales Tax full member (verified 2026-05-03
against the SST member roster on streamlinedsalestax.org). The
general statewide retail sales-and-use-tax rate is **4.75%** per
**N.C.G.S. section 105-164.4(a)** (rate raised from 4.5% to 4.75%
effective **2011-10-15** by the 2011 budget act, S.L. 2011-145
section 31A.1; the 4.75% state rate has been stable since).

## Local-jurisdiction landscape

North Carolina counties impose layered local sales taxes by
voter approval and statutory authorization under N.C.G.S.
Chapter 105, Subchapter VIII (Articles 39, 40, 42, 43, 46) and
related provisions. The typical county stack is:

- **2.00% Article 39 first one-cent** (N.C.G.S. section 105-466)
  -- the original local option, levied by every NC county
- **0.50% Article 40 first one-half cent** (section 105-480) and
  **0.50% Article 42 second one-half cent** (section 105-495) --
  later additions, also levied county-wide in nearly every county
- **0.50% (or 0.25%) Article 43/46 transit, education, or
  general option** -- voter-approved overlays in specific
  counties (Mecklenburg, Durham, Orange, Wake, etc.)

Combined statewide-plus-local general rates therefore typically
fall in the **6.75% (4.75% state + 2.00% Article 39 only) to
7.50% (4.75% + 2.00% + 0.50% + 0.25%)** range. As an SST member,
NC's per-jurisdiction rates flow through the standard SST
quarterly rate file; the inherited :class:`SstStateModule`
parser handles them without state-specific overrides. The
default jurisdiction-type code mapping (45 state, 00 county,
01 city, 63 district) is presumed -- consistent with MN/WI/IA
empirical validation -- and should be confirmed against an
actual ``NCR<...>.csv`` capture by the next maintainer.

## The North Carolina "food county tax" -- the unusual quirk

Groceries (food and food ingredients) are **EXEMPT from the
state 4.75% portion** under **N.C.G.S. section 105-164.13B(a)**
(the "food exemption" enacted by the 1996 General Assembly
session in S.L. 1996-13 / 2nd Ext. session, codified at
section 105-164.13B). However, **a uniform 2.00% local food
tax applies in EVERY one of the 100 NC counties** under
**N.C.G.S. section 105-468.1** (the "Article 39A food county
tax"). The structure is unusual: rather than the standard
state-and-local layering, the General Assembly excluded
qualifying food from the state portion and from the regular
Article 39/40/42 local sales taxes, then re-imposed a single
uniform 2.00% county-level food tax that is mandatory state-
wide. Net effective rate on qualifying groceries is therefore
**2.00% statewide** -- the state portion is 0%, but the 2%
local food tax always applies.

Encoded with ``rate_modifier=Decimal("2.000")`` to mark the
2% effective rate (mirrors the MS / VA / MO pattern; the
engine applies rate_modifier (since v0.11.1), so until v0.6+ wires
it through the engine over-collects on NC grocery line items
by 2.75 percentage points -- the difference between the full
4.75% state rate and the actual 2.00% effective grocery rate).
The MS precedent (``mississippi.py``) already encodes a
similar reduced-state-rate pattern with ``rate_modifier``;
NC differs in that the state portion is fully ZERO and the 2%
is a separate statutory local food tax rather than a reduced
state rate, but the in-engine encoding (a single per-category
effective rate via ``rate_modifier``) is identical.

Items NOT meeting the SST "food and food ingredients"
definition (candy, soft drinks, dietary supplements,
alcoholic beverages, tobacco) and prepared food are EXCLUDED
from the food exemption and tax at the full combined state +
local rate (typically 6.75%-7.50%) per N.C.G.S. section
105-164.13B(a)(1) (incorporating the SST-uniform definition).

## Taxability matrix (per N.C.G.S. Chapter 105, Article 5)

- **General tangible personal property** -- TAXABLE at 4.75%
  per N.C.G.S. section 105-164.4(a)(1) (the imposition
  statute).
- **Clothing** -- TAXABLE year-round at the full combined
  rate. North Carolina has **no general clothing exemption**
  in Article 5; clothing and footwear are general tangible
  personal property and tax at the rate set by section
  105-164.4(a)(1). NC repealed its annual back-to-school
  sales-tax holiday effective 2014 (see "Sales-tax holidays"
  below).
- **Groceries (food and food ingredients)** -- EXEMPT from
  the state 4.75% portion per N.C.G.S. section 105-164.13B(a)
  but SUBJECT TO a uniform 2.00% local food tax per N.C.G.S.
  section 105-468.1 in every county. Encoded with
  ``is_taxable=True`` and ``rate_modifier=Decimal("2.000")``
  to capture the 2.00% effective statewide grocery rate
  (state portion 0% + uniform 2% local food county tax).
- **Prescription drugs** -- EXEMPT per **N.C.G.S. section
  105-164.13(13)** (drugs, including over-the-counter drugs,
  required by federal law to be dispensed only by
  prescription, and other prescribed medical items including
  insulin sold to a pharmacist for a person diagnosed with
  diabetes by a licensed physician).
- **Prepared food** -- TAXABLE at the full combined rate per
  N.C.G.S. section 105-164.4(a)(1) and section 105-164.3
  (definitions). "Prepared food" is expressly excluded from
  the section 105-164.13B(a) food exemption -- restaurant
  meals, hot deli items, ready-to-eat food, and food served
  with eating utensils tax at the full state + local rate.
  A handful of NC counties also impose a separate prepared-
  food and beverage tax authorized by individual local-and-
  private-laws acts (e.g., Mecklenburg County 1.0% prepared-
  food and beverage tax under the Mecklenburg County
  Convention Center Act); those are NOT general sales taxes
  and are NOT modeled by this module.
- **Digital goods (specified digital products)** -- TAXABLE
  at the general 4.75% state rate (plus full local rate) per
  **N.C.G.S. section 105-164.4(a)(6b)** (digital property),
  added by S.L. 2009-451 section 27A.4(a) effective
  **2010-01-01**. The statute incorporates the SST-uniform
  "specified digital products" definition: digital audio
  works, digital audiovisual works, digital books, digital
  magazines, digital newspapers, digital photographs,
  digital greeting cards -- whether transferred with a
  permanent right of use or under a subscription /
  conditional access model. Prewritten ("canned") computer
  software delivered by any means is also taxable as
  tangible personal property under N.C.G.S. section
  105-164.3 (definitions); custom computer software and
  most true SaaS arrangements (where the customer takes
  neither possession nor control of the software) remain
  non-taxable per NC DOR Sales and Use Tax Bulletin section
  44-2.

## Sales-tax holidays

**NONE.** North Carolina **repealed its annual back-to-school
sales-tax holiday effective 2014** by **S.L. 2013-316 section
4.1** (the 2013 tax-reform act). NC also repealed its annual
Energy Star sales-tax holiday by the same act. From the 2002
enactment of the back-to-school holiday (S.L. 2002-126
section 30A.1, codified at former N.C.G.S. section
105-164.13C) through 2013, North Carolina held an annual
August holiday exempting clothing under $100, school supplies
under $100, sports/recreation equipment under $50, computers
under $3,500, and computer accessories. The 2013 General
Assembly let the holiday expire as part of broader tax-base
broadening; the underlying authorizing statute (former
section 105-164.13C) was repealed.

The General Assembly has not re-enacted any sales-tax holiday
since (legislative proposals have surfaced in subsequent
sessions but none has passed). The ``holidays_for(year)``
method returns an empty iterator for **every** year (mirrors
DC, ID, IN, KS, GA). Should the General Assembly re-authorize
a holiday in a future session, a maintainer must explicitly
add the year's data; the empty iterable is intentional
regression protection.

## Loading

North Carolina's rate data loads from the SST quarterly rate
file via the inherited :class:`SstStateModule.parse_rates`
machinery. Boundary loading inherits the generic ``z``-record
ZIP5 walker. Per :mod:`specs.research.sst-file-format`, NC's
SST rate file is expected to use the canonical jurisdiction-
type code mapping (45=state, 00=county, 01=city, 63=district);
this is consistent with SST's stated goal of uniform data
formats across member states. NC data has not been empirically
inspected at promotion time; the default mapping is applied
and documented as an assumption a future maintainer should
validate against an actual ``NCR<...>.csv`` file.

State maintainer: vacant -- see MAINTAINERS.md. Natural next
maintenance tasks: validate the NC SST jurisdiction-type
codes against an actual quarterly capture; track the NC
General Assembly's sessions for any future re-enactment of
a back-to-school or other periodic holiday; track any
adjustments to the section 105-468.1 uniform 2% food county
tax (the 2003-enacted rate has been stable but is a
politically visible line item).

DISCLAIMER: This is calculation logic, not legal or tax
advice. Maintainers and users are responsible for verifying
current North Carolina Department of Revenue guidance before
relying on these rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# ---------------------------------------------------------------------------
# NC-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
# ASSUMPTION: NC's SST rate file uses the same jurisdiction-type
# codes as MN, WI, and IA (all empirically validated against
# 2026Q2 data). This is consistent with SST's stated goal of
# uniform data formats across member states. A state maintainer
# should validate against an actual NCR<...>.csv file at next
# refresh and override ``jurisdiction_types`` on the subclass if
# any code differs.
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Static taxability matrix per N.C.G.S. Chapter 105, Article 5.
# Categories not listed default to taxable (engine behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in North Carolina year-round at the "
            "full combined state + local rate per N.C.G.S. section "
            "105-164.4(a)(1). North Carolina General Statutes Chapter "
            "105, Article 5 contains no general clothing exemption; "
            "clothing and footwear are general tangible personal "
            "property and tax at the 4.75% state rate plus any "
            "applicable local sales taxes. North Carolina REPEALED "
            "its annual back-to-school sales-tax holiday effective "
            "2014 by S.L. 2013-316 section 4.1 (the 2013 tax-reform "
            "act); the underlying authorizing statute (former "
            "N.C.G.S. section 105-164.13C) was repealed and the "
            "General Assembly has not re-enacted any sales-tax "
            "holiday since. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("2.000"),
        notes=(
            "Food and food ingredients are EXEMPT from the North "
            "Carolina state 4.75% sales tax per N.C.G.S. section "
            "105-164.13B(a). HOWEVER, a uniform 2.00% LOCAL food "
            "tax (the 'Article 39A food county tax') applies in "
            "EVERY one of the 100 NC counties per N.C.G.S. section "
            "105-468.1. Net effective statewide grocery rate is "
            "therefore 2.00% (state portion 0% + uniform 2% local "
            "food county tax). The 'food and food ingredients' "
            "definition in N.C.G.S. section 105-164.3 tracks the "
            "SST common definition; items NOT meeting it (candy, "
            "soft drinks, dietary supplements, alcoholic beverages, "
            "tobacco) and prepared food remain at the full combined "
            "state + local rate (typically 6.75%-7.50%) per section "
            "105-164.4(a)(1). Encoded with rate_modifier=Decimal("
            "'2.000') to capture the 2.00% effective statewide "
            "grocery rate (mirrors the MS/VA/MO rate_modifier "
            "pattern, but NC's structure is unusual: state portion "
            "is fully ZERO and the 2% is a separate statutory LOCAL "
            "food tax rather than a reduced state rate). The "
            "rate_modifier is stored but the engine does not yet "
            "apply it (shipped in v0.11.1); until then the engine "
            "over-collects on NC grocery line items by 2.75 "
            "percentage points (full 4.75% state instead of the 2% "
            "effective grocery rate). Calculation only -- not legal "
            "or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT from North Carolina sales "
            "and use tax per N.C.G.S. section 105-164.13(13). The "
            "exemption covers drugs (including over-the-counter "
            "drugs required by federal law to be dispensed only by "
            "prescription) sold pursuant to a prescription, plus "
            "insulin sold to a pharmacist for a person diagnosed "
            "with diabetes by a licensed physician, and certain "
            "related prescribed medical items. Over-the-counter "
            "drugs sold without a prescription are NOT covered by "
            "the exemption and tax at the general 4.75% state rate "
            "plus applicable local rate. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-"
            "eat deli items, food sold with eating utensils) is "
            "TAXABLE in North Carolina at the full combined state + "
            "local rate per N.C.G.S. section 105-164.4(a)(1) and "
            "section 105-164.3 (definitions). Prepared food is "
            "expressly EXCLUDED from the section 105-164.13B(a) "
            "food exemption AND from the section 105-468.1 uniform "
            "2% local food county tax (which applies only to the "
            "narrower SST 'food and food ingredients' definition). "
            "A handful of NC counties (notably Mecklenburg) impose "
            "a separate prepared-food and beverage tax authorized "
            "by individual local-and-private-laws acts (e.g., the "
            "Mecklenburg County Convention Center Act 1.0% prepared-"
            "food tax); those are NOT general sales taxes and are "
            "NOT modeled by this module. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in North "
            "Carolina at the general 4.75% state rate (plus full "
            "local rate) per N.C.G.S. section 105-164.4(a)(6b), "
            "added by S.L. 2009-451 section 27A.4(a) effective "
            "January 1, 2010. The statute incorporates the SST-"
            "uniform 'specified digital products' definition: "
            "digital audio works, digital audiovisual works, "
            "digital books, digital magazines, digital newspapers, "
            "digital photographs, and digital greeting cards -- "
            "whether transferred with a permanent right of use or "
            "under a subscription / conditional access model. "
            "Prewritten ('canned') computer software delivered by "
            "any means is also taxable as tangible personal "
            "property under N.C.G.S. section 105-164.3 "
            "(definitions). EXCLUDED from the dominant taxable "
            "case: custom computer software and most true SaaS "
            "arrangements (where the customer takes neither "
            "possession nor control of the software) per NC DOR "
            "Sales and Use Tax Bulletin section 44-2 -- "
            "documented for the next maintainer; the engine "
            "encodes the dominant case as taxable. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "North Carolina at the 4.75% state rate per N.C.G.S. "
            "section 105-164.4(a)(1) (rate raised from 4.5% to "
            "4.75% effective October 15, 2011 by S.L. 2011-145 "
            "section 31A.1, the 2011 budget act; stable at 4.75% "
            "since). Local sales taxes (county Article 39 / 40 / "
            "42 / 43 / 46 layers) stack on top via the SST "
            "quarterly rate file, yielding combined rates "
            "typically in the 6.75%-7.50% range. Calculation only "
            "-- not legal or tax advice."
        ),
    ),
}


class NorthCarolina(SstStateModule):
    """North Carolina state module (tier 1, SST member).

    Inherits the generic SST rate / boundary parser from
    :class:`SstStateModule`. Overrides the default taxability
    matrix and the jurisdiction-type code mapping with NC-specific
    research grounded in N.C.G.S. Chapter 105, Article 5. North
    Carolina has no current sales-tax holidays (the 2002-enacted
    back-to-school holiday was repealed effective 2014 by S.L.
    2013-316), so the inherited empty-iterator ``holidays_for``
    default is used unchanged.

    The defining NC quirk is the ``groceries`` rule: state
    portion is exempt under N.C.G.S. section 105-164.13B but a
    uniform 2% local food county tax under section 105-468.1
    applies in every county. Encoded via
    ``rate_modifier=Decimal("2.000")`` on the groceries rule.
    """

    state_abbrev: str = "NC"
    state_name: str = "North Carolina"
    state_fips: str = "37"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Override the base-class defaults with NC-specific data.
    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated NC district-name table; fall back to placeholder."""
        from opensalestax.states.nc_names import district_name as _nc_district

        if authority_type == "district":
            friendly = _nc_district(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.north_carolina``
# registers North Carolina under "NC" in the state registry.
_PROTOCOL_CHECK: StateModule = NorthCarolina()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to
# the rate (mirrors INDIANA, IOWA, KANSAS, etc.). North Carolina's
# RateRow emits ``rate_pct=Decimal("4.750")`` from the SST file;
# the constant below is purely documentary so future readers can
# grep the codebase for the rate.
NORTH_CAROLINA_GENERAL_RATE_PCT: Decimal = Decimal("4.750")

# The uniform 2% local food county tax under N.C.G.S. section
# 105-468.1. Documentary constant; this is the value encoded as
# the ``rate_modifier`` on the groceries TaxabilityRule. The
# section 105-468.1 rate has been 2.00% since the section was
# enacted; tracking any legislative adjustment is a maintainer
# responsibility.
NORTH_CAROLINA_FOOD_COUNTY_TAX_PCT: Decimal = Decimal("2.000")

NORTH_CAROLINA = register(NorthCarolina())
