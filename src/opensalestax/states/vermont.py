# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Vermont state module (tier 1, SST member).

VT is a Streamlined Sales Tax full member (verified 2026-05-03
against the SST member roster on streamlinedsalestax.org). The
statewide rate is **6.0%** per **Vt. Stat. Ann. tit. 32, section
9771** (the imposition statute in the Vermont Sales and Use Tax
Act, Title 32, Chapter 233). The 6% rate has been in effect since
**October 1, 2003** -- raised from 5% by Act 68 of the 2003
Legislative Session as part of the education-funding reform
package. Prior maintainers: this rate has been stable for 20+
years; no rate change is currently in the legislative pipeline.

## RATE COMPOSITION -- STATE BASE + OPTIONAL 1% LOCAL OPTION

Vermont's local-jurisdiction landscape is unusually simple:

- The **state** imposes the 6% general sales tax under 32 V.S.A.
  section 9771.
- **Counties impose NO sales tax.** Vermont has 14 counties, none
  of which have general sales-tax authority.
- **Municipalities (cities and towns) MAY adopt a Local Option
  Sales Tax (LOST) of EXACTLY 1%** under **24 V.S.A. section 138**
  (originally enacted by Act 60 of 1997, the Equal Educational
  Opportunity Act, expanded by Act 68 of 2003, and amended in
  subsequent sessions). The local option is fixed at 1% by
  statute -- a municipality cannot adopt 0.5% or 1.5%; it is
  either 0% (the default) or exactly 1%. Adoption requires both
  charter authorization and a binding voter referendum; a
  municipality opting in collects the additional 1% on the same
  base as the state 6% sales tax (with the same exemptions).
  Combined rates in opted-in municipalities are therefore
  **EXACTLY 7.0%**; combined rates in non-opted-in municipalities
  are exactly the 6% state rate.

  As of 2026 approximately **17 Vermont municipalities** have
  opted in, including the larger commercial centers: **Burlington,
  South Burlington, Williston, Colchester, Essex Junction,
  Winooski, Stowe, Brattleboro, Manchester, Killington, Dover,
  Wilmington, St. Albans Town, Rutland Town, Middlebury,
  Montpelier, and Brandon** (the precise list shifts as towns
  adopt or rescind by referendum; the authoritative current list
  is the Vermont Department of Taxes "Municipalities with a Local
  Option Tax" page at
  https://tax.vermont.gov/business/lot/municipalities). The
  Department of Taxes administers and remits the local option to
  the adopting municipality (less a small administrative fee
  retained by the state) -- the seller remits a single combined
  amount to the Department, which makes Vermont's local-tax
  collection mechanically simpler than home-rule states like
  Colorado or independent-locals states like Alabama.

- A separate **1% Local Option Meals and Rooms Tax** and a
  separate **1% Local Option Alcoholic Beverages Tax** are
  authorized by the same 24 V.S.A. section 138, layered on top
  of the state 9% Meals and Rooms Tax (32 V.S.A. chapter 225)
  and the state 10% Alcoholic Beverages Tax. These are **NOT
  general sales taxes** -- they apply to a defined category list
  outside this engine's scope. Documented for completeness so a
  Burlington restaurant integrator knows the engine's general-
  rate calculation does not cover meals/rooms/alcohol; those
  layers are handled by separate non-sales-tax tables.

## v1 LOADING POSTURE -- STATE BASE ONLY

The municipality-level Local Option Sales Tax is **deferred to
per-municipality data ingestion**. The SST quarterly rate file
ships VT rate rows that include the state 6% row plus per-
municipality 1% rows for opted-in towns; the inherited
:class:`SstStateModule.parse_rates` machinery will pick these up
once an empirical capture of a VT SST file confirms the
jurisdiction-type code mapping. Until then v1 ships VT at the
state-only 6% rate -- which is the legally-collectable rate at
the dominant case (the ~230 of ~247 Vermont municipalities that
have NOT opted in to LOST). For the LOST-adopted edge case the
v1 calculation UNDER-collects by 1 percentage point on
transactions in those 17 municipalities; the seller in such a
municipality would need to manually collect the additional 1% to
remain compliant with 24 V.S.A. section 138.

This is the same deferred-locals posture used by NJ (UEZ / Salem
County) and is consistent with the Phase 6/7 ratchet's "ship
state base; per-locality work follows" pattern. A future
contribution can promote per-municipality LOST loading once the
SST file's VT-specific jurisdiction codes are validated empirically.

## TAXABILITY MATRIX (per Vt. Stat. Ann. tit. 32, Chapter 233)

- **General tangible personal property** -- TAXABLE at 6% per
  **Vt. Stat. Ann. tit. 32, section 9771** (the imposition
  statute) and the definition of "tangible personal property"
  in **Vt. Stat. Ann. tit. 32, section 9701(7)**.
- **Clothing** -- **EXEMPT** per **Vt. Stat. Ann. tit. 32,
  section 9741(45)**. Vermont is one of a small set of states
  that broadly exempts clothing and footwear from sales tax,
  joining **Pennsylvania, Massachusetts, Minnesota, New Jersey,
  and Rhode Island** in the broad-clothing-exemption club. The
  VT exemption applies year-round; there is no per-item dollar
  cap and no date restriction (contrast with NY's $110-per-item
  threshold and MA's $175-per-item threshold). The exemption
  excludes certain enumerated items: **clothing accessories**
  (jewelry, handbags, briefcases, watches, etc. -- general TPP);
  **sport / recreational equipment**; **protective equipment**
  for use other than as everyday clothing; **fur clothing** (still
  exempt under the general 32 V.S.A. 9741(45) exemption per the
  Department of Taxes Reg. 1.9741(45) -- VT does NOT impose a
  separate fur-clothing surtax of the kind NJ has). See VT Dept.
  of Taxes Reg. 1.9741(45) for the precise exclusions list.
- **Groceries (food and food ingredients)** -- EXEMPT per
  **Vt. Stat. Ann. tit. 32, section 9741(13)**. The exemption
  tracks the Streamlined Sales Tax Project's uniform definition
  of "food and food ingredients" and excludes candy, soft drinks,
  dietary supplements, and prepared food (those remain taxable
  at the 6% state rate and at the 1% local option in adopting
  municipalities). NOTE: Vermont also imposes a **separate 6%
  Sugar-Sweetened Beverage tax** on certain soft drinks under
  32 V.S.A. section 9242 (added by Act 18 of 2018) -- documented
  for completeness but outside the general sales-tax base.
- **Prescription drugs** -- EXEMPT per **Vt. Stat. Ann. tit. 32,
  section 9741(2)**. The exemption covers drugs sold pursuant to
  a written prescription by a licensed practitioner. Over-the-
  counter (non-prescription) drugs are NOT covered by this
  exemption and remain taxable at the 6% state rate.
- **Prepared food** -- TAXABLE under the **Vermont Meals and
  Rooms Tax at 9%** (32 V.S.A. chapter 225, section 9241), NOT
  the 6% sales tax. Prepared food (restaurant meals, hot deli
  items, ready-to-eat foods) is expressly excluded from the
  food-and-food-ingredients exemption in 32 V.S.A. 9741(13) AND
  is brought into the higher 9% Meals and Rooms Tax base by
  32 V.S.A. 9202(10). The general sales-tax engine models the
  6% rate; integrators selling prepared food in Vermont should
  apply the 9% Meals and Rooms Tax instead. For the v1 sales-tax
  calculation we mark prepared food as TAXABLE at the 6% rate as
  a conservative default -- a caller can override per-line if the
  transaction is clearly a prepared-food sale subject to the 9%
  rate. The 9% Meals and Rooms Tax is a separate non-general-
  sales-tax base and is not modeled by this engine in v1.
- **Digital goods (specified digital products)** -- TAXABLE at
  6% per **Vt. Stat. Ann. tit. 32, section 9701(31)(B)** (the
  defined-term cross-reference to "specified digital products"
  in the SST uniform definitions), as added by **H. 528 of the
  2014 Legislative Session (Act 174 of 2014)** with an
  effective date of **July 1, 2015**. Section 9701(31)(B) brings
  digital audio works, digital audiovisual works, digital books,
  and ringtones (delivered electronically -- i.e. obtained by
  means other than tangible storage media) into the sales-tax
  base, whether transferred with a permanent right of use or
  with less-than-permanent use (subscription / conditional
  access). Prewritten ("canned") computer software delivered by
  any means is also taxable as TPP under the long-standing
  definition in 32 V.S.A. section 9701(7). Custom software
  developed for a specific customer is NOT taxable per
  Department of Taxes Reg. 1.9701(7).

## SALES TAX HOLIDAYS

**NONE.** Vermont has **NO sales-tax holiday** in any year and
none has been enacted by the General Assembly. The
:meth:`Vermont.holidays_for` method returns the empty iterator
for every year (mirrors NJ, NE, DC, ID, IN, ND, MI, KY, NV, NC).
Verified 2026-05-03 against the Vermont Department of Taxes
Sales Tax landing page (https://tax.vermont.gov/business/sales-
and-use-tax) -- no holiday notice for 2024, 2025, 2026, or any
future year -- and against the Sales Tax Institute holiday
compendium for cross-reference.

If the General Assembly enacts a holiday in a future session,
the per-state maintainer should add the explicit year's
:class:`HolidayWindow` to ``holidays_for`` (do NOT extrapolate
from any neighboring state's holiday framework -- a future VT
holiday would be defined by its own enabling statute with its
own dates, scope, and per-item cap).

## LOADING

Vermont's rate data loads from the SST quarterly rate file via
the inherited :class:`SstStateModule.parse_rates` machinery. Per
:mod:`specs.research.sst-file-format`, the VT SST rate file is
presumed to use the same jurisdiction-type code mapping that MN
and WI validate at 2026Q2 (codes ``00`` county, ``01`` city,
``45`` state, ``63`` district). The MN/WI codes are the SST
empirical default; if a future quarterly capture of a Vermont
rate file shows different codes, override
``jurisdiction_types`` on this subclass at that time. Until
then we inherit the
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping. In Vermont's case the state-level row (code ``45``) is
the dominant expected match; per-municipality 1% LOST rows
(code ``01``) for the ~17 opted-in towns will be loaded by the
inherited parser once boundary data ties them to ZIPs.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Vermont Department of Taxes guidance before relying on these
rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Vermont taxability matrix per Vt. Stat. Ann. tit. 32, Chapter 233.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=False,
        notes=(
            "Clothing and footwear are EXEMPT in Vermont per Vt. Stat. "
            "Ann. tit. 32, section 9741(45). VT is one of a small set "
            "of states with a broad year-round clothing exemption "
            "(others: PA, MA, MN, NJ; NY and RI use threshold-based "
            "exemptions). The exemption has no per-item dollar cap "
            "and no date restriction. Statutory exclusions from the "
            "exemption (i.e. items that REMAIN taxable at 6%): "
            "clothing accessories (jewelry, handbags, briefcases, "
            "watches, similar items -- general TPP); sport / "
            "recreational equipment; and protective equipment for "
            "use other than as everyday clothing. See VT Department "
            "of Taxes Reg. 1.9741(45) for the precise exclusions "
            "list. Unlike NJ, Vermont does NOT impose a separate "
            "fur-clothing surtax -- fur clothing remains exempt under "
            "the general 9741(45) exemption. Calculation only -- "
            "not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients are EXEMPT in Vermont per "
            "Vt. Stat. Ann. tit. 32, section 9741(13). The exemption "
            "tracks the Streamlined Sales Tax Project's uniform "
            "definition of 'food and food ingredients' and excludes "
            "candy, soft drinks, dietary supplements, and prepared "
            "food (those remain taxable at the 6% state rate and at "
            "the 1% local option in adopting municipalities; "
            "prepared food is also brought into the separate 9% "
            "Vermont Meals and Rooms Tax base under 32 V.S.A. "
            "chapter 225). NOTE: Vermont also imposes a separate "
            "6% Sugar-Sweetened Beverage tax on certain soft drinks "
            "under 32 V.S.A. section 9242 (added by Act 18 of 2018) "
            "-- documented for completeness but outside the general "
            "sales-tax base. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Vermont per Vt. Stat. "
            "Ann. tit. 32, section 9741(2). The exemption covers "
            "drugs sold pursuant to a written prescription by a "
            "licensed practitioner. Over-the-counter (non-"
            "prescription) drugs are NOT covered by the exemption "
            "and remain taxable at the 6% state rate (and at the 1% "
            "local option in adopting municipalities). Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, "
            "ready-to-eat foods) is expressly EXCLUDED from the "
            "food-and-food-ingredients exemption in Vt. Stat. Ann. "
            "tit. 32, section 9741(13) and is therefore TAXABLE in "
            "Vermont. NOTE: prepared food in Vermont is principally "
            "taxed under the separate 9% Vermont Meals and Rooms "
            "Tax (32 V.S.A. chapter 225, section 9241), NOT the 6% "
            "general sales tax. Adopting municipalities also impose "
            "a 1% Local Option Meals and Rooms Tax under 24 V.S.A. "
            "section 138, layered on top of the state 9% Meals and "
            "Rooms Tax. The general sales-tax engine models the 6% "
            "rate as a conservative default for prepared food line "
            "items; integrators selling prepared food in Vermont "
            "should apply the 9% Meals and Rooms Tax (plus 1% local "
            "option in adopting municipalities) outside this engine "
            "for correct collection. Calculation only -- not legal "
            "or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Vermont at "
            "the 6% state rate per Vt. Stat. Ann. tit. 32, section "
            "9701(31)(B) (the defined-term cross-reference to "
            "'specified digital products' in the SST uniform "
            "definitions), as added by H. 528 of the 2014 "
            "Legislative Session (Act 174 of 2014) with an effective "
            "date of July 1, 2015. Section 9701(31)(B) brings "
            "digital audio works, digital audiovisual works, digital "
            "books, and ringtones (delivered electronically -- i.e. "
            "obtained by means other than tangible storage media) "
            "into the sales-tax base, whether transferred with a "
            "permanent right of use or with less-than-permanent use "
            "(subscription / conditional access). Prewritten "
            "('canned') computer software delivered by any means "
            "is also taxable as tangible personal property under "
            "32 V.S.A. section 9701(7); custom software developed "
            "for a specific customer is NOT taxable per VT "
            "Department of Taxes Reg. 1.9701(7). Calculation only "
            "-- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Vermont at 6% per Vt. Stat. Ann. tit. 32, section 9771 "
            "(the imposition statute in the Vermont Sales and Use "
            "Tax Act, Title 32 Chapter 233) and Vt. Stat. Ann. tit. "
            "32, section 9701(7) (definition of tangible personal "
            "property). The 6% rate has been in effect since "
            "October 1, 2003 (raised from 5% by Act 68 of 2003). "
            "Local jurisdictions: counties impose NO sales tax; "
            "incorporated municipalities (cities and towns) MAY "
            "adopt a Local Option Sales Tax (LOST) of EXACTLY 1% "
            "under 24 V.S.A. section 138 (originally Act 60 of "
            "1997, expanded by Act 68 of 2003). The local option is "
            "fixed at 1% by statute (a town adopts it or does not -- "
            "no other rate is permitted). Approximately 17 of "
            "Vermont's ~247 incorporated municipalities have opted "
            "in (Burlington, South Burlington, Williston, "
            "Brattleboro, Stowe, Manchester, Killington, Dover, "
            "Wilmington, Montpelier, and others); combined rates in "
            "those municipalities are EXACTLY 7.0%, and combined "
            "rates everywhere else in Vermont are exactly 6.0%. "
            "Per-municipality LOST rows flow through the SST "
            "quarterly rate file via the inherited parser. The "
            "separate 1% Local Option Meals and Rooms Tax and 1% "
            "Local Option Alcoholic Beverages Tax (also under 24 "
            "V.S.A. section 138) layer on top of the state 9% Meals "
            "and Rooms Tax / 10% Alcoholic Beverages Tax and are "
            "NOT general sales taxes -- outside this engine's scope. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}


class Vermont(SstStateModule):
    """Vermont state module (tier 1, SST member; state-only baseline + 1% LOST).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS) and the taxability
    matrix. Rate parsing, boundary parsing, special cases, and the
    empty-holidays default are all inherited.

    Vermont is mechanically simple: 6% state rate per 32 V.S.A.
    9771 (in effect since 2003-10-01), plus an OPTIONAL exactly-1%
    Local Option Sales Tax under 24 V.S.A. 138 in approximately 17
    opted-in municipalities (Burlington, South Burlington,
    Williston, Brattleboro, Stowe, etc.). Combined rates are
    therefore EXACTLY 6.0% (most of Vermont) or EXACTLY 7.0%
    (LOST-adopted municipalities) -- no fractional rates exist.

    The Local Option Sales Tax is **deferred to per-municipality
    data ingestion** in v1; the inherited SST parser will pick up
    the per-municipality rows once the VT SST file's jurisdiction-
    type codes are empirically validated. Until then, v1 ships
    Vermont at the state-only 6% rate (the legally-collectable rate
    at the dominant case of non-opted-in municipalities). For LOST
    municipalities the v1 calculation under-collects by 1
    percentage point; sellers in those towns must manually collect
    the additional 1% to remain compliant with 24 V.S.A. 138.

    Clothing is BROADLY EXEMPT in Vermont year-round per 32 V.S.A.
    9741(45) (VT joins PA, MA, MN, NJ in the broad-exemption club).
    No per-item dollar cap; no date restriction.

    Vermont has NO sales-tax holiday in any year and none is
    currently scheduled (verified 2026-05-03 against the Vermont
    Department of Taxes). The inherited empty-iterator default
    from :class:`SstStateModule.holidays_for` is correct.

    Prepared food in Vermont is principally taxed under the
    separate 9% Meals and Rooms Tax (32 V.S.A. chapter 225), NOT
    the 6% general sales tax modeled here. The general sales-tax
    matrix marks prepared food as taxable at 6% as a conservative
    default; integrators selling prepared food in Vermont should
    apply the 9% rate outside this engine.
    """

    state_abbrev: str = "VT"
    state_name: str = "Vermont"
    state_fips: str = "50"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.vermont`` registers
# Vermont under "VT" in the state registry.
_PROTOCOL_CHECK: StateModule = Vermont()
del _PROTOCOL_CHECK

# Module-level constants for callers / future maintainers. The actual
# rate that flows into the engine comes from the SST quarterly file
# via the inherited parser; these constants are documentary anchors
# for the 6% statewide rate and the exactly-1% Local Option Sales Tax
# authorized by 24 V.S.A. 138.
VERMONT_STATEWIDE_RATE_PCT: Decimal = Decimal("6.000")
VERMONT_LOCAL_OPTION_RATE_PCT: Decimal = Decimal("1.000")
VERMONT_COMBINED_RATE_LOST_PCT: Decimal = Decimal("7.000")

VERMONT = register(Vermont())
