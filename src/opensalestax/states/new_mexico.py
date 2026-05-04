# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""New Mexico state module (tier 1, non-SST).

============================================================================
TAX MODEL: GROSS RECEIPTS TAX (GRT) -- NOT A SALES TAX
============================================================================

New Mexico is one of three US jurisdictions (with Hawaii's General Excise
Tax and the now-renamed-to-sales-tax-but-historically-similar Arizona
Transaction Privilege Tax) that does **not** impose a traditional retail
sales tax. Instead, NM levies the **Gross Receipts Tax (GRT)** under
NMSA 1978 Chapter 7, Article 9 (the "Gross Receipts and Compensating
Tax Act").

The legal distinctions matter:

- **Sales tax** (typical US state) -- imposed on the BUYER as a percentage
  of the purchase price; the seller is a collection agent for the state.
- **Gross Receipts Tax** (NM) -- imposed on the **SELLER's gross
  receipts** from doing business in New Mexico (NMSA 7-9-4). The seller
  owes the tax even if they choose not to itemize a "tax line" on the
  customer's receipt. As a market practice nearly all NM sellers
  pass GRT through to buyers (the same way HI sellers pass GET
  through), making the consumer-facing math indistinguishable from
  sales tax. But the legal incidence is on the seller.

**For OpenSalesTax v1: this module models NM GRT as if it were sales
tax for API-shape compatibility**, identical to the approach taken for
HI's GET. A consumer calling ``/v1/calculate`` for an NM address gets
back a "tax amount" that matches the GRT a typical NM merchant would
add to the receipt. The legal-incidence distinction does not change
the calculation; it changes who is statutorily liable to remit, which
is downstream of OpenSalesTax's calculation scope (see constitution
section 13: "NOT a tax-filing service").

The first OpenSalesTax abstraction-bearing change to formally encode
the GRT model (e.g., a ``tax_model`` enum on ``StateModule``) is
deferred to v1.0+ when HI, NM, and any future GRT-style jurisdictions
need the same primitive and the abstraction can be designed once.

============================================================================
LOCAL GRT IS **NOT MODELED** in this v1 module
============================================================================

Each of New Mexico's **33 counties** and many of its **~106
municipalities** independently impose **local-option GRT increments**
on top of the 4.875% state rate. The combined rate at any given
address therefore ranges from about **5.5%** (an unincorporated
rural area with minimal county add-on) to about **9.5%** in the
densest urban codes (Albuquerque, Santa Fe, Las Cruces). A handful
of special-district codes can push the combined rate above 9.5%.

The New Mexico Taxation and Revenue Department (TRD) publishes a
quarterly **Gross Receipts Tax Rate Schedule** (the "FYI-200
companion" CSV / PDF) that maps every NM "location code" to its
combined rate. **v1 ships the state 4.875% portion only** -- a
caller computing tax for any populated NM address will under-collect
by the local-option layer (typically 1-4 percentage points).

This deferral mirrors the precedent set by:

- Colorado (state-only; ~70 home-rule cities deferred -- see
  ``specs/decisions/04-colorado-home-rule.md``)
- Louisiana (state-only; 64 parishes deferred -- see
  ``specs/decisions/05-louisiana-parishes.md``)
- South Carolina, Mississippi, Missouri, Nevada (statewide rate
  only; per-county add-ons deferred to per-county data ingestion)

A future per-NM-county loader -- analogous to a planned CO DR 1002
loader and a future LA-parish loader -- is the natural follow-on
contribution; the TRD location-code CSV is publicly downloadable
under no license restrictions and is the canonical primary source.

============================================================================
STATEWIDE RATE: 4.875% effective 2023-07-01
============================================================================

The current 4.875% state-portion GRT rate took effect **2023-07-01**
under **HB 163 of the 2022 Regular Session of the New Mexico
Legislature** (signed by Governor Lujan Grisham 2022-03-08), which
amended NMSA 7-9-4 to reduce the state portion from 5.000% to 4.875%
in two steps:

1. **5.000% -> 4.875%** effective 2022-07-01 (first step under HB 163)
   -- the actual 2022 step was 5.000% -> 5.0% (no change in headline),
   with the further reduction kicking in 2023-07-01.
2. **5.000% -> 4.875%** effective 2023-07-01 (second step, currently
   in effect)

A further reduction to 4.500% was contemplated in HB 163's original
language but was made contingent on revenue triggers that have **not**
been met as of the 2026 verification date; the rate remains at
**4.875%** for 2026 transactions. Future legislative action could
amend or repeal the trigger.

============================================================================
TAXABILITY MATRIX (state portion only)
============================================================================

- **Clothing** -- TAXABLE year-round at the 4.875% state GRT rate.
  NM has no general clothing exemption outside the annual
  back-to-school holiday described below.
- **Groceries (food for home consumption)** -- DEDUCTIBLE from
  GRT at retail food stores per **NMSA 7-9-92** ("Deduction; gross
  receipts; sale of food at retail food store"), effective
  **2005-01-01**. The deduction definition cross-references the
  federal SNAP-eligible food definition at 7 USCA 2012(k)(1).
  CRITICAL: unlike Georgia (state-only grocery exemption with
  locals still taxing), NM uses a **state hold-harmless
  distribution** under NMSA 7-1-6.46 and 7-1-6.47 -- the state
  general fund reimburses counties and municipalities for the
  local GRT they would otherwise have collected on grocery sales.
  As a result groceries are effectively exempt at BOTH state AND
  local levels at the consumer's perspective. The module marks
  groceries ``is_taxable=False`` and that answer is correct for
  the combined rate at every NM address.
- **Prescription drugs** -- DEDUCTIBLE per **NMSA 7-9-73.2**
  ("Deduction; gross receipts tax and governmental gross receipts
  tax; prescription drugs; oxygen; cannabis"). The deduction also
  covers insulin, oxygen and oxygen services provided by a
  licensed Medicare durable medical equipment provider, and
  cannabis products sold under the Lynn and Erin Compassionate
  Use Act (medical cannabis only -- the separate adult-use
  cannabis excise tax under the 2021 Cannabis Regulation Act is
  not modeled here). The deduction was enacted in 1998 and has
  been expanded multiple times.
- **Prepared food** -- TAXABLE. The food deduction in NMSA 7-9-92
  expressly applies to food **for home consumption** at retail
  food stores; restaurant meals, hot prepared foods, and similar
  ready-to-eat sales remain in the GRT base.
- **Digital goods** -- TAXABLE at the 4.875% state GRT rate
  effective **2019-07-01** under **HB 6 of the 2019 Regular
  Session** (signed 2019-04-04), which amended NMSA 7-9-3.5 to
  expand the definition of "property" subject to GRT to include
  "specified digital goods" -- music, photography, video, reading
  material, software, applications, ringtones, and similar
  digital products delivered electronically. SaaS / remotely-
  accessed software is taxable under the broader GRT base
  treating service receipts as taxable by default (NMSA 7-9-3.5's
  receipts-from-services language).
- **General tangible personal property** -- TAXABLE at the
  4.875% state rate per NMSA 7-9-4.

============================================================================
SALES-TAX HOLIDAY -- Annual Back-to-School Tax-Free Holiday
============================================================================

Per **NMSA 7-9-95** ("Deduction; gross receipts tax; sales of
certain tangible personal property; limited period"), as **amended
by HB 218 of the 2025 Regular Session** (signed April 2025), NM
runs an **annual back-to-school holiday** beginning at 12:01 a.m.
on the **last Friday in July** and ending at midnight the
following Sunday. (HB 218 moved the holiday forward by one week
from the historical "first Friday in August" timing because NM
public-school calendars now start earlier; the previous "first
Friday in August" formula governed the holiday from its 2005
enactment through 2024.)

For **2026** the last Friday in July is **July 31, 2026**, so the
2026 holiday runs **Friday July 31, 2026 through Sunday August 2,
2026** (three days, midnight-to-midnight inclusive).

NMSA 7-9-95 enumerates six categories of qualifying tangible
personal property each with its own per-item dollar threshold:

- **Clothing or footwear** designed to be worn on or about the
  human body, sales price **less than $100** per article (excludes
  athletic / protective gear and accessories like jewelry,
  handbags, luggage, umbrellas, wallets, watches)
- **Bookbags, backpacks, maps, and globes** sales price **less
  than $100** per article
- **Computers** (desktop, laptop, tablet, or notebook), sales
  price **$1,000 or less** per article (per the statute, includes
  e-readers with computing functions)
- **Computer-related items** (keyboards, microphones, monitors,
  mice, speakers, etc.), sales price **$500 or less** per article
- **Handheld calculators**, sales price **less than $200** per
  article
- **School supplies** (notebooks, paper, pencils, pens, art
  supplies, etc.), sales price **less than $30** per article

The holiday is encoded as **six separate ``HolidayWindow``
instances** (one per scope), each with the appropriate
``max_amount_per_item`` cap, so the engine can evaluate per-line-
item caps independently.

CRITICAL CAVEAT -- merchant election. Unlike most other states'
back-to-school holidays, NMSA 7-9-95 establishes a **deduction
the seller may claim**, not an automatic exemption. NM TRD
guidance (FYI-203) states: "Retailers electing to participate in
the tax holiday may claim a deduction for qualifying items;
those that don't participate must pay tax on otherwise eligible
sales and may recover the tax from the customer." The
``OpenSalesTax`` engine has no concept of "merchant elected to
participate" in v1, so the module yields the holiday windows
unconditionally -- callers should treat the reported zero-tax
result as the **eligible-for-exemption** answer, and downstream
business logic (e.g., point-of-sale software) should still allow
the merchant to choose whether to honor the holiday on each
qualifying line item. This caveat is repeated in each
``HolidayWindow.notes`` field.

The holiday applies to **state AND local GRT** (the entire
combined rate), so when the per-county loader eventually lands
the holiday windows here continue to govern.

Subsequent years (2027+) require an explicit data update; do
not extrapolate the statutory formula -- the legislature has
amended the date formula twice in twenty years and may do so
again.

============================================================================
LOADING AND MAINTAINER NOTES
============================================================================

The v0.2 loader treats ``NewMexico.parse_rates`` as "self-seeded"
-- it returns the single statewide row and ignores the source-file
argument. Use ``opensalestax data load --state NM
--version v1-statewide`` to insert it.

State maintainer: vacant -- see MAINTAINERS.md. The natural
next-contribution work for a NM maintainer:

1. A per-county / per-municipality loader against the TRD
   quarterly Gross Receipts Tax Rate Schedule CSV (publicly
   available; no license fee). This would close the
   under-collection gap that exists today for every NM address.
2. Tracking the contingent-trigger 4.500% rate-cut path in
   HB 163 of 2022 -- if the revenue triggers ever fire, the
   ``parse_rates`` row needs an ``effective_to`` and a successor
   row.
3. Annual update to the back-to-school holiday once the NM
   Legislature publishes the next year's date confirmation.

DISCLAIMER: This module is calculation infrastructure, not tax
advice. Maintainers and users are responsible for verifying
current TRD guidance and statutory text before relying on these
rules in production. Local GRT is NOT modeled in v1 and a v1
caller will under-collect on every populated NM address by the
local-option layer (typically 1-4 percentage points). Sellers
remain legally responsible for GRT under NMSA 7-9-4 regardless of
what their billing software computes.
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

# New Mexico GRT taxability matrix per NMSA 1978 Chapter 7, Article 9
# (state portion only). All citations are to NMSA 1978 unless otherwise
# noted. Per the constitution, every rule's notes field carries a
# statutory citation so a future maintainer can re-verify after any
# legislative session.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in New Mexico year-round at the 4.875% "
            "state GRT rate per NMSA 7-9-4 (general GRT imposition). "
            "NM has no general clothing exemption; only the annual "
            "back-to-school holiday under NMSA 7-9-95 (last Friday of "
            "July through following Sunday) deducts qualifying clothing "
            "and footwear under $100 per article. NM imposes a Gross "
            "Receipts Tax (NOT a sales tax) -- the legal incidence is "
            "on the seller's gross receipts, but the consumer-facing "
            "math is identical to a sales tax because sellers commonly "
            "pass GRT through. Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food for home consumption sold at a retail food store is "
            "DEDUCTIBLE from GRT per NMSA 7-9-92 (effective 2005-01-01). "
            "The deduction definition cross-references the federal SNAP "
            "definition of food at 7 USCA 2012(k)(1) and 'retail food "
            "store' at 7 USCA 2012(o)(1). Unlike Georgia (state-only "
            "exemption with locals still taxing groceries), NM uses a "
            "STATE HOLD-HARMLESS DISTRIBUTION under NMSA 7-1-6.46 and "
            "7-1-6.47 -- the state general fund reimburses counties and "
            "municipalities for local GRT that would otherwise apply, "
            "so groceries are effectively exempt at BOTH state AND "
            "local levels from the consumer perspective. Prepared food, "
            "candy, soft drinks, and restaurant meals are NOT covered "
            "by the section 7-9-92 deduction and remain in the GRT "
            "base. Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are DEDUCTIBLE from GRT per NMSA "
            "7-9-73.2 ('Deduction; gross receipts tax and governmental "
            "gross receipts tax; prescription drugs; oxygen; "
            "cannabis'), enacted 1998 and expanded multiple times. The "
            "deduction also covers insulin, oxygen and oxygen services "
            "provided by a licensed Medicare durable medical equipment "
            "provider, and cannabis products sold under the Lynn and "
            "Erin Compassionate Use Act (medical cannabis only). The "
            "separate adult-use cannabis excise tax (2021 Cannabis "
            "Regulation Act) is NOT modeled here. Calculation only -- "
            "not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot prepared foods, "
            "ready-to-eat deli items) is TAXABLE under GRT at the "
            "4.875% state rate per NMSA 7-9-4. The food-for-home-"
            "consumption deduction in NMSA 7-9-92 covers retail food "
            "stores and explicitly excludes prepared meals. Many NM "
            "municipalities additionally levy local-option GRT on top "
            "of the state portion (not modeled in v1 -- see module "
            "docstring). Calculation only -- not tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are TAXABLE under New Mexico GRT at the "
            "4.875% state rate effective 2019-07-01 per HB 6 of the "
            "2019 Regular Session (signed 2019-04-04), which amended "
            "NMSA 7-9-3.5 to expand 'property' subject to GRT to "
            "include 'specified digital goods' -- music, photography, "
            "video, reading material, software, applications, "
            "ringtones, and similar products delivered electronically. "
            "SaaS / remotely-accessed software is taxable under the "
            "broader GRT base treating receipts from services as "
            "taxable by default. Pre-2019-07-01 transactions used a "
            "narrower digital base; this module encodes the "
            "post-2019-07-01 state. Calculation only -- not tax "
            "advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property and most services are "
            "subject to New Mexico Gross Receipts Tax at the 4.875% "
            "state rate per NMSA 7-9-4 (effective 2023-07-01 under "
            "HB 163 of the 2022 Regular Session, which reduced the "
            "state portion from 5.000% to 4.875%). NM imposes a GROSS "
            "RECEIPTS TAX on the seller's gross receipts, NOT a sales "
            "tax on the buyer; this module encodes the consumer-facing "
            "math as if it were a sales tax (sellers pass GRT through "
            "to customers as a market practice). LOCAL GRT (county + "
            "municipal local-option increments, typically 1-4 "
            "percentage points) is NOT modeled in v1 -- combined rates "
            "actually range about 5.5% to 9.5% across NM addresses. "
            "See module docstring for the deferred-locals rationale "
            "(mirrors CO/LA precedent). Calculation only -- not tax "
            "advice."
        ),
    ),
}

# Statewide-rate effective date: July 1, 2023. The 4.875% state-portion
# rate took effect under HB 163 of the 2022 Regular Session (signed
# 2022-03-08), which amended NMSA 7-9-4. A further contingent reduction
# to 4.500% remains on the books but has not been triggered as of 2026.
_RATE_EFFECTIVE_FROM = dt.date(2023, 7, 1)
_RATE_PCT = Decimal("4.875")


class NewMexico:
    """New Mexico state module (tier 1; STATE PORTION ONLY in v1).

    NM imposes a GROSS RECEIPTS TAX (NOT a sales tax) -- see the
    module docstring for the GRT-vs-sales-tax legal distinction and
    the rationale for encoding the consumer-facing math as if it
    were sales tax for OpenSalesTax v1 compatibility.

    Local-option GRT (county + municipal increments) is NOT modeled
    in v1; combined rates at any populated NM address are
    under-collected by 1-4 percentage points until a per-county
    loader against the TRD location-code CSV lands. See the module
    docstring for the deferred-locals rationale.
    """

    state_abbrev: str = "NM"
    state_name: str = "New Mexico"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # NM is not an SST member and has no quarterly upstream rate file
    # the loader can read; parse_rates returns the same statewide row
    # regardless of source_file. The loader checks this flag to skip
    # the cache-file requirement.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield New Mexico's statewide 4.875% GRT rate.

        ``source_file`` is intentionally ignored -- NM is non-SST and
        has no upstream file. Pass ``None`` from the loader.

        The 4.875% rate took effect 2023-07-01 under HB 163 of the
        2022 Regular Session amending NMSA 7-9-4. ``effective_to`` is
        ``None`` because the further-reduction triggers in HB 163
        have not fired and there is no scheduled sunset; if/when the
        4.500% trigger fires this method must be updated to emit a
        successor row with the appropriate effective dates.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="New Mexico",
            authority_type="state",
            rate_pct=_RATE_PCT,
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundaries shipped in v1.

        NM has 33 counties + ~106 municipalities each with their own
        local-option GRT increment. A per-county loader against the
        TRD quarterly Gross Receipts Tax Rate Schedule CSV is the
        natural next contribution; until then no sub-state authorities
        are emitted. See the module docstring for the deferred-locals
        rationale (mirrors CO/LA/SC/MS/MO/NV precedent).
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return NM's state-portion GRT taxability rule for ``item_category``.

        Note: groceries and prescription drugs answer
        ``is_taxable=False`` for both state and local layers because
        the NM hold-harmless distribution under NMSA 7-1-6.46 /
        7-1-6.47 reimburses locals for the deductions allowed by
        sections 7-9-92 / 7-9-73.2 -- the consumer sees zero tax on
        these items at any NM address. See module docstring.
        """
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No SpecialCase entries tracked for NM in v1.

        The GRT-vs-sales-tax model distinction and the merchant-
        election quirk on the back-to-school holiday are documented
        in the module docstring; the SpecialCase API is reserved for
        engine-consumed quirks (Phase 5+).
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """New Mexico Annual Back-to-School Tax-Free Holiday.

        Per NMSA 7-9-95 as amended by HB 218 of the 2025 Regular
        Session, the holiday begins at 12:01 a.m. on the **last
        Friday in July** and ends at midnight the following Sunday.
        Prior to the HB 218 amendment the formula was "first Friday
        in August through following Sunday"; the change moved the
        holiday forward by one week to better align with NM public-
        school start dates.

        For 2026 the last Friday in July is **Friday, July 31,
        2026**, so the 2026 holiday runs **July 31 through
        August 2, 2026**.

        The holiday is encoded as SIX separate ``HolidayWindow``
        instances (one per statutory scope), each with the
        appropriate per-item dollar cap:

        - Clothing/footwear < $100 per article
        - Bookbags/backpacks/maps/globes < $100 per article
        - Computers (desktop, laptop, tablet, notebook) <= $1,000
          per article
        - Computer-related items (keyboards, monitors, etc.)
          <= $500 per article
        - Handheld calculators < $200 per article
        - School supplies < $30 per article

        CRITICAL CAVEAT -- merchant election. NMSA 7-9-95 creates a
        deduction the SELLER may claim, not an automatic exemption.
        Per TRD FYI-203, retailers may opt in or out per transaction;
        non-participating sellers must remit GRT and may recover it
        from the customer. The OpenSalesTax engine has no
        merchant-election concept in v1, so this module yields the
        windows unconditionally -- callers should treat the
        zero-tax result as the eligible-for-exemption answer.

        Subsequent years require explicit data updates; do not
        extrapolate the statutory formula -- the legislature has
        amended the date formula twice in twenty years and may do so
        again.
        """
        if year != 2026:
            return iter(())
        # 2026 holiday: July 31 (last Friday in July) through August 2.
        starts_on = dt.date(2026, 7, 31)
        ends_on = dt.date(2026, 8, 2)
        # Common notes prefix (statute + merchant-election caveat)
        # repeated per-window so the warning surfaces wherever the
        # engine quotes a HolidayWindow.notes field.
        _COMMON = (
            "NMSA 7-9-95 (Back-to-School Tax-Free Holiday) as amended "
            "by HB 218 of 2025 (last Friday in July through following "
            "Sunday). Applies to STATE AND LOCAL GRT. MERCHANT-"
            "ELECTION caveat: NMSA 7-9-95 creates a deduction the "
            "SELLER may claim, not an automatic exemption -- per TRD "
            "FYI-203 retailers opt in or out per transaction; "
            "non-participating sellers remit GRT and may recover from "
            "the customer. OpenSalesTax v1 has no merchant-election "
            "concept; callers should treat the zero-tax result as the "
            "ELIGIBLE-FOR-EXEMPTION answer. Calculation only -- not "
            "tax advice."
        )
        return iter(
            [
                HolidayWindow(
                    name="New Mexico Back-to-School: Clothing and Footwear (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("clothing",),
                    # Statute: "less than $100" per article -- engine
                    # treats max_amount_per_item as inclusive cap; we
                    # encode 99.99 to mirror the strict "less than"
                    # threshold while keeping the field a Decimal.
                    max_amount_per_item=Decimal("99.99"),
                    notes=(
                        "Clothing/footwear designed to be worn on or "
                        "about the human body, sales price LESS THAN "
                        "$100 per article. EXCLUDES athletic / "
                        "protective gear primarily designed for sport "
                        "or protective use, and accessories (jewelry, "
                        "handbags, luggage, umbrellas, wallets, "
                        "watches). " + _COMMON
                    ),
                ),
                HolidayWindow(
                    name="New Mexico Back-to-School: Bookbags and Backpacks (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("bookbags",),
                    max_amount_per_item=Decimal("99.99"),
                    notes=(
                        "Bookbags, backpacks, maps, and globes, sales "
                        "price LESS THAN $100 per article. " + _COMMON
                    ),
                ),
                HolidayWindow(
                    name="New Mexico Back-to-School: Computers (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("computers",),
                    # Statute: "$1,000 or less" per article -- inclusive,
                    # so $1000.00 exactly is encoded.
                    max_amount_per_item=Decimal("1000.00"),
                    notes=(
                        "Computers (desktop, laptop, tablet, "
                        "notebook), sales price $1,000 OR LESS per "
                        "article. Per the statute, includes e-readers "
                        "with computing functions. " + _COMMON
                    ),
                ),
                HolidayWindow(
                    name="New Mexico Back-to-School: Computer Hardware (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("computer_hardware",),
                    # Statute: "$500 or less" per article -- inclusive.
                    max_amount_per_item=Decimal("500.00"),
                    notes=(
                        "Computer-related items (keyboards, "
                        "microphones, monitors, mice, speakers, and "
                        "similar peripherals), sales price $500 OR "
                        "LESS per article. " + _COMMON
                    ),
                ),
                HolidayWindow(
                    name="New Mexico Back-to-School: Handheld Calculators (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("calculators",),
                    # Statute: "less than $200" per article.
                    max_amount_per_item=Decimal("199.99"),
                    notes=(
                        "Handheld calculators, sales price LESS THAN "
                        "$200 per article. " + _COMMON
                    ),
                ),
                HolidayWindow(
                    name="New Mexico Back-to-School: School Supplies (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("school_supplies",),
                    # Statute: "less than $30" per article.
                    max_amount_per_item=Decimal("29.99"),
                    notes=(
                        "School supplies (notebooks, paper, pencils, "
                        "pens, art supplies, and similar items), "
                        "sales price LESS THAN $30 per article. " + _COMMON
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = NewMexico()
del _PROTOCOL_CHECK

NEW_MEXICO = register(NewMexico())
