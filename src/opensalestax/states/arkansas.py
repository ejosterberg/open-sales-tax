# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Arkansas state module (tier 1, SST member).

AR is a Streamlined Sales Tax member. The general statewide rate
is **6.5%** per Ark. Code Ann. section 26-52-301 (effective
2013-07-01 per the Arkansas Department of Finance and
Administration -- DFA -- published rate history). Local
jurisdictions (75 counties + many cities) stack additional rates;
combined rates commonly fall in the 9-11% range. Local rates are
ingested via the SST quarterly rate file rather than hard-coded.

Per :mod:`specs.research.sst-file-format`, AR's SST rate file is
expected to use the same jurisdiction-type code mapping as MN and
WI (both validated against 2026Q2 data). AR data has not been
empirically inspected at promotion time; the default mapping is
applied and documented as an assumption. A future state maintainer
should validate against an actual ``ARR<...>.csv`` file:

- ``45`` = state (single row carrying 6.5%)
- ``00`` = county
- ``01`` = city / local
- ``63`` = special district

Per the AR DFA Streamlined Sales Tax page (retrieved 2026-05-03),
"the Rate Database Table provides Arkansas' taxing jurisdictions
and rates by Federal Information Processing Standards (FIPS)
codes". AR's state FIPS is ``05``; counties and cities are listed
by FIPS code. The structure matches the SST canonical layout, so
the inherited :class:`SstStateModule` parser is expected to work
without override.

Taxability matrix (per Ark. Code Title 26, Chapter 52):

- **General tangible personal property** -- TAXABLE at 6.5% per
  Ark. Code Ann. section 26-52-301.
- **Clothing** -- TAXABLE year-round (no general clothing
  exemption). The annual August Sales Tax Holiday (Ark. Code Ann.
  section 26-52-444) provides a 2-day window for clothing under
  $100 and clothing accessories under $50.
- **Groceries (food and food ingredients)** -- TAXABLE but at
  the **0.000% reduced state rate effective January 1, 2026**
  per the Grocery Tax Relief Act (codified at Ark. Code Ann.
  section 26-52-317 as amended). Prior history:

    - Pre-2011: full 6% state rate
    - 2011-07-01 to 2018-12-31: reduced 1.5% state rate
    - 2019-01-01 to 2025-12-31: reduced 0.125% state rate
    - **2026-01-01 onward: 0.000% state rate**

  Local sales taxes still apply to groceries; only the state
  portion was eliminated. Encoded with
  ``rate_modifier=Decimal("0.000")`` to mark the special state
  rate (the engine applies rate_modifier (since v0.11.1); until v0.6+
  wires it through, the engine over-collects the 6.5% state
  portion on grocery line items in AR -- documented in the
  ``notes`` and the API disclaimer). Items NOT meeting the SST
  "food and food ingredients" definition (candy, soft drinks,
  prepared food, dietary supplements, alcoholic beverages,
  tobacco) remain at the general 6.5% rate.
- **Prescription drugs** -- NON-taxable per Ark. Code Ann.
  section 26-52-406. The exemption covers drugs that may only be
  legally dispensed by prescription, when sold by a licensed
  pharmacist, hospital, or physician for human use. Oxygen sold
  for human use on a physician's prescription is also exempt.
  Drugs available without a prescription do NOT qualify even if
  prescribed.
- **Prepared food** -- TAXABLE at the general 6.5% rate. The
  reduced grocery rate explicitly excludes prepared food per the
  SST food-definition framework adopted by AR.
- **Digital goods (specified digital products and digital codes)**
  -- TAXABLE at 6.5% per Act 141 of 2017 (H.B. 1162), effective
  January 1, 2018. The Act amended Ark. Code Ann. section
  26-52-301 (and added section 26-52-103 definitions) to bring
  specified digital products -- music, e-books, video, ringtones,
  software, digital codes -- into the sales-tax base.

Sales tax holiday:

AR has a single annual Back-to-School Sales Tax Holiday per Ark.
Code Ann. section 26-52-444. By statute it falls on the **first
Saturday and Sunday of August**. Per the DFA 2026 holiday page
(retrieved 2026-05-03), the **2026 holiday runs August 1
(Saturday) through August 2 (Sunday)**. The holiday exempts both
state AND local sales/use tax on five categories:

- **Clothing** -- per-item under **$100**
- **Clothing accessories or equipment** -- per-item under **$50**
- **School supplies** -- no per-item dollar cap
- **School art supplies** -- no per-item dollar cap
- **School instructional materials** -- no per-item dollar cap
- **Electronic devices** -- no per-item dollar cap (added by
  Act 944 of 2021, effective for the 2021 holiday and onward)

Each scope is encoded as a separate :class:`HolidayWindow` so the
engine can match per-category. Per-item caps are encoded in
``max_amount_per_item`` for the two scopes that have them; the
remaining scopes set ``max_amount_per_item=None``.

State maintainer: vacant -- see MAINTAINERS.md. Confirming AR's
SST jurisdiction-type codes against an actual ARR file is the
natural next maintenance task. Tracking the biennial legislative
session for any rate or holiday changes (especially around
electronics-cap proposals) is a maintainer responsibility.

DISCLAIMER: This is calculation logic, not tax advice. Maintainers
and users are responsible for verifying current AR DFA guidance
before relying on these rules in production.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import (
    HolidayWindow,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# ---------------------------------------------------------------------------
# AR-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
# ASSUMPTION: AR's SST rate file uses the same jurisdiction-type
# codes as MN and WI (both empirically validated against 2026Q2
# data). This is consistent with SST's stated goal of uniform
# data formats across member states and with the AR DFA
# Streamlined Sales Tax page describing rates "by FIPS codes"
# (which matches the canonical layout). A state maintainer should
# validate against an actual ARR<...>.csv file at next refresh.
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Static taxability matrix per Ark. Code Title 26, Chapter 52.
# Categories not listed default to taxable (engine behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Arkansas year-round at the general "
            "6.5% state rate (Ark. Code Ann. section 26-52-301). The "
            "annual August Sales Tax Holiday (Ark. Code Ann. section "
            "26-52-444) provides a 2-day exemption for clothing items "
            "under $100 and clothing accessories under $50. "
            "Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("0.000"),
        notes=(
            "Food and food ingredients are taxable at a REDUCED 0.000% "
            "state rate effective January 1, 2026 per the Arkansas "
            "Grocery Tax Relief Act (codified at Ark. Code Ann. "
            "section 26-52-317 as amended). Prior reduced rates: "
            "1.5% (2011-07-01 through 2018-12-31), 0.125% (2019-01-01 "
            "through 2025-12-31). Local sales taxes still apply -- "
            "only the state portion was eliminated. Items NOT meeting "
            "the SST 'food and food ingredients' definition (candy, "
            "soft drinks, prepared food, dietary supplements, alcohol, "
            "tobacco) remain at the general 6.5% rate. The "
            "rate_modifier is stored but the engine applies (as of v0.11.1) "
            "it (shipped in v0.11.1); until then the engine will "
            "over-collect the 6.5% state portion on grocery line items. "
            "Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are exempt from Arkansas sales and use "
            "tax per Ark. Code Ann. section 26-52-406 when sold by a "
            "licensed pharmacist, hospital, or physician for human "
            "use. The exemption covers only drugs that may legally be "
            "dispensed by prescription; over-the-counter drugs do NOT "
            "qualify even when prescribed. Oxygen sold for human use "
            "on a physician's prescription is also exempt. "
            "Calculation only -- not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food is taxable at the general 6.5% state rate "
            "per Ark. Code Ann. section 26-52-301. Prepared food is "
            "explicitly excluded from the reduced grocery rate "
            "(section 26-52-317) under the SST 'food and food "
            "ingredients' definition. Calculation only -- not tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products and digital codes (music, "
            "e-books, video, ringtones, software, etc.) are taxable "
            "at the general 6.5% state rate per Act 141 of 2017 "
            "(H.B. 1162), effective January 1, 2018, which amended "
            "Ark. Code Ann. section 26-52-301 and added definitions. "
            "Sales to an end user with the right of permanent or less "
            "than permanent use are taxable. Calculation only -- not "
            "tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at the "
            "6.5% state rate per Ark. Code Ann. section 26-52-301. "
            "Local rates stack on top via the SST quarterly rate "
            "file. Calculation only -- not tax advice."
        ),
    ),
}


class Arkansas(SstStateModule):
    """Arkansas state module (tier 1, SST member).

    Inherits the generic SST rate/boundary parser from
    :class:`SstStateModule`. Overrides the default taxability
    matrix and the jurisdiction-type code mapping with AR-specific
    research; provides the August Back-to-School holiday windows.
    """

    state_abbrev: str = "AR"
    state_name: str = "Arkansas"
    state_fips: str = "05"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Override the base-class defaults with AR-specific data.
    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Arkansas's annual Back-to-School Sales Tax Holiday.

        Per Ark. Code Ann. section 26-52-444, the holiday begins
        at 12:01 a.m. on the first Saturday in August and ends at
        11:59 p.m. on the following Sunday. For 2026 this is
        August 1 (Saturday) through August 2 (Sunday), as
        confirmed by the DFA 2026 holiday page (retrieved
        2026-05-03).

        Five distinct scopes are encoded as separate
        :class:`HolidayWindow` instances so the engine can match
        per-category. Two scopes carry per-item dollar caps:

        - clothing -- under $100 per item
        - clothing accessories or equipment -- under $50 per item

        The remaining three scopes (school supplies, school art
        supplies, school instructional materials) plus electronic
        devices (added by Act 944 of 2021) have NO per-item cap
        under the statute.

        Subsequent years require an explicit data update; do NOT
        extrapolate. The legislature occasionally adjusts the
        category list (Act 944 of 2021 added electronics) and
        could in principle adjust the cap thresholds.
        """
        if year != 2026:
            return iter(())
        # 2026 dates: first Saturday of August is August 1;
        # holiday ends Sunday August 2.
        starts_on = dt.date(2026, 8, 1)
        ends_on = dt.date(2026, 8, 2)
        return iter(
            [
                HolidayWindow(
                    name="Arkansas Back-to-School Sales Tax Holiday -- Clothing (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Ark. Code Ann. section 26-52-444. Two-day "
                        "exemption from state and local sales/use tax "
                        "for clothing items priced less than $100 per "
                        "item. The statute defines 'clothing' as 'an "
                        "item of human wearing apparel suitable for "
                        "general use'. Calculation only -- not tax "
                        "advice."
                    ),
                ),
                HolidayWindow(
                    name=(
                        "Arkansas Back-to-School Sales Tax Holiday -- "
                        "Clothing Accessories (2026)"
                    ),
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("clothing_accessories",),
                    max_amount_per_item=Decimal("50.00"),
                    notes=(
                        "Ark. Code Ann. section 26-52-444. Two-day "
                        "exemption from state and local sales/use tax "
                        "for clothing accessories or equipment priced "
                        "less than $50 per item. 'Clothing accessory "
                        "or equipment' means an incidental item worn "
                        "on the person or in conjunction with "
                        "clothing. Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name=("Arkansas Back-to-School Sales Tax Holiday -- " "School Supplies (2026)"),
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("school_supplies",),
                    max_amount_per_item=None,
                    notes=(
                        "Ark. Code Ann. section 26-52-444. Two-day "
                        "exemption from state and local sales/use tax "
                        "for school supplies. NO per-item dollar cap "
                        "under the AR statute (contrast with VA which "
                        "caps school supplies at $20). Calculation "
                        "only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name=(
                        "Arkansas Back-to-School Sales Tax Holiday -- " "School Art Supplies (2026)"
                    ),
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("school_art_supplies",),
                    max_amount_per_item=None,
                    notes=(
                        "Ark. Code Ann. section 26-52-444. Two-day "
                        "exemption from state and local sales/use tax "
                        "for school art supplies. NO per-item dollar "
                        "cap. Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name=(
                        "Arkansas Back-to-School Sales Tax Holiday -- "
                        "School Instructional Materials (2026)"
                    ),
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("school_instructional_materials",),
                    max_amount_per_item=None,
                    notes=(
                        "Ark. Code Ann. section 26-52-444. Two-day "
                        "exemption from state and local sales/use tax "
                        "for school instructional materials. NO "
                        "per-item dollar cap. Calculation only -- not "
                        "tax advice."
                    ),
                ),
                HolidayWindow(
                    name=(
                        "Arkansas Back-to-School Sales Tax Holiday -- " "Electronic Devices (2026)"
                    ),
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("electronic_devices",),
                    max_amount_per_item=None,
                    notes=(
                        "Ark. Code Ann. section 26-52-444 as amended "
                        "by Act 944 of 2021. Two-day exemption from "
                        "state and local sales/use tax for electronic "
                        "devices commonly used by a student in a "
                        "course of study. NO per-item dollar cap "
                        "under the AR statute. Calculation only -- "
                        "not tax advice."
                    ),
                ),
            ]
        )


# Register the singleton instance.
ARKANSAS = register(Arkansas())
