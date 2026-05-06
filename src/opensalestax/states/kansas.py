# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Kansas state module (tier 1, SST member).

KS is a Streamlined Sales Tax member (full member; verified
2026-05-03 against the SST member roster on
streamlinedsalestax.org). The general statewide retailers' sales
tax rate is **6.5%** per **K.S.A. section 79-3603(a)** (rate
last increased from 5.3% to 6.5% effective July 1, 2015 by 2015
House Substitute for Senate Bill 270; the 6.5% rate has been
stable since).

## Local-jurisdiction landscape

Kansas allows counties, cities, and a variety of special
districts (Community Improvement Districts -- CIDs under K.S.A.
chapter 12, article 60; Transportation Development Districts --
TDDs under K.S.A. chapter 12, article 17; Star Bonds and
redevelopment districts) to impose local sales taxes by voter
approval or governing-body resolution. Combined rates commonly
fall in the **8-11%** range, with the highest rates appearing
inside CIDs in major-metro retail corridors. As an SST member,
Kansas's per-jurisdiction rates flow through the standard SST
quarterly rate file; the inherited :class:`SstStateModule`
parser handles them without state-specific overrides.

Per :mod:`specs.research.sst-file-format`, KS's SST rate file is
expected to use the same jurisdiction-type code mapping as MN
and WI (both empirically validated against 2026Q2 data). KS data
has not been empirically inspected at promotion time; the default
mapping is applied and documented as an assumption. A future
state maintainer should validate against an actual
``KSR<...>.csv`` file:

- ``45`` = state (single row carrying 6.5%)
- ``00`` = county
- ``01`` = city / local
- ``63`` = special district (CIDs, TDDs, etc.)

## Taxability matrix (per K.S.A. chapter 79, article 36)

- **General tangible personal property** -- TAXABLE at 6.5% per
  K.S.A. section 79-3603(a) (the imposition statute).
- **Clothing** -- TAXABLE year-round at the full combined rate.
  Kansas has **no general clothing exemption** in chapter 79,
  article 36; clothing and footwear are general tangible personal
  property and tax at the rate set by section 79-3603(a). Kansas
  has never enacted a back-to-school sales-tax holiday (see
  "Sales-tax holidays" below).
- **Groceries (food and food ingredients)** -- TAXABLE but at
  the **0.000% reduced state rate effective January 1, 2025**.
  Kansas Senate Substitute for House Bill 2106 (2022 session)
  created a multi-year phase-down of the state sales-tax rate
  on "food and food ingredients" as defined by K.S.A. section
  79-3602(o), codified at K.S.A. section 79-3603(p). The
  phase-down history:

    - Pre-2023-01-01: 6.5% state rate (full general rate)
    - 2023-01-01 to 2023-12-31: reduced 4.0% state rate
    - 2024-01-01 to 2024-12-31: reduced 2.0% state rate
    - **2025-01-01 onward: 0.000% state rate**

  **Local sales taxes (county, city, CID, TDD) still apply at
  the full local rate** -- the phase-down zeroed only the state
  portion. Encoded with ``rate_modifier=Decimal("0.000")`` to
  mark the special state rate (mirrors the AR Grocery Tax
  Relief Act pattern at section 26-52-317; the engine does not
  yet apply rate_modifier, so as of v0.11.1, the
  engine over-collects the 6.5% state portion on grocery line
  items in KS). Items NOT meeting the SST "food and food
  ingredients" definition (candy, soft drinks, dietary
  supplements, alcoholic beverages, tobacco) and prepared food
  remain at the general 6.5% rate.
- **Prescription drugs** -- EXEMPT per **K.S.A. section
  79-3606(p)**. The exemption covers "all sales of drugs ...
  dispensed pursuant to a prescription order by a licensed
  practitioner" for human use, plus prosthetic devices, mobility-
  enhancing equipment, and insulin sold for human use under
  the same subsection (the statutory exemption bundles related
  medical items consistent with the SST Agreement). Over-the-
  counter drugs sold without a prescription are NOT covered by
  the exemption and tax at the general 6.5% rate.
- **Prepared food** -- TAXABLE at the general 6.5% state rate
  (plus full local rate). Kansas's grocery rate phase-down at
  section 79-3603(p) explicitly excludes prepared food, candy,
  soft drinks, dietary supplements, alcoholic beverages, and
  tobacco -- consistent with the SST common definition adopted
  by the state. Restaurant meals, hot deli items, and ready-to-
  eat foods tax at the rate set by section 79-3603(a).
- **Digital goods (specified digital products)** -- TAXABLE at
  6.5% per **K.S.A. section 79-3603(d)** as amended by 2021
  Senate Bill 50. S.B. 50 (signed May 3, 2021; effective July 1,
  2021) brought digital products and digital codes into the
  Kansas sales-tax base by amending the definition of "tangible
  personal property" / scope of section 79-3603 to reach
  "specified digital products" -- digital audio works, digital
  audio-visual works, and digital books transferred
  electronically with a permanent right of use, plus digital
  codes and certain subscription products. Prewritten ("canned")
  computer software delivered by any means (including
  electronically) is also taxable as tangible personal property
  under the long-standing definition incorporated into section
  79-3603. Custom software and most true SaaS arrangements
  (where the customer takes neither possession nor control of
  the software) remain non-taxable -- documented for the next
  maintainer; the encoded rule treats the dominant case
  (specified digital products with permanent right of use) as
  taxable.

## Sales-tax holidays

**NONE.** Kansas has never enacted a recurring sales-tax
holiday. Confirmed 2026-05-03 against the Kansas Department of
Revenue's published guidance and a search of K.S.A. chapter 79,
article 36 for any periodic exemption window -- there is no
back-to-school holiday, no disaster-prep holiday, no Energy Star
holiday, and no other recurring exemption period in Kansas law.
Multiple legislative proposals have been introduced over the
years (most recently 2024 H.B. 2680 proposing a back-to-school
holiday) but none has been enacted as of 2026-05-03. The
``holidays_for(year)`` method returns an empty iterator for
every year (mirroring DC, ID, and IN).

## Loading

Kansas's rate data loads from the SST quarterly rate file via
the inherited :class:`SstStateModule.parse_rates` machinery. The
file ships state, county, city, and special-district rows; the
inherited parser maps them through the canonical
:data:`opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (assumed -- see jurisdiction-type-code mapping note
above). Boundary loading inherits the generic ``z``-record ZIP5
walker.

State maintainer: vacant -- see MAINTAINERS.md. The natural
next maintenance task is validating KS's SST jurisdiction-type
codes against an actual KSR file. Tracking the legislative
session for any rate changes (a potential further-grocery
adjustment, a future back-to-school holiday proposal) is a
maintainer responsibility.

DISCLAIMER: This is calculation logic, not legal or tax advice.
Maintainers and users are responsible for verifying current
Kansas Department of Revenue guidance before relying on these
rules in production.
"""

from __future__ import annotations

from decimal import Decimal

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import StateModule, StateTier, TaxabilityRule
from opensalestax.states.registry import register

# ---------------------------------------------------------------------------
# KS-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
# ASSUMPTION: KS's SST rate file uses the same jurisdiction-type
# codes as MN and WI (both empirically validated against 2026Q2
# data). This is consistent with SST's stated goal of uniform
# data formats across member states. A state maintainer should
# validate against an actual KSR<...>.csv file at next refresh.
_JURISDICTION_TYPE: dict[str, str | None] = {
    "45": "state",
    "00": "county",
    "01": "city",
    # KS code-63 rows encode Community Improvement Districts (CIDs) and
    # Transportation Development Districts (TDDs): special-purpose
    # local-improvement districts that apply only to addresses inside
    # the district boundary, not to every retail sale in the ZIP. The
    # SST quarterly boundary file binds them to ZIPs via type-'A'
    # (address-level) records; once those records are parsed (which they
    # are post-c512354), a ZIP-level lookup picks up every CID/TDD that
    # touches the ZIP -- adding ~6% spurious tax to KS Lawrence/
    # Salina/Wichita on general retail. Same pattern as TN code-63
    # (see src/opensalestax/states/tennessee.py for the original
    # writeup); ``None`` here tells the inherited base parser to skip
    # the row entirely. ZIP-level callers may slightly under-collect
    # for addresses physically inside a CID, but the previously
    # observed ZIP-wide over-collection was the larger correctness
    # problem.
    "63": None,
}

# Static taxability matrix per K.S.A. chapter 79, article 36.
# Categories not listed default to taxable (engine behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Kansas year-round at the full "
            "combined state + local rate per K.S.A. section "
            "79-3603(a). Kansas Statutes Annotated chapter 79, "
            "article 36 contains no general clothing exemption; "
            "clothing and footwear are general tangible personal "
            "property and tax at the 6.5% state rate plus any "
            "applicable local sales taxes. Kansas has never enacted "
            "a back-to-school sales-tax holiday (multiple proposals "
            "have been introduced -- most recently 2024 H.B. 2680 -- "
            "but none has passed). Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("0.000"),
        notes=(
            "Food and food ingredients are taxable at a REDUCED "
            "0.000% state rate effective January 1, 2025 per the "
            "Kansas grocery rate phase-down enacted by Senate "
            "Substitute for House Bill 2106 (2022 session), codified "
            "at K.S.A. section 79-3603(p). Phase-down history: 6.5% "
            "(pre-2023-01-01), 4.0% (2023-01-01 through 2023-12-31), "
            "2.0% (2024-01-01 through 2024-12-31), 0.000% "
            "(2025-01-01 onward). LOCAL sales taxes (county, city, "
            "CID, TDD) STILL APPLY at the full local rate -- only "
            "the state portion was phased to zero. The 'food and "
            "food ingredients' definition in K.S.A. section "
            "79-3602(o) tracks the SST common definition; items NOT "
            "meeting it (candy, soft drinks, dietary supplements, "
            "alcoholic beverages, tobacco) and prepared food remain "
            "at the general 6.5% state rate. The rate_modifier is "
            "stored but the engine applies (as of v0.11.1) it (deferred "
            "to v0.6+); until then the engine over-collects the 6.5% "
            "state portion on grocery line items in Kansas. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT from Kansas sales and "
            "use tax per K.S.A. section 79-3606(p), which exempts "
            "all sales of drugs dispensed pursuant to a prescription "
            "order by a licensed practitioner for human use, plus "
            "prosthetic devices, mobility-enhancing equipment, and "
            "insulin sold for human use under the same subsection. "
            "Over-the-counter drugs sold without a prescription are "
            "NOT covered by the exemption and tax at the general "
            "6.5% rate even when prescribed. Calculation only -- "
            "not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-"
            "eat deli items) is TAXABLE in Kansas at the general "
            "6.5% state rate per K.S.A. section 79-3603(a), plus "
            "the full local rate. Prepared food is expressly "
            "EXCLUDED from the reduced grocery rate at K.S.A. "
            "section 79-3603(p) (along with candy, soft drinks, "
            "dietary supplements, alcoholic beverages, and tobacco) "
            "consistent with the SST 'food and food ingredients' "
            "definition. Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products are TAXABLE in Kansas at "
            "the general 6.5% state rate per K.S.A. section "
            "79-3603(d) as amended by 2021 Senate Bill 50 (signed "
            "May 3, 2021; effective July 1, 2021). S.B. 50 brought "
            "digital products and digital codes into the Kansas "
            "sales-tax base; the statute reaches digital audio "
            "works, digital audio-visual works, digital books "
            "transferred electronically with a permanent right of "
            "use, plus digital codes and certain subscription "
            "products. Prewritten ('canned') computer software "
            "delivered by any means is also taxable as tangible "
            "personal property under the long-standing definition "
            "incorporated into section 79-3603. EXCLUDED from the "
            "dominant taxable case: custom computer programs and "
            "true SaaS arrangements (remotely accessed software "
            "where the customer takes neither possession nor "
            "control of the software) -- documented for the next "
            "maintainer; the engine encodes the dominant case as "
            "taxable. Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Kansas at the 6.5% state rate per K.S.A. section "
            "79-3603(a) (rate raised from 5.3% to 6.5% effective "
            "July 1, 2015 by 2015 House Substitute for Senate Bill "
            "270; stable at 6.5% since). Local sales taxes (county, "
            "city, CID, TDD, Star Bond / redevelopment district) "
            "stack on top via the SST quarterly rate file. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}


class Kansas(SstStateModule):
    """Kansas state module (tier 1, SST member).

    Inherits the generic SST rate / boundary parser from
    :class:`SstStateModule`. Overrides the default taxability
    matrix and the jurisdiction-type code mapping with KS-specific
    research grounded in K.S.A. chapter 79, article 36. Kansas has
    no annual sales-tax holiday, so the inherited empty-iterator
    ``holidays_for`` default is used unchanged.
    """

    state_abbrev: str = "KS"
    state_name: str = "Kansas"
    state_fips: str = "20"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    # Override the base-class defaults with KS-specific data.
    jurisdiction_types: dict[str, str | None] = _JURISDICTION_TYPE
    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated KS city-name table; fall back to placeholder."""
        from opensalestax.states.ks_names import city_name as _ks_city

        if authority_type == "city":
            friendly = _ks_city(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)


# Compile-time Protocol satisfaction check + module-import-time
# registration. Importing ``opensalestax.states.kansas`` registers
# Kansas under "KS" in the state registry.
_PROTOCOL_CHECK: StateModule = Kansas()
del _PROTOCOL_CHECK

# Module-level constant for callers that want a stable handle to the
# instance (mirrors INDIANA, IOWA, etc.). Kansas's RateRow emits
# ``rate_pct=Decimal("6.500")`` from the SST file; the constant
# below is purely documentary so future readers can grep the
# codebase for the rate.
KANSAS_GENERAL_RATE_PCT: Decimal = Decimal("6.500")

KANSAS = register(Kansas())
