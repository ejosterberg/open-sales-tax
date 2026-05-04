# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""West Virginia state module (tier 1, SST member).

WV is a Streamlined Sales Tax member (verified 2026-05-03 against
the SST member roster on streamlinedsalestax.org). The general
statewide rate is **6%** per **W. Va. Code section 11-15-3** (the
imposition statute for the West Virginia consumers sales and
service tax), in place at the 6% level since January 1, 2003 when
H.B. 2007 (Second Extraordinary Session, 2002) raised the rate
from 5% to 6%.

West Virginia local-jurisdiction landscape:

- WV does not authorize a general county sales tax. Local
  sales-tax authority is limited to **municipal home rule**
  participants under **W. Va. Code section 8-13C** (the
  Municipal Home Rule Pilot Program, made permanent by H.B.
  4009 of the 2019 regular session). Participating
  municipalities may impose a municipal sales and service tax
  at a rate of **up to 1.0%**, in addition to the 6% state rate.
- ~50+ municipalities have adopted the local 1% under the
  Home Rule program (Charleston, Huntington, Morgantown,
  Wheeling, Parkersburg, Beckley, etc.), giving combined
  rates in the **6.0%-7.0%** range. As an SST member, WV's
  per-jurisdiction rates flow through the standard SST
  quarterly file via the inherited :class:`SstStateModule`
  parser. This subclass only adds the WV-specific taxability
  matrix and the August sales-tax holiday.

Per :mod:`specs.research.sst-file-format`, the WV SST rate file
is presumed to use the same jurisdiction-type code mapping that
MN and WI validate at 2026Q2 (codes ``00`` county, ``01`` city,
``45`` state, ``63`` district). The MN/WI codes are the SST
empirical default; if a future quarterly capture of a WV rate
file shows different codes, override ``jurisdiction_types`` on
this subclass at that time. Until then we inherit the
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping.

Taxability matrix (per W. Va. Code Chapter 11, Article 15):

- **General tangible personal property** -- TAXABLE at 6% per
  W. Va. Code section 11-15-3 (the imposition statute, in
  place at 6% since 2003-01-01).
- **Clothing** -- TAXABLE year-round at 6%. WV has **no
  general clothing exemption** in chapter 11, article 15;
  clothing and footwear are general tangible personal
  property and tax at the rate set by section 11-15-3. The
  annual Sales Tax Holiday on the first Friday-Monday of
  August (W. Va. Code section 11-15-9o) provides a 4-day
  window for clothing/footwear items priced under $125 --
  modeled in :meth:`WestVirginia.holidays_for`.
- **Groceries (food and food ingredients for home consumption)**
  -- **EXEMPT** since 2013-07-01 per **W. Va. Code section
  11-15-3a**. The grocery sales tax in West Virginia was phased
  down over a multi-year period:

    * Pre-2006: full 6% (the general rate)
    * Effective 2006-01-01: reduced to 5% (H.B. 4346, 2005
      Regular Session)
    * Effective 2007-07-01: reduced to 4% (H.B. 4067, 2006
      Regular Session)
    * Effective 2008-07-01: reduced to 3% (H.B. 4006, 2008
      Regular Session)
    * Effective 2012-01-01: reduced to 2% (S.B. 234, 2011
      Regular Session)
    * Effective 2012-07-01: reduced to 1% (continuation of the
      same phase-down schedule)
    * Effective **2013-07-01: ELIMINATED (0%)** -- the final
      step in the multi-year phase-out; the grocery exemption
      under section 11-15-3a has been in place at 0% ever since.

  Encoded as ``is_taxable=False`` -- food and food ingredients
  are fully exempt from the state sales tax. Items NOT meeting
  the SST "food and food ingredients" definition (candy, soft
  drinks, dietary supplements, prepared food) are NOT covered
  by the section 11-15-3a exemption and remain taxable at the
  general 6% rate. Note: municipal home-rule sales taxes
  (under section 8-13C) generally also exempt food and food
  ingredients in conformity with the state exemption, though
  per-municipality variation is possible -- documented for
  the next maintainer.
- **Prescription drugs** -- EXEMPT per **W. Va. Code section
  11-15-9(a)(11)** (the article 15 exemption for "drugs,
  durable medical goods, mobility-enhancing equipment, and
  prosthetic devices dispensed upon prescription"). The
  exemption tracks the SST uniform "drugs sold by prescription"
  definition; over-the-counter drugs are NOT covered and
  remain taxable.
- **Prepared food** -- TAXABLE at 6%. WV's grocery exemption
  in section 11-15-3a expressly excludes prepared food, candy,
  soft drinks, and dietary supplements; restaurant meals,
  hot deli items, and ready-to-eat foods tax at the general
  6% rate set by section 11-15-3.
- **Digital goods (specified digital products)** -- TAXABLE at
  6% per **W. Va. Code section 11-15B-2** (the SST conforming
  definitions article), effective with West Virginia's full
  SST conformity adoption (effective 2008 -- WV joined SST as
  a full member effective October 1, 2005 and adopted the
  uniform digital-products definitions effective 2008). Section
  11-15B-2 incorporates the SST "specified digital products"
  definitions (digital audio works, digital audiovisual works,
  digital books); West Virginia's general imposition statute
  (section 11-15-3) reaches "tangible personal property and
  selected services," and the State Tax Department has
  consistently treated electronically-delivered specified
  digital products as taxable under section 11-15-3 as
  informed by the section 11-15B-2 definitions. Canned
  (prewritten) computer software delivered by any means is
  also taxable under the long-standing definition of tangible
  personal property in chapter 11, article 15.

Sales tax holiday -- West Virginia Annual Sales Tax Holiday
(W. Va. Code section 11-15-9o):

- Recurring date: **first Friday in August at 12:00 a.m.
  through the following Monday at 11:59 p.m.** (a 4-day
  window). The holiday was enacted by H.B. 2025 of the 2021
  Regular Session and codified as section 11-15-9o.
- Multi-scope holiday with FIVE distinct per-item caps:

    * **Clothing and footwear**: $125 or less per item
    * **School supplies**: $50 or less per item
    * **School instructional materials**: $20 or less per item
    * **Sports equipment**: $150 or less per item
    * **Computers / tablets / laptops** (intended for personal
      non-business use): $500 or less per item

- Each scope is encoded as a SEPARATE :class:`HolidayWindow`
  because :attr:`HolidayWindow.max_amount_per_item` is a
  single-value field. The same pattern is used by VA, MO, and
  other multi-scope-holiday states.
- 2026 dates: **August 7 (Friday) - August 10 (Monday), 2026**
  (first Friday in August 2026 is August 7).

State maintainer: vacant -- see MAINTAINERS.md. WV's per-city
home-rule sales tax rates are loaded from the SST quarterly file
via the inherited parser; tracking statutory changes (rate
changes, holiday scope amendments, new home-rule participants)
is a maintainer responsibility. The Municipal Home Rule program
periodically admits new participants; the SST quarterly file is
the source of truth for per-municipality rates.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
West Virginia State Tax Department guidance before relying on
these rules in production.
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

# West Virginia taxability matrix per W. Va. Code chapter 11,
# article 15 (consumers sales and service tax).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in West Virginia year-round at the "
            "6% state rate. W. Va. Code chapter 11, article 15 "
            "contains no general clothing exemption; clothing and "
            "footwear are general tangible personal property and tax "
            "at the rate set by W. Va. Code section 11-15-3. The "
            "annual West Virginia Sales Tax Holiday on the first "
            "Friday-Monday of August (W. Va. Code section 11-15-9o) "
            "provides a 4-day exemption for clothing and footwear "
            "priced $125 or less per item. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients for home consumption are "
            "EXEMPT in West Virginia per W. Va. Code section "
            "11-15-3a, with the exemption fully effective at 0% "
            "since 2013-07-01. The grocery sales tax was phased "
            "down over a multi-year schedule: 6% (pre-2006) -> 5% "
            "(2006-01-01, H.B. 4346) -> 4% (2007-07-01, H.B. 4067) "
            "-> 3% (2008-07-01, H.B. 4006) -> 2% (2012-01-01, "
            "S.B. 234) -> 1% (2012-07-01, same phase-down "
            "schedule) -> 0% (2013-07-01, completing the "
            "phase-out). The exemption tracks the SST uniform "
            "'food and food ingredients' definition and excludes "
            "candy, soft drinks, dietary supplements, and prepared "
            "food -- those remain taxable at the general 6% rate. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in West Virginia per "
            "W. Va. Code section 11-15-9(a)(11), which exempts "
            "drugs, durable medical goods, mobility-enhancing "
            "equipment, and prosthetic devices dispensed upon "
            "prescription. Insulin and certain related items are "
            "also covered. The exemption tracks the SST uniform "
            "'drugs sold by prescription' definition; "
            "over-the-counter (non-prescription) drugs are NOT "
            "covered by this exemption and remain taxable. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food is TAXABLE in West Virginia at the "
            "general 6% rate. W. Va. Code section 11-15-3a "
            "(the food/food-ingredients exemption) expressly "
            "EXCLUDES prepared food, candy, soft drinks, and "
            "dietary supplements; restaurant meals, hot deli items, "
            "and ready-to-eat foods tax at the rate set by W. Va. "
            "Code section 11-15-3. Calculation only -- not legal "
            "or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in West "
            "Virginia at the general 6% rate. W. Va. Code section "
            "11-15B-2 (the SST conforming definitions article) "
            "incorporates the SST uniform 'specified digital "
            "products' definitions (digital audio works, digital "
            "audiovisual works, digital books), in place since West "
            "Virginia's adoption of the SST uniform digital-products "
            "definitions effective 2008. The general imposition "
            "statute at W. Va. Code section 11-15-3 reaches "
            "tangible personal property and selected services; the "
            "State Tax Department has treated electronically-"
            "delivered specified digital products as taxable under "
            "section 11-15-3 as informed by the section 11-15B-2 "
            "definitions. Canned (prewritten) computer software "
            "delivered by any means is also taxable as tangible "
            "personal property under the long-standing definition "
            "in chapter 11, article 15. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in West "
            "Virginia at the 6% state rate per W. Va. Code section "
            "11-15-3 (the imposition statute, in place at 6% since "
            "2003-01-01 when H.B. 2007 (Second Extraordinary "
            "Session, 2002) raised the rate from 5% to 6%). "
            "Municipal home-rule sales taxes under W. Va. Code "
            "section 8-13C add up to 1% in participating "
            "municipalities; combined rates are typically in the "
            "6.0%-7.0% range. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
}


class WestVirginia(SstStateModule):
    """West Virginia state module (tier 1, SST member).

    West Virginia is a full SST member (effective October 1, 2005),
    so the inherited :class:`SstStateModule` parsers handle the
    quarterly rate and boundary files. This subclass overrides the
    taxability matrix with WV-specific rules grounded in W. Va.
    Code chapter 11, article 15 and adds the annual August sales-
    tax holiday under W. Va. Code section 11-15-9o.

    Notable WV history encoded in the docstring + grocery rule:

    - The WV grocery sales tax was phased down over 7 years
      (2006-2013), reaching 0% on 2013-07-01 -- a multi-year
      sequence of legislative steps culminating in full
      elimination per section 11-15-3a.
    - The annual August holiday (section 11-15-9o, enacted 2021)
      is a 4-day, multi-scope holiday with five distinct per-item
      caps (clothing $125, school supplies $50, instructional
      materials $20, sports equipment $150, computers $500).
    """

    state_abbrev: str = "WV"
    state_name: str = "West Virginia"
    state_fips: str = "54"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # West Virginia-specific taxability matrix replaces the default
    # tier-2 grocery-only matrix.
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated WV city-name table; fall back to placeholder."""
        from opensalestax.states.wv_names import city_name as _wv_city

        if authority_type == "city":
            friendly = _wv_city(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """West Virginia's annual sales-tax holiday under section 11-15-9o.

        Recurring statutory date: first Friday in August at 12:00
        a.m. through the following Monday at 11:59 p.m. -- a 4-day
        window. The holiday covers FIVE distinct scopes with
        different per-item caps; each scope is encoded as a
        separate :class:`HolidayWindow` because
        :attr:`HolidayWindow.max_amount_per_item` is a single-value
        field. This is the same pattern used by VA, MO, and other
        multi-scope-holiday states.

        Per-scope caps:

        - Clothing and footwear: $125 or less per item
        - School supplies: $50 or less per item
        - School instructional materials: $20 or less per item
        - Sports equipment: $150 or less per item
        - Computers / tablets / laptops for personal use:
          $500 or less per item

        2026 dates encoded explicitly per the recurring statutory
        rule. Subsequent years require an explicit data update (do
        NOT extrapolate -- the legislature could amend the dates,
        scope, or per-item caps at any time, and a future
        maintainer must verify against the West Virginia State
        Tax Department's published guidance for each year).
        """
        if year != 2026:
            return iter(())
        # 2026 dates: first Friday of August is August 7;
        # holiday ends the following Monday, August 10.
        starts_on = dt.date(2026, 8, 7)
        ends_on = dt.date(2026, 8, 10)
        return iter(
            [
                HolidayWindow(
                    name="West Virginia Sales Tax Holiday -- Clothing & Footwear (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("125.00"),
                    notes=(
                        "W. Va. Code section 11-15-9o (enacted by "
                        "H.B. 2025, 2021 Regular Session). Four-day "
                        "exemption from the 6% state sales tax (and "
                        "from local municipal home-rule sales taxes "
                        "under section 8-13C) for clothing and "
                        "footwear priced $125 or LESS per item. The "
                        "$125 threshold is per item, not per "
                        "transaction. The holiday runs from 12:00 "
                        "a.m. on the first Friday in August through "
                        "11:59 p.m. on the following Monday. 2026: "
                        "first Friday in August is August 7; holiday "
                        "runs through Monday August 10. Calculation "
                        "only -- not legal or tax advice."
                    ),
                ),
                HolidayWindow(
                    name="West Virginia Sales Tax Holiday -- School Supplies (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("school_supplies",),
                    max_amount_per_item=Decimal("50.00"),
                    notes=(
                        "W. Va. Code section 11-15-9o. Four-day "
                        "exemption from the 6% state sales tax for "
                        "qualifying school supplies (binders, "
                        "calculators, notebooks, pens, pencils, "
                        "paper, etc.) priced $50 or LESS per item. "
                        "2026 dates: August 7 (Friday) through "
                        "August 10 (Monday). Calculation only -- "
                        "not legal or tax advice."
                    ),
                ),
                HolidayWindow(
                    name=(
                        "West Virginia Sales Tax Holiday -- "
                        "School Instructional Materials (2026)"
                    ),
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("school_instructional_materials",),
                    max_amount_per_item=Decimal("20.00"),
                    notes=(
                        "W. Va. Code section 11-15-9o. Four-day "
                        "exemption from the 6% state sales tax for "
                        "qualifying school instructional materials "
                        "(reference books, reference maps and "
                        "globes, textbooks, workbooks) priced $20 "
                        "or LESS per item. 2026 dates: August 7 "
                        "(Friday) through August 10 (Monday). "
                        "Calculation only -- not legal or tax "
                        "advice."
                    ),
                ),
                HolidayWindow(
                    name="West Virginia Sales Tax Holiday -- Sports Equipment (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("sports_equipment",),
                    max_amount_per_item=Decimal("150.00"),
                    notes=(
                        "W. Va. Code section 11-15-9o. Four-day "
                        "exemption from the 6% state sales tax for "
                        "qualifying sports equipment priced $150 or "
                        "LESS per item. 2026 dates: August 7 "
                        "(Friday) through August 10 (Monday). "
                        "Calculation only -- not legal or tax "
                        "advice."
                    ),
                ),
                HolidayWindow(
                    name="West Virginia Sales Tax Holiday -- Computers & Tablets (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("computers",),
                    max_amount_per_item=Decimal("500.00"),
                    notes=(
                        "W. Va. Code section 11-15-9o. Four-day "
                        "exemption from the 6% state sales tax for "
                        "qualifying computers, laptops, and tablets "
                        "intended for personal (non-business) use, "
                        "priced $500 or LESS per item. 2026 dates: "
                        "August 7 (Friday) through August 10 "
                        "(Monday). Calculation only -- not legal or "
                        "tax advice."
                    ),
                ),
            ]
        )


# Compile-time check + register
_PROTOCOL_CHECK: StateModule = WestVirginia()
del _PROTOCOL_CHECK

WEST_VIRGINIA = register(WestVirginia())
