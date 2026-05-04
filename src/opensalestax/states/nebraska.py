# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Nebraska state module (tier 1, SST member).

NE is a Streamlined Sales Tax member (verified 2026-05-03 against
the SST member roster on streamlinedsalestax.org). The general
statewide rate is **5.5%** per **Neb. Rev. Stat. section 77-2701.02**,
the rate having been set at five and one-half percent effective
**October 1, 2002** by L.B. 1085 (97th Legislature, Second Session).
The 5.5% rate has been stable since.

## Notable rate exception: Good Life Districts (LB 1317 of 2024)

Effective **July 1, 2024**, Neb. Rev. Stat. section 77-2701.02 (as
amended by LB 1317, 108th Legislature, Second Session) imposes a
**REDUCED state rate of 2.75%** on transactions occurring within
that portion of a Good Life District (established under the Good
Life Transformational Projects Act, codified at Neb. Rev. Stat.
sections 77-4401 et seq.) which is located within the corporate
limits of a city or village. Transactions within a GLD that are
NOT within a city's or village's corporate limits remain at the
general 5.5% rate.

Effective **July 1, 2025**, a city containing a GLD may impose a
new local **GLD Local Option Sales and Use Tax of up to 2.75%**
on transactions within the GLD, in addition to the existing local
option sales tax under section 77-27,142. This local layer is
authorized by LB 1317 sections amending Neb. Rev. Stat. chapter 77.

The Good Life District rate logic is **NOT modeled in this
module's** taxability matrix because it is a sub-state geographic
overlay rather than a per-category taxability rule. Rate ingestion
flows through the SST quarterly rate file via the inherited
:class:`SstStateModule` parser, which is the appropriate place for
the GLD geographic boundaries (the Nebraska Department of Revenue
publishes the GLD rates and boundaries with each quarterly file
update under the same FIPS-based jurisdiction structure used for
city/county locals). A future state maintainer should validate
that the SST file's GLD rows are surfaced correctly through the
generic parser; if a new SST jurisdiction-type code is introduced
specifically for GLDs, override ``jurisdiction_types`` on this
subclass at that time. Until then we inherit the canonical
MN/WI scheme.

## Local jurisdictions

Neb. Rev. Stat. section 77-27,142 authorizes any incorporated
municipality (other than a city of the metropolitan class) to
impose a local option sales and use tax of **0.5%, 1%, 1.5%,
1.75%, or 2%** on retail sales within the municipality, by voter
approval. Combined NE rates therefore typically fall in the
**5.5%-7.5%** range (state 5.5% + local up to 2%). A separate
GLD layer can stack on top within the GLD boundaries (see above).

Counties may also impose a 0.5% local option sales and use tax
under sections 77-27,148 and 77-27,148.01 (limited to certain
public-safety / capital-improvement purposes), but this is rare.
The SST quarterly file carries the per-jurisdiction rates and is
the canonical source -- the rates documented in this docstring
are background/context only.

## SST jurisdiction-type code mapping

Per :mod:`specs.research.sst-file-format`, NE's SST rate file is
expected to use the same jurisdiction-type code mapping as MN and
WI (both validated against 2026Q2 data). NE data has not been
empirically inspected at promotion time; the default mapping is
applied and documented as an assumption. A future state maintainer
should validate against an actual ``NER<...>.csv`` file:

- ``45`` = state (5.5% general; may also include 2.75% GLD rows)
- ``00`` = county (rare; 0.5% public-safety locals)
- ``01`` = city / municipal local option (0.5%-2%)
- ``63`` = special district (potentially the GLD overlay)

If a future quarterly capture of an NE rate file shows different
codes (especially for GLDs), override ``jurisdiction_types`` on
this subclass at that time. Until then we inherit the
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping.

## Taxability matrix (per Neb. Rev. Stat. Chapter 77)

- **General tangible personal property** -- TAXABLE at 5.5% per
  Neb. Rev. Stat. section 77-2703 (imposition) and section
  77-2701.02 (rate). Section 77-2701.16 defines gross receipts
  including sales of tangible personal property.
- **Clothing** -- TAXABLE year-round at 5.5%. Nebraska has **no
  general clothing exemption**; clothing and footwear are general
  tangible personal property and tax at the rate set by section
  77-2701.02. Nebraska has **never enacted a sales-tax holiday**
  for clothing or any other category (verified against the
  Nebraska Department of Revenue 2026-05-03).
- **Groceries (food and food ingredients)** -- EXEMPT per **Neb.
  Rev. Stat. section 77-2704.24**, which exempts the gross
  receipts from the sale, lease, or rental of (and the storage,
  use, or other consumption of) food or food ingredients,
  EXCEPT for prepared food and food sold through vending machines.
  The exemption tracks the SST common definition; NE Sales and Use
  Tax Regulation 1-087 elaborates the exemption boundaries
  (heated food, mixed/combined food, dietary supplements, candy,
  soft drinks, and alcoholic beverages remain TAXABLE as general
  TPP or as prepared food).
- **Prescription drugs** -- EXEMPT per **Neb. Rev. Stat. section
  77-2704.09** ("Insulin; prescription drugs; mobility enhancing
  equipment; medical equipment; exemptions"). The exemption covers
  insulin, prescription drugs sold for use by a patient, and drugs
  purchased by a physician for prescription / dispensing /
  administration / transfer to a patient. Mobility enhancing
  equipment and certain durable medical equipment are also exempt
  when prescribed. Over-the-counter drugs sold without a
  prescription do NOT qualify.
- **Prepared food** -- TAXABLE at 5.5%. The food-and-food-
  ingredients exemption in section 77-2704.24 expressly excludes
  prepared food and food sold through vending machines; restaurant
  meals, hot deli items, and ready-to-eat foods tax at the rate
  set by section 77-2701.02.
- **Digital goods (specified digital products)** -- TAXABLE at
  5.5% per **Neb. Rev. Stat. section 77-2701.16(2)(e)**, which
  brings into "gross receipts" the retail sale of digital audio
  works, digital audiovisual works, digital codes, and digital
  books delivered electronically when the same products would be
  taxable on tangible storage media. Section 77-2701.16 also
  addresses transfers of permanent right-of-use, conditional
  right-of-use, and continued-payment-conditioned right-of-use --
  bringing subscription / streaming / locker-style digital
  delivery into the tax base. Canned (prewritten) computer
  software delivered by any means is taxable as TPP under the
  long-standing definition in section 77-2701; SaaS / remotely
  accessed software that does NOT transfer possession or control
  to the customer is generally NOT taxable as TPP per the
  Nebraska DOR's published guidance, though that distinction is
  not encoded as a separate sub-category in this module.

## Sales tax holidays

**NONE.** Nebraska has never enacted a recurring statewide
sales-tax holiday. Confirmed 2026-05-03 against the Nebraska
Department of Revenue's published guidance and the Sales Tax
Handbook compendium (https://www.salestaxhandbook.com/nebraska/sales-tax-holidays
returns "Nebraska does not offer a sales tax holiday or
temporary exemption period for any product categories" as of
2026). The :meth:`Nebraska.holidays_for` method returns an empty
iterator for every year (mirroring DC, ID, IN).

## Loading

Nebraska's rate data loads from the SST quarterly rate file via
the inherited ``SstStateModule.parse_rates`` machinery. The file
ships state-level + city/county-level rows in the canonical SST
layout. Boundary loading inherits the generic ``z``-record ZIP5
walker; the engine answers Nebraska ZIPs with the appropriate
state + local rate stack. GLD rate handling depends on how the
NE DOR encodes GLD boundaries in the quarterly file (see the
SST jurisdiction-type code mapping section above).

State maintainer: vacant -- see MAINTAINERS.md. Validating the
SST jurisdiction-type codes against an actual NER file (and
empirically determining how GLD rows are encoded) is the natural
next maintenance task. Tracking the biennial legislative session
for any rate changes (especially around GLD scope or the 2.75%
state rate) is a maintainer responsibility.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Nebraska Department of Revenue guidance before relying on these
rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# Nebraska taxability matrix per Neb. Rev. Stat. Chapter 77.
# Categories not listed default to taxable (engine behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Nebraska year-round at the 5.5% "
            "state rate (Neb. Rev. Stat. section 77-2701.02). Nebraska "
            "Revised Statute Chapter 77 contains no general clothing "
            "exemption; clothing and footwear are general tangible "
            "personal property under section 77-2701.16 and tax at the "
            "rate set by section 77-2701.02. Nebraska has never "
            "enacted a sales-tax holiday for clothing (or any other "
            "category). Local option sales tax under section "
            "77-27,142 (up to 2%) stacks on top of the state rate. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients are EXEMPT in Nebraska per Neb. "
            "Rev. Stat. section 77-2704.24, which exempts the gross "
            "receipts from the sale, lease, or rental of (and the "
            "storage, use, or other consumption of) food or food "
            "ingredients, EXCEPT for prepared food and food sold "
            "through vending machines. The exemption tracks the SST "
            "common definition; NE Sales and Use Tax Regulation 1-087 "
            "elaborates the boundaries -- heated food, mixed/combined "
            "food (other than enumerated exceptions), candy, dietary "
            "supplements, soft drinks, and alcoholic beverages are "
            "NOT covered by the exemption and remain TAXABLE at the "
            "5.5% state rate (plus locals). Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Nebraska per Neb. Rev. "
            "Stat. section 77-2704.09 (caption: 'Insulin; prescription "
            "drugs; mobility enhancing equipment; medical equipment; "
            "exemptions'). The exemption covers insulin, prescription "
            "drugs sold for use by a patient, and drugs purchased by "
            "a physician to be prescribed, dispensed, administered, "
            "or transferred to a patient. Mobility enhancing equipment "
            "and certain durable medical equipment are also exempt "
            "when sold pursuant to a prescription. Over-the-counter "
            "drugs sold without a prescription are NOT covered by "
            "this exemption and remain taxable at the general 5.5% "
            "rate. Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot deli items, "
            "ready-to-eat foods, food sold through vending machines) "
            "is TAXABLE in Nebraska at the 5.5% state rate per Neb. "
            "Rev. Stat. section 77-2703 (imposition) and section "
            "77-2701.02 (rate). Prepared food is expressly excluded "
            "from the food-and-food-ingredients exemption in section "
            "77-2704.24. Several Nebraska municipalities additionally "
            "impose a local occupation tax on prepared food / "
            "restaurant sales (commonly called a 'food and beverage' "
            "or 'restaurant occupation' tax); those are narrow "
            "industry-specific levies authorized by separate municipal "
            "code provisions and are NOT modeled by this module "
            "(which applies the state sales tax + general local "
            "option sales tax). Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Nebraska at "
            "the 5.5% state rate per Neb. Rev. Stat. section "
            "77-2701.16(2)(e), which brings into 'gross receipts' "
            "the retail sale of digital audio works, digital "
            "audiovisual works, digital codes, and digital books "
            "delivered electronically when the same products would "
            "be taxable on tangible storage media. Section "
            "77-2701.16 also addresses transfers of permanent "
            "right-of-use, conditional right-of-use, and "
            "continued-payment-conditioned right-of-use -- bringing "
            "subscription / streaming / locker-style digital "
            "delivery into the tax base. Canned (prewritten) "
            "computer software delivered by any means is also "
            "taxable as tangible personal property under section "
            "77-2701. EXCLUDED from the dominant taxable case: SaaS "
            "/ remotely accessed software where the customer takes "
            "neither possession nor control of the software -- per "
            "Nebraska DOR published guidance, that is generally NOT "
            "taxable as tangible personal property. The engine "
            "encodes the dominant case as taxable; callers shipping "
            "true SaaS to Nebraska customers should categorize those "
            "line items differently or apply an exemption until a "
            "sub-category split lands. Calculation only -- not legal "
            "or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Nebraska at the 5.5% state rate per Neb. Rev. Stat. "
            "section 77-2703 (imposition) and section 77-2701.02 "
            "(rate, set at five and one-half percent effective "
            "October 1, 2002 by L.B. 1085, 97th Legislature, Second "
            "Session). Local option sales tax under section "
            "77-27,142 (up to 2% in incorporated municipalities) "
            "stacks on top, giving combined rates typically in the "
            "5.5%-7.5% range. A reduced 2.75% state rate applies "
            "within Good Life Districts located inside city or "
            "village corporate limits per LB 1317 of 2024 (effective "
            "2024-07-01); GLD geography flows through the SST "
            "quarterly rate file rather than this taxability matrix. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}


class Nebraska(SstStateModule):
    """Nebraska state module (tier 1, SST member).

    Subclass of :class:`SstStateModule` that overrides the metadata
    (state abbrev / name / FIPS) and the taxability matrix with
    Nebraska-specific rules grounded in Neb. Rev. Stat. Chapter 77.
    Rate parsing, boundary parsing, special cases, and the
    empty-holidays default are all inherited (Nebraska has no
    sales-tax holidays).
    """

    state_abbrev: str = "NE"
    state_name: str = "Nebraska"
    state_fips: str = "31"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Nebraska-specific taxability matrix replaces the default
    # tier-2 grocery-only matrix. Jurisdiction-type codes inherit
    # the canonical MN/WI mapping (documented assumption pending
    # empirical validation against an actual NER<...>.csv file).
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated NE city-name table; fall back to placeholder."""
        from opensalestax.states.ne_names import city_name as _ne_city

        if authority_type == "city":
            friendly = _ne_city(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.nebraska`` registers
# Nebraska under "NE" in the state registry.
_PROTOCOL_CHECK: StateModule = Nebraska()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# general state rate. The actual rate that flows into the engine
# comes from the SST rate file via the inherited parser; the constant
# below is purely documentary so future readers can grep the codebase
# for the rate.
NEBRASKA_GENERAL_RATE_PCT: Decimal = Decimal("5.500")

NEBRASKA = register(Nebraska())
