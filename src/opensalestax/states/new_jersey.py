# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""New Jersey state module (tier 1, SST member).

NJ is a Streamlined Sales Tax member (verified 2026-05-03 against
the SST member roster on streamlinedsalestax.org). The statewide
rate is **6.625%** per **N.J.S.A. section 54:32B-3**, the rate
having been reduced from 7% to 6.875% effective **January 1,
2017** and then to its current **6.625%** effective **January 1,
2018** by P.L. 2016, c. 57 (the Transportation Trust Fund
reauthorization compromise that traded a sales-tax cut for a
gas-tax increase).

## RATE COMPOSITION -- STATEWIDE-ONLY BASELINE

Unlike most states, **New Jersey imposes NO general local
(municipal or county) sales tax**. The 6.625% statewide rate is
the combined rate at every NJ address EXCEPT:

- **Urban Enterprise Zones (UEZs)** -- see deferral discussion
  immediately below.
- **Salem County** -- see deferral discussion immediately below.
- **Atlantic City Luxury Tax** -- a SEPARATE tax on hotels,
  restaurants, alcohol, and certain entertainment within Atlantic
  City; NOT part of the general sales tax. Documented for
  completeness but outside this module's scope (the engine
  models general state sales tax, not city-luxury / occupancy
  / amusement levies).

Outside the three exceptions above, the SST quarterly rate file
ships only a single state-level rate row for NJ; per-county /
per-city add-on rows are absent because the statute imposes no
such add-ons. A v1 caller calculating tax on a typical NJ
transaction (anywhere outside a UEZ-certified business, outside
Salem County, and not subject to Atlantic City luxury tax) gets
the correct combined 6.625% rate from the inherited
:class:`SstStateModule` parser without further configuration.

## URBAN ENTERPRISE ZONES (UEZ) -- HALF-RATE -- DEFERRED IN v1

**N.J.S.A. section 52:27H-80** (the Urban Enterprise Zones Act,
P.L. 1983, c. 303, as amended) authorizes qualified retail
purchases at certified UEZ businesses to be taxed at **HALF the
statewide rate (3.3125%)** rather than the full 6.625%. The
program is administered by the New Jersey Department of
Community Affairs (DCA) and the Division of Taxation; eligible
sellers obtain a UZ-2 Urban Enterprise Zone Business
Certification, and qualifying sales of tangible personal property
(with statutory category exclusions for motor vehicles, certain
energy, and specified other items) collect tax at the reduced
3.3125% rate.

Approximately **32 New Jersey municipalities** have UEZ
designations as of the 2026 program year (the list has shifted
over time as new zones were authorized and as some original
zones reached their statutory sunset / renewal milestones; the
current authoritative list is maintained by the NJ DCA at
https://www.nj.gov/dca/divisions/dhcr/offices/ueztaxinfo.html).
Notable UEZ municipalities include: Asbury Park, Bayonne,
Bridgeton, Camden, Carteret, East Orange, Elizabeth, Gloucester
City, Guttenberg, Hillside, Irvington, Jersey City, Kearny,
Lakewood, Long Branch, Millville, Mount Holly, New Brunswick,
Newark, North Bergen, Orange, Passaic, Paterson, Pemberton,
Perth Amboy, Phillipsburg, Plainfield, Pleasantville, Roselle,
Trenton, Union City, Vineland, West New York, and Wildwood.

**v1 decision: the UEZ reduced rate is NOT modeled.** The reduced
rate is **business-eligibility-restricted** (it depends on
whether the SELLER holds a current UZ-2 certification) and
**category-restricted** (motor vehicles, certain energy, and
specified items are excluded by statute even at certified UEZ
sellers). This makes UEZ structurally similar to Nevada's
National Guard Sales Tax Holiday (NRS 372.7282) -- a
non-geographic eligibility dimension that the engine does not
currently model. Encoding UEZ as a geographic rate override
keyed by ZIP / municipality would systematically OVER-collect on
non-certified sellers operating within UEZ boundaries (the
overwhelming majority of sellers in any UEZ municipality are NOT
UEZ-certified) and UNDER-collect on the category-excluded
purchases at certified sellers.

The conservative correctness posture is to ship NJ at the full
6.625% statewide rate and document the UEZ exception
prominently. A future contribution -- gated on a per-seller
exemption / certification model landing in the calculation API
(similar to the Phase 5 exemption-cert feature reserved in the
constitution / current-state roadmap) -- can re-enable the UEZ
reduced rate as a seller-class-restricted modifier rather than
a geographic rate override.

This decision matches the same correctness-over-coverage posture
applied to Nevada's National Guard holiday: a missing UEZ
reduction over-charges a buyer at a certified UEZ seller (which
the buyer can correct via the Division of Taxation refund
process under N.J.S.A. 54:32B-20) but a misapplied UEZ reduction
under-collects at every non-certified seller within UEZ
boundaries (which the seller would have to make up out of its
own funds plus penalties under N.J.S.A. 54:32B-14). Under-
collection on a non-eligible seller is the more harmful failure
mode.

## SALEM COUNTY -- HALF-RATE -- DEFERRED IN v1

**N.J.S.A. section 54:32B-8.45** authorizes qualified retail
sales of tangible personal property occurring at retail stores
in **Salem County** (in southern NJ, on the Delaware River
across from Wilmington) to be taxed at **HALF the statewide rate
(3.3125%)**. The Salem County reduced rate exists to keep New
Jersey retailers competitive with no-sales-tax Delaware retailers
just across the Delaware Memorial Bridge. The reduction applies
to substantially the same category of qualifying retail sales
as the UEZ reduction (statutory exclusions for motor vehicles,
energy, restaurant meals, etc.).

**v1 decision: the Salem County reduced rate is NOT modeled.**
Same rationale as the UEZ deferral above: the reduced rate is
seller-eligibility-restricted (the seller must be a "retail
store" in the qualifying category, not, e.g., a service
provider or wholesale operation) and category-restricted (the
exclusion list mirrors the UEZ exclusion list). A geographic
override keyed by Salem County ZIPs would over- or under-collect
on the eligibility / category edges. This is the same
deferred-locals pattern used by NV (county add-ons), LA
(parishes), CO (home-rule cities), and SC (county-option taxes)
-- see ``specs/decisions/05-louisiana-parishes.md`` for the
trade-off discussion (Option A: state-only with prominent
deferral) that applies equally here.

A v1 caller calculating tax on a Salem County NJ address will
collect the full 6.625% statewide rate -- which is the legally-
collectable rate at the dominant case (non-qualifying sellers,
non-qualifying categories, services, etc.). For the
qualifying-retail edge case at a Salem County retail store, the
v1 calculation OVER-collects by the 3.3125 percentage points; a
buyer entitled to the reduction obtains it by refund through
the Division of Taxation under N.J.S.A. 54:32B-20.

## ATLANTIC CITY LUXURY TAX -- OUT OF SCOPE

**N.J.S.A. section 40:48-8.15 et seq.** (P.L. 1981, c. 77, as
amended) authorizes Atlantic City to impose a **3% Atlantic City
Luxury Tax** on hotel room rentals, restaurant meals, alcoholic
beverages, cover charges, ticket sales for shows / sporting
events / amusements, and certain other "luxury" expenditures
within the city limits. This is a SEPARATE municipal tax that
stacks ON TOP of the 6.625% state sales tax for items in its
defined category list (and state law also imposes an additional
9% ACTRA -- Atlantic City Tourism Promotion Fee -- on hotel
rooms, layered as well).

The Atlantic City Luxury Tax is a city-imposed amusement /
hospitality / luxury tax, NOT a general sales tax. It applies to
a defined enumerated category list rather than to general
tangible personal property. The OpenSalesTax engine models
general state sales tax (and state-permitted local sales-tax
add-ons that share the sales-tax base); it does NOT model
amusement / occupancy / luxury / restaurant / hotel taxes that
operate outside the sales-tax base. Atlantic City luxury tax is
documented here for completeness so that an integrator selling
hotel-room or restaurant-meal transactions in Atlantic City
knows the engine's general-rate calculation is incomplete for
those specific category transactions in that specific
geography. A v1 caller calculating general TPP tax for an
Atlantic City address gets the correct 6.625% state rate; a
v1 caller calculating tax on a hotel-room rental in Atlantic
City needs to add the 3% luxury tax + 9% ACTRA outside this
engine.

## TAXABILITY MATRIX (per N.J.S.A. Title 54, Chapter 32B)

- **General tangible personal property** -- TAXABLE at 6.625%
  per **N.J.S.A. section 54:32B-3** (the imposition statute) and
  the definition of "tangible personal property" in **N.J.S.A.
  section 54:32B-2(g)**.
- **Clothing** -- **EXEMPT** per **N.J.S.A. section 54:32B-8.4**.
  New Jersey is one of a small set of states that broadly exempts
  clothing and footwear from sales tax (the others being
  Pennsylvania, Massachusetts, Minnesota, Vermont, and -- with
  thresholds -- New York and Rhode Island). The NJ exemption
  applies year-round; there is no per-item dollar cap and no
  date restriction (contrast with NY's $110-per-item threshold
  and MA's $175-per-item threshold). The exemption excludes
  certain enumerated items: fur clothing (taxable per N.J.S.A.
  section 54:32B-3 plus a separate fur-clothing surtax),
  clothing accessories (jewelry, handbags, briefcases, watches,
  etc. -- general TPP), sport / recreational equipment, and
  protective equipment for use other than as everyday clothing
  (see N.J.S.A. 54:32B-8.4 for the precise exclusions list).
- **Groceries (food and food ingredients)** -- EXEMPT per
  **N.J.S.A. section 54:32B-8.2**. The exemption tracks the
  Streamlined Sales Tax Project's uniform definition of "food
  and food ingredients" and excludes candy, soft drinks,
  dietary supplements, and prepared food (those remain taxable
  at the 6.625% rate).
- **Prescription drugs** -- EXEMPT per **N.J.S.A. section
  54:32B-8.1**. The exemption covers drugs sold pursuant to a
  written prescription by a licensed practitioner; over-the-
  counter (non-prescription) drugs are NOT covered by this
  exemption and remain taxable at the 6.625% rate.
- **Prepared food** -- TAXABLE at 6.625%. Prepared food
  (restaurant meals, hot deli items, ready-to-eat foods) is
  expressly excluded from the food-and-food-ingredients
  exemption in N.J.S.A. 54:32B-8.2 and taxes at the general
  rate set by N.J.S.A. 54:32B-3.
- **Digital goods (specified digital products)** -- TAXABLE at
  6.625% per **N.J.S.A. section 54:32B-3(a)** (the imposition
  statute) as amended by **P.L. 2011, c. 49** (effective May 1,
  2011), which extended the sales-tax base from "tangible
  personal property" to "tangible personal property or a
  specified digital product." The defined term "specified
  digital product" is at **N.J.S.A. section 54:32B-2(zz)** and
  covers digital audio works, digital audiovisual works, and
  digital books delivered electronically (i.e. obtained by means
  other than tangible storage media), whether transferred with a
  permanent right of use or with less-than-permanent use. Note:
  N.J.S.A. section 54:32B-8.56 (added by the same P.L. 2011,
  c. 49) is a separate EXEMPTION for prewritten software
  delivered electronically AND used directly and exclusively in
  the conduct of the purchaser's business -- a narrow business-
  use exemption that doesn't change the general taxability of
  consumer-facing digital goods. Prewritten ("canned") computer
  software delivered by any means to a consumer is taxable as
  TPP under the long-standing definition in N.J.S.A.
  54:32B-2(g).

## SALES TAX HOLIDAYS

**None currently; previously held in 2022 and 2023 only, then
repealed.** New Jersey enacted an annual "Back-to-School Sales
Tax Holiday" by **P.L. 2022, c. 21** (the FY2023 budget bill),
codified at the now-repealed N.J.S.A. section 54:32B-8.66.
The holiday ran for a 10-day window in late August / early
September of 2022 and 2023, exempting clothing/footwear, school
supplies, school art supplies, school instructional materials,
sport or recreational equipment, and computers (with a $3,000
per-item cap on computers and a $1,000 per-item cap on
recreational equipment) from the 6.625% sales tax.

The Legislature **REPEALED** the holiday by **P.L. 2024, c. 19**
(Assembly Substitute A4702, signed by Governor Murphy on
2024-06-28 as part of the FY2025 budget package), with the
repeal taking immediate effect -- before the 2024 holiday window
would have run. The repealing chapter struck N.J.S.A. section
54:32B-8.66 from the books and concurrently phased out the
zero-emission-vehicle exemption that had been at section
54:32B-8.55. As a result, **NJ has held no sales-tax holiday
in 2024, 2025, or 2026, and none is currently scheduled for any
future year** (verified 2026-05-03 against the New Jersey
Division of Taxation Sales Tax Holiday landing page and the
Sales Tax Handbook 2026 compendium).

The :meth:`NewJersey.holidays_for` method therefore returns the
empty iterator for **every** year (mirroring NE, DC, ID, IN). If
the Legislature re-enacts a sales-tax holiday in a future
session, the per-state maintainer should add the explicit
year's :class:`HolidayWindow` to ``holidays_for`` (do NOT
extrapolate from the 2022/2023 history -- a re-enactment would
likely have different dates, scope, and per-item caps than the
repealed framework).

## LOADING

New Jersey's rate data loads from the SST quarterly rate file
via the inherited :class:`SstStateModule.parse_rates` machinery.
The SST file ships only the state-level row (no county / city
rows because NJ levies no general local sales tax outside the
two deferred reduced-rate exceptions documented above). Until
an empirical capture of an NJ SST file confirms the
jurisdiction-type code mapping, the inherited
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (00 county / 01 city / 45 state / 63 district) applies
-- in NJ's case the state-level row (code 45) is the only
expected match.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current New
Jersey Division of Taxation guidance before relying on these
rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# New Jersey taxability matrix per N.J.S.A. Title 54, Chapter 32B.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=False,
        notes=(
            "Clothing and footwear are EXEMPT in New Jersey per "
            "N.J.S.A. section 54:32B-8.4. NJ is one of a small set "
            "of states with a broad year-round clothing exemption "
            "(others: PA, MA, MN, VT; NY and RI have threshold-based "
            "exemptions). The exemption has no per-item dollar cap "
            "and no date restriction. Statutory exclusions from the "
            "exemption (i.e. items that REMAIN taxable): fur "
            "clothing (also subject to a separate fur-clothing "
            "surtax); clothing accessories (jewelry, handbags, "
            "briefcases, watches, similar items -- general TPP); "
            "sport / recreational equipment; and protective "
            "equipment for use other than as everyday clothing. See "
            "N.J.S.A. 54:32B-8.4 for the precise exclusions list. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients are EXEMPT in New Jersey per "
            "N.J.S.A. section 54:32B-8.2. The exemption tracks the "
            "Streamlined Sales Tax Project's uniform definition of "
            "'food and food ingredients' and excludes candy, soft "
            "drinks, dietary supplements, and prepared food (those "
            "remain taxable at the 6.625% statewide rate). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in New Jersey per "
            "N.J.S.A. section 54:32B-8.1. The exemption covers "
            "drugs sold pursuant to a written prescription by a "
            "licensed practitioner. Over-the-counter (non-"
            "prescription) drugs are NOT covered by the exemption "
            "and remain taxable at the 6.625% statewide rate. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, "
            "ready-to-eat foods) is TAXABLE in New Jersey at the "
            "6.625% statewide rate. The food-and-food-ingredients "
            "exemption in N.J.S.A. section 54:32B-8.2 expressly "
            "excludes prepared food (along with candy, soft drinks, "
            "and dietary supplements); restaurant meals and ready-"
            "to-eat foods tax at the general rate set by N.J.S.A. "
            "section 54:32B-3. Note: Atlantic City restaurant meals "
            "are ALSO subject to the separate 3% Atlantic City "
            "Luxury Tax (N.J.S.A. 40:48-8.15 et seq.), which is NOT "
            "modeled by this engine -- see module docstring. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in New Jersey "
            "at the 6.625% statewide rate per N.J.S.A. section "
            "54:32B-3(a) (the imposition statute) as amended by "
            "P.L. 2011, c. 49 (effective May 1, 2011), which "
            "extended the sales-tax base from 'tangible personal "
            "property' to 'tangible personal property or a "
            "specified digital product.' The defined term "
            "'specified digital product' lives at N.J.S.A. section "
            "54:32B-2(zz) and covers digital audio works, digital "
            "audiovisual works, and digital books delivered "
            "electronically (i.e. obtained by means other than "
            "tangible storage media), whether transferred with a "
            "permanent right of use or with less-than-permanent "
            "use. Note: N.J.S.A. section 54:32B-8.56 (added by the "
            "same P.L. 2011, c. 49) is a SEPARATE narrow exemption "
            "for prewritten software delivered electronically AND "
            "used directly and exclusively in the conduct of the "
            "purchaser's business -- it does not change the "
            "general taxability of consumer-facing digital goods. "
            "Prewritten ('canned') computer software delivered by "
            "any means to a consumer is taxable as tangible "
            "personal property under N.J.S.A. section 54:32B-2(g). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in New "
            "Jersey at 6.625% per N.J.S.A. section 54:32B-3 (the "
            "imposition statute) and N.J.S.A. section 54:32B-2(g) "
            "(definition of tangible personal property). The 6.625% "
            "rate has been in effect since January 1, 2018 (reduced "
            "from 6.875% effective Jan 1, 2017, which was reduced "
            "from 7.000% effective Jan 1, 2017, by P.L. 2016, c. "
            "57). NJ levies NO general local (municipal/county) "
            "sales tax outside two narrow exceptions: (1) Urban "
            "Enterprise Zones (N.J.S.A. 52:27H-80) -- qualified "
            "retail purchases at certified UEZ sellers tax at HALF "
            "rate (3.3125%); ~32 UEZ municipalities; NOT modeled in "
            "v1 (seller-eligibility-restricted -- see module "
            "docstring); (2) Salem County (N.J.S.A. 54:32B-8.45) -- "
            "qualified retail sales at retail stores tax at HALF "
            "rate (3.3125%); NOT modeled in v1 (seller-eligibility-"
            "restricted -- see module docstring). Atlantic City "
            "Luxury Tax (N.J.S.A. 40:48-8.15) is a separate 3% "
            "city tax on hotels / restaurants / alcohol / "
            "amusements -- NOT a general sales tax and NOT modeled "
            "by this engine. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
}


class NewJersey(SstStateModule):
    """New Jersey state module (tier 1, SST member; statewide rate only).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS) and the taxability
    matrix. Rate parsing, boundary parsing, special cases, and the
    empty-holidays default are all inherited.

    NJ levies NO general local sales tax outside two narrow
    exceptions that are intentionally NOT modeled in v1:

    - **Urban Enterprise Zones (UEZs)**: ~32 municipalities where
      qualified retail purchases at certified UEZ sellers tax at
      half rate (3.3125%) per N.J.S.A. 52:27H-80. Seller-
      eligibility-restricted (depends on the seller holding a
      current UZ-2 certification); category-restricted (motor
      vehicles, energy, etc. excluded). Encoding as a geographic
      override would systematically over-collect on non-certified
      sellers in UEZ municipalities.
    - **Salem County**: half-rate (3.3125%) on qualified retail
      sales per N.J.S.A. 54:32B-8.45 (Delaware competition).
      Same seller / category eligibility constraints.

    See the module docstring for full deferral rationale (analogous
    to NV's National Guard holiday deferral). Both reductions can
    be enabled later by a per-seller exemption / certification
    feature; in the interim, an over-collected buyer can refund
    through the Division of Taxation under N.J.S.A. 54:32B-20.

    Atlantic City Luxury Tax (N.J.S.A. 40:48-8.15 et seq.) is a
    separate 3% city tax on hotels / restaurants / alcohol /
    amusements within Atlantic City -- NOT a general sales tax and
    outside this engine's scope.

    Clothing is BROADLY EXEMPT in NJ year-round per N.J.S.A.
    54:32B-8.4 (NJ joins PA, MA, MN, VT in the broad-exemption
    club). No per-item dollar cap; no date restriction.
    """

    state_abbrev: str = "NJ"
    state_name: str = "New Jersey"
    state_fips: str = "34"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.new_jersey`` registers
# New Jersey under "NJ" in the state registry.
_PROTOCOL_CHECK: StateModule = NewJersey()
del _PROTOCOL_CHECK

# Module-level constants for callers / future maintainers. The actual
# rate that flows into the engine comes from the SST quarterly file
# via the inherited parser; these constants are documentary anchors
# for the headline 6.625% statewide rate and the half-rate
# (3.3125%) used by both the UEZ and Salem County deferred
# reduced-rate exceptions.
NEW_JERSEY_STATEWIDE_RATE_PCT: Decimal = Decimal("6.625")
NEW_JERSEY_REDUCED_RATE_PCT: Decimal = Decimal("3.3125")

NEW_JERSEY = register(NewJersey())
