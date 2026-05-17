# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Utah state module (tier 1, SST member).

UT is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The general statewide combined sales
and use tax rate is **4.85%** per **Utah Code section 59-12-103**
(the imposition statute in the Utah Sales and Use Tax Act, Title
59 Chapter 12). State FIPS: 49.

## Statewide rate composition (4.85%)

The 4.85% statewide combined rate is composed of three statutory
components, all imposed at the state level and uniform statewide:

- **4.70%** -- general state sales and use tax per Utah Code
  section 59-12-103(2)(a)(i)(A) (the principal imposition rate;
  raised from 4.65% to 4.70% effective April 1, 2019 by Senate
  Bill 2001 of the 2018 Third Special Session).
- **0.10%** -- statewide-uniform local-option rate per Utah Code
  section 59-12-204 (a state-administered local-option sales tax
  imposed at the same rate in every Utah county and city; the
  proceeds flow back to local governments).
- **0.05%** -- mass transit basic rate per Utah Code section
  59-12-103(2)(a)(i)(C) (statewide-uniform; deposited to the
  Transportation Investment Fund).

These three components together add up to **4.85%** -- the
"statewide rate" that applies in every Utah jurisdiction. The
Utah State Tax Commission (https://tax.utah.gov/) publishes this
as the "combined state rate" in its quarterly Sales and Use Tax
Rate publications. **All three components are encoded together
as a single state row** in the SST data file, so the inherited
:class:`SstStateModule` parser yields one ``state`` row of
``4.850%`` rather than three separate component rows.

## Local-jurisdiction landscape

On top of the 4.85% statewide composite, Utah counties, cities,
towns, and special transit districts may stack additional local
sales taxes under various enabling acts in Title 59 Chapter 12,
Parts 2 (general local options) and Parts 4-22 (specialized
local taxes -- transit, resort, county hospital, tourism short-
term lodging, etc.). Combined statewide-plus-local rates
typically fall in the **6.10% - 9.05%** range across Utah's major
metro areas (Salt Lake County, Utah County, Davis County,
Weber County). As an SST member, Utah's per-jurisdiction local
rates flow through the standard SST quarterly rate file; the
inherited :class:`SstStateModule` parser handles them without
state-specific overrides.

Per :mod:`specs.research.sst-file-format`, UT's SST rate file is
expected to use the same jurisdiction-type code mapping as MN
and WI (both empirically validated against 2026Q2 data). UT data
has not been empirically inspected at promotion time; the default
mapping is applied and documented as an assumption. A future
state maintainer should validate against an actual
``UTR<...>.csv`` file:

- ``45`` = state (single row carrying 4.850%)
- ``00`` = county
- ``01`` = city / town
- ``63`` = special district (transit, resort, etc.)

## Navajo Nation -- DEFERRED sub-state regime (do NOT model in v1)

The Navajo Nation reservation extends into northeastern Utah
(San Juan County), as well as into Arizona and New Mexico. The
**Navajo Nation imposes its own gross receipts tax under the
Navajo Nation Sales Tax (Title 24, Navajo Nation Code section
601 et seq.)**, administered by the **Navajo Tax Commission**
(https://www.navajotax.org/). For sales by **Navajo-enrolled-
member businesses** within the Navajo Nation portion of Utah,
the **Navajo Nation gross receipts tax is the only tax that
applies** -- the Utah state sales tax does NOT apply, on the
basis of long-standing federal Indian-law preemption (see e.g.
*Warren Trading Post v. Arizona Tax Commission*, 380 U.S. 685
(1965); *Central Machinery Co. v. Arizona Tax Commission*, 448
U.S. 160 (1980)). For sales by **non-tribal-member businesses**
on the reservation, Utah sales tax may apply and the legal
analysis is fact-specific.

This is structurally analogous to other deferred sub-state
regimes already documented elsewhere in the codebase:

- Louisiana parishes (separately administered local sales taxes;
  see ``specs/decisions/05-louisiana-parishes.md``)
- Colorado home-rule cities (independently administered local
  sales taxes; see ``specs/decisions/04-colorado-home-rule.md``)
- Alabama "self-administering" municipalities

**The Navajo Nation tax regime is NOT modeled in v1 of
OpenSalesTax.** Calls to ``/v1/calculate`` for addresses inside
the Navajo Nation portion of Utah will return the standard Utah
sales tax rate, which is **incorrect for sales by Navajo-
enrolled-member businesses on the reservation** (the only
correct tax is the Navajo Nation gross receipts tax, not Utah
sales tax). Operators serving Navajo Nation businesses must
apply an exemption certificate at the line-item level rather
than relying on this engine's default. A future phase may add a
:class:`SubJurisdiction` Protocol extension to first-class-model
tribal-nation tax regimes alongside parishes and home-rule
cities; this is captured for v1.0+ design.

## Taxability matrix (per Utah Code Title 59, Chapter 12)

- **General tangible personal property** -- TAXABLE at 4.85% per
  Utah Code section 59-12-103(1)(a) (the imposition statute,
  layered with section 59-12-204 and -103(2)(a)(i)(C) for the
  uniform local-option and mass-transit components).
- **Clothing** -- TAXABLE year-round at the full combined rate.
  Utah has **NO general clothing exemption** in Title 59 Chapter
  12; clothing and footwear are general tangible personal
  property and tax at the rate set by section 59-12-103. Utah
  also has **NO state sales-tax holiday** (see "Sales-tax
  holidays" below) -- there is no annual back-to-school window
  that exempts clothing.
- **Groceries (food and food ingredients)** -- TAXABLE at a
  REDUCED state combined rate of **3.00%** (instead of the
  general 4.85%) per **Utah Code section 59-12-103(2)(a)(ii)**
  (the food-and-food-ingredients reduced-rate provision in the
  imposition statute) and the parallel reduced-rate sub-
  components in section 59-12-103(2)(c) and section 59-12-204.
  The 3.00% food rate is composed of:

  - **1.75%** state portion (the reduced state rate; section
    59-12-103(2)(a)(ii)(A))
  - **1.00%** county / city local option (the standard local-
    option rate, NOT reduced for food; see Utah Code section
    59-12-204)
  - **0.25%** county option (the standard county-option rate,
    NOT reduced for food)

  **Important caveat:** the reduced-rate treatment applies ONLY
  to the state portion (1.75% vs 4.85%). The 1.00% statewide-
  uniform local-option, the 0.25% county option, and any other
  city / town / transit-district local sales taxes apply to
  groceries at their FULL local rate. The 3.00% figure is the
  composite for typical groceries-on-food-and-food-ingredients
  in jurisdictions that impose the standard 1.25% local stack;
  jurisdictions with additional local rates (transit, resort,
  etc.) apply those at their full rate on grocery sales. See
  Utah State Tax Commission Publication 25 (Sales and Use Tax
  General Information) for the worked example.

  Encoded with ``rate_modifier=Decimal("1.75")`` to record the
  reduced **state portion** rate (1.75%) -- mirroring the
  Illinois (1.000% reduced grocery rate at 35 ILCS 105/3-10),
  Missouri (1.225% reduced state grocery rate at section
  144.014), Virginia (1.000% reduced state grocery rate at
  section 58.1-611.1), and Tennessee (4.000% reduced state
  grocery rate, plus full local) patterns. The engine does not
  yet apply ``rate_modifier`` (shipped in v0.11.1); until v0.6+
  wires the modifier through, the engine over-collects the
  difference between 4.85% and 1.75% (i.e., 3.10 percentage
  points) on grocery line items in Utah. Retailers selling
  groceries in Utah should verify with the Utah State Tax
  Commission until the modifier is wired through.

  **Recent legislative history:** Utah voters had a chance to
  fully eliminate the state portion of the grocery tax via
  **Constitutional Amendment A on the November 5, 2024 general-
  election ballot**. Amendment A would have removed the Utah
  Constitution's earmark on income tax revenue (currently
  restricted to education), enabling the legislature to enact a
  companion bill (House Bill 54 of the 2023 General Session)
  that would have eliminated the 1.75% state portion of the
  grocery tax in exchange for the constitutional change.
  However, Amendment A was **struck from the 2024 ballot by
  the Utah Third District Court** (and affirmed by the Utah
  Supreme Court) on the basis that the legislature failed to
  properly publish the amendment under Utah Code section
  20A-1-201.5, leaving the constitutional language unchanged
  and the 1.75% state-portion grocery tax in effect. As of the
  module's verification date (2026-05-03), the 1.75% reduced
  state rate continues to apply; future legislative sessions
  may revisit the constitutional question and pass a follow-on
  measure. A maintainer should verify the current encoded rate
  against Utah State Tax Commission publications at each
  quarterly refresh.
- **Prescription drugs** -- EXEMPT per **Utah Code section
  59-12-104(11)**, which exempts the gross receipts from sales
  of prescription drugs (drugs sold pursuant to a written
  prescription by a person licensed to prescribe drugs for
  human use under Title 58, Chapter 17b) and certain related
  prescription medical equipment. Insulin and prescription-only
  medical oxygen are also exempt. Over-the-counter drugs sold
  WITHOUT a prescription are NOT covered by this exemption and
  remain taxable at the general rate.
- **Prepared food** -- TAXABLE at the full general 4.85% state
  rate (plus full local rate). Prepared food is expressly
  EXCLUDED from the food-and-food-ingredients reduced-rate
  treatment in section 59-12-103(2)(a)(ii); restaurant meals,
  hot foods, ready-to-eat deli items, and food sold in a
  heated state tax at the rate set by section 59-12-103(1)(a).
  Some Utah municipalities additionally impose a separate
  "restaurant tax" (Utah Code section 59-12-603, ~1.00%
  restaurant tax administered by counties); that is a separate
  non-sales-tax layer not modeled here.
- **Digital goods (products transferred electronically)** --
  TAXABLE at 4.85% per **Utah Code section 59-12-103(1)(a)**
  read together with the Utah definitions of "tangible personal
  property" and "products transferred electronically" in **Utah
  Code section 59-12-102**. Senate Bill 65 of the 2008 General
  Session amended section 59-12-102 to expressly add "products
  transferred electronically" to the sales-tax base, treating
  digital audio works, digital books, digital audiovisual
  works, and similar electronically-delivered products on equal
  footing with tangible personal property. Subsequent
  amendments through 2024 (notably 2018 changes responding to
  the *South Dakota v. Wayfair* economic-nexus regime) preserved
  the digital-products treatment. Prewritten ("canned") computer
  software delivered by any means -- tangible storage medium or
  electronic transfer -- is also taxable as TPP under the
  long-standing definition in section 59-12-102(132).

## Sales-tax holidays

**Utah has NO state sales-tax holiday in any year.** Verified
2026-05-03 against the Utah State Tax Commission's published
guidance (https://tax.utah.gov/) -- there is no annual back-to-
school holiday, no annual Energy Star / disaster-preparedness
holiday, and no other recurring state sales-tax exemption window
codified in Title 59 Chapter 12 as of the verification date.
Several legislative proposals to enact a back-to-school holiday
have been introduced in past sessions (most recently HB 296 of
the 2017 General Session) and have failed to pass.
:meth:`Utah.holidays_for` returns an empty iterator for every
year accordingly. If a future legislature enacts a holiday, this
module's :meth:`holidays_for` must be updated explicitly per
year (no extrapolation; legislative-action-required model).

## Loading

Utah's rate data loads from the SST quarterly rate file via the
inherited :class:`SstStateModule.parse_rates` machinery. The
file ships state, county, city, and special-district rows; the
inherited parser maps them through the canonical
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (assumed -- see jurisdiction-type-code mapping note
above). Boundary loading inherits the generic ``z``-record ZIP5
walker.

State maintainer: vacant -- see MAINTAINERS.md. The natural
next maintenance tasks are: (a) validating UT's SST jurisdiction-
type codes against an actual UTR file; (b) tracking the Utah
legislative session for any re-introduction of the constitutional
grocery-tax-elimination measure (Amendment A's successor); and
(c) documenting whether any local jurisdictions impose
non-state-administered local sales taxes that fall outside the
SST quarterly file (none known at verification time).

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Utah State Tax Commission guidance before relying on these
rules in production.
"""

from __future__ import annotations

from collections.abc import Iterable
from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import (
    HolidayWindow,
    ShippingRule,
    ShippingRuleSet,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# ---------------------------------------------------------------------------
# UT-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
# ASSUMPTION: UT's SST rate file uses the same jurisdiction-type
# codes as MN and WI (both empirically validated against 2026Q2
# data). This is consistent with SST's stated goal of uniform
# data formats across member states. A state maintainer should
# validate against an actual UTR<...>.csv file at next refresh.
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Static taxability matrix per Utah Code Title 59, Chapter 12.
# Categories not listed default to taxable (engine behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Utah year-round at the full "
            "combined state + local rate per Utah Code section "
            "59-12-103. Title 59 Chapter 12 contains no general "
            "clothing exemption; clothing and footwear are general "
            "tangible personal property and tax at the 4.85% "
            "statewide combined rate (4.70% state + 0.10% statewide-"
            "uniform local-option + 0.05% mass transit basic) plus "
            "any applicable city, county, or special-district local "
            "sales taxes. Utah has NO state sales-tax holiday in any "
            "year (verified 2026-05-03 against Utah State Tax "
            "Commission publications). Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("1.75"),
        notes=(
            "Food and food ingredients are TAXABLE in Utah at a "
            "REDUCED STATE rate of 1.75% (vs the general 4.85% "
            "statewide combined rate) per Utah Code section "
            "59-12-103(2)(a)(ii) (the food-and-food-ingredients "
            "reduced-rate provision in the imposition statute). The "
            "rate_modifier=Decimal('1.75') encodes the reduced STATE "
            "PORTION only; the 1.00% statewide-uniform local-option "
            "(section 59-12-204), the 0.25% county option, and any "
            "additional city / town / transit-district local sales "
            "taxes APPLY TO GROCERIES AT THEIR FULL LOCAL RATE. The "
            "composite tax on typical groceries in jurisdictions with "
            "the standard 1.25% local stack is therefore 3.00% (1.75% "
            "state + 1.25% local), per Utah State Tax Commission "
            "Publication 25 (Sales and Use Tax General Information). "
            "RECENT LEGISLATIVE HISTORY: Constitutional Amendment A "
            "on the 2024 general-election ballot would have enabled "
            "House Bill 54 (2023 General Session) to fully eliminate "
            "the 1.75% state-portion grocery tax, but Amendment A "
            "was struck from the ballot by the Utah Third District "
            "Court (affirmed by the Utah Supreme Court) for failure "
            "to properly publish the amendment under Utah Code "
            "section 20A-1-201.5; the 1.75% state-portion grocery "
            "tax continues to apply. The engine applies (as of v0.11.1) "
            "rate_modifier (shipped in v0.11.1); until then the "
            "engine over-collects the difference (3.10 percentage "
            "points) on grocery line items in Utah. Retailers "
            "selling groceries in UT should verify with the Utah "
            "State Tax Commission until v0.6+ wires the modifier "
            "through. Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT from Utah sales and use "
            "tax per Utah Code section 59-12-104(11), which exempts "
            "the gross receipts from sales of drugs sold pursuant to "
            "a written prescription by a person licensed under Title "
            "58, Chapter 17b to prescribe drugs for human use, plus "
            "insulin and prescription-only medical oxygen. The "
            "exemption also covers certain prescription medical "
            "equipment and prosthetic devices. Over-the-counter "
            "drugs sold without a prescription are NOT covered by "
            "the exemption and tax at the general 4.85% statewide "
            "combined rate even when prescribed (the controlling "
            "test is whether the drug is dispensed pursuant to a "
            "valid written prescription). Calculation only -- not "
            "legal or tax advice."
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
            "item) is TAXABLE in Utah at the general 4.85% statewide "
            "combined rate per Utah Code section 59-12-103(1)(a), "
            "plus the full local rate. Prepared food is expressly "
            "EXCLUDED from the food-and-food-ingredients reduced-"
            "rate treatment in section 59-12-103(2)(a)(ii). Some "
            "Utah counties additionally impose a separate ~1.00% "
            "RESTAURANT TAX under Utah Code section 59-12-603 (the "
            "Tourism, Recreation, Cultural, Convention, and Airport "
            "Facilities Tax Act) which stacks on top of the general "
            "sales tax for prepared food sales; that restaurant tax "
            "is a separate non-sales-tax layer and is not modeled "
            "in this module. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products (digital audio works, "
            "digital books, digital audiovisual works, ringtones, "
            "downloaded software, streaming subscriptions, and "
            "similar 'products transferred electronically') are "
            "TAXABLE in Utah at the general 4.85% statewide combined "
            "rate per Utah Code section 59-12-103(1)(a), read "
            "together with the definition of 'product transferred "
            "electronically' added to Utah Code section 59-12-102 by "
            "Senate Bill 65 of the 2008 General Session. SB 65 "
            "expressly placed digital products on equal footing with "
            "tangible personal property in the sales-tax base. "
            "Subsequent amendments through 2024 (notably the 2018 "
            "responses to the South Dakota v. Wayfair economic-nexus "
            "decision) preserved the digital-products treatment. "
            "Prewritten ('canned') computer software delivered by "
            "any means -- tangible storage medium or electronic "
            "transfer -- is also taxable as TPP under section "
            "59-12-102(132). Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Utah "
            "at the 4.85% statewide combined rate per Utah Code "
            "section 59-12-103 (the imposition statute in the Utah "
            "Sales and Use Tax Act, Title 59 Chapter 12). The 4.85% "
            "is composed of 4.70% general state rate (section "
            "59-12-103(2)(a)(i)(A)), 0.10% statewide-uniform local-"
            "option rate (section 59-12-204), and 0.05% mass transit "
            "basic rate (section 59-12-103(2)(a)(i)(C)). City, "
            "county, and special-district local sales taxes stack "
            "on top via the SST quarterly rate file; combined "
            "rates typically fall in the 6.10%-9.05% range across "
            "Utah's major metro areas. NAVAJO NATION CAVEAT: sales "
            "by Navajo-enrolled-member businesses inside the Navajo "
            "Nation portion of San Juan County are subject ONLY to "
            "the Navajo Nation gross receipts tax (Title 24, Navajo "
            "Nation Code section 601 et seq.), not Utah sales tax "
            "-- this engine does NOT model that sub-state regime "
            "in v1; operators serving Navajo Nation businesses must "
            "apply an exemption certificate at the line-item level. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}


class Utah(SstStateModule):
    """Utah state module (tier 1, SST member).

    Inherits the generic SST rate / boundary parser from
    :class:`SstStateModule`. Overrides the default taxability
    matrix and the jurisdiction-type code mapping with UT-specific
    research grounded in Utah Code Title 59 Chapter 12. Utah has
    NO state sales-tax holiday in any year -- :meth:`holidays_for`
    returns an empty iterator (per the inherited base) for every
    year.

    See the module docstring for: (a) the 4.85% statewide rate
    composition (4.70% + 0.10% + 0.05%), (b) the 1.75% reduced
    state grocery rate encoded via ``rate_modifier``, and
    (c) the Navajo Nation deferred sub-state regime caveat.
    """

    state_abbrev: str = "UT"
    state_name: str = "Utah"
    state_fips: str = "49"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Override the base-class defaults with UT-specific data.
    jurisdiction_types: dict[str, str] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated UT city-name table; fall back to placeholder."""
        from opensalestax.states.ut_names import city_name as _ut_city

        if authority_type == "city":
            friendly = _ut_city(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Utah has NO state sales-tax holiday in any year.

        Verified 2026-05-03 against Utah State Tax Commission
        publications (https://tax.utah.gov/) -- there is no annual
        back-to-school holiday, no annual Energy Star / disaster-
        preparedness holiday, and no other recurring state sales-
        tax exemption window codified in Title 59 Chapter 12 as
        of the verification date. Several legislative proposals
        to enact a back-to-school holiday have been introduced in
        past sessions (most recently HB 296 of the 2017 General
        Session) and have failed to pass.

        Returns an empty iterator unconditionally (no
        legislatively-enacted holiday for any year). If a future
        legislature enacts a holiday, this method must be updated
        explicitly per year (no extrapolation; legislative-action-
        required model).
        """
        del year
        return iter(())

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return UT's shipping rule.

        Separately stated transportation charges are excluded from
        "purchase price"; bundled transportation is taxable.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.EXEMPT_IF_SEPARATELY_STATED,
            citation="UCA 59-12-103",
        )


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.utah`` registers
# Utah under "UT" in the state registry.
_PROTOCOL_CHECK: StateModule = Utah()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# rate. Utah's RateRow emits ``rate_pct=Decimal("4.850")`` from
# the SST file; the constant below is purely documentary so future
# readers can grep the codebase for the rate.
UTAH_GENERAL_RATE_PCT: Decimal = Decimal("4.850")

# Documentary constant for the reduced state-portion grocery rate
# (1.75%) per Utah Code section 59-12-103(2)(a)(ii). Encoded into
# the groceries TaxabilityRule's ``rate_modifier`` field; this
# constant exists so future readers can grep for the value.
UTAH_GROCERY_STATE_RATE_PCT: Decimal = Decimal("1.75")

UTAH = register(Utah())
