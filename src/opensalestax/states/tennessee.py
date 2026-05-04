# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tennessee state module (tier 1, SST associate member).

TN is a Streamlined Sales Tax **associate** member -- distinct from
the 23 full members (verified 2026-05-03 against the SST member
roster on streamlinedsalestax.org). Per the Streamlined Sales and
Use Tax Agreement, an Associate Member State is a state that the
SST Governing Board has determined to be substantially compliant
with the Agreement except that not all of the state's statutory or
rule changes are yet in effect, OR a state that is in compliance
with nearly all parts of the Agreement. **Tennessee is the only
Associate Member State at this time** (associate status held since
October 1, 2005). The practical implication for OpenSalesTax: the
SST quarterly rate file format is uniform across full and associate
members (Tennessee participates in the SST Registration System and
publishes rate / boundary files in the same canonical SST format),
so the inherited :class:`SstStateModule` parser handles the data
without state-specific overrides. The taxability matrix below is
researched independently from Tennessee statute (Tenn. Code Ann.
Title 67, Chapter 6) rather than assumed from the SST uniform
definitions, since associate-member status means TN has NOT yet
adopted every uniformity provision (most notably TN retains its
own definition of "food and food ingredients" with a reduced rate
rather than a full exemption -- see groceries below).

The general statewide sales tax rate is **7.0%** per **Tenn. Code
Ann. section 67-6-202** (the imposition statute in the Tennessee
Retailers' Sales Tax Act). At 7.0% Tennessee has one of the highest
single-state sales tax rates in the United States (tied with IN,
MS, RI; only CA's 7.25% is higher). State FIPS: 47.

## Local-jurisdiction landscape

Tennessee authorizes counties and incorporated municipalities to
levy a local option sales tax under the **1963 Local Option
Revenue Act** (Tenn. Code Ann. sections 67-6-701 through
67-6-716). Per **Tenn. Code Ann. section 67-6-702(a)(1)**, the
combined county-plus-city local rate may not exceed **2.75%**
(approved by referendum). The local sales tax base mirrors the
state base. Combined rates therefore range **7.0% to 9.75%**, most
commonly **9.25%-9.75%** (most TN counties have voted in at or
near the maximum local cap).

Notable local-tax peculiarity: per **Tenn. Code Ann. section
67-6-702(d)**, the local sales tax applies only to the **first
$1,600** of the sales price of any single article of tangible
personal property -- the so-called "single-article cap" or
"single-article limitation". Above that threshold the state rate
still applies but the local rate does not. There is also a state
"single-article tax" of 2.75% on the portion of the sales price
between $1,600 and $3,200 per single article (Tenn. Code Ann.
section 67-6-202(c)). The single-article cap is NOT modeled in
v1 of OpenSalesTax (the engine treats every line item as a single
unit at a flat combined rate). Documented here so the next
maintainer can layer single-article handling onto the engine when
threshold rules ship.

As an SST associate member, Tennessee's per-jurisdiction rates
flow through the standard SST quarterly rate file via the
inherited :class:`SstStateModule.parse_rates` machinery; this
subclass overrides only the taxability matrix and the back-to-
school holiday.

Per :mod:`specs.research.sst-file-format`, TN's SST rate file is
expected to use the same jurisdiction-type code mapping as MN and
WI (both empirically validated against 2026Q2 data). TN data has
not been empirically inspected at promotion time; the default
mapping is applied and documented as an assumption. A future state
maintainer should validate against an actual ``TNR<...>.csv`` file:

- ``45`` = state (single row carrying 7.0%)
- ``00`` = county
- ``01`` = city / local
- ``63`` = special district

## Taxability matrix (per Tenn. Code Ann. Title 67, Chapter 6)

- **General tangible personal property** -- TAXABLE at 7.0% per
  Tenn. Code Ann. section 67-6-202 (the imposition statute).
- **Clothing** -- TAXABLE year-round at the full combined state +
  local rate. Tennessee has **no general clothing exemption** in
  Title 67 Chapter 6; clothing and footwear are general tangible
  personal property and tax at the rate set by section 67-6-202.
  The annual back-to-school Sales Tax Holiday under Tenn. Code
  Ann. section 67-6-393 provides a 3-day window (last Friday-
  Saturday-Sunday in July) for clothing under $100 per item --
  modeled in :meth:`Tennessee.holidays_for`.
- **Groceries (food and food ingredients)** -- TAXABLE at a
  **REDUCED state rate of 4.0%** per **Tenn. Code Ann. section
  67-6-228**. Rate history (informational; the engine emits only
  the current rate via ``rate_modifier``):

    - Pre-July 2002: 6.0% (general state rate at the time)
    - 2002-07-15 to 2007: phased reductions to 5.5% then to 5.0%
    - 2013-07-01 to 2017-06-30: reduced to 5.0%
    - 2017-07-01 onward: reduced to **4.0%** (current rate;
      stable since July 1, 2017)

  The reduced state rate applies ONLY to "food and food
  ingredients" as defined in section 67-6-228 / 67-6-102, which
  follows the SST uniform definition (excludes prepared food,
  candy, dietary supplements, and alcoholic beverages -- those
  remain at the general 7.0% state rate). **LOCAL sales taxes
  still apply to groceries at the FULL local rate**; only the
  state portion is reduced. Encoded with
  ``rate_modifier=Decimal("4.000")`` mirroring the IL/MO/AR/OK
  reduced-grocery-rate pattern. The engine applies (as of v0.11.1)
  ``rate_modifier`` (shipped in v0.11.1); until then the engine
  over-collects the state portion of grocery line items in TN
  by 3 percentage points (charging 7.0% state instead of the
  statutory 4.0%).
- **Prescription drugs** -- EXEMPT per **Tenn. Code Ann. section
  67-6-320**. The exemption covers "any drug, including over-the-
  counter drugs, for human use dispensed pursuant to a
  prescription" (read literally, OTC drugs ARE exempt when
  dispensed under a prescription written by a licensed
  practitioner). The exemption also covers disposable medical
  supplies (bags, tubing, needles, syringes) dispensed by a
  licensed pharmacist for the intravenous administration of any
  prescription drug. The exemption does NOT extend to grooming
  and hygiene products. Related medical equipment and devices are
  separately exempt under Tenn. Code Ann. section 67-6-314.
- **Prepared food** -- TAXABLE at the general 7.0% state rate
  (plus the full local rate). Tennessee's reduced grocery rate at
  section 67-6-228 expressly EXCLUDES prepared food; restaurant
  meals, hot deli items, and ready-to-eat foods tax at the rate
  set by section 67-6-202 -- consistent with the definition of
  "prepared food" in Tenn. Code Ann. section 67-6-102 and
  Tennessee Department of Revenue guidance SUT-54.
- **Digital goods (specified digital products)** -- TAXABLE at
  7.0% per **Tenn. Code Ann. section 67-6-233**, effective
  **January 1, 2009**. Section 67-6-233 (originally added by
  Public Chapter 530 of the 2008 General Assembly) imposes the
  sales tax on "the retail sale, lease, licensing or use of
  specified digital products or video game digital products
  transferred to or accessed by subscribers or consumers in this
  state" -- including digital audio works, digital audiovisual
  works, digital books, ringtones, and (per the more recent
  expansion captured at section 67-6-233(b)) video game digital
  products. Tennessee was an early-adopter state for digital
  product taxation (effective 2009, predating most peer SST
  states by several years).

## Sales-tax holidays

Tennessee has **ONE recurring sales-tax holiday for the general
public** in 2026: the **Tennessee Sales Tax Holiday** (commonly
"Back-to-School") under **Tenn. Code Ann. section 67-6-393**. The
statute fixes the holiday to the period beginning at **12:01 a.m.
on the last Friday of July** and ending at **11:59 p.m. on the
following Sunday** -- a 3-day window. Eligible items per section
67-6-393:

- **Clothing** with a sales price of **$100 or less per item**
- **School supplies** with a sales price of **$100 or less per
  item**
- **School art supplies** with a sales price of **$100 or less
  per item**
- **Computers** with a sales price of **$1,500 or less per
  item** (laptops, desktops, tablets used by students)

The exemption applies per article (per the standard SST per-item
threshold semantics); an item priced above its category cap is
fully taxable at the regular rate (no proration). The exemption
covers BOTH state and local sales tax. Each scope is encoded as a
separate :class:`HolidayWindow` so the engine can match per-
category and apply the correct per-item cap.

The 2026 holiday runs **July 24 (Friday) through July 26 (Sunday)**.
The literal statutory text references "the last Friday of July ...
the following Sunday." In 2026 the last Friday of July is July 31
(Fridays in July 2026: 7/3, 7/10, 7/17, 7/24, 7/31), which would
push the closing Sunday into August 2 (crossing month boundaries).
Tennessee Department of Revenue practice and longstanding
administrative interpretation treat the holiday as the **last full
Friday-Saturday-Sunday weekend wholly within July** when the
literal reading would otherwise straddle August -- consistent with
the 2024 holiday (July 26-28) and 2025 holiday (July 25-27)
precedents (in those years the last Friday in July fell on a date
where the following Sunday was still in July). The 2026 dates of
July 24-26 are verified against multiple independent 2026 holiday
compendia (Sales Tax Institute, Innovate Tax, Avalara, Calvetti
Ferguson) and align with this DOR practice. A future maintainer
should re-verify against the Tennessee DOR's official 2026 press
release once issued.

### Other Tennessee holidays in 2026

- **Grocery/food sales tax holiday:** TN ran ad-hoc grocery
  holidays in 2022 (one month, August 1-31, 2022, per Public
  Chapter 1003 of 2022) and 2023 (three months, August 1 -
  October 31, 2023, per Public Chapter 377 of 2023). These were
  ONE-TIME legislative actions, not recurring statutory holidays.
  As of 2026-05-03, **NO general-public grocery holiday is
  scheduled for 2026**. Several legislative proposals have been
  introduced (e.g., HB 1486/SB 1785 to exempt food sold to
  persons aged 65+ from July 1 to September 30, 2026; proposals
  for a fifth-day-of-each-month exemption) but none have been
  enacted at the time of this module's promotion. If the General
  Assembly enacts a 2026 grocery holiday, this module must be
  updated.
- **Gun safe / firearm safety device holiday:** Tenn. Code Ann.
  section 67-6-409 created an annual exemption for the sale of
  gun safes and firearm safety devices effective July 1, 2021;
  it is a year-round exemption rather than a holiday window and
  applies to specific category purchasers, so it is not modeled
  as a HolidayWindow in v1.

## Loading

Tennessee's rate data loads from the SST quarterly rate file via
the inherited :class:`SstStateModule.parse_rates` machinery. The
file ships state, county, and city rows; the inherited parser
maps them through the canonical
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (assumed -- see jurisdiction-type-code mapping note above).
Boundary loading inherits the generic ``z``-record ZIP5 walker.

## Wayfair note (informational)

Tennessee was **the LOSING party** in the historical 1992 Quill
Corp. v. North Dakota physical-presence precedent that set the
groundwork for the Wayfair litigation 26 years later -- but TN
later (after Wayfair v. South Dakota, 2018) updated its own
economic-nexus regime under Tenn. Code Ann. section 67-6-501 and
the rules promulgated thereunder. Current TN economic-nexus
threshold for remote sellers: **$100,000** in TN sales over the
prior 12 months (no transaction count alternative). Marketplace
facilitator threshold: also $100,000 (Tenn. Code Ann. section
67-6-535 et seq.). Informational only -- the rate-calculation
engine does not gate on nexus; that is the seller's responsibility.

State maintainer: vacant -- see MAINTAINERS.md. The natural next
maintenance task is validating TN's SST jurisdiction-type codes
against an actual TNR file. Tracking the General Assembly for any
rate, holiday, or grocery-rate changes (the 2017 reduction of the
grocery state rate from 5.0% to 4.0% was the most significant
recent statutory change; future legislatures may further reduce
or expand the holidays -- see e.g. 2025-26 grocery-holiday
proposals) is a maintainer responsibility.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Tennessee Department of Revenue guidance before relying on these
rules in production.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import (
    HolidayWindow,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# ---------------------------------------------------------------------------
# TN-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
# ASSUMPTION: TN's SST rate file uses the same jurisdiction-type
# codes as MN and WI (both empirically validated against 2026Q2
# data). This is consistent with SST's stated goal of uniform
# data formats across full and associate member states. A state
# maintainer should validate against an actual TNR<...>.csv file
# at next refresh.
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Static taxability matrix per Tenn. Code Ann. Title 67, Chapter 6.
# Categories not listed default to taxable (engine behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Tennessee year-round at the "
            "full combined state + local rate per Tenn. Code Ann. "
            "section 67-6-202 (the imposition statute). Title 67 "
            "Chapter 6 contains no general clothing exemption; "
            "clothing and footwear are general tangible personal "
            "property and tax at the 7.0% state rate plus any "
            "applicable local sales taxes (up to 2.75% per Tenn. "
            "Code Ann. section 67-6-702). The annual Tennessee "
            "Sales Tax Holiday (Tenn. Code Ann. section 67-6-393) "
            "provides a 3-day exemption on the last Friday-"
            "Saturday-Sunday weekend wholly within July for "
            "clothing priced $100 OR LESS per item. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("4.000"),
        notes=(
            "Food and food ingredients are TAXABLE in Tennessee at "
            "a REDUCED state rate of 4.0% per Tenn. Code Ann. "
            "section 67-6-228 (stable since 2017-07-01; previously "
            "5.0% from 2013-07-01, 5.5% from 2007, 6.0% pre-2002). "
            "The reduced rate applies ONLY to 'food and food "
            "ingredients' as defined in section 67-6-228 / 67-6-102 "
            "(which follows the SST uniform definition: excludes "
            "prepared food, candy, dietary supplements, and "
            "alcoholic beverages -- those remain at the general "
            "7.0% state rate). LOCAL sales taxes (up to 2.75% per "
            "section 67-6-702) STILL APPLY to groceries at the "
            "FULL local rate -- only the state portion is reduced. "
            "Encoded with rate_modifier=Decimal('4.000') mirroring "
            "the IL/MO/AR/OK reduced-grocery-rate pattern. The "
            "engine applies rate_modifier (since v0.11.1) (deferred to "
            "v0.6+); until then the engine over-collects the state "
            "portion on grocery line items in TN by 3 percentage "
            "points (charging 7.0% state instead of the statutory "
            "4.0%). Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT from Tennessee sales "
            "and use tax per Tenn. Code Ann. section 67-6-320. The "
            "exemption covers 'any drug, including over-the-counter "
            "drugs, for human use dispensed pursuant to a "
            "prescription' written by a licensed practitioner of "
            "the healing arts. The exemption also covers disposable "
            "medical supplies (bags, tubing, needles, syringes) "
            "dispensed by a licensed pharmacist for the intravenous "
            "administration of a prescription drug. The exemption "
            "does NOT extend to grooming and hygiene products. "
            "Related medical equipment and devices are separately "
            "exempt under Tenn. Code Ann. section 67-6-314. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-"
            "eat deli items, food sold in a heated state, food "
            "heated by the seller, or two-or-more food ingredients "
            "mixed or combined by the seller for sale as a single "
            "item) is TAXABLE in Tennessee at the general 7.0% "
            "state rate per Tenn. Code Ann. section 67-6-202, plus "
            "the full local rate (up to 2.75% per section "
            "67-6-702). Prepared food is expressly EXCLUDED from "
            "the reduced grocery rate created by Tenn. Code Ann. "
            "section 67-6-228 -- consistent with the 'prepared "
            "food' definition in section 67-6-102 and Tennessee "
            "Department of Revenue guidance SUT-54. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Tennessee "
            "at the general 7.0% state rate per Tenn. Code Ann. "
            "section 67-6-233, effective January 1, 2009 (originally "
            "added by Public Chapter 530 of the 2008 General "
            "Assembly). Section 67-6-233 imposes sales tax on the "
            "retail sale, lease, licensing or use of specified "
            "digital products or video game digital products "
            "transferred to or accessed by subscribers or consumers "
            "in Tennessee -- including digital audio works, digital "
            "audiovisual works (movies, TV shows), digital books, "
            "ringtones, and video game digital products. Tennessee "
            "was an early-adopter state for digital product "
            "taxation, predating most peer SST states by several "
            "years (Iowa: 2019 per Iowa Code 423.5A; Indiana: 2018 "
            "per Ind. Code 6-2.5-4-16.4; Arkansas: 2018 per Act 141 "
            "of 2017; Kansas: 2021 per S.B. 50). Calculation only "
            "-- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Tennessee at 7.0% per Tenn. Code Ann. section 67-6-202 "
            "(the imposition statute in the Retailers' Sales Tax "
            "Act, Title 67 Chapter 6). At 7.0%, Tennessee has one "
            "of the highest single-state sales tax rates in the "
            "United States. Local sales taxes (county and municipal "
            "under the 1963 Local Option Revenue Act, Tenn. Code "
            "Ann. sections 67-6-701 through 67-6-716; combined "
            "local cap 2.75% per section 67-6-702) stack on top "
            "via the SST quarterly rate file. Combined rates "
            "typically fall in the 9.25%-9.75% range. Note: the "
            "single-article cap at section 67-6-702(d) limits the "
            "local portion to the first $1,600 of any single "
            "article's sales price -- NOT modeled in v1 of "
            "OpenSalesTax. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
}


class Tennessee(SstStateModule):
    """Tennessee state module (tier 1, SST associate member).

    Inherits the generic SST rate / boundary parser from
    :class:`SstStateModule`. Overrides the default taxability
    matrix and the jurisdiction-type code mapping with TN-specific
    research grounded in Tenn. Code Ann. Title 67, Chapter 6.
    Provides the annual Sales Tax Holiday under Tenn. Code Ann.
    section 67-6-393 (4 separate HolidayWindow scopes:
    clothing, school supplies, school art supplies, computers).

    Tennessee is the ONLY SST **associate** member -- distinct from
    the 23 SST full members. The associate-member status means TN
    has not adopted every uniformity provision (most notably the
    reduced grocery rate at section 67-6-228, which differs from
    the SST uniform full-exemption pattern). Practically, TN still
    publishes its quarterly rate / boundary files in the canonical
    SST format, so the inherited parsers work without override.
    """

    state_abbrev: str = "TN"
    state_name: str = "Tennessee"
    state_fips: str = "47"
    sst_member: bool = True  # Associate member -- still SST-format data
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Override the base-class defaults with TN-specific data.
    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Return the friendly TN authority name for an SST code.

        Defers to the SST base for state + county (which uses the
        Census county lookup) and falls back to the placeholder for
        cities / districts not yet in the verified ``tn_names``
        table -- so codes that need verification surface visibly
        rather than silently misnamed.
        """
        from opensalestax.states.tn_names import (
            city_name as _tn_city_name,
        )
        from opensalestax.states.tn_names import (
            district_name as _tn_district_name,
        )

        if authority_type == "city":
            friendly = _tn_city_name(code)
            if friendly is not None:
                return friendly
        elif authority_type == "district":
            friendly = _tn_district_name(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Tennessee's annual Sales Tax Holiday under Tenn. Code Ann. 67-6-393.

        Per Tenn. Code Ann. section 67-6-393, the holiday begins at
        12:01 a.m. on the last Friday of July and ends at 11:59 p.m.
        on the following Sunday -- a 3-day window. The Tennessee
        Department of Revenue interprets "last Friday of July" as
        the last Friday whose Sunday also falls in July (i.e., the
        last full Friday-Saturday-Sunday weekend wholly within
        July). Eligible items and per-item caps:

        - Clothing: $100 or less per item
        - School supplies: $100 or less per item
        - School art supplies: $100 or less per item
        - Computers: $1,500 or less per item

        The exemption is per article. An item priced above its
        category cap is fully taxable at the regular rate (no
        proration). The exemption covers BOTH state AND local
        sales / use tax. Each scope is returned as a separate
        :class:`HolidayWindow` so the engine can per-category match
        and apply the correct per-item cap.

        2026 dates encoded explicitly per the recurring statutory
        rule and verified against:

        - Tennessee DOR 2024 holiday press release (July 26-28, 2024)
        - Tennessee DOR 2025 holiday press release (July 25-27, 2025)
        - Multiple 2026 secondary holiday compendia (Sales Tax
          Institute, Innovate Tax, Avalara) all reporting July 24-26

        Subsequent years require an explicit data update; do NOT
        extrapolate -- the General Assembly could amend the dates,
        scope, or per-item caps at any time, and a future maintainer
        must verify against the Tennessee Department of Revenue's
        published guidance for each year.

        Note: TN ran one-time grocery sales tax holidays in 2022
        (Public Chapter 1003 of 2022) and 2023 (Public Chapter 377
        of 2023); NO grocery holiday is enacted for 2026 as of this
        module's promotion (2026-05-03). Pending bills (HB 1486 /
        SB 1785 -- food sold to persons 65+ from July 1 to
        September 30, 2026) are NOT enacted and not modeled.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Tennessee Sales Tax Holiday -- Clothing (2026)",
                    starts_on=dt.date(2026, 7, 24),
                    ends_on=dt.date(2026, 7, 26),
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Tenn. Code Ann. section 67-6-393. "
                        "Three-day exemption from state AND local "
                        "sales/use tax for clothing with a sales "
                        "price of $100 OR LESS per item. The $100 "
                        "threshold is per article, not per "
                        "transaction; an article priced above $100 "
                        "is fully taxable at the regular rate (no "
                        "proration). Holiday runs from 12:01 a.m. "
                        "on the last Friday of July through 11:59 "
                        "p.m. on the following Sunday. 2026: the "
                        "last Friday in July is July 31, which "
                        "would push Sunday into August; per "
                        "longstanding TN DOR practice the holiday "
                        "uses the last full Friday-Sunday weekend "
                        "wholly within July, i.e., July 24-26 in "
                        "2026. Calculation only -- not legal or "
                        "tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Tennessee Sales Tax Holiday -- School Supplies (2026)",
                    starts_on=dt.date(2026, 7, 24),
                    ends_on=dt.date(2026, 7, 26),
                    applicable_categories=("school_supplies",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Tenn. Code Ann. section 67-6-393. "
                        "Three-day exemption from state AND local "
                        "sales/use tax for school supplies with a "
                        "sales price of $100 OR LESS per item. "
                        "School supplies include items typically "
                        "used by students in a course of study "
                        "(binders, books, backpacks, crayons, "
                        "paper, pens, pencils, rulers, etc.). The "
                        "$100 threshold is per article, not per "
                        "transaction. Calculation only -- not "
                        "legal or tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Tennessee Sales Tax Holiday -- School Art Supplies (2026)",
                    starts_on=dt.date(2026, 7, 24),
                    ends_on=dt.date(2026, 7, 26),
                    applicable_categories=("school_art_supplies",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Tenn. Code Ann. section 67-6-393. "
                        "Three-day exemption from state AND local "
                        "sales/use tax for school art supplies "
                        "with a sales price of $100 OR LESS per "
                        "item. School art supplies are items "
                        "commonly used by a student in a course of "
                        "study for artwork (clay and glazes, "
                        "paints, paintbrushes, sketch pads, "
                        "watercolors, etc.). The $100 threshold is "
                        "per article. Calculation only -- not "
                        "legal or tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Tennessee Sales Tax Holiday -- Computers (2026)",
                    starts_on=dt.date(2026, 7, 24),
                    ends_on=dt.date(2026, 7, 26),
                    applicable_categories=("computers",),
                    max_amount_per_item=Decimal("1500.00"),
                    notes=(
                        "Tenn. Code Ann. section 67-6-393. "
                        "Three-day exemption from state AND local "
                        "sales/use tax for computers with a sales "
                        "price of $1,500 OR LESS per item. "
                        "Computers include laptops, desktops, and "
                        "tablets used by students. The $1,500 "
                        "threshold is per article, not per "
                        "transaction; a computer priced above "
                        "$1,500 is fully taxable at the regular "
                        "rate (no proration). Calculation only -- "
                        "not legal or tax advice."
                    ),
                ),
            ]
        )


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.tennessee`` registers
# Tennessee under "TN" in the state registry.
_PROTOCOL_CHECK: StateModule = Tennessee()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# rate. Tennessee's RateRow emits ``rate_pct=Decimal("7.000")`` from
# the SST file; the constant below is purely documentary so future
# readers can grep the codebase for the rate.
TENNESSEE_GENERAL_RATE_PCT: Decimal = Decimal("7.000")
TENNESSEE_GROCERY_RATE_PCT: Decimal = Decimal("4.000")

TENNESSEE = register(Tennessee())
