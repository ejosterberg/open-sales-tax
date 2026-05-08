# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Alabama state module (tier 1, non-SST) -- top-30-city coverage.

WARNING -- INDEPENDENT-LOCALS / HOME-RULE LIMITATION (PARTIAL)
--------------------------------------------------------------
Alabama has the most fragmented local sales-tax landscape in the
United States. The state has:

- **67 counties**, most of which levy their own county sales taxes.
- **Approximately 700+ municipalities** (cities and towns), many of
  which **self-administer** their own sales tax with their own
  rates, exemptions, and definitions of taxable items. Some
  municipalities use the Alabama Department of Revenue (ALDOR) for
  collection of their local tax (state-administered locals); many
  others contract with private third-party administrators (RDS,
  Avenu, Berman) or administer collection in-house.

The combined state + county + city sales tax rate at any given
Alabama address commonly falls in the **9-12%** range and reaches
**13.5%** in a handful of cities (Arab in Marshall/Cullman counties
historically among the highest combined rates). The state portion
alone is **only 4.0%**, one of the lowest state-level general sales
tax rates in the nation per Ala. Code section 40-23-2(1) -- a deliberate
design choice that pushes the bulk of sales-tax revenue down to the
county and municipal layers.

**This module ships the state 4.0% rate plus a top-30-city seed**
covering Birmingham, Huntsville, Mobile, Montgomery, Tuscaloosa,
Hoover, Auburn, Dothan, Decatur, Madison, Florence, Vestavia Hills,
Phenix City, Prattville, Gadsden, Alabaster, Opelika, Northport,
Enterprise, Daphne, Homewood, Bessemer, Athens, Pelham, Anniston,
Mountain Brook, Trussville, Helena, Foley, and Selma. All 67
counties are emitted (counties NOT touched by a covered city sit at
a 0.000% PLACEHOLDER pending future maintainer audit, mirroring the
MO long-tail pattern). See :mod:`opensalestax.states.al_data` for
per-county rates and per-city ZIP coverage.

The remaining ~670 self-administering home-rule municipalities are
**still NOT modelled** -- API consumers calling ``/v1/calculate``
for an address inside an unseeded Alabama locality (or a
PLACEHOLDER-county ZIP) will continue to receive a partial
**under-collection** of tax (the unseeded city's portion plus, where
applicable, an unseeded county's portion).

The full architectural rationale for the home-rule deferral
(applied here only to the long tail of ~670 unseeded cities; the
top 30 are covered by this ratchet) lives in
``specs/decisions/04-colorado-home-rule.md`` (the Colorado precedent
with the same self-administering-cities pattern) and
``specs/decisions/05-louisiana-parishes.md`` (the Louisiana parish
precedent for a state with comparable local fragmentation). Full
coverage of the entire ~700-city landscape requires the
**SubJurisdiction Protocol** extension that those decision documents
identify as future work; that schema change is intentionally
deferred to v1.0+ when Colorado, Louisiana, and the rest of the
Alabama long tail can all be the canonical first consumers of the
new abstraction at once.

State-level model summary
-------------------------
Three concurrent regimes operate in Alabama:

1. **State** -- 4.0% statewide general sales tax per Ala. Code
   section 40-23-2(1), in effect since 1959 (raised to 4.0% in 1969;
   has been stable at 4.0% since). Specific lower state rates apply
   to certain transaction categories (groceries -- see below;
   automotive 2.0%; manufacturing machinery 1.5%; farm machinery
   1.5%) which the v1 engine does not yet apply per category.
2. **County** (67 counties) -- additional county sales taxes,
   typically 1.0-3.0%. Some county taxes are state-administered
   (ALDOR collects); others are administered by the county itself
   or a third-party administrator. **All 67 are emitted as
   authorities** by this module so the boundary loader can resolve
   every AL ZIP to a county, but counties NOT touched by a covered
   city sit at a 0.000% PLACEHOLDER pending future maintainer audit.
3. **Municipal** (~700+ cities/towns) -- additional municipal
   sales taxes that vary widely; many are **self-administered**
   under Ala. Code section 11-51-200 et seq. (the municipal
   sales/use tax statute) which permits home-rule administration.
   Combined municipal rates of 4.0-5.5% are common. **Top 30 by
   population are seeded; the remaining ~670 are deferred** to a
   future SubJurisdiction Protocol ratchet.

GROCERY PHASE-DOWN -- HISTORICAL AND CURRENT RATE
-------------------------------------------------
Alabama is one of the few remaining states that historically taxed
food at the full general state rate. The legislature has been
phasing the state-portion grocery rate down:

- **Pre-2023-09-01:** food taxed at the full 4.0% general state rate.
- **HB 479 of 2023 (Act 2023-554):** reduced the state-portion
  grocery rate to **3.0%** effective **2023-09-01**, with a
  conditional further reduction to 2.0% if Education Trust Fund
  growth conditions were met.
- **HB 386 of 2024 (Act 2024-437):** removed the ETF-growth
  precondition and reduced the state-portion grocery rate to
  **2.0%** effective **2025-09-01**.

The **current state-portion grocery rate (verified 2026-05-03) is
2.0%.** Codified at Ala. Code section 40-23-2(5) (post-2024
renumbering). Local sales taxes (county and municipal) still apply
to groceries at their full local rate -- the state phase-down does
NOT reduce the local-portion grocery tax. Combined effective grocery
rates inside Alabama cities therefore commonly remain in the 7-9%
range despite the reduced state rate.

Encoded in this module via ``rate_modifier=Decimal("2.000")`` on the
groceries TaxabilityRule (mirrors the AR/KS/OK reduced-grocery-rate
pattern). The engine has applied ``rate_modifier`` since v0.11.1.

Taxability matrix (statewide rules; per Ala. Code Title 40, Chapter
23)
-------------------------------------------------------------------

- **Clothing** -- TAXABLE at the full 4.0% state rate. Alabama has
  no general clothing exemption; clothing is taxed as ordinary
  tangible personal property (Ala. Code section 40-23-2(1)). The
  annual Back-to-School Sales Tax Holiday (Ala. Code section
  40-23-211) provides a three-day exemption for clothing items
  priced $100 or less per item (see "Sales-tax holidays" below).
- **Groceries (food and food ingredients)** -- TAXABLE at the
  REDUCED 2.0% state rate effective 2025-09-01 per HB 386 of 2024.
  See the "Grocery phase-down" section above for the full statutory
  history. Local sales taxes apply at full local rate; only the
  state portion is reduced.
- **Prescription drugs** -- EXEMPT per Ala. Code section
  40-23-4(a)(20). Drugs prescribed by a licensed physician,
  dentist, optometrist, or other licensed practitioner are exempt
  from state sales/use tax when sold by a registered pharmacy.
  Most counties and municipalities follow the state exemption but
  exemption status varies locally and is not modeled here.
- **Prepared food** -- TAXABLE at the full 4.0% state rate. The
  reduced 2.0% grocery rate explicitly excludes prepared food (any
  food sold heated, sold with eating utensils provided by the
  seller, or sold in a state where it is ready for immediate
  consumption). Many Alabama municipalities layer additional
  restaurant or hospitality taxes that are administered locally
  and not modeled here.
- **Digital goods** -- TAXABLE at the 4.0% state rate. Alabama
  treats "specified digital products" as tangible personal
  property under ALDOR Administrative Rule 810-6-1-.37 and the
  related Title 40 definitions (the underlying statutory text in
  Ala. Code section 40-23-1 includes electronic transfers within
  the "tangible personal property" definition for sales-tax
  purposes; ALDOR has issued guidance applying the rule to
  downloaded software, music, video, books, and games). Streaming
  services are a moving target across multiple legislative
  attempts; verify current ALDOR guidance before relying on the
  digital_goods rule for streaming transactions specifically.

Sales-tax holidays (state-side scope; counties/cities must opt in)
------------------------------------------------------------------
Alabama has TWO annual sales-tax holidays codified in Title 40,
Chapter 23. Both are STATE holidays -- the **state portion** is
exempted automatically; **counties and municipalities must opt
in** by ordinance/resolution to extend the exemption to their local
portion. Many do; many do not. ALDOR publishes an annual list of
participating localities each year; this module encodes only the
state-side scope and documents the local-opt-in caveat.

1. **Severe Weather Preparedness Sales Tax Holiday** -- Ala. Code
   section 40-23-210 et seq. Three-day weekend (Friday through
   Sunday) covering the **last full weekend of February**. For
   2026 the dates are **February 27 (Friday) through March 1
   (Sunday)** because February 28, 2026 is a Saturday and the
   first day of the weekend is Friday February 27. Covers:

   - **Generators with sales price $1,000 or less per item**
     (typically portable, gasoline-powered backup generators)
   - **Severe-weather-preparedness items with sales price $60 or
     less per item** (batteries, flashlights, weather-band radios,
     tarps, plywood, ground anchor systems, gas/diesel fuel
     containers, ice packs, fire extinguishers, smoke / CO
     detectors, first-aid kits, etc.)

2. **Back-to-School Sales Tax Holiday** -- Ala. Code section
   40-23-211. Three-day weekend (Friday through Sunday) covering
   the **third full weekend of July**. For 2026 the dates are
   **July 17 (Friday) through July 19 (Sunday)**. Covers four
   scopes:

   - **Clothing -- $100 or less per article**
   - **Computers / computer equipment / software -- $750 or less
     per item** (single-purchase transaction)
   - **School supplies -- $50 or less per item**
   - **Books -- $30 or less per item** (noncommercial purchases)

Both holidays are encoded as separate ``HolidayWindow`` instances
per scope so the engine can apply per-item caps correctly. Future
years require explicit data updates -- the legislature has
historically been stable on these dates but local-opt-in
participation lists change annually.

Loading
-------
The v0.2 loader treats ``Alabama.parse_rates`` as "self-seeded"
(Alabama is non-SST and has no quarterly upstream file). Use
``opensalestax data load --state AL --version v0.13-statewide`` to
insert the state row.

State maintainer: vacant -- see MAINTAINERS.md. Alabama is one of the
**three canonical priority candidates** (alongside Colorado and
Louisiana) for the v1.0+ SubJurisdiction Protocol abstraction. An
interested maintainer who knows the ALDOR rate database and at least
one major Alabama metro's municipal tax code (Birmingham, Mobile,
Huntsville, Montgomery) would be the natural lead.

DISCLAIMER: This is calculation logic, not tax advice. Maintainers
and users are responsible for verifying current ALDOR, county, and
municipal guidance before relying on these rules in production.
County and municipal tax portions are NOT modeled in v1; a v1 caller
will under-collect tax on every populated Alabama address. See the
"INDEPENDENT-LOCALS / HOME-RULE LIMITATION" section above and
``specs/decisions/04-colorado-home-rule.md``.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.states.al_data import (
    AL_CITIES,
    AL_COUNTY_RATE_PCT,
    AL_STATE_EFFECTIVE_FROM,
    AL_STATE_RATE_PCT,
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

# Alabama taxability matrix per Ala. Code Title 40, Chapter 23 (state
# portion only). County and municipal taxability vary independently
# under the home-rule / self-administered-locals regime and are NOT
# captured here -- see the module docstring's
# INDEPENDENT-LOCALS / HOME-RULE LIMITATION section and
# specs/decisions/04-colorado-home-rule.md for the architectural
# rationale for the deferral.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Alabama year-round at the 4.0% "
            "state rate per Ala. Code section 40-23-2(1) (general "
            "tangible personal property). Alabama has no general "
            "clothing exemption. The annual Back-to-School Sales Tax "
            "Holiday (Ala. Code section 40-23-211) provides a "
            "three-day exemption in mid-July for clothing items "
            "priced $100 or less per article. County and municipal "
            "sales taxes apply at full local rate and may diverge "
            "from the state -- this module models the state portion "
            "only. Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("2.000"),
        notes=(
            "Food and food ingredients are TAXABLE in Alabama at a "
            "REDUCED 2.0% state rate effective 2025-09-01 per HB 386 "
            "of 2024 (Act 2024-437), codified at Ala. Code section "
            "40-23-2(5). Statutory history of the state-portion "
            "grocery rate phase-down: 4.0% pre-2023-09-01; 3.0% "
            "effective 2023-09-01 per HB 479 of 2023 (Act 2023-554); "
            "2.0% effective 2025-09-01 per HB 386 of 2024. The "
            "rate_modifier=Decimal('2.000') marks the special state "
            "rate; the engine has applied rate_modifier since v0.11.1 "
            "(mirrors the AR/KS/OK/NC/MS/MO reduced-grocery-rate "
            "pattern). Items NOT meeting the SST 'food and food "
            "ingredients' definition (candy, soft drinks, prepared "
            "food, dietary supplements, alcohol, tobacco) remain at "
            "the general 4.0% state rate. Local sales taxes (county "
            "and municipal) apply to groceries at FULL local rate -- "
            "the state phase-down does not reduce the local-portion "
            "grocery tax. Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT from the Alabama state "
            "sales tax per Ala. Code section 40-23-4(a)(20). The "
            "exemption covers drugs prescribed by a licensed "
            "physician, dentist, optometrist, or other licensed "
            "practitioner, when sold by a registered pharmacy for "
            "human use. Over-the-counter drugs do NOT qualify even "
            "when prescribed. Most Alabama counties and "
            "municipalities follow the state exemption but local "
            "exemption status is not uniform; verify with the "
            "specific locality before relying. Calculation only -- "
            "not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot prepared foods, "
            "food sold with eating utensils provided by the seller, "
            "food sold ready for immediate consumption) is TAXABLE "
            "at the full 4.0% Alabama state rate per Ala. Code "
            "section 40-23-2(1). The reduced 2.0% grocery rate at "
            "section 40-23-2(5) explicitly excludes prepared food "
            "under the SST 'food and food ingredients' definition "
            "framework. Many Alabama municipalities layer additional "
            "restaurant or hospitality taxes that are administered "
            "locally and not modeled here. Calculation only -- not "
            "tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products (downloaded software, music, "
            "video, books, games, ringtones) are TAXABLE in Alabama "
            "at the 4.0% state rate. Alabama treats digital products "
            "as tangible personal property under ALDOR "
            "Administrative Rule 810-6-1-.37 and the related Ala. "
            "Code section 40-23-1 definitions. Streaming services "
            "and SaaS are a MOVING TARGET across multiple "
            "legislative sessions and pending ALDOR guidance "
            "iterations; verify the current ALDOR position before "
            "relying on the digital_goods rule for streaming or "
            "subscription-based transactions specifically. "
            "Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in "
            "Alabama at the 4.0% state rate per Ala. Code section "
            "40-23-2(1). Specific lower state rates apply to certain "
            "categories (automotive 2.0% per section 40-23-2(4); "
            "manufacturing machinery 1.5% per section 40-23-2(3); "
            "farm machinery 1.5% per section 40-23-37) but the v1 "
            "engine does not yet apply per-category state rates "
            "outside the rate_modifier mechanism used for groceries. "
            "WARNING -- Alabama has the most fragmented local "
            "sales-tax landscape in the United States: 67 counties "
            "(most levying their own sales tax) and ~700+ "
            "municipalities, MANY of which SELF-ADMINISTER their own "
            "sales tax with their own rates, exemptions, and "
            "definitions under Ala. Code section 11-51-200 et seq. "
            "(home-rule municipal sales/use tax). Combined rates "
            "inside Alabama localities commonly fall in 9-12% (and "
            "reach 13.5% in some cities) -- this module does NOT "
            "model county or municipal sales taxes and the engine "
            "will under-collect by 5-9 percentage points on every "
            "populated Alabama address. The architectural deferral "
            "to a future SubJurisdiction Protocol abstraction is "
            "documented in specs/decisions/04-colorado-home-rule.md "
            "(same self-administering-cities pattern as Colorado) "
            "and specs/decisions/05-louisiana-parishes.md "
            "(Louisiana parish precedent for the same kind of "
            "fragmented local landscape). Calculation only -- not "
            "tax advice."
        ),
    ),
}

# Statewide 4.0% general rate has been in effect since 1969 per Ala.
# Code section 40-23-2(1) (the rate was raised from 3.0% to 4.0% by
# Act 1969-833 effective 1969-12-08, and has been stable at 4.0% in
# the general-tangible-personal-property tier ever since). Both the
# rate value (4.000) and the effective_from date (1969-12-08) are
# imported from :mod:`opensalestax.states.al_data` -- the constants
# below are aliases kept for ergonomic in-module reading.
_RATE_EFFECTIVE_FROM = AL_STATE_EFFECTIVE_FROM

# Statewide rate per ALDOR Sales Tax FAQ "What is the state sales
# tax rate?" (https://revenue.alabama.gov/sales-use/faq/), retrieved
# 2026-05-03; cross-checked against Ala. Code section 40-23-2(1).
_RATE_PCT = AL_STATE_RATE_PCT


class Alabama:
    """Alabama state module (tier 1; top-30-city seed + state 4.0%).

    The top 30 AL cities by population are seeded via
    :mod:`opensalestax.states.al_data`. The remaining ~670
    self-administering home-rule municipalities are NOT modeled and
    will under-collect by the unseeded city's portion. See the module
    docstring's "INDEPENDENT-LOCALS / HOME-RULE LIMITATION (PARTIAL)"
    section and ``specs/decisions/04-colorado-home-rule.md`` for the
    full architectural deferral rationale for the long tail. Alabama
    is one of the three canonical priority candidates (with CO and
    LA) for the v1.0+ SubJurisdiction Protocol abstraction.
    """

    state_abbrev: str = "AL"
    state_name: str = "Alabama"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require a
    # cached upstream file. AL is non-SST and has no quarterly upstream
    # file; parse_rates returns the same statewide row regardless of
    # source_file.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield AL's state + per-county + per-city rates.

        Counties yielded: every county in :data:`AL_COUNTY_RATE_PCT`
        (all 67 AL counties). The ZIP_COUNTY-driven boundary loader
        binds every AL ZIP to its county, so every county must have a
        queryable rate (counties not touched by a covered city sit at
        a 0.000% PLACEHOLDER, mirroring the MO long-tail pattern).
        Cities yielded: every :data:`AL_CITIES` entry (top 30 by
        population). ``source_file`` is intentionally ignored -- AL
        is non-SST and has no SST upstream file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Alabama",
            authority_type="state",
            rate_pct=_RATE_PCT,
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a RateRow for every AL county. The ZIP_COUNTY-driven
        # boundary loader binds every AL ZIP to its county, so every
        # county must have a queryable rate (even the PLACEHOLDER 0%
        # ones).
        for al_county_name in sorted(AL_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=al_county_name,
                authority_type="county",
                rate_pct=AL_COUNTY_RATE_PCT[al_county_name],
                effective_from=_RATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Alabama",
            )
        for city_name, (al_city_county, city_rate, _zips) in sorted(AL_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=_RATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=al_city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, city]) boundary rows for every AL ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county bindings for every ZIP intersecting an
           AL county. This covers the entire state -- not just the
           ZIPs in the top-30 city seed -- so an AL ZIP outside any
           covered city resolves to state + county (combined 4% +
           per-county portion) instead of state-only at 4%.

        2. Fall back to :data:`AL_CITIES` for any city ZIP missed by
           the Census ZCTA pass (USPS-only / PO-box-only ZIPs that
           aren't published as Census ZCTAs), then emit the city
           BoundaryRow on top of the state + county stack.

        Per the FL/AZ/CA pattern, emit at most ONE county per ZIP per
        Census ZCTA, preferring the city-anchor county if the ZIP is
        in :data:`AL_CITIES`. Without this, ZIPs that physically span
        county lines (e.g., 35173 Trussville: Jefferson + St. Clair;
        35080 Helena: Jefferson + Shelby; 36066 Prattville: Autauga +
        Elmore) would get bound to BOTH counties and double-count
        the local tax.
        """
        del source_file, version_label
        # Build city-anchor county map for cross-county-line ZIPs.
        # When a ZIP is in AL_CITIES, the city's declared county wins.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, _rate, czs) in AL_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Pass 1: state + county for every AL ZIP per Census ZCTA.
        # Emit at most one county per ZIP: prefer the city-anchor
        # county if known, else the first Census-listed AL county
        # in deterministic FIPS-sorted order.
        #
        # ZIP_COUNTY values are frozensets, so iteration order is
        # non-deterministic; we sort by FIPS for stable test results.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            sorted_al_pairs = sorted(cf for sa, cf in pairs if sa == "AL")
            chosen_county: str | None = None
            for county_fips in sorted_al_pairs:
                al_county_name = county_name("AL", county_fips)
                if al_county_name is None or al_county_name not in AL_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if al_county_name == preferred_county:
                        chosen_county = al_county_name
                        break
                    # keep iterating in hopes of finding the city's county
                    continue
                # No city anchor for this ZIP -- take the first AL county.
                chosen_county = al_county_name
                break
            if chosen_county is None and preferred_county is not None:
                # ZIP is in a city but Census doesn't list the city's
                # county at all (USPS-only / boundary-mismatch). Trust
                # the city's declared county.
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Alabama",
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

        # Pass 2: city BoundaryRows for AL_CITIES. Also emit state +
        # county for any city ZIP missed by the Census pass (USPS-only
        # codes not in ZCTA) so we never regress city coverage.
        for city_name, (al_city_county, _city_rate, zips) in AL_CITIES.items():
            for zip5 in zips:
                if zip5 not in emitted_zips:
                    yield BoundaryRow(
                        authority_name="Alabama",
                        authority_type="state",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    yield BoundaryRow(
                        authority_name=al_city_county,
                        authority_type="county",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    emitted_zips.add(zip5)
                yield BoundaryRow(
                    authority_name=city_name,
                    authority_type="city",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return AL's state-portion taxability rule for ``item_category``.

        Note: county and municipal taxability commonly diverges from
        state taxability (notably, locals continue to tax groceries
        at full local rate even though the state has phased the
        state-portion grocery rate down to 2.0%). v1 only encodes
        the state-portion answer.
        """
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No SpecialCase entries tracked for AL in v1.

        The independent-locals topology is documented in the module
        docstring and the relevant decision docs; the SpecialCase
        API is reserved for engine-consumed quirks (Phase 5+).
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Alabama's two annual sales-tax holidays.

        Both holidays are STATE holidays -- the state-portion
        exemption is automatic; counties and municipalities must
        OPT IN by ordinance/resolution to extend the exemption to
        their local portion. Many do; many do not. ALDOR publishes
        an annual list of participating localities; this module
        encodes only the STATE-side scope and the local-opt-in
        caveat is documented in each window's notes.

        1. **Severe Weather Preparedness Sales Tax Holiday** --
           Ala. Code section 40-23-210 et seq. Last full weekend
           of February (Friday-Sunday). For 2026: Feb 27 - Mar 1.
           Two scopes:

           - generators with sales price $1,000 or less per item
           - severe-weather-preparedness items with sales price
             $60 or less per item

        2. **Back-to-School Sales Tax Holiday** -- Ala. Code section
           40-23-211. Third full weekend of July (Friday-Sunday).
           For 2026: July 17 - 19. Four scopes:

           - clothing -- $100 or less per article
           - computers/computer equipment/software -- $750 or less
             per single-purchase transaction
           - school supplies -- $50 or less per item
           - books -- $30 or less per item (noncommercial)

        Subsequent years require an explicit data update -- the
        statutory weekend formulas are stable but local-opt-in
        participation lists change annually and the legislature
        could in principle adjust caps or scopes.
        """
        if year != 2026:
            return iter(())
        # Severe Weather Preparedness Holiday 2026: last full weekend
        # of February. Feb 28 2026 is a Saturday, so the Friday is
        # Feb 27 and the Sunday is March 1.
        swp_starts = dt.date(2026, 2, 27)
        swp_ends = dt.date(2026, 3, 1)
        # Back-to-School Holiday 2026: third full weekend of July.
        # Fridays in July 2026 are 3, 10, 17, 24, 31; the third is
        # July 17, holiday ends Sunday July 19.
        bts_starts = dt.date(2026, 7, 17)
        bts_ends = dt.date(2026, 7, 19)
        return iter(
            [
                HolidayWindow(
                    name=(
                        "Alabama Severe Weather Preparedness Sales Tax "
                        "Holiday -- Generators (2026)"
                    ),
                    starts_on=swp_starts,
                    ends_on=swp_ends,
                    applicable_categories=("generators",),
                    max_amount_per_item=Decimal("1000.00"),
                    notes=(
                        "Ala. Code section 40-23-210 et seq. (Severe "
                        "Weather Preparedness Sales Tax Holiday). "
                        "Three-day exemption from STATE 4.0% sales tax "
                        "for portable backup generators with sales "
                        "price $1,000 or less per item. Counties and "
                        "municipalities MUST OPT IN by ordinance to "
                        "extend the exemption to their local portion; "
                        "many do, many do not -- ALDOR publishes an "
                        "annual participating-locality list. "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name=(
                        "Alabama Severe Weather Preparedness Sales Tax "
                        "Holiday -- Preparedness Supplies (2026)"
                    ),
                    starts_on=swp_starts,
                    ends_on=swp_ends,
                    applicable_categories=("severe_weather_preparedness_supplies",),
                    max_amount_per_item=Decimal("60.00"),
                    notes=(
                        "Ala. Code section 40-23-210 et seq. (Severe "
                        "Weather Preparedness Sales Tax Holiday). "
                        "Three-day exemption from STATE 4.0% sales tax "
                        "for severe-weather-preparedness supplies "
                        "(batteries, flashlights, weather-band radios, "
                        "tarps, plywood, ground anchor systems, "
                        "gas/diesel fuel containers, ice packs, fire "
                        "extinguishers, smoke / carbon monoxide "
                        "detectors, first-aid kits, and similar items) "
                        "with sales price $60 or less per item. "
                        "Counties and municipalities MUST OPT IN by "
                        "ordinance to extend the exemption to their "
                        "local portion; ALDOR publishes the annual "
                        "participating-locality list. Calculation only "
                        "-- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name=("Alabama Back-to-School Sales Tax Holiday -- Clothing (2026)"),
                    starts_on=bts_starts,
                    ends_on=bts_ends,
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Ala. Code section 40-23-211 (Back-to-School "
                        "Sales Tax Holiday). Three-day exemption from "
                        "STATE 4.0% sales tax for clothing items with "
                        "sales price $100 or less per article. Counties "
                        "and municipalities MUST OPT IN by ordinance to "
                        "extend the exemption to their local portion; "
                        "many do, many do not -- ALDOR publishes an "
                        "annual participating-locality list. "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Alabama Back-to-School Sales Tax Holiday -- Computers / Software (2026)",
                    starts_on=bts_starts,
                    ends_on=bts_ends,
                    applicable_categories=("computers",),
                    max_amount_per_item=Decimal("750.00"),
                    notes=(
                        "Ala. Code section 40-23-211 (Back-to-School "
                        "Sales Tax Holiday). Three-day exemption from "
                        "STATE 4.0% sales tax for computers, computer "
                        "equipment, computer software, and school "
                        "computer supplies with sales price $750 or "
                        "less per single-purchase transaction (the "
                        "$750 cap applies to the entire transaction, "
                        "not per individual line item). Counties and "
                        "municipalities MUST OPT IN by ordinance to "
                        "extend the exemption to their local portion; "
                        "ALDOR publishes the annual participating-"
                        "locality list. Calculation only -- not tax "
                        "advice."
                    ),
                ),
                HolidayWindow(
                    name=("Alabama Back-to-School Sales Tax Holiday -- School Supplies (2026)"),
                    starts_on=bts_starts,
                    ends_on=bts_ends,
                    applicable_categories=("school_supplies",),
                    max_amount_per_item=Decimal("50.00"),
                    notes=(
                        "Ala. Code section 40-23-211 (Back-to-School "
                        "Sales Tax Holiday). Three-day exemption from "
                        "STATE 4.0% sales tax for school supplies, "
                        "school art supplies, and school instructional "
                        "materials with sales price $50 or less per "
                        "item. Counties and municipalities MUST OPT IN "
                        "by ordinance to extend the exemption to their "
                        "local portion. Calculation only -- not tax "
                        "advice."
                    ),
                ),
                HolidayWindow(
                    name=("Alabama Back-to-School Sales Tax Holiday -- Books (2026)"),
                    starts_on=bts_starts,
                    ends_on=bts_ends,
                    applicable_categories=("books",),
                    max_amount_per_item=Decimal("30.00"),
                    notes=(
                        "Ala. Code section 40-23-211 (Back-to-School "
                        "Sales Tax Holiday). Three-day exemption from "
                        "STATE 4.0% sales tax for noncommercial book "
                        "purchases with sales price $30 or less per "
                        "book. Counties and municipalities MUST OPT IN "
                        "by ordinance to extend the exemption to their "
                        "local portion; ALDOR publishes the annual "
                        "participating-locality list. Calculation only "
                        "-- not tax advice."
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Alabama()
del _PROTOCOL_CHECK

ALABAMA = register(Alabama())
