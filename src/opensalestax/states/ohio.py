# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Ohio state module (tier 1, SST member).

OH is a Streamlined Sales Tax full member (verified 2026-05-03
against the SST member roster on streamlinedsalestax.org). The
statewide general sales/use tax rate is **5.75%** per
**Ohio Rev. Code section 5739.02(A)(1)**, which sets the rate at
"five and three-fourths per cent" for retail sales of tangible
personal property and selected services.

## RATE COMPOSITION + LOCAL JURISDICTIONS

The 5.75% state rate is the floor; counties and (in limited
circumstances) regional transit authorities layer additional
sales/use tax on top under **Ohio Rev. Code Chapter 5739** (the
permissive county sales tax under **section 5739.021**, the
permissive transit-authority sales tax under **section 5739.023**,
and various special-county provisions). Combined county rates
typically fall in the **6.5%-8.0%** range, with the heaviest
combined rates clustered in the Cuyahoga County (Cleveland) area
where the RTA transit-authority levy stacks on top of the county
rate.

Ohio's 88 counties + a small number of regional transit
authorities produce a per-county combined rate that the Ohio
Department of Taxation publishes as a quarterly rate chart and
that the SST quarterly rate file ships as per-jurisdiction rows.
The inherited :class:`SstStateModule` parser handles the actual
per-jurisdiction loading; this subclass only adds the
Ohio-specific taxability matrix and the August sales-tax holiday.

Per :mod:`specs.research.sst-file-format`, this module assumes the
canonical SST jurisdiction-type code mapping (``45`` = state,
``00`` = county, ``01`` = city, ``63`` = district), which the MN
and WI quarterly files validate empirically. Validating against
an actual ``OHR<...>.csv`` rate-file capture is a natural
follow-up for the next maintainer; if the codes differ, override
``jurisdiction_types`` on this subclass at that time.

## TAXABILITY MATRIX (per Ohio Rev. Code Chapter 5739)

- **General tangible personal property** -- TAXABLE at 5.75% per
  **Ohio Rev. Code section 5739.02(A)(1)** (the imposition
  statute and rate; "five and three-fourths per cent").
- **Clothing** -- TAXABLE year-round at 5.75%. Ohio has **no
  general clothing exemption** in chapter 5739; clothing and
  footwear are general tangible personal property and tax at the
  rate set by section 5739.02(A)(1). The annual three-day
  back-to-school sales-tax holiday under
  **section 5739.02(B)(55)** (first Friday-Saturday-Sunday of
  August) provides a temporary exemption for clothing priced
  $75 or less per item -- modeled in :meth:`Ohio.holidays_for`.
- **Groceries (food for off-premises consumption)** -- EXEMPT
  per **Ohio Rev. Code section 5739.02(B)(2)**, which exempts
  "sales of food for human consumption off the premises where
  sold." The exemption tracks the Streamlined definition of
  "food and food ingredients" -- candy, soft drinks, dietary
  supplements, alcoholic beverages, and prepared food are NOT
  included in the exemption (those tax at the general 5.75%
  rate). Food consumed ON the premises where sold (restaurants,
  cafeterias, etc.) is TAXABLE under the carve-out language of
  the same subsection.
- **Prescription drugs** -- EXEMPT per **Ohio Rev. Code section
  5739.02(B)(18)**, which exempts "sales of drugs for a human
  being that may be dispensed only pursuant to a prescription."
  Over-the-counter (non-prescription) drugs are NOT covered by
  this exemption and remain taxable at the general 5.75% rate.
- **Prepared food** -- TAXABLE at 5.75%. Ohio's grocery
  exemption in section 5739.02(B)(2) applies only to food for
  consumption "off the premises where sold"; restaurant meals,
  hot deli items, and food consumed on-premises are excluded
  from the exemption and tax at the general rate. Vending-
  machine sales and certain catering / drive-through
  configurations are addressed by Ohio Department of Taxation
  Information Release ST 2004-01 and successor releases.
- **Specified digital products** -- TAXABLE at 5.75%. Ohio Rev.
  Code section 5739.01(B)(12) defines "sale" to include "all
  transactions by which a specified digital product is provided
  for permanent use or less than permanent use, regardless of
  whether continued payment is required" (i.e., both perpetual-
  license downloads and subscription / streaming access are
  taxable). "Specified digital product" itself is defined at
  **section 5739.01(OOO)** to mean an electronically transferred
  digital audio-visual work, digital audio work, or digital
  book. The Ohio Department of Taxation also taxes electronic
  information services and certain SaaS configurations under
  the broader chapter 5739 service definitions; integrators
  shipping non-enumerated digital services to Ohio should
  consult the Department's published guidance for borderline
  cases.

## SALES TAX HOLIDAY -- 2026 AND HISTORY

Ohio law provides for **TWO statutory frameworks** for sales-tax
holidays:

### Traditional 3-day back-to-school holiday (Ohio Rev. Code
### section 5739.02(B)(55))

The longstanding statutory holiday under **section 5739.02(B)(55)**
runs **the first Friday of August and the following Saturday and
Sunday** (a 3-day window). Eligible items:

- **Clothing priced $75 or less per item**
- **School supplies priced $20 or less per item**
- **School instructional materials priced $20 or less per item**

The per-item caps are absolute thresholds: an article priced over
the cap is fully taxable at the regular rate (no proration of the
first $75 / $20). The holiday applies to the 5.75% state rate AND
to all county and transit-authority local taxes layered on top.

### Expanded "Tax Holiday Fund" framework (Ohio Rev. Code
### section 5739.41 / H.B. 33 of 135th General Assembly, 2023)

H.B. 33 of the 135th General Assembly (2023) created a separate
expanded-holiday framework codified at **Ohio Rev. Code section
5739.41**. When the Expanded Sales Tax Holiday Fund holds enough
surplus state revenue, the Tax Commissioner designates a holiday
of at least three days, longer when the fund can cover the
forgone revenue (section 131.44(B)(2)), covering **most tangible
personal property priced $500 or less per item** (section
5739.02(B)(64)). Section 5739.01(UUU) excludes watercraft and
outboard motors required to be titled, motor vehicles, alcoholic
beverages, tobacco, vapor products, and items containing
marijuana.

### Recent-year history

- **2024**: Expanded holiday declared. Tuesday July 30, 2024
  through Thursday August 8, 2024 -- a 10-day window covering
  most TPP priced $500 or less per item. Authority: section
  5739.41 (HB 33 of 2023).
- **2025**: Expanded holiday declared. Approximately two-week
  window (early August), same $500-per-item scope. Authority:
  section 5739.41.
- **2026**: **Expanded holiday CANCELLED**. **H.B. 186 of the
  136th General Assembly** (signed by Governor DeWine on
  **December 19, 2025** as part of a broader property-tax-
  reform package) repurposed the Expanded Sales Tax Holiday
  Fund to offset reduced school district property tax
  collections, prohibiting any expanded holiday in August 2026
  and delaying certification of fund revenue for a 2027
  expanded holiday. Ohio reverts to the **traditional 3-day
  back-to-school holiday** under section 5739.02(B)(55) for
  2026.
- **2026 dates** (per Governor DeWine's May 1, 2026
  announcement and the Ohio Department of Taxation):
  **Friday August 7, 2026 (12:00 a.m.) through Sunday
  August 9, 2026 (11:59 p.m.)** -- the first Friday of
  August 2026 is August 7, and the following Saturday-Sunday
  fall on August 8-9.
- **2027**: **Expanded holiday, fifteen days**, Sunday August 1
  through Sunday August 15, 2027. Section 513.10(D) of H.B. 96
  of the 136th General Assembly, as amended by Section 12 of
  **H.B. 479** (signed June 24, 2026; the governor's line-item
  veto struck only Section 259.20), sets those dates
  notwithstanding sections 5739.41 and 131.44(B)(2). Section
  5739.02(B)(55) suspends the traditional 3-day holiday in any
  year a section 5739.41 holiday is held.

:meth:`Ohio.holidays_for` encodes 2026 and 2027. Later years need
a fresh check: the traditional 3-day holiday applies unless a
section 5739.41 holiday is held that year, and the two are
mutually exclusive.

The 2026 holiday's per-category caps (clothing $75; school
supplies and school instructional materials $20) are modeled as
two windows over the same dates, one per cap. The 2027 expanded
holiday covers every item of tangible personal property priced
$500 or less except the section 5739.01(UUU) exclusions.
:class:`HolidayWindow` cannot express an exclusion list, so the
2027 window lists the tangible categories it covers; digital
goods are left out because specified digital products are not
tangible personal property. A caller that files an excluded item
(alcohol, tobacco, a motor vehicle) under ``general`` must not
apply the window to it.

## LOADING

Ohio's per-county and per-transit-authority rate data loads from
the SST quarterly rate file via the inherited
:class:`SstStateModule.parse_rates` machinery. Per the empirical
default in :data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`,
the assumed code mapping (45 state / 00 county / 01 city / 63
district) is the MN/WI canonical default until validated against
an empirical OH rate-file capture.

State maintainer: vacant -- see MAINTAINERS.md. Ohio's per-county
rates and any annual updates to the sales-tax holiday framework
(particularly the section 5739.41 expanded-holiday fund
certification each spring) are the maintainer's ongoing
responsibility.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current Ohio
Department of Taxation guidance before relying on these rules in
production.
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

# Ohio taxability matrix per Ohio Rev. Code Chapter 5739.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Ohio year-round at the 5.75% state "
            "rate (plus county and transit-authority local rates). "
            "Ohio Rev. Code chapter 5739 contains no general clothing "
            "exemption; clothing and footwear are general tangible "
            "personal property and tax at the rate set by Ohio Rev. "
            "Code section 5739.02(A)(1). The annual three-day "
            "back-to-school sales-tax holiday under Ohio Rev. Code "
            "section 5739.02(B)(55) (first Friday, Saturday, and "
            "Sunday of August) provides a 3-day exemption for "
            "clothing priced $75 or less per item. The expanded "
            "section 5739.41 holiday framework (HB 33 of 2023) was "
            "exercised in 2024 and 2025 but was cancelled for 2026 "
            "by HB 186 of the 136th General Assembly (signed "
            "December 19, 2025); 2026 reverts to the traditional "
            "3-day back-to-school holiday. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food for human consumption OFF the premises where sold "
            "is EXEMPT in Ohio per Ohio Rev. Code section "
            "5739.02(B)(2) ('sales of food for human consumption off "
            "the premises where sold'). The exemption tracks the "
            "Streamlined Sales Tax Project's uniform definition of "
            "'food and food ingredients' and excludes candy, soft "
            "drinks, dietary supplements, alcoholic beverages, and "
            "prepared food (those remain taxable at the general "
            "5.75% state rate plus locals). Food consumed ON the "
            "premises where sold (restaurants, cafeterias, etc.) is "
            "TAXABLE -- see the prepared_food rule. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Ohio per Ohio Rev. "
            "Code section 5739.02(B)(18), which exempts 'sales of "
            "drugs for a human being that may be dispensed only "
            "pursuant to a prescription.' Related medical-supply "
            "exemptions (insulin, hypodermic devices, prosthetic "
            "devices, oxygen, durable medical equipment when "
            "prescribed) appear in adjacent subsections of section "
            "5739.02(B). Over-the-counter (non-prescription) drugs "
            "are NOT covered by the exemption and remain taxable at "
            "the general 5.75% rate plus locals. Calculation only -- "
            "not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, food "
            "consumed on the premises where sold, ready-to-eat "
            "foods) is TAXABLE in Ohio at the general 5.75% state "
            "rate plus locals. Ohio Rev. Code section 5739.02(B)(2) "
            "exempts only food for human consumption OFF the "
            "premises where sold; food consumed on-premises and "
            "prepared food generally fall outside that exemption. "
            "The Department's longstanding guidance (Information "
            "Release ST 2004-01 and successors) addresses borderline "
            "cases including drive-through, vending-machine, and "
            "catering configurations. Calculation only -- not legal "
            "or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Ohio at the "
            "general 5.75% state rate plus locals. Ohio Rev. Code "
            "section 5739.01(B)(12) defines 'sale' to include 'all "
            "transactions by which a specified digital product is "
            "provided for permanent use or less than permanent use, "
            "regardless of whether continued payment is required' -- "
            "i.e., both perpetual-license downloads and subscription "
            "/ streaming access are taxable. 'Specified digital "
            "product' is defined at Ohio Rev. Code section "
            "5739.01(OOO) to mean an electronically transferred "
            "digital audio-visual work, digital audio work, or "
            "digital book. Prewritten ('canned') computer software "
            "delivered by any means is also taxable as TPP. "
            "Electronic information services and SaaS may be "
            "taxable under chapter 5739's service definitions; "
            "integrators with non-enumerated digital services should "
            "consult the Ohio Department of Taxation's published "
            "guidance for borderline classifications. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Ohio "
            "at 5.75% per Ohio Rev. Code section 5739.02(A)(1) "
            "('the rate of the tax shall be five and three-fourths "
            "per cent'). County permissive sales taxes (Ohio Rev. "
            "Code section 5739.021) and transit-authority sales "
            "taxes (section 5739.023) layer additional rate on top, "
            "yielding combined county rates typically in the "
            "6.5%-8.0% range. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
}


class Ohio(SstStateModule):
    """Ohio state module (tier 1, SST member).

    Ohio is a full SST member, so the inherited
    :class:`SstStateModule` parsers handle the quarterly rate and
    boundary files. This subclass overrides the taxability matrix
    with Ohio-specific rules grounded in Ohio Rev. Code chapter
    5739 and adds the annual 3-day back-to-school sales-tax
    holiday under section 5739.02(B)(55).

    See the module docstring for the full discussion of Ohio's
    dual sales-tax-holiday frameworks (the longstanding 3-day
    holiday under section 5739.02(B)(55) versus the expanded
    14-day framework under section 5739.41 / HB 33 of 2023) and
    why 2026 reverts to the traditional 3-day version after
    HB 186 of the 136th General Assembly (signed
    December 19, 2025) cancelled the 2026 expansion.
    """

    state_abbrev: str = "OH"
    state_name: str = "Ohio"
    state_fips: str = "39"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Ohio-specific taxability matrix replaces the default tier-2
    # grocery-only matrix.
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Override district names to use the curated OH transit names.

        Codes that don't match the verified ``oh_names`` table fall
        back to the SST base implementation (placeholder).
        """
        from opensalestax.states.oh_names import district_name as _oh_district

        if authority_type == "district":
            friendly = _oh_district(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Ohio's sales-tax holidays for the years encoded in this module.

        - 2026: the traditional holiday under Ohio Rev. Code section
          5739.02(B)(55), the first Friday of August through Sunday
          (August 7-9, 2026). Clothing priced $75 or less per item;
          school supplies and school instructional materials priced
          $20 or less per item. One window per cap.
        - 2027: the expanded holiday under section 5739.41, fifteen
          days from August 1 through August 15, 2027 (section
          513.10(D) of H.B. 96 of the 136th General Assembly, as
          amended by H.B. 479). Tangible personal property priced
          $500 or less per item, minus the section 5739.01(UUU)
          exclusions. The traditional holiday does not run in 2027.

        Other years return nothing; add them as they are verified.
        """
        if year == 2026:
            return iter(
                [
                    HolidayWindow(
                        name="Ohio Back-to-School Sales Tax Holiday -- Clothing (2026)",
                        starts_on=dt.date(2026, 8, 7),
                        ends_on=dt.date(2026, 8, 9),
                        applicable_categories=("clothing",),
                        max_amount_per_item=Decimal("75.00"),
                        notes=(
                            "Ohio Rev. Code section 5739.02(B)(55)(a)(i): clothing "
                            "priced $75 or less per item, exempt from the state "
                            "sales tax and the county and transit-authority taxes "
                            "layered on it. An article over the cap is fully "
                            "taxable (no proration). HB 186 of the 136th General "
                            "Assembly cancelled the 2026 expanded section 5739.41 "
                            "holiday. Calculation only -- not legal or tax advice."
                        ),
                    ),
                    HolidayWindow(
                        name=(
                            "Ohio Back-to-School Sales Tax Holiday -- School Supplies "
                            "and Instructional Materials (2026)"
                        ),
                        starts_on=dt.date(2026, 8, 7),
                        ends_on=dt.date(2026, 8, 9),
                        applicable_categories=("school_supplies", "instructional_materials"),
                        max_amount_per_item=Decimal("20.00"),
                        notes=(
                            "Ohio Rev. Code section 5739.02(B)(55)(a)(ii)-(iii): "
                            "school supplies and school instructional materials "
                            "priced $20 or less per item. An article over the cap "
                            "is fully taxable (no proration). HB 186 of the 136th "
                            "General Assembly cancelled the 2026 expanded section "
                            "5739.41 holiday. Calculation only -- not legal or tax "
                            "advice."
                        ),
                    ),
                ]
            )
        if year == 2027:
            return iter(
                [
                    HolidayWindow(
                        name="Ohio Expanded Sales Tax Holiday (2027)",
                        starts_on=dt.date(2027, 8, 1),
                        ends_on=dt.date(2027, 8, 15),
                        applicable_categories=(
                            "general",
                            "clothing",
                            "prepared_food",
                            "school_supplies",
                            "instructional_materials",
                        ),
                        max_amount_per_item=Decimal("500.00"),
                        notes=(
                            "Ohio Rev. Code sections 5739.41 and 5739.02(B)(64); "
                            "dates set by section 513.10(D) of H.B. 96 of the 136th "
                            "General Assembly as amended by H.B. 479. Tangible "
                            "personal property priced $500 or less per item. "
                            "Excluded by section 5739.01(UUU): watercraft and "
                            "outboard motors required to be titled, motor "
                            "vehicles, alcoholic beverages, tobacco, vapor "
                            "products, and items containing marijuana. Specified "
                            "digital products are not tangible personal property "
                            "and stay taxable. Calculation only -- not legal or "
                            "tax advice."
                        ),
                    ),
                ]
            )
        return iter(())


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.ohio`` registers
# Ohio under "OH" in the state registry.
_PROTOCOL_CHECK: StateModule = Ohio()
del _PROTOCOL_CHECK

OHIO = register(Ohio())
