# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Hawaii state module (tier 1, non-SST) -- GENERAL EXCISE TAX MODEL.

WARNING -- HAWAII DOES NOT HAVE A SALES TAX
-------------------------------------------
Hawaii is one of a small group of US states that does **NOT** levy a
retail sales tax. Instead, Hawaii imposes the **General Excise Tax
(GET)** under **Hawaii Revised Statutes (HRS) Chapter 237**. The GET is
a fundamentally different legal instrument from a sales tax:

- **Sales tax:** a transactional tax on the BUYER, collected by the
  seller as the state's agent at the point of sale. The seller's
  legal exposure is failure to collect/remit; the economic burden is
  on the buyer.
- **General Excise Tax (GET):** a **gross-receipts tax on the SELLER**
  for the privilege of doing business in Hawaii. The seller is the
  taxpayer; the GET is owed on the seller's gross income whether or
  not it is passed on to the buyer. Sellers commonly DO pass the GET
  through to buyers (HRS § 237-49 expressly permits "visible
  pass-through" of the GET as a separate line item), but the
  pass-through is permissive seller pricing -- not a transactional
  tax the seller is obligated to collect.

Because the GET is itself part of the seller's gross receipts, a
seller who passes the GET through at the bare 4.0% rate slightly
under-recovers the actual GET liability. The maximum visible
pass-through rate Hawaii allows on Oahu (where the combined GET +
county surcharge is 4.5%) is **4.7120%**, computed as
0.045 / (1 - 0.045); on the neighbor islands at the bare 4.0% GET
the maximum visible pass-through is **4.1666%**, computed as
0.04 / (1 - 0.04). These pass-through grossing-up rates are a
seller-pricing nuance documented in Department of Taxation
Tax Information Release No. 2018-07; **the OpenSalesTax engine does
NOT compute or apply them.** The engine returns the bare statutory
4.0% (or 4.5% on Oahu, when per-county surcharges are encoded) -- the
same result an API consumer would expect from a 4.0%/4.5% sales tax.

API SHAPE: HAWAII IS MODELED AS A SALES TAX FOR API PURPOSES
------------------------------------------------------------
For the OpenSalesTax v1 API surface, Hawaii is encoded as if it were
a 4.0% sales tax. API consumers calling ``/v1/calculate`` for a
Hawaii address experience the GET identically to how they would
experience a sales tax: a percentage applied to the line-item amount.
This API-shape choice is deliberate:

- Per-state research brief explicitly directs: "model HI as if it
  were sales tax (API-shape) while documenting the GET legal model
  prominently in the module docstring."
- A separate ``tax_model`` Protocol attribute (sales | TPT | GET |
  GRT) is larger architectural work that should happen if/when other
  GRT states (NM) and TPT states (AZ -- already shipped) need a
  unified taxonomy. AZ currently ships its TPT as a sales tax for
  the same reason; HI mirrors that approach.
- The legal nuance (seller-side liability, pass-through grossing-up,
  no transactional collection obligation) lives in this docstring,
  in the TaxabilityRule.notes fields below, and in
  ``specs/research/references.md`` for any future maintainer who
  needs to understand why Hawaii is encoded as a 4.0% rate row.

Statewide rate: 4.0% per HRS § 237-13
-------------------------------------
The general 4% GET rate applies to retail sales of tangible personal
property, services, and most other gross income categories under HRS
§ 237-13. The 4% rate has been the general retail/services rate since
**1965-01-01** (Act 155, SLH 1965, raised the rate from 3.5% to 4.0%
effective 1965-01-01 and the 4.0% rate has persisted unchanged
since). The module pins ``effective_from`` to **1965-01-01** because
that is when the current 4.0% rate first applied.

HRS § 237-13 also provides two reduced GET rates that the v1 module
does **NOT** emit because they are B2B / industry-specific and
outside the consumer-facing API surface:

- **0.5% wholesale** rate on sales between licensed wholesalers
  ("intermediary" sales) under HRS § 237-13(2)(A) -- not relevant to
  the consumer-transaction calculation API.
- **0.15% insurance commissions** rate under HRS § 237-13(7) -- not
  relevant to the consumer-transaction calculation API.

These reduced rates are documented in
``specs/research/references.md`` for completeness; the engine does
not surface them via ``/v1/calculate`` in v1.

Per-county surcharges (DEFERRED in v1; documented here)
-------------------------------------------------------
Hawaii authorizes each of its four counties to enact a **0.5% county
surcharge** on top of the state GET under **HRS § 46-16.8** (county
surcharge on state tax). All four counties have enacted the
surcharge as of 2026-01-01:

- **Honolulu County** (City and County of Honolulu, the entire
  island of Oahu) -- **0.5% effective 2007-01-01**, the longest-
  running county surcharge. Combined Oahu GET rate: **4.5%**.
- **Kauai County** (the entire island of Kauai) -- **0.5% effective
  2019-01-01**.
- **Hawaii County** (the Big Island) -- **0.5% effective
  2020-01-01**.
- **Maui County** (Maui, Molokai, Lanai, and Kahoolawe) -- **0.5%
  effective 2024-01-01**, the most recent enactment.

The county surcharges apply to the same gross-receipts base as the
state GET, which means the combined effective rate is **4.5% on every
inhabited Hawaiian island** as of 2026. Because HI has no Streamlined
Sales Tax membership and no machine-readable per-county GET file
analogous to Texas's Comptroller file, **per-county surcharge data
ingestion is deferred** (mirrors the documented-deferral pattern used
by Colorado, South Carolina, Missouri, Mississippi, and Nevada). API
consumers calling ``/v1/calculate`` for a Hawaii address in v1
receive the **state-only 4.0% rate** -- an under-collection of 0.5
percentage points on every inhabited Hawaii address. The module's
docstring AND the general taxability rule's notes call this out
explicitly so an integrator does not silently miscompute Hawaii tax.

Once a Hawaii per-county data path lands (Phase 4+ when address-level
resolution + boundaries ship, or earlier if a contributor builds a
Hawaii County / Maui County / Kauai County / Honolulu County boundary
file by ZIP), this module should emit four additional ``RateRow``
instances with ``authority_type='county'`` and
``parent_authority_name='Hawaii'``.

Taxability matrix (per HRS Chapter 237)
---------------------------------------

- **General gross income / tangible personal property** -- TAXABLE at
  4.0% per HRS § 237-13(2)(A) (general retail rate). Services are
  also generally taxable under the same provision -- a notable
  Hawaii peculiarity vs. most US states which do not tax services
  generally.
- **Clothing** -- TAXABLE at 4.0%. HRS Chapter 237 contains no
  clothing exemption; clothing is general gross income subject to
  the 4.0% rate.
- **Groceries** -- **TAXABLE at 4.0%**. Hawaii is one of the very
  few US states that fully taxes groceries at the GET rate. HRS
  Chapter 237 contains no general food/grocery exemption. Hawaii
  does provide grocery-cost relief through the **refundable
  food/excise tax credit** under **HRS § 235-55.85**, but that is an
  **income-tax credit** (Chapter 235, not Chapter 237) available on
  the annual income-tax return to qualifying low-income filers --
  NOT a reduction of the GET owed at the register. The OpenSalesTax
  engine therefore correctly applies the full 4.0% GET to grocery
  sales. (This mirrors Idaho's "groceries taxable + separate income-
  tax credit" structure documented in ``idaho.py``.)
- **Prescription drugs** -- EXEMPT per **HRS § 237-24.3(6)**, which
  exempts amounts received from sales of prescription drugs and
  prosthetic devices. The exemption requires the drug to be
  dispensed pursuant to a prescription order issued by a person
  authorized by HRS Chapter 461 or otherwise.
- **Prepared food / meals** -- TAXABLE at 4.0% (general gross-income
  rate). HRS Chapter 237 imposes no separate prepared-food rate
  (unlike Maine's statutory 8% prepared-food rate). Restaurant
  meals, takeout, and catering are all subject to the standard 4.0%
  GET (4.5% on Oahu when the surcharge is encoded).
- **Digital goods** -- TAXABLE at 4.0%. The Hawaii Department of
  Taxation has consistently interpreted "tangible personal property"
  and "services" under HRS § 237-13 to include digital products and
  software regardless of delivery method (download, streaming,
  subscription). Tax Information Release No. 2018-09 ("Tax Treatment
  of Income from Software Sales") confirms that gross income from
  software sales -- canned, custom, downloaded, or accessed remotely
  -- is subject to the GET at the applicable rate. Subscription-
  based digital media (streaming) is also taxable under the same
  reasoning. The unified GET-on-gross-income approach means HI does
  NOT need a sub-category split between "permanent right" and
  "subscription" digital goods (unlike Idaho).

Sales-tax holidays
------------------
Hawaii has **NO state-level GET holiday**. Confirmed 2026-05-03
against the Hawaii Department of Taxation published guidance and the
text of HRS Chapter 237. Hawaii has never enacted a recurring
GET holiday; bills proposing GET holidays for back-to-school or
hurricane preparedness have been introduced in past sessions but
none have passed into law. ``holidays_for(year)`` returns an empty
iterator for every year, with a regression test that exercises
2024-2030 (mirrors Maine's no-holiday regression pattern).

State maintainer: vacant -- see MAINTAINERS.md. The most likely
sources of follow-up work are (a) per-county surcharge data
ingestion (see deferred-county notes above) and (b) any future GET
exemption or rate change enacted by the Hawaii Legislature.

Disclaimer: this module computes tax; it does not provide legal or
tax advice. The GET-vs-sales-tax legal distinction is significant
for compliance purposes (seller registration, return filing, audit
exposure) but is invisible to the tax-amount calculation. Verify
against the Hawaii Department of Taxation for any compliance
decision.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.states.protocol import (
    BoundaryRow,
    HolidayWindow,
    RateRow,
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# Hawaii GET taxability matrix per HRS Chapter 237.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Hawaii at the 4.0% General Excise "
            "Tax (GET) rate. HRS Chapter 237 contains no clothing "
            "exemption; clothing is general gross income subject to the "
            "4.0% rate under HRS section 237-13(2)(A) (the 'general "
            "retail' rate). Hawaii has no annual back-to-school holiday. "
            "NOTE: the GET is a gross-receipts tax on the seller, not a "
            "transactional tax on the buyer -- see module docstring for "
            "the GET-vs-sales-tax legal distinction. Calculation only -- "
            "not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        notes=(
            "Groceries ARE taxable in Hawaii at the full 4.0% GET rate. "
            "Hawaii is one of the very few US states that fully taxes "
            "groceries at the standard rate; HRS Chapter 237 contains "
            "no general food/grocery exemption. Hawaii provides "
            "grocery-cost relief through a SEPARATE refundable "
            "food/excise tax credit under HRS section 235-55.85 -- but "
            "that credit is an INCOME-TAX credit (Chapter 235) claimed "
            "on the annual income-tax return by qualifying low-income "
            "filers, NOT a reduction of the GET owed at the register. "
            "The engine therefore correctly applies the full 4.0% GET to "
            "grocery sales. (Mirrors Idaho's structure: groceries fully "
            "taxed + separate income-tax credit.) Calculation only -- "
            "not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Hawaii per HRS section "
            "237-24.3(6), which exempts amounts received from sales of "
            "prescription drugs and prosthetic devices. The exemption "
            "requires the drug to be dispensed pursuant to a "
            "prescription order issued by a person authorized under "
            "HRS Chapter 461 (or otherwise authorized). Over-the-counter "
            "medications without a prescription are NOT covered and "
            "remain taxable at the 4.0% rate. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food / meals / drinks are TAXABLE in Hawaii at the "
            "4.0% GET rate. HRS Chapter 237 imposes no separate prepared-"
            "food rate (unlike Maine's statutory 8% prepared-food rate); "
            "restaurant meals, takeout, and catering are all subject to "
            "the standard 4.0% GET under HRS section 237-13(2)(A). On "
            "Oahu the combined rate is 4.5% (state 4.0% + Honolulu "
            "County 0.5% surcharge), but per-county surcharges are "
            "deferred from v1 (see module docstring). Calculation only "
            "-- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are TAXABLE in Hawaii at the 4.0% GET rate. "
            "The Hawaii Department of Taxation has consistently "
            "interpreted HRS section 237-13's broad 'tangible personal "
            "property' and 'services' base to include digital products "
            "regardless of delivery method (download, streaming, "
            "subscription). Tax Information Release No. 2018-09 ('Tax "
            "Treatment of Income from Software Sales') confirms that "
            "gross income from software sales -- canned, custom, "
            "downloaded, or remotely accessed (SaaS) -- is subject to "
            "the GET. The unified GET-on-gross-income approach means "
            "Hawaii does NOT need a sub-category split between "
            "'permanent right' digital media and subscription streaming "
            "(unlike Idaho, where HRS-equivalent code section 63-3616(b) "
            "treats them differently). Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General gross income (tangible personal property AND "
            "services) is taxable in Hawaii at 4.0% under the General "
            "Excise Tax (GET) per HRS section 237-13(2)(A). NOTE -- "
            "Hawaii does NOT levy a sales tax: the GET is a gross-"
            "receipts tax on the SELLER, not a transactional tax on the "
            "buyer (see module docstring for the legal distinction). "
            "WARNING -- per-county surcharges (Honolulu 0.5% since 2007, "
            "Kauai 0.5% since 2019, Hawaii County 0.5% since 2020, Maui "
            "0.5% since 2024) bring the combined rate to 4.5% at every "
            "inhabited Hawaii address as of 2026, but the v1 engine "
            "models the state-only 4.0% rate -- an under-collection of "
            "0.5 percentage points on every Hawaii transaction until the "
            "per-county surcharge data path lands. Calculation only -- "
            "not legal or tax advice."
        ),
    ),
}

# Statewide-rate effective date: January 1, 1965. The 4.0% general-
# retail GET rate took effect under Act 155, SLH 1965, which raised
# the rate from 3.5% to 4.0% effective 1965-01-01. The 4.0% general
# rate has been stable for the 60+ years since (per-county 0.5%
# surcharges are layered on top under HRS section 46-16.8 and are
# deferred from v1).
_RATE_EFFECTIVE_FROM = dt.date(1965, 1, 1)


class Hawaii:
    """Hawaii state module (tier 1; 4.0% GET; per-county surcharges deferred).

    See module docstring for the General Excise Tax legal model and
    the rationale for encoding HI as a sales tax for API purposes.
    """

    state_abbrev: str = "HI"
    state_name: str = "Hawaii"
    sst_member: bool = False  # HI is NOT a Streamlined Sales Tax member
    has_sales_tax: bool = True  # API-shape: GET modeled as sales tax
    tier: StateTier = 1
    # Hawaii has no SST upstream file; parse_rates returns the same row
    # regardless of source_file, so the loader must skip the cache-file
    # requirement for HI.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Hawaii's statewide 4.0% GET rate.

        ``source_file`` is intentionally ignored -- HI is non-SST and
        has no upstream file. Pass ``None`` from the loader.

        The four 0.5% county surcharges (Honolulu, Kauai, Hawaii
        County, Maui) authorized under HRS section 46-16.8 are NOT
        emitted as RateRow instances in v1; per-county data
        ingestion is deferred until a Hawaii boundary loader lands.
        See the module docstring's "Per-county surcharges" section
        for the full deferral rationale and the four enactment dates.
        Once that loader lands, additional ``RateRow`` instances with
        ``authority_type='county'`` and
        ``parent_authority_name='Hawaii'`` should be emitted here.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Hawaii",
            authority_type="state",
            rate_pct=Decimal("4.000"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundary rows shipped in v1.

        Hawaii has no county-level GET data file analogous to SST
        quarterly files or to Texas's Comptroller file. The four
        county surcharges (Honolulu / Kauai / Hawaii County / Maui)
        are documented in the module docstring; per-county boundary
        ingestion is deferred (mirrors CO/SC/MO/MS/NV deferral
        patterns).
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return Hawaii's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases consumed by the engine in v1.

        The GET pass-through grossing-up nuance (max visible
        pass-through 4.1666% on bare 4.0% GET; 4.7120% on Oahu's
        4.5% combined rate) is documented in the module docstring
        and ``specs/research/references.md`` for follow-up work; it
        is a seller-pricing concern, not a calculation-engine
        concern, and is intentionally not exposed via SpecialCase.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Hawaii has NO state-level GET holidays.

        Confirmed 2026-05-03 against the Hawaii Department of
        Taxation published guidance and the text of HRS Chapter
        237: there is no back-to-school holiday, no hurricane-prep
        holiday, no Energy Star holiday, and no other recurring
        exemption window. Bills proposing GET holidays have been
        introduced in past sessions but none have passed into law.
        Returns an empty iterator for every year, with a regression
        test in ``test_state_hawaii.py`` that exercises 2024-2030.
        """
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = Hawaii()
del _PROTOCOL_CHECK

HAWAII = register(Hawaii())
