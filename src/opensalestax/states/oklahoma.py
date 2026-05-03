# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Oklahoma state module (tier 1, SST member).

OK is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The general statewide sales tax rate
is **4.5%** per **68 O.S. section 1354** (the imposition statute
in the Oklahoma Sales Tax Code, Title 68 Chapter 25). State
FIPS: 40.

## Local-jurisdiction landscape

Oklahoma authorizes counties (under 68 O.S. sections 1370 et
seq.) and incorporated municipalities (under 68 O.S. sections
2701 et seq.) to impose local sales taxes by voter approval.
Combined rates commonly fall in the **6.0%-11.5%** range, among
the highest combined ranges in the country -- a typical Oklahoma
city + county stack adds **+1.5% to +5.5%** on top of the 4.5%
state rate. As an SST member, Oklahoma's per-jurisdiction rates
flow through the standard SST quarterly rate file; the inherited
:class:`SstStateModule` parser handles them without state-specific
overrides.

Per :mod:`specs.research.sst-file-format`, OK's SST rate file is
expected to use the same jurisdiction-type code mapping as MN
and WI (both empirically validated against 2026Q2 data). OK data
has not been empirically inspected at promotion time; the default
mapping is applied and documented as an assumption. A future
state maintainer should validate against an actual
``OKR<...>.csv`` file:

- ``45`` = state (single row carrying 4.5%)
- ``00`` = county
- ``01`` = city / local
- ``63`` = special district

## Taxability matrix (per 68 O.S. Title 68, Chapter 25)

- **General tangible personal property** -- TAXABLE at 4.5% per
  68 O.S. section 1354 (the imposition statute).
- **Clothing** -- TAXABLE year-round at the full combined rate.
  Oklahoma has **no general clothing exemption** in 68 O.S.
  Chapter 25; clothing and footwear are general tangible personal
  property and tax at the rate set by section 1354. The annual
  August Sales Tax Holiday under 68 O.S. section 1357.10 (the
  state-side exemption) and 68 O.S. section 1377 (the parallel
  county / municipal-side exemption) provides a 3-day window for
  clothing and footwear under $100 per item -- modeled in
  :meth:`Oklahoma.holidays_for`.
- **Groceries (food and food ingredients)** -- TAXABLE but at
  the **0.000% reduced state rate effective August 29, 2024**.
  House Bill 1955 (2024 session; signed February 27, 2024 by
  Governor Stitt; effective August 29, 2024) amended 68 O.S.
  section 1357 to exempt the sale of "food and food ingredients"
  from the state portion of sales tax. **Local sales taxes
  (county, city) STILL APPLY at the full local rate** -- the bill
  zeroed only the state portion. The Oklahoma definition of
  "food and food ingredients" -- per HB 1955 / 68 O.S. section
  1352 definitions as amended -- **expressly INCLUDES bottled
  water, candy, and soft drinks** (broader than the standard SST
  uniform definition that excludes those three). The exemption
  EXCLUDES prepared food, alcoholic beverages, dietary
  supplements, tobacco, and marijuana products -- those remain
  taxable at the general 4.5% state rate (plus full local rate).
  Encoded with ``rate_modifier=Decimal("0.000")`` to mark the
  special state rate (mirrors the AR Grocery Tax Relief Act
  pattern at section 26-52-317 and the KS phase-down pattern at
  K.S.A. 79-3603(p)). The engine applies (as of v0.11.1)
  ``rate_modifier``; as of v0.11.1, the engine
  over-collects the 4.5% state portion on grocery line items in
  Oklahoma.
- **Prescription drugs** -- EXEMPT per **68 O.S. section 1357**
  (the general-exemptions section). The exemption covers sales
  of drugs sold pursuant to a prescription written for the
  treatment of human beings by a person licensed to prescribe
  the drugs, plus sales of insulin and medical oxygen. Related
  exemptions for medical appliances, medical devices, and other
  medical equipment (corrective eyeglasses, contact lenses,
  hearing aids) when prescribed and reimbursed under Medicare /
  Medicaid are codified separately at **68 O.S. section
  1357.6**. Over-the-counter drugs sold without a prescription
  are NOT covered and tax at the general 4.5% rate even when
  prescribed.
- **Prepared food** -- TAXABLE at the general 4.5% state rate
  (plus the full local rate). Oklahoma's grocery exemption
  expressly EXCLUDES prepared food (as defined in 68 O.S.
  section 1352 / Oklahoma Tax Commission rules at OAC 710:65
  Subchapter 13). Prepared food is food sold in a heated state,
  food heated by the seller, or two-or-more food ingredients
  mixed or combined by the seller for sale as a single item;
  restaurant meals, hot deli items, and ready-to-eat foods tax
  at the rate set by 68 O.S. section 1354.
- **Digital goods (specified digital products)** -- **NOT
  TAXABLE** in Oklahoma. This is a notable peer-state difference:
  unlike Iowa (Iowa Code 423.5A), Indiana (Ind. Code
  6-2.5-4-16.4), Arkansas (Act 141 of 2017), Kansas (2021 S.B.
  50), and many other SST members, Oklahoma has NOT enacted a
  sales-tax expansion to specified digital products. Per
  **Oklahoma Tax Commission letter rulings** and **Oklahoma
  Administrative Code section 710:65-19-156**, sales of digital
  products delivered electronically -- including music, video,
  ringtones, e-books, prewritten software downloads, software-
  maintenance contracts delivered electronically, video-game
  console points cards, and online membership cards -- are NOT
  subject to Oklahoma sales and use tax. The underlying rationale
  is that 68 O.S. section 1354 only reaches "tangible personal
  property" (and certain enumerated services), and Oklahoma has
  not adopted the SST "specified digital products" definitions
  into statute. Prewritten ("canned") computer software
  delivered on a tangible storage medium IS taxable as TPP; the
  same software delivered electronically is NOT.

## Sales-tax holidays

Oklahoma has **ONE recurring sales-tax holiday**: the **Oklahoma
Annual Sales Tax Holiday** (commonly "Back-to-School") under 68
O.S. section 1357.10 (state-side) and 68 O.S. section 1377
(parallel county/municipal-side). The statute fixes the holiday
to the **first Friday in August at 12:01 a.m. through midnight
on the following Sunday** -- a 3-day window. Eligible items:
**clothing and footwear with a sales price of less than $100 per
item**. The exemption is per article, not per transaction; an
article priced at $100 or more is fully taxable at the regular
rate (no proration).

EXCLUDED from the holiday: clothing accessories (jewelry,
handbags, briefcases, luggage, umbrellas, wallets, watches, and
similar items); special clothing or footwear primarily designed
for athletic activity or protective use that is not normally
worn except when used for athletic activity or protective use;
and rentals of clothing or footwear. Notably the Oklahoma
holiday covers ONLY clothing and footwear -- NOT school
supplies, NOT school art supplies, NOT instructional materials,
NOT computers / electronics (contrast with AR's 26-52-444 which
covers all of these in addition to clothing).

The 2026 holiday runs **August 7 (Friday) through August 9
(Sunday)**, per the Oklahoma Tax Commission Sales Tax Holiday
publication (retrieved 2026-05-03) and the recurring statutory
rule (first Friday in August 2026 is August 7).

## Loading

Oklahoma's rate data loads from the SST quarterly rate file via
the inherited :class:`SstStateModule.parse_rates` machinery. The
file ships state, county, city, and special-district rows; the
inherited parser maps them through the canonical
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (assumed -- see jurisdiction-type-code mapping note
above). Boundary loading inherits the generic ``z``-record ZIP5
walker.

## Marketplace / nexus note

OK's marketplace facilitator economic-nexus threshold is
dramatically lower than its remote-seller threshold: marketplace
facilitators must collect when they make or facilitate **$10,000
or more** in Oklahoma sales (or comply with notice-and-reporting
requirements), versus the **$100,000** threshold for remote
sellers (68 O.S. section 1391 et seq.). This is informational
only and does NOT affect rate calculation; OpenSalesTax v1
calculates rates regardless of whether the seller has nexus.
Documented here so the next maintainer is aware.

State maintainer: vacant -- see MAINTAINERS.md. The natural
next maintenance task is validating OK's SST jurisdiction-type
codes against an actual OKR file. Tracking the legislative
session for any rate or holiday changes (the August 2024
elimination of the state-portion grocery tax was the most
significant statutory change in years; future legislatures may
expand or contract the holiday list -- see e.g. 2025-26 Senate
proposals to expand the holiday's scope) is a maintainer
responsibility.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Oklahoma Tax Commission guidance before relying on these rules
in production.
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
# OK-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
# ASSUMPTION: OK's SST rate file uses the same jurisdiction-type
# codes as MN and WI (both empirically validated against 2026Q2
# data). This is consistent with SST's stated goal of uniform
# data formats across member states. A state maintainer should
# validate against an actual OKR<...>.csv file at next refresh.
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Static taxability matrix per 68 O.S. Title 68, Chapter 25.
# Categories not listed default to taxable (engine behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Oklahoma year-round at the full "
            "combined state + local rate per 68 O.S. section 1354. "
            "Title 68 Chapter 25 contains no general clothing "
            "exemption; clothing and footwear are general tangible "
            "personal property and tax at the 4.5% state rate plus "
            "any applicable local sales taxes. The annual Oklahoma "
            "Sales Tax Holiday (68 O.S. section 1357.10 state-side "
            "and 68 O.S. section 1377 county/municipal-side) provides "
            "a 3-day exemption on the first Friday-Saturday-Sunday "
            "in August for clothing and footwear priced LESS THAN "
            "$100 per item. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("0.000"),
        notes=(
            "Food and food ingredients are taxable at a REDUCED "
            "0.000% state rate effective August 29, 2024 per House "
            "Bill 1955 (2024 session; signed by Governor Stitt on "
            "February 27, 2024) which amended 68 O.S. section 1357 "
            "(general exemptions) and the food/food-ingredients "
            "definitions in 68 O.S. section 1352. LOCAL sales taxes "
            "(county, city) STILL APPLY at the full local rate -- "
            "only the state portion was zeroed. Oklahoma's "
            "definition of 'food and food ingredients' EXPRESSLY "
            "INCLUDES bottled water, candy, and soft drinks (broader "
            "than the standard SST uniform definition that excludes "
            "those three). Items NOT in the definition -- prepared "
            "food, alcoholic beverages, dietary supplements, tobacco, "
            "and marijuana products -- remain at the general 4.5% "
            "state rate plus full local rate. The rate_modifier is "
            "stored but the engine applies (as of v0.11.1) it (deferred "
            "to v0.6+); until then the engine over-collects the 4.5% "
            "state portion on grocery line items in Oklahoma. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT from Oklahoma sales and "
            "use tax per 68 O.S. section 1357 (the general "
            "exemptions section). The exemption covers sales of "
            "drugs sold pursuant to a prescription written for the "
            "treatment of human beings by a person licensed to "
            "prescribe the drugs, plus sales of insulin and medical "
            "oxygen. Related exemptions for medical appliances, "
            "medical devices, and other medical equipment "
            "(corrective eyeglasses, contact lenses, hearing aids) "
            "when prescribed and reimbursed under Medicare or "
            "Medicaid are codified at 68 O.S. section 1357.6. "
            "Over-the-counter drugs sold without a prescription are "
            "NOT covered by the exemption and tax at the general "
            "4.5% rate even when prescribed. Calculation only -- "
            "not legal or tax advice."
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
            "item) is TAXABLE in Oklahoma at the general 4.5% state "
            "rate per 68 O.S. section 1354, plus the full local "
            "rate. Prepared food is expressly EXCLUDED from the "
            "food/food-ingredients exemption created by HB 1955 "
            "(2024) at 68 O.S. section 1357 -- consistent with the "
            "definitions at 68 O.S. section 1352 and Oklahoma Tax "
            "Commission rules at OAC 710:65 Subchapter 13. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=False,
        notes=(
            "Specified digital products delivered electronically "
            "(music, video, ringtones, e-books, prewritten software "
            "downloads, software-maintenance contracts delivered "
            "electronically, video-game console points cards, "
            "online membership cards, etc.) are NOT taxable in "
            "Oklahoma. Notable peer-state difference: unlike Iowa "
            "(Iowa Code 423.5A), Indiana (Ind. Code 6-2.5-4-16.4), "
            "Arkansas (Act 141 of 2017), and Kansas (2021 S.B. 50), "
            "Oklahoma has NOT enacted a sales-tax expansion to "
            "specified digital products. The basis is Oklahoma Tax "
            "Commission letter rulings and Oklahoma Administrative "
            "Code section 710:65-19-156: 68 O.S. section 1354 "
            "reaches only 'tangible personal property' (and certain "
            "enumerated services), and Oklahoma has not adopted the "
            "SST 'specified digital products' definitions into "
            "statute. Prewritten ('canned') computer software "
            "delivered on a tangible storage medium IS taxable as "
            "TPP; the same software delivered electronically is "
            "NOT. Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Oklahoma at the 4.5% state rate per 68 O.S. section "
            "1354 (the imposition statute in the Oklahoma Sales "
            "Tax Code, Title 68 Chapter 25). Local sales taxes "
            "(county under 68 O.S. sections 1370 et seq.; "
            "municipal under 68 O.S. sections 2701 et seq.) stack "
            "on top via the SST quarterly rate file. Combined "
            "rates commonly fall in the 6.0%-11.5% range -- among "
            "the highest combined ranges in the United States. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}


class Oklahoma(SstStateModule):
    """Oklahoma state module (tier 1, SST member).

    Inherits the generic SST rate / boundary parser from
    :class:`SstStateModule`. Overrides the default taxability
    matrix and the jurisdiction-type code mapping with OK-specific
    research grounded in 68 O.S. Title 68 Chapter 25. Provides the
    annual August Sales Tax Holiday under 68 O.S. section 1357.10.
    """

    state_abbrev: str = "OK"
    state_name: str = "Oklahoma"
    state_fips: str = "40"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Override the base-class defaults with OK-specific data.
    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Oklahoma's annual Sales Tax Holiday under 68 O.S. section 1357.10.

        Per 68 O.S. section 1357.10 (state-side exemption) and the
        parallel 68 O.S. section 1377 (county/municipal-side
        exemption), the holiday begins at 12:01 a.m. on the first
        Friday in August and ends at midnight on the following
        Sunday -- a 3-day window. Eligible items: clothing and
        footwear with a sales price of LESS THAN $100 per item.
        The exemption is per article, not per transaction; an
        article priced at $100 or more is fully taxable at the
        regular rate (no proration).

        EXCLUDED from the holiday: clothing accessories (jewelry,
        handbags, briefcases, luggage, umbrellas, wallets, watches,
        and similar items); special clothing or footwear primarily
        designed for athletic activity or protective use that is
        not normally worn except when used for athletic activity
        or protective use; and rentals of clothing or footwear.
        Unlike Arkansas's 26-52-444, Oklahoma's holiday covers
        ONLY clothing and footwear -- NOT school supplies, NOT
        school art supplies, NOT instructional materials, NOT
        computers / electronics.

        2026 dates encoded explicitly per the recurring statutory
        rule (first Friday in August 2026 is August 7) and
        verified against the Oklahoma Tax Commission Sales Tax
        Holiday publication (retrieved 2026-05-03). Subsequent
        years require an explicit data update; do NOT extrapolate
        -- the legislature could amend the dates, scope, or per-
        item cap at any time, and a future maintainer must verify
        against the OK Tax Commission's published guidance for
        each year.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Oklahoma Annual Sales Tax Holiday (2026)",
                    starts_on=dt.date(2026, 8, 7),
                    ends_on=dt.date(2026, 8, 9),
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "68 O.S. section 1357.10 (state-side "
                        "exemption) and 68 O.S. section 1377 "
                        "(parallel county/municipal-side exemption). "
                        "Three-day exemption from state AND local "
                        "sales/use tax for clothing and footwear "
                        "priced LESS THAN $100 per item. The $100 "
                        "threshold is per article, not per "
                        "transaction; an article priced at $100 or "
                        "more is fully taxable at the regular rate "
                        "(no proration). EXCLUDED from the holiday: "
                        "clothing accessories (jewelry, handbags, "
                        "briefcases, luggage, umbrellas, wallets, "
                        "watches, and similar items); special "
                        "clothing or footwear primarily designed "
                        "for athletic activity or protective use "
                        "that is not normally worn except when "
                        "used for athletic activity or protective "
                        "use; and rentals of clothing or footwear. "
                        "Unlike Arkansas's 26-52-444, Oklahoma's "
                        "holiday covers ONLY clothing and footwear "
                        "-- NOT school supplies, school art "
                        "supplies, instructional materials, or "
                        "electronics. The holiday runs from 12:01 "
                        "a.m. on the first Friday in August through "
                        "midnight on the following Sunday. 2026: "
                        "first Friday in August is August 7; "
                        "holiday runs through Sunday August 9. "
                        "Calculation only -- not legal or tax "
                        "advice."
                    ),
                ),
            ]
        )


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.oklahoma`` registers
# Oklahoma under "OK" in the state registry.
_PROTOCOL_CHECK: StateModule = Oklahoma()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# rate. Oklahoma's RateRow emits ``rate_pct=Decimal("4.500")`` from
# the SST file; the constant below is purely documentary so future
# readers can grep the codebase for the rate.
OKLAHOMA_GENERAL_RATE_PCT: Decimal = Decimal("4.500")

OKLAHOMA = register(Oklahoma())
