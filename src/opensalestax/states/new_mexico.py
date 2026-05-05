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
LOCAL GRT MODELING -- top-30 location coverage via published combined rates
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
combined rate.

**This module ships the top-30 NM locations by population** with
combined rates seeded from the TRD GRT Rate Schedule effective
2026-01-01 (see :mod:`opensalestax.states.nm_data` for the source
URL, retrieval date, and the per-location rate table). Coverage:

- Albuquerque, Santa Fe, Las Cruces, Rio Rancho, Roswell,
  Farmington, Hobbs, Carlsbad, Clovis, Alamogordo, Gallup,
  Los Lunas, Sunland Park, Las Vegas (NM), Deming, Lovington,
  Artesia, Portales, Silver City, Espanola, Grants, Anthony,
  Bernalillo (town), Aztec, Bloomfield, Truth or Consequences,
  Belen, Taos, Ruidoso (29 distinct location codes; together
  ~70%+ of NM population).

**Published-combined-rate model:** TRD publishes ONE combined rate
per location code rather than the state/county/city breakdown.
This module mirrors that source-of-truth shape -- the per-location
combined-local rate (combined - 4.875%) is encoded as a single
"city" authority and the county authority sits at 0.000%. A
downstream caller asking about Albuquerque sees state 4.875% +
county 0.000% + city 3.000% = 7.875% combined, exactly reproducing
the published TRD value. See :mod:`opensalestax.states.nm_data`
docstring for the published-source rationale and the Connecticut-
pattern precedent.

**Deferred coverage** (long-tail): NM ZIPs entirely outside the
30 covered locations resolve to (state 4.875% + county 0.000%) =
4.875%, which under-counts the actual unincorporated-county GRT by
the county portion. The remaining unincorporated-county GRT is
NOT modeled in this ratchet -- a future per-county loader against
the TRD location-code CSV would close this remaining gap; the TRD
CSV is publicly downloadable under no license restrictions.

This phased deferral mirrors the precedent set by Colorado
(top home-rule cities first, long-tail home-rules deferred --
see ``specs/decisions/04-colorado-home-rule.md``), Louisiana
(state-only with 64 parishes deferred), Missouri (top-15 cities
+ statewide ZIP coverage with 0% long-tail counties in v0.30),
and South Carolina (per-county with city anchors).

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

The loader treats ``NewMexico.parse_rates`` as "self-seeded"
-- it returns the embedded state + per-county + per-location rows
and ignores the source-file argument. Use ``opensalestax data load
--state NM --version v1-state-county-city`` to insert them.

State maintainer: vacant -- see MAINTAINERS.md. The natural
next-contribution work for a NM maintainer:

1. A full per-county / per-municipality loader against the TRD
   quarterly Gross Receipts Tax Rate Schedule CSV (publicly
   available; no license fee). This would close the remaining
   under-collection gap on unincorporated-county ZIPs outside
   the top-30 covered locations.
2. Refresh ``NM_LOCATION_RATES`` and ``NM_LOCATION_EFFECTIVE_FROM``
   each January 1 and July 1 when TRD publishes a new schedule
   (rates may change at either revision date per NMSA 7-1-7).
3. Tracking the contingent-trigger 4.500% rate-cut path in
   HB 163 of 2022 -- if the revenue triggers ever fire, the
   ``parse_rates`` state row needs an ``effective_to`` and a
   successor row.
4. Annual update to the back-to-school holiday once the NM
   Legislature publishes the next year's date confirmation.

DISCLAIMER: This module is calculation infrastructure, not tax
advice. Maintainers and users are responsible for verifying
current TRD guidance and statutory text before relying on these
rules in production. Long-tail unincorporated-county GRT is not
yet fully modeled and ZIPs outside the top-30 covered locations
will under-collect by the county-portion. Sellers remain legally
responsible for GRT under NMSA 7-9-4 regardless of what their
billing software computes.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.states.nm_data import (
    NM_LOCATION_EFFECTIVE_FROM,
    NM_LOCATION_RATES,
    NM_STATE_EFFECTIVE_FROM,
    NM_STATE_RATE_PCT,
)
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
            "percentage points) is encoded for the top-30 NM locations "
            "by population via the published-combined-rate model in "
            "``nm_data`` (single 'city' authority per location, county "
            "at 0%); ZIPs outside the top 30 locations are NOT modeled "
            "yet for local GRT and resolve to 4.875% only -- combined "
            "rates actually range about 5.5% to 9.5% across all NM "
            "addresses. See module docstring for the deferred long-tail "
            "rationale (mirrors CO/LA precedent). Calculation only -- "
            "not tax advice."
        ),
    ),
}

# Statewide-rate constants live in :mod:`opensalestax.states.nm_data`
# (NM_STATE_RATE_PCT = 4.875%, NM_STATE_EFFECTIVE_FROM = 2023-07-01)
# along with the per-location combined-local rates seeded in
# NM_LOCATION_RATES. See that module's docstring for the published-
# combined-rate model and the published-source citation (TRD GRT
# Rate Schedule effective Jan 1, 2026).


class NewMexico:
    """New Mexico state module (tier 1; top-30 location coverage).

    NM imposes a GROSS RECEIPTS TAX (NOT a sales tax) -- see the
    module docstring for the GRT-vs-sales-tax legal distinction and
    the rationale for encoding the consumer-facing math as if it
    were sales tax for OpenSalesTax v1 compatibility.

    Local-option GRT (county + municipal increments) is now modeled
    for the top 30 NM locations by population using the
    published-combined-rate model -- the per-location combined-local
    rate is encoded as a single "city" authority and the county
    sits at 0.000%. See ``nm_data`` for the seeded locations and the
    NM TRD GRT Rate Schedule citation. NM ZIPs outside the top 30
    locations resolve to state 4.875% only (the remaining
    unincorporated-county GRT is NOT modeled in this ratchet,
    pending a future per-county loader).
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
        """Yield NM's state + per-county + per-location (city) rates.

        ``source_file`` is intentionally ignored -- NM is non-SST and
        has no upstream SST file. The combined-local rates are
        embedded in :mod:`opensalestax.states.nm_data` against the
        NM TRD GRT Rate Schedule effective 2026-01-01.

        Yields:

        - ONE state row at 4.875% (NMSA 7-9-4, effective 2023-07-01
          under HB 163 of 2022).
        - ONE county row per NM county at 0.000% (the county portion
          is folded into the per-location combined-local rate; see
          ``nm_data`` docstring for the published-source model). The
          county row exists so the engine can resolve every NM ZIP
          to a (state, county) authority stack via the boundary
          loader's ZIP_COUNTY pass.
        - ONE city row per :data:`NM_LOCATION_RATES` entry whose
          ``rate_pct`` is the combined-local (county + city +
          districts) layered on top of the 4.875% state portion.
          A consumer asking about Albuquerque sees state 4.875% +
          county 0.000% + city 3.000% = 7.875% combined, exactly
          reproducing the published TRD rate.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="New Mexico",
            authority_type="state",
            rate_pct=NM_STATE_RATE_PCT,
            effective_from=NM_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit ONE county RateRow per NM county that appears in the
        # location table at 0.000%. This lets the engine answer
        # "what county is ZIP X in" while keeping the entire local
        # GRT inside the city authority (matching how NM TRD
        # publishes rates). Sorted for deterministic output.
        nm_counties = sorted({county for (county, _r, _z) in NM_LOCATION_RATES.values()})
        for nm_county_name in nm_counties:
            yield RateRow(
                authority_name=nm_county_name,
                authority_type="county",
                rate_pct=Decimal("0.000"),
                effective_from=NM_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="New Mexico",
            )
        # Emit ONE city RateRow per covered location. The "city"
        # authority carries the combined-local (county + city +
        # special-district) rate -- see nm_data docstring.
        for location_name, (loc_county, loc_rate, _zips) in sorted(NM_LOCATION_RATES.items()):
            yield RateRow(
                authority_name=location_name,
                authority_type="city",
                rate_pct=loc_rate,
                effective_from=NM_LOCATION_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=loc_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, city]) boundary rows for NM ZIPs.

        Two passes (parallel to the SC/MO statewide-coverage pattern
        introduced in v0.31):

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county bindings for every ZIP intersecting an
           NM county represented in :data:`NM_LOCATION_RATES`. ZIPs
           that span multiple NM counties prefer the city-anchor
           county when the ZIP is in :data:`NM_LOCATION_RATES`.

        2. Emit city BoundaryRows for every :data:`NM_LOCATION_RATES`
           ZIP. Also emit state + county fallbacks for any city ZIP
           missed by the Census ZCTA pass (USPS-only ZIPs not in the
           Census ZCTA file).

        Per the FL/AZ/CA/SC/MO pattern, emit AT MOST ONE county per
        ZIP per Census ZCTA so cross-county-line ZIPs don't get bound
        to multiple counties (which would let the engine apply two
        different city rates to the same ZIP).

        Coverage caveat: an NM ZIP entirely outside any covered
        location resolves to (state 4.875% + county 0.000%) = 4.875%,
        which under-counts the actual unincorporated-county GRT by
        the county-portion. The 30 covered locations cover ~70%+ of
        NM population; the long-tail unincorporated under-collection
        is the deferred per-county loader work documented in the
        module docstring.
        """
        del source_file, version_label
        nm_counties_with_rates = {county for (county, _r, _z) in NM_LOCATION_RATES.values()}
        # Build city-anchor county map for cross-county-line ZIPs.
        city_county_for_zip: dict[str, str] = {}
        for _ln, (cc, _r, czs) in NM_LOCATION_RATES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Pass 1: state + county for every NM ZIP per Census ZCTA.
        # Emit at most one county per ZIP. Prefer the city-anchor
        # county if known; else the first NM county in deterministic
        # FIPS-sorted order (ZIP_COUNTY values are frozensets so we
        # must sort for stable output across test runs).
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            sorted_nm_pairs = sorted(cf for sa, cf in pairs if sa == "NM")
            chosen_county: str | None = None
            for county_fips in sorted_nm_pairs:
                nm_county_name = county_name("NM", county_fips)
                if nm_county_name is None or nm_county_name not in nm_counties_with_rates:
                    continue
                if preferred_county is not None:
                    if nm_county_name == preferred_county:
                        chosen_county = nm_county_name
                        break
                    # keep iterating in hopes of finding the city's county
                    continue
                # No city anchor -- take the first matching NM county.
                chosen_county = nm_county_name
                break
            if chosen_county is None and preferred_county is not None:
                # Census ZCTA didn't list the city's county at all
                # (USPS-only / boundary-mismatch ZIP). Trust the
                # city's declared county.
                chosen_county = preferred_county
            if chosen_county is None:
                # ZIP is in NM but in a county we don't yet have a
                # rate for (long-tail unincorporated counties). Skip
                # without binding so the engine returns "no match"
                # rather than a wrong county; future per-county
                # loader closes this gap.
                continue
            yield BoundaryRow(
                authority_name="New Mexico",
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
            emitted_zips.add(zip5)
        # Pass 2: city BoundaryRows for NM_LOCATION_RATES. Emit state
        # + county fallbacks for any city ZIP missed by Pass 1 so we
        # never regress city coverage.
        for location_name, (loc_county, _loc_rate, zips) in NM_LOCATION_RATES.items():
            for zip5 in zips:
                if zip5 not in emitted_zips:
                    yield BoundaryRow(
                        authority_name="New Mexico",
                        authority_type="state",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    yield BoundaryRow(
                        authority_name=loc_county,
                        authority_type="county",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    emitted_zips.add(zip5)
                yield BoundaryRow(
                    authority_name=location_name,
                    authority_type="city",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )

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
