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

Per-county surcharges (SHIPPED in v0.32)
----------------------------------------
Hawaii authorizes each of its four inhabited counties to enact a
**0.5% county surcharge** on top of the state GET under **HRS
section 46-16.8** (county surcharge on state tax). As of the Hawaii
Department of Taxation county-surcharge schedule (verified
2026-07-06), all four inhabited counties now impose the 0.5%
surcharge:

- **Honolulu County** (City and County of Honolulu, the entire
  island of Oahu) -- **0.5% effective 2007-01-01**, the longest-
  running county surcharge. Combined Oahu GET rate: **4.5%**.
- **Kauai County** (the entire island of Kauai) -- **0.5% effective
  2019-01-01**. Combined GET: **4.5%**.
- **Hawaii County** (the Big Island) -- **0.5% effective
  2020-01-01**. Combined GET: **4.5%**.
- **Maui County** (Maui, Molokai, Lanai, and Kahoolawe) -- **0.5%
  effective 2024-01-01** through 2030-12-31, enacted by County
  Ordinance 5511 (signed 2023-07-19). Combined GET: **4.5%**.
  (Corrected 2026-07-06: an earlier revision wrongly recorded Maui
  at 4.0% "no surcharge"; the surcharge has in fact been in effect
  since 2024-01-01.)

Per-county data is now seeded in :mod:`opensalestax.states.hi_data`
(``HI_COUNTY_RATE_PCT`` / ``HI_COUNTY_SURCHARGE_EFFECTIVE``).
:meth:`Hawaii.parse_rates` emits a state RateRow plus one county
RateRow per HI county; :meth:`Hawaii.parse_boundaries` iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` and emits state +
county bindings for every HI ZIP (mirrors the SC/VA/MS pattern with
FIPS-sort + city-anchor dedup).

A 5th HI county FIPS exists for **Kalawao County** (FIPS 005, the
former Hansen's-disease settlement on Molokai administered by the
State Department of Health, ~80 residents); it has no county
government authority to levy a surcharge and is encoded at 0% so
the boundary loader can resolve its single ZIP (96742) to a
queryable state-only rate.

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
from pathlib import Path

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.states.hi_data import (
    HI_COUNTY_RATE_PCT,
    HI_COUNTY_SURCHARGE_EFFECTIVE,
    HI_STATE_EFFECTIVE_FROM,
    HI_STATE_RATE_PCT,
)
from opensalestax.states.protocol import (
    BoundaryRow,
    HolidayWindow,
    RateRow,
    ShippingRule,
    ShippingRuleSet,
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
            "all four inhabited counties the combined rate is 4.5% "
            "(state 4.0% + 0.5% county surcharge under HRS section "
            "46-16.8); Maui County's surcharge took effect 2024-01-01. "
            "Calculation only -- not legal or tax advice."
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
            "Per-county surcharges under HRS section 46-16.8 are now "
            "encoded (v0.32): Honolulu 0.5% since 2007, Kauai 0.5% "
            "since 2019, Hawaii County 0.5% since 2020, Maui 0.5% "
            "since 2024 (all four inhabited counties now at combined "
            "4.5%). Calculation only -- not legal or tax advice."
        ),
    ),
}

# Statewide-rate effective date: January 1, 1965. The 4.0% general-
# retail GET rate took effect under Act 155, SLH 1965, which raised
# the rate from 3.5% to 4.0% effective 1965-01-01. The 4.0% general
# rate has been stable for the 60+ years since. Per-county 0.5%
# surcharges layered on top under HRS section 46-16.8 are now
# encoded (v0.32) via :mod:`opensalestax.states.hi_data`.
_RATE_EFFECTIVE_FROM = HI_STATE_EFFECTIVE_FROM


class Hawaii:
    """Hawaii state module (tier 1; state 4.0% GET + per-county surcharges).

    See module docstring for the General Excise Tax legal model and
    the rationale for encoding HI as a sales tax for API purposes.
    Per-county surcharges (Honolulu / Kauai / Hawaii / Maui)
    shipped in v0.32 via :mod:`opensalestax.states.hi_data`.
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
        """Yield Hawaii's state 4.0% GET + per-county surcharge rates.

        ``source_file`` is intentionally ignored -- HI is non-SST and
        has no upstream file. Pass ``None`` from the loader.

        Counties yielded: every county in :data:`HI_COUNTY_RATE_PCT`
        (Hawaii / Honolulu / Kalawao / Kauai / Maui). The
        ZIP_COUNTY-driven boundary loader binds every HI ZIP to its
        county, so every county must have a queryable rate (even the
        0% ones -- Kalawao has no county tax authority). Per-county
        effective
        dates from :data:`HI_COUNTY_SURCHARGE_EFFECTIVE` are used for
        counties with a surcharge enacted; the state effective date is
        used as a placeholder for 0% counties so the audit trail still
        records a valid effective range.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Hawaii",
            authority_type="state",
            rate_pct=HI_STATE_RATE_PCT,
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a county RateRow for every HI county. The ZIP_COUNTY-
        # driven boundary loader binds every HI ZIP to its county, so
        # every county must have a queryable rate (even the 0% ones).
        for hi_county_name in sorted(HI_COUNTY_RATE_PCT):
            county_effective = (
                HI_COUNTY_SURCHARGE_EFFECTIVE.get(hi_county_name) or _RATE_EFFECTIVE_FROM
            )
            yield RateRow(
                authority_name=hi_county_name,
                authority_type="county",
                rate_pct=HI_COUNTY_RATE_PCT[hi_county_name],
                effective_from=county_effective,
                effective_to=None,
                parent_authority_name="Hawaii",
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county) boundary rows for every HI ZIP.

        Iterates :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
        emits state + county bindings for every ZIP intersecting an
        HI county. Mirrors the v0.31 SC/VA/MS pattern with FIPS-sort
        + city-anchor dedup -- HI has no city-level GET, so there is
        no city-anchor map to consult; the FIPS-sorted single-county
        pick handles the (very rare) cross-county-line ZIP cases
        (e.g., a ZIP that Census lists under both Maui and Kalawao).
        """
        del source_file, version_label
        # Pass 1: state + county for every HI ZIP per Census ZCTA.
        # Emit at most one county per ZIP: take the first HI county
        # in deterministic FIPS-sorted order. (HI has no city-level
        # GET, so no city-anchor preference is needed.)
        for zip5, pairs in ZIP_COUNTY.items():
            sorted_hi_pairs = sorted(cf for sa, cf in pairs if sa == "HI")
            chosen_county: str | None = None
            for county_fips in sorted_hi_pairs:
                hi_county_name = county_name("HI", county_fips)
                if hi_county_name is None or hi_county_name not in HI_COUNTY_RATE_PCT:
                    continue
                chosen_county = hi_county_name
                break
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Hawaii",
                authority_type="state",
                zip5=zip5,
                zip4_low=None,
                zip4_high=None,
            )
            yield BoundaryRow(
                authority_name=chosen_county,
                authority_type="county",
                zip5=zip5,
                zip4_low=None,
                zip4_high=None,
            )

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

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Hawaii's GET applies unconditionally to all gross receipts.

        Unlike most US states, HI levies a Gross Excise Tax on the
        seller rather than a sales tax on the buyer; "gross receipts"
        includes shipping with no separately-stated or
        items-taxable exception. Shipping is therefore always taxable
        whether bundled or itemized.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.ALWAYS_TAXABLE,
            citation="Hawaii GET applies to all gross receipts including shipping (HRS chapter 237)",
        )


_PROTOCOL_CHECK: StateModule = Hawaii()
del _PROTOCOL_CHECK

HAWAII = register(Hawaii())
