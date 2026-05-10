# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Iowa state module (tier 1, SST member).

IA is a Streamlined Sales Tax member (verified 2026-05-03 against
the SST member roster on streamlinedsalestax.org). The statewide
rate is **6%** per **Iowa Code section 423.2**, the rate having
been increased from 5% to 6% effective **July 1, 2008** by Senate
File 2400 of the 2008 General Assembly (the same act that
extended Iowa's school-infrastructure local-option sales tax
into a statewide local-option supplement).

Iowa's local-jurisdiction landscape:

- Counties and incorporated cities may, by voter approval, impose
  a **Local Option Sales Tax (LOST)** of typically **1%** under
  **Iowa Code chapter 423B**. Most Iowa cities impose the 1%
  LOST, giving combined rates of **6%-7%** statewide. A small
  number of jurisdictions impose other tested local options
  (e.g., school infrastructure local option in some counties;
  hotel/motel taxes which are NOT general sales taxes and are
  outside this engine's scope).
- Iowa is an SST member, so per-jurisdiction rates flow through
  the standard SST quarterly file. The SstStateModule base class
  provides the parser; this subclass only adds the Iowa-specific
  taxability matrix and the August sales-tax holiday.

Per :mod:`specs.research.sst-file-format`, the IA SST rate file
is presumed to use the same jurisdiction-type code mapping that
MN and WI validate at 2026Q2 (codes ``00`` county, ``01`` city,
``45`` state, ``63`` district). The MN/WI codes are the SST
empirical default; if a future quarterly capture of an Iowa rate
file shows different codes, override ``jurisdiction_types`` on
this subclass at that time. Until then we inherit the
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping.

Taxability matrix (per Iowa Code chapter 423):

- **General tangible personal property** -- TAXABLE at 6% per
  Iowa Code section 423.2 (the imposition statute).
- **Clothing** -- TAXABLE year-round at 6%. Iowa has **no
  general clothing exemption** in chapter 423; clothing and
  footwear are general tangible personal property and tax at
  the rate set by section 423.2. The annual sales-tax holiday
  on the first Friday and Saturday of August (Iowa Code section
  423.3(68)) provides a 2-day window for items priced under
  $100/article -- modeled in :meth:`Iowa.holidays_for`.
- **Groceries** -- EXEMPT per **Iowa Code section 423.3(57)**,
  which exempts the gross receipts from the sale of "food and
  food ingredients" (the Streamlined Sales Tax Project's
  uniform definition). The exemption tracks the SST common
  definition: candy, soft drinks, dietary supplements, and
  prepared food are NOT included in the exemption (those are
  taxable as general TPP or as prepared food).
- **Prescription drugs** -- EXEMPT per **Iowa Code section
  423.3(60)**, which exempts the gross receipts from the sale
  of prescription drugs (and certain related items including
  oxygen equipment for human use, insulin, hypodermic syringes
  for human use, and prosthetic devices when sold pursuant to
  a written prescription).
- **Prepared food** -- TAXABLE at 6%. Iowa's grocery exemption
  in section 423.3(57) expressly excludes prepared food, soft
  drinks, candy, and dietary supplements; prepared food (deli
  meals, restaurant meals, hot foods) tax at the general 6%
  rate.
- **Digital goods (specified digital products)** -- TAXABLE at
  6% per **Iowa Code section 423.5A**, added by House File 779
  of the 2018 General Assembly (effective January 1, 2019).
  Section 423.5A imposes the sales tax on the sale of
  "specified digital products" delivered electronically,
  including digital audio works, digital audiovisual works,
  digital books, and "other digital products" -- whether sold
  with a permanent right to use or under a subscription /
  conditional access. Sales of canned (prewritten) computer
  software delivered by any means are also taxable as TPP
  under the long-standing definition in section 423.1.

Computer-software exemption note (NOT in the general matrix):
Iowa Code section 423.3(47) exempts certain computer-related
purchases by manufacturers and certain insurance / financial-
institution / commercial-enterprise users when the software is
used in a qualifying way. This is a USE-based exemption that
the general taxability matrix doesn't model; downstream callers
shipping software to Iowa manufacturers should apply an
exemption certificate at the line-item level rather than
relying on the per-state taxability default. Documented here
for the next maintainer.

Sales tax holiday -- Iowa Annual Sales Tax Holiday
(Iowa Code section 423.3(68)):

- Recurring date: **first Friday in August at 12:01 a.m.
  through following Saturday at 11:59 p.m.** (a 2-day window).
- Eligible items: clothing and footwear with a sales price of
  **less than $100** per article. The exemption is per article,
  not per transaction.
- **EXCLUDED** from the holiday: clothing accessories
  (jewelry, handbags, briefcases, luggage, umbrellas, wallets,
  watches, similar items); athletic and protective clothing
  intended for use in athletic or recreational activity; rentals
  of clothing or footwear; alterations to clothing or footwear
  performed during the holiday. Any single article priced at
  $100 or more does NOT qualify (the entire article's price
  taxes at the regular rate; there is no "first $100 exempt"
  proration).
- 2026 dates: **August 7 (Friday) - August 8 (Saturday), 2026**
  (first Friday in August 2026 is August 7).

State maintainer: vacant -- see MAINTAINERS.md. Iowa's per-city
LOST rates are loaded from the SST quarterly file via the
inherited parser; tracking statutory changes (rate changes,
holiday scope amendments, digital-goods updates) is the
maintainer responsibility.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Iowa Department of Revenue guidance before relying on these
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

# Iowa taxability matrix per Iowa Code chapter 423.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Iowa year-round at the 6% state "
            "rate. Iowa Code chapter 423 contains no general clothing "
            "exemption; clothing and footwear are general tangible "
            "personal property and tax at the rate set by Iowa Code "
            "section 423.2. The annual Iowa Sales Tax Holiday on the "
            "first Friday and Saturday of August (Iowa Code section "
            "423.3(68)) provides a 2-day exemption for clothing and "
            "footwear priced less than $100 per article. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients are EXEMPT in Iowa per Iowa "
            "Code section 423.3(57), which exempts the gross receipts "
            "from the sale of food and food ingredients (using the "
            "Streamlined Sales Tax Project's uniform definition). The "
            "exemption excludes candy, soft drinks, dietary "
            "supplements, and prepared food -- those remain taxable "
            "at the general 6% rate. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Iowa per Iowa Code "
            "section 423.3(60), which exempts the gross receipts from "
            "the sale of prescription drugs and related items "
            "(insulin, hypodermic syringes for human use, oxygen "
            "equipment for human use, and prosthetic devices) when "
            "dispensed pursuant to a written prescription by a "
            "licensed practitioner. Over-the-counter (non-prescription) "
            "drugs are NOT covered by this exemption and remain "
            "taxable. Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food is TAXABLE in Iowa at the general 6% rate. "
            "Iowa Code section 423.3(57) expressly excludes prepared "
            "food (along with candy, soft drinks, and dietary "
            "supplements) from the food-and-food-ingredients "
            "exemption; restaurant meals, hot deli items, and "
            "ready-to-eat foods tax at the rate set by Iowa Code "
            "section 423.2. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Iowa at the "
            "general 6% rate per Iowa Code section 423.5A, added by "
            "House File 779 of the 2018 General Assembly (effective "
            "January 1, 2019). Section 423.5A imposes sales tax on "
            "digital audio works, digital audiovisual works, digital "
            "books, and 'other digital products' delivered "
            "electronically -- whether transferred with a permanent "
            "right of use or under a subscription / conditional "
            "access model. Canned (prewritten) computer software "
            "delivered by any means is also taxable as tangible "
            "personal property under Iowa Code section 423.1. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Iowa at "
            "6% per Iowa Code section 423.2 (the imposition statute, "
            "raised from 5% to 6% effective July 1, 2008 by S.F. 2400, "
            "82nd G.A.). Calculation only -- not legal or tax advice."
        ),
    ),
}


class Iowa(SstStateModule):
    """Iowa state module (tier 1, SST member).

    Iowa is a full SST member, so the inherited
    :class:`SstStateModule` parsers handle the quarterly rate
    and boundary files. This subclass overrides the taxability
    matrix with Iowa-specific rules grounded in Iowa Code chapter
    423 and adds the annual August sales-tax holiday under
    section 423.3(68).
    """

    state_abbrev: str = "IA"
    state_name: str = "Iowa"
    state_fips: str = "19"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Iowa-specific taxability matrix replaces the default
    # tier-2 grocery-only matrix.
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated IA district-name table; fall back to placeholder."""
        from opensalestax.states.ia_names import district_name as _ia_district

        if authority_type == "district":
            friendly = _ia_district(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)

    # iter-80 supplement: Johnson County's 1% LOST is genuinely
    # missing from the IA SST quarterly file (verified against the
    # latest IAR2025Q3MAY30.zip published per the SST listing). The
    # tax has been collected since July 1, 2010 per the Johnson
    # County ordinance approved Nov 2009. Without this supplement,
    # Iowa City / Coralville / North Liberty / Solon / etc. all
    # under-collect by 1.0%. Pattern matches the iter-68 USPS PO-box
    # ZCTA supplement: hand-curated data layered on top of SST.
    _SUPPLEMENT_DISTRICT_NAME = "Johnson County Local Option Sales Tax"
    _SUPPLEMENT_DISTRICT_CODE = "19103-LOST"  # FIPS 19=IA, 103=Johnson Co
    _JOHNSON_COUNTY_FIPS = "103"

    def parse_rates(self, source_file, version_label):
        """Yield SST rates plus the Johnson County LOST supplement.

        See _SUPPLEMENT_DISTRICT_NAME comment above for context.
        """
        from decimal import Decimal

        from opensalestax.states.protocol import RateRow

        yield from super().parse_rates(source_file, version_label)
        yield RateRow(
            authority_name=self._SUPPLEMENT_DISTRICT_NAME,
            authority_type="district",
            rate_pct=Decimal("1.000"),
            effective_from=dt.date(2010, 7, 1),
            effective_to=None,
            parent_authority_name=self.state_name,
        )

    def parse_boundaries(self, source_file, version_label):
        """Yield SST boundaries plus Johnson County LOST bindings."""
        from opensalestax.data.zip_county import ZIP_COUNTY
        from opensalestax.states.protocol import BoundaryRow

        yield from super().parse_boundaries(source_file, version_label)

        # Bind Johnson County LOST to every IA ZIP whose Census ZCTA
        # places it in Johnson County (FIPS 19103). The dedup is
        # done by the loader's existing (authority, zip, zip4_low,
        # zip4_high) seen-set so emitting these in addition to the
        # SST records is safe.
        seen_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            for state_abbrev, county_fips in pairs:
                if state_abbrev != "IA":
                    continue
                if county_fips != self._JOHNSON_COUNTY_FIPS:
                    continue
                if zip5 in seen_zips:
                    continue
                seen_zips.add(zip5)
                yield BoundaryRow(
                    authority_name=self._SUPPLEMENT_DISTRICT_NAME,
                    authority_type="district",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
                break

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Iowa's annual sales-tax holiday under Iowa Code section 423.3(68).

        Recurring statutory date: first Friday in August at 12:01 a.m.
        through Saturday at 11:59 p.m. -- a 2-day window. Eligible
        items: clothing and footwear priced less than $100 per
        article. Excluded: clothing accessories (jewelry, handbags,
        watches, etc.) and athletic / protective clothing intended
        for use in athletic or recreational activity.

        2026 dates encoded explicitly per the recurring statutory
        rule. Subsequent years require an explicit data update (do
        NOT extrapolate -- the legislature could amend the dates,
        scope, or per-item cap at any time, and a future maintainer
        must verify against the Iowa Department of Revenue's
        published guidance for each year).
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Iowa Annual Sales Tax Holiday (2026)",
                    starts_on=dt.date(2026, 8, 7),
                    ends_on=dt.date(2026, 8, 8),
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Iowa Code section 423.3(68). Two-day "
                        "exemption from the 6% state sales tax (and "
                        "from local-option sales taxes imposed under "
                        "chapter 423B) for clothing and footwear "
                        "priced LESS THAN $100 per article. The "
                        "$100 threshold is per article, not per "
                        "transaction; an article priced at $100 or "
                        "more is fully taxable at the regular rate "
                        "(no proration). EXCLUDED from the holiday: "
                        "clothing accessories (jewelry, handbags, "
                        "briefcases, luggage, umbrellas, wallets, "
                        "watches, and similar items); athletic and "
                        "protective clothing intended for use in "
                        "athletic or recreational activity; rentals "
                        "of clothing or footwear; alterations "
                        "performed during the holiday. The holiday "
                        "runs from 12:01 a.m. on the first Friday "
                        "in August through 11:59 p.m. on the "
                        "following Saturday. 2026: first Friday in "
                        "August is August 7; holiday runs through "
                        "Saturday August 8. Calculation only -- not "
                        "legal or tax advice."
                    ),
                ),
            ]
        )


# Compile-time check + register
_PROTOCOL_CHECK: StateModule = Iowa()
del _PROTOCOL_CHECK

IOWA = register(Iowa())
