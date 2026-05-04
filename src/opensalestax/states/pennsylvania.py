# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Pennsylvania state module (tier 1, non-SST).

PA is **not** a Streamlined Sales Tax member. The statewide
sales-tax rate is **6.0%** per the Pennsylvania Department of
Revenue (https://revenue.pa.gov), imposed under 72 P.S. section
7202(a) (Tax Reform Code of 1971). Two counties impose a local
sales tax on top of the state rate:

- **Allegheny County (Pittsburgh metro): +1.0%** -- 72 P.S. section
  7202 (the 1994 Allegheny Regional Asset District 1% local levy).
  Combined rate: **7.0%**.
- **Philadelphia City/County: +2.0%** -- 72 P.S. section 7202(b)
  (raised from 1% to 2% effective 2009-10-08; cross-referenced in
  61 Pa. Code section 60.16). Philadelphia city and Philadelphia
  County are coterminous, so this 2% functions as both the city
  and county sales tax. Combined rate: **8.0%**.
- **All other 65 PA counties:** no local sales tax. Combined rate:
  **6.0%** (statewide flat).

Per-city seed (top 15 by population) wires Philadelphia and
Pittsburgh to the correct county so combined rates land at 8.0%
and 7.0%; the remaining 13 cities stay at the 6.0% statewide
flat. See :mod:`opensalestax.states.pa_data` for the per-county
rates, per-city ZIP coverage, and the architectural choice to
encode local taxes at the county level rather than the city
level (since Philadelphia is a coterminous city/county and the
single 1%/2% local line on a PA receipt has no city/county
distinction in practice).

**Statewide ZIP coverage via Census ZCTA**
(parallels FL/AZ/CA in v0.28). :meth:`Pennsylvania.parse_boundaries`
iterates :data:`opensalestax.data.zip_county.ZIP_COUNTY` and emits
state + county bindings for every PA ZIP -- not just the ones in
the top-15 city seed. Effect: every Pittsburgh suburb in Allegheny
County (Monroeville, Bethel Park, McKeesport, etc.) now picks up
the +1.0% Allegheny county tax, and every Philadelphia-County ZIP
not in PA_CITIES picks up the +2.0% city/county tax, instead of
falling back to state-only at 6.0%.

Taxability matrix (per 72 P.S. Article II + Pa. Dept. of Revenue
Retailer's Information Guide REV-717):

- **Clothing** -- NON-TAXABLE in Pennsylvania. PA broadly exempts
  "wearing apparel" per 72 P.S. section 7204(26); athletic
  uniforms, fur articles, and formal attire have nuanced taxable-
  status rules per 61 Pa. Code section 53.1. Consult the PA
  Retailer's Information Guide for edge cases.
- **Groceries (food and beverages for off-premises consumption)**
  -- NON-TAXABLE per 72 P.S. section 7204(29) and 61 Pa. Code
  section 57.1. Soft drinks, alcoholic beverages, and prepared
  food are taxable.
- **Prescription drugs** -- NON-TAXABLE per 72 P.S. section
  7204(17).
- **Prepared food** -- TAXABLE at the standard combined rate
  (state 6% + county add-on if applicable).
- **Digital goods** -- TAXABLE per Act 84 of 2016, which amended
  72 P.S. section 7201(k) to include digital downloads (music,
  ebooks, streaming, photographs, ringtones, prewritten software,
  apps) within the scope of taxable tangible personal property.
- **General** -- TAXABLE at the combined rate (state 6% +
  Allegheny 1% if in Allegheny County / Philadelphia 2% if in
  Philadelphia County).

Sales-tax holidays: Pennsylvania has **none**. The legislature
has periodically debated back-to-school holidays but no statute
has been enacted as of 2026.

State maintainer: vacant -- see MAINTAINERS.md.

Disclaimer: this module is calculation infrastructure, not tax
advice. Verify every rule against the Pennsylvania Department of
Revenue (https://revenue.pa.gov) before relying on it for
compliance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.states.pa_data import (
    PA_CITIES,
    PA_COUNTY_RATE_PCT,
    PA_STATE_EFFECTIVE_FROM,
    PA_STATE_RATE_PCT,
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

_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=False,
        notes=(
            "Clothing is NON-taxable in Pennsylvania per 72 P.S. "
            "section 7204(26) (broad 'wearing apparel' exemption). "
            "Athletic uniforms, fur articles, and formal attire have "
            "nuanced taxable-status rules per 61 Pa. Code section "
            "53.1; consult the PA Retailer's Information Guide "
            "(REV-717) for edge cases. Calculation only -- not tax "
            "advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Groceries (food and beverages for off-premises human "
            "consumption) are NON-taxable in Pennsylvania per 72 P.S. "
            "section 7204(29) and 61 Pa. Code section 57.1. Soft "
            "drinks, alcoholic beverages, and prepared food remain "
            "taxable. Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are NON-taxable in Pennsylvania per "
            "72 P.S. section 7204(17). Calculation only -- not tax "
            "advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food is taxable at the combined Pennsylvania "
            "rate per 72 P.S. section 7202 (state 6% + Allegheny 1% / "
            "Philadelphia 2% local where applicable). The grocery "
            "exemption at 72 P.S. section 7204(29) explicitly excludes "
            "food sold ready-for-consumption by restaurants and "
            "similar establishments. Some Philadelphia establishments "
            "are also subject to a separate locally-administered "
            "liquor-by-the-drink or hotel-occupancy tax not modeled "
            "here. Calculation only -- not tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods (downloaded music, ebooks, streaming, "
            "photographs, ringtones, prewritten software, mobile "
            "applications) are TAXABLE in Pennsylvania per Act 84 of "
            "2016, which amended 72 P.S. section 7201(k) to include "
            "electronically-delivered digital products in the "
            "definition of taxable tangible personal property. "
            "Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at the "
            "Pennsylvania combined rate per 72 P.S. section 7202: "
            "state 6.0% + Allegheny County 1.0% (Pittsburgh) / "
            "Philadelphia 2.0% local where applicable. Calculation "
            "only -- not tax advice."
        ),
    ),
}


class Pennsylvania:
    """Pennsylvania state module (tier 1; state + Allegheny + Philadelphia local)."""

    state_abbrev: str = "PA"
    state_name: str = "Pennsylvania"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # PA has no SST upstream file; parse_rates returns the same rows
    # regardless of source_file, so the loader must skip the cache-
    # file requirement.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield PA's state + per-county + per-city rates.

        Counties yielded: every county in :data:`PA_COUNTY_RATE_PCT`
        (all 67 PA counties). The ZIP_COUNTY-driven boundary loader
        binds every PA ZIP to its county, so every county must have
        a queryable rate (even the 0% ones). Cities yielded: every
        PA_CITIES entry. The city rate is 0% in all cases -- the
        local tax (where it exists) is encoded as the county rate per
        the implementation choice documented in :mod:`pa_data`
        (Philadelphia city/county are coterminous so the 2% sits
        naturally on the county; Allegheny County's 1% likewise sits
        on the county). ``source_file`` is intentionally ignored --
        PA is non-SST and has no upstream file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Pennsylvania",
            authority_type="state",
            rate_pct=PA_STATE_RATE_PCT,
            effective_from=PA_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a RateRow for every PA county. The ZIP_COUNTY-driven
        # boundary loader binds every PA ZIP to its county, so every
        # county must have a queryable rate (even the 0% ones).
        for pa_county_name in sorted(PA_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=pa_county_name,
                authority_type="county",
                rate_pct=PA_COUNTY_RATE_PCT[pa_county_name],
                effective_from=PA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Pennsylvania",
            )
        for city_name, (city_county, city_rate, _zips) in sorted(PA_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=PA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, city]) boundary rows for every PA ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county bindings for every ZIP intersecting a
           PA county. This covers the entire state, not just the ZIPs
           in the :data:`PA_CITIES` top-15 seed list -- so every
           Pittsburgh suburb in Allegheny County (Monroeville, Bethel
           Park, McKeesport, etc.) now picks up the +1.0% Allegheny
           county tax instead of falling back to state-only at 6.0%.

        2. Fall back to :data:`PA_CITIES` for any city ZIP missed by
           the Census ZCTA pass (USPS-only / PO-box-only ZIPs that
           aren't published as Census ZCTAs), then emit the city
           BoundaryRow on top of the state + county stack so the
           friendly city anchor is preserved.

        Per the FL/AZ/CA pattern, emit at most ONE county per ZIP per
        Census ZCTA, preferring the city-anchor county if the ZIP is
        in :data:`PA_CITIES`. Without this, ZIPs that physically span
        county lines would get bound to BOTH counties and double-count
        the local tax.
        """
        del source_file, version_label
        # Build city-anchor county map for cross-county-line ZIPs.
        # When a ZIP is in PA_CITIES, the city's declared county wins.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, _rate, czs) in PA_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Pass 1: state + county for every PA ZIP per Census ZCTA.
        # Emit at most one county per ZIP: prefer the city-anchor
        # county if known, else the first Census-listed PA county.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            for state_abbrev, county_fips in pairs:
                if state_abbrev != "PA":
                    continue
                pa_county_name = county_name("PA", county_fips)
                if pa_county_name is None or pa_county_name not in PA_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if pa_county_name == preferred_county:
                        chosen_county = pa_county_name
                        break
                    # keep iterating in hopes of finding the city's county
                    continue
                # No city anchor for this ZIP -- take the first PA county.
                chosen_county = pa_county_name
                break
            if chosen_county is None and preferred_county is not None:
                # ZIP is in a city but Census doesn't list the city's
                # county at all (USPS-only / boundary-mismatch). Trust
                # the city's declared county.
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Pennsylvania",
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
        # Pass 2: city BoundaryRows for PA_CITIES. Also emit state +
        # county for any city ZIP missed by the Census pass (USPS-only
        # codes not in ZCTA) so we never regress city coverage.
        for city_name, (county_name_for_city, _city_rate, zips) in PA_CITIES.items():
            for zip5 in zips:
                if zip5 not in emitted_zips:
                    yield BoundaryRow(
                        authority_name="Pennsylvania",
                        authority_type="state",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    yield BoundaryRow(
                        authority_name=county_name_for_city,
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
        """Return PA's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for PA."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Pennsylvania has no annual sales-tax holidays."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = Pennsylvania()
del _PROTOCOL_CHECK

PENNSYLVANIA = register(Pennsylvania())
