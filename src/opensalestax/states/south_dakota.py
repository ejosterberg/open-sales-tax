# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""South Dakota state module (tier 1, SST member).

SD is a Streamlined Sales Tax full member (verified 2026-05-03
against the SST member roster on streamlinedsalestax.org). The
statewide general sales/use tax rate is **4.2%** per **SDCL
section 10-45-2** (the imposition statute of the South Dakota
Retail Sales and Service Tax, codified at SDCL chapter 10-45).
The 4.2% rate took effect **2023-07-01** when **House Bill 1137
of the 98th South Dakota Legislative Session (2023)** reduced
the prior 4.5% rate to 4.2%.

## STATUTORY RATE SUNSET (CRITICAL)

**HB 1137 (2023) included an explicit statutory sunset on the
4.2% rate: the reduction expires on 2027-06-30** unless the
legislature acts to extend it. If the sunset takes effect with
no further legislative action, the rate reverts to 4.5%
effective **2027-07-01**. Maintainers must monitor SD legislative
activity in 2027 (and any earlier session that revisits the
rate) and update the rate row in the SST quarterly file
ingestion path AND any documentary constants in this module
when the legislature confirms either an extension, a further
reduction, or the sunset's actual expiration.

## WAYFAIR CONNECTION (HISTORICAL CONTEXT)

South Dakota is the plaintiff state in **South Dakota v. Wayfair,
Inc., 138 S. Ct. 2080 (2018)** -- the U.S. Supreme Court
decision that overturned the physical-presence rule of
*Quill Corp. v. North Dakota*, 504 U.S. 298 (1992) and
established the modern "economic nexus" standard for state sales
tax collection. SD's underlying statute (SDCL section 10-64-2,
the Wayfair-era remote-seller economic-nexus statute setting
the now-canonical $100,000 / 200-transaction threshold) predates
this module and is not directly relevant to per-address rate
calculation -- but every SST and non-SST state's economic-nexus
regime traces lineage to Wayfair. Documenting the connection
here so the next maintainer (and downstream readers using SD as
a reference implementation) understand why South Dakota's
four-letter abbreviation looms so large in U.S. sales-tax law.

## SD's local-tax landscape

Unlike Indiana, Kentucky, or Michigan (peer SST members with NO
local sales tax), South Dakota DOES allow local-option sales
taxes. Three principal local-tax authorities apply on top of the
4.2% state rate:

- **SDCL chapter 10-52 -- municipal non-ad-valorem taxes.**
  Municipalities may impose:
  - A **municipal gross receipts tax of up to 2.0%** under
    SDCL section 10-52-2 (the most common local-option sales
    tax; most participating SD municipalities are at 2.0%).
  - A **municipal special tax of up to 1.0%** under SDCL section
    10-52A-2 (additional municipal authority on lodging,
    prepared food and beverages, and ticket admissions; not a
    general sales tax but layers atop SDCL chapter 10-45).
- **Tribal gross receipts taxes** on reservation land under
  intergovernmental tax-collection agreements between the State
  of South Dakota and federally-recognized tribes (Cheyenne River
  Sioux, Crow Creek Sioux, Oglala Sioux, Rosebud Sioux,
  Standing Rock Sioux, Yankton Sioux, plus several others).
  These are administered through the SD Department of Revenue
  via the same rate-collection mechanism as municipal taxes;
  per-jurisdiction rates flow through the SST quarterly file.

Combined effective rates on tangible personal property therefore
range from **4.2% (unincorporated areas with no local tax) to
roughly 6.2% in most participating municipalities** (4.2% state
+ 2.0% municipal). Per-jurisdiction rates load via the inherited
:class:`SstStateModule` parser; this module does not codify
per-municipality rates inline.

The default jurisdiction-type code mapping (state ``45`` /
county ``00`` / city ``01`` / district ``63``) is inherited from
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`.
This mapping is empirically validated against MN and WI 2026Q2
files; if a future quarterly capture of a South Dakota SST file
shows different codes for any sub-state authority, override
``jurisdiction_types`` on this subclass at that time.

## Taxability matrix (per SDCL chapter 10-45)

- **General tangible personal property** -- TAXABLE at 4.2% per
  **SDCL section 10-45-2** (imposition of the state retail
  sales tax on the gross receipts from retail sales of tangible
  personal property and certain services), complemented by the
  use tax in SDCL chapter 10-46.
- **Clothing** -- TAXABLE. South Dakota has **no general
  clothing exemption** in chapter 10-45; clothing and footwear
  are ordinary tangible personal property and tax at the full
  4.2% state rate plus any applicable municipal rates. South
  Dakota has **no annual back-to-school sales-tax holiday** (see
  "Sales-tax holidays" below).
- **Groceries (food and food ingredients)** -- **TAXABLE at the
  full 4.2% state rate** per **SDCL section 10-45-2.4**, which
  expressly subjects "food" to the full state sales tax. South
  Dakota is one of a small handful of states that fully tax
  groceries -- a notable peer-state difference from the SST
  norm of exempting food and food ingredients (most SST member
  states -- IA, KS, KY, ND, NE, etc. -- exempt groceries; SD
  does NOT). Joining SD in fully taxing groceries: ID (with a
  grocery-credit refund), HI (under GET), and historically MS
  and AL. Voters rejected a 2024 ballot measure (Initiated
  Measure 28) that would have eliminated the state grocery tax;
  the legislature has periodically debated grocery-tax reform
  without enacting it. **Encode is_taxable=True** -- this is
  the most-likely-to-be-overlooked rule in the SD module and is
  explicitly tested in the unit tests as a regression guard.
- **Prescription drugs** -- EXEMPT per **SDCL section 10-45-14**,
  which exempts the gross receipts from the sale of prescription
  drugs (and certain related items including insulin, oxygen
  for human consumption, and prosthetic / durable medical
  equipment when sold pursuant to a written prescription).
  Over-the-counter (non-prescription) drugs are NOT covered by
  this exemption and remain taxable as general TPP.
- **Prepared food** -- TAXABLE at 4.2% per the general
  imposition in SDCL section 10-45-2 (and confirmed by the full
  taxation of food generally under section 10-45-2.4). Prepared
  food (restaurant meals, hot deli items, ready-to-eat foods)
  may also be subject to the 1.0% municipal special tax under
  SDCL section 10-52A-2 in participating municipalities.
- **Digital goods (specified digital products)** -- TAXABLE at
  4.2% per **SDCL section 10-45-1.1**, added by **SB 207 of the
  83rd South Dakota Legislative Session (2008)** which extended
  the sales tax to "specified digital products" delivered
  electronically. Section 10-45-1.1 incorporates the SST
  uniform definitions of digital audio works, digital
  audio-visual works, digital books, and "other digital
  products" -- whether sold with a permanent right of use or
  under a subscription / conditional access model. Prewritten
  ("canned") computer software delivered by any means is also
  taxable as tangible personal property under the longstanding
  definitions in SDCL section 10-45-1.

## Sales-tax holidays

**NONE.** South Dakota has never enacted a recurring sales-tax
holiday. Confirmed 2026-05-03 against the South Dakota
Department of Revenue's published guidance (https://dor.sd.gov/)
and a search of SDCL chapter 10-45 for any periodic exemption
window -- there is no back-to-school holiday, no
disaster-prep holiday, no Energy Star holiday, and no other
recurring exemption period in South Dakota law. The
``holidays_for(year)`` method returns an empty iterator for
every year (mirroring Kentucky, Indiana, North Dakota, DC,
and Idaho).

## Loading

South Dakota's rate data loads from the SST quarterly rate file
via the inherited ``SstStateModule.parse_rates`` machinery. The
file ships state-level + per-municipality + tribal rate rows;
the inherited parser converts each into a ``RateRow`` with the
appropriate ``authority_type``. Boundary loading uses the
generic ``z``-record ZIP5 walker.

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
South Dakota Department of Revenue guidance before relying on
these rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# South Dakota taxability matrix per SDCL chapter 10-45.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in South Dakota at the 4.2% state "
            "rate (plus any applicable municipal rates of up to 2.0% "
            "under SDCL chapter 10-52). SDCL chapter 10-45 contains "
            "no general clothing exemption; clothing and footwear are "
            "ordinary tangible personal property and tax at the rate "
            "set by SDCL section 10-45-2. South Dakota has no annual "
            "back-to-school sales-tax holiday. Calculation only -- "
            "not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        notes=(
            "Groceries (food and food ingredients) are TAXABLE in "
            "South Dakota at the full 4.2% state rate per SDCL "
            "section 10-45-2.4, which expressly subjects food to the "
            "full state sales tax. South Dakota is one of a small "
            "minority of U.S. states that fully tax groceries -- a "
            "notable peer-state difference from the SST norm of "
            "exempting food and food ingredients (Iowa, Kansas, "
            "Kentucky, North Dakota, Nebraska, etc. all exempt "
            "groceries; South Dakota does NOT). Voters rejected "
            "Initiated Measure 28 in November 2024, which would have "
            "eliminated the state grocery tax; the rule remains in "
            "effect. Municipal gross receipts taxes under SDCL "
            "chapter 10-52 may also apply (combined effective "
            "grocery rates of 4.2%-6.2% statewide). Calculation only "
            "-- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in South Dakota per SDCL "
            "section 10-45-14, which exempts the gross receipts from "
            "the sale of prescription drugs and related items "
            "(including insulin, oxygen for human consumption, and "
            "certain prosthetic / durable medical equipment when sold "
            "pursuant to a written prescription by a licensed "
            "practitioner). Over-the-counter drugs sold without a "
            "prescription are NOT covered by the exemption and tax "
            "at the general 4.2% state rate. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-"
            "eat deli items) is TAXABLE in South Dakota at the 4.2% "
            "state rate per SDCL section 10-45-2 (imposition); "
            "additionally, participating municipalities may impose a "
            "municipal special tax of up to 1.0% on prepared food "
            "and beverages under SDCL section 10-52A-2, layering on "
            "top of both the state rate and any general municipal "
            "gross receipts tax. Note that South Dakota also fully "
            "taxes ordinary groceries (see the 'groceries' rule); "
            "the 'prepared_food' versus 'groceries' distinction does "
            "NOT change taxability in SD as it does in most peer "
            "states, though the 1.0% prepared-food special tax does "
            "give the categories different combined rates in some "
            "municipalities. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in South Dakota "
            "at the 4.2% state rate per SDCL section 10-45-1.1, "
            "added by SB 207 of the 83rd South Dakota Legislative "
            "Session (2008). Section 10-45-1.1 incorporates the SST "
            "uniform definitions of digital audio works, digital "
            "audio-visual works, digital books, and other 'specified "
            "digital products' delivered electronically -- whether "
            "transferred with a permanent right of use or under a "
            "subscription / conditional access model. Prewritten "
            "('canned') computer software delivered by any means is "
            "also taxable as tangible personal property under the "
            "longstanding definitions in SDCL section 10-45-1. "
            "Callers shipping digital goods or SaaS to South Dakota "
            "should verify their specific product category against "
            "current SD Department of Revenue guidance. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in South "
            "Dakota at the 4.2% state rate per SDCL section 10-45-2 "
            "(imposition of the state retail sales tax), "
            "complemented by the use tax in SDCL chapter 10-46. The "
            "4.2% rate took effect 2023-07-01 per HB 1137 of the "
            "98th SD Legislative Session (2023), reduced from a "
            "prior 4.5% rate. HB 1137 included an explicit statutory "
            "sunset: the 4.2% rate expires on 2027-06-30 and the "
            "rate reverts to 4.5% on 2027-07-01 unless the "
            "legislature extends the reduction. Municipal "
            "gross-receipts taxes under SDCL chapter 10-52 (up to "
            "2.0% general + up to 1.0% special on certain "
            "categories) and tribal gross-receipts taxes layer on "
            "top; combined rates typically range from 4.2% "
            "(unincorporated, no local tax) to roughly 6.2% in most "
            "participating municipalities. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
}


class SouthDakota(SstStateModule):
    """South Dakota state module (tier 1, SST member).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS) and the taxability
    matrix. Rate parsing, boundary parsing, jurisdiction-type
    code mapping, special cases, and the empty-holidays default
    are all inherited.

    SD is the plaintiff in *South Dakota v. Wayfair, Inc.*, 138
    S. Ct. 2080 (2018) -- the case that established economic-
    nexus standards nationwide. See module docstring for the
    rate-sunset (2027-06-30) and groceries-fully-taxed peer-
    state difference.
    """

    state_abbrev: str = "SD"
    state_name: str = "South Dakota"
    state_fips: str = "46"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    taxability: dict[str, TaxabilityRule] = _TAXABILITY


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.south_dakota``
# registers South Dakota under "SD" in the state registry.
_PROTOCOL_CHECK: StateModule = SouthDakota()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# state-rate value. South Dakota's RateRow emits
# ``rate_pct=Decimal("4.200")`` from the SST file (effective
# 2023-07-01 per HB 1137 of the 98th SD Legislative Session, with a
# statutory sunset on 2027-06-30 unless extended by the legislature).
# The constant below is purely documentary so future readers can grep
# the codebase for the rate.
SOUTH_DAKOTA_GENERAL_RATE_PCT: Decimal = Decimal("4.200")

# Documentary constant for the statutory sunset date on the 4.2%
# rate. If the legislature does not extend the reduction, the rate
# reverts to 4.5% on 2027-07-01. Maintainers MUST update this
# constant (and the docstring above) when the legislature acts.
SOUTH_DAKOTA_RATE_SUNSET_ISO: str = "2027-06-30"

SOUTH_DAKOTA = register(SouthDakota())
