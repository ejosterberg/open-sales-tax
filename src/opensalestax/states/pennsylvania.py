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

        Counties yielded: only those touched by a covered PA_CITIES
        entry. Cities yielded: every PA_CITIES entry. The city rate
        is 0% in all cases -- the local tax (where it exists) is
        encoded as the county rate per the implementation choice
        documented in :mod:`pa_data` (Philadelphia city/county are
        coterminous so the 2% sits naturally on the county; Allegheny
        County's 1% likewise sits on the county). ``source_file`` is
        intentionally ignored -- PA is non-SST and has no upstream
        file.
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
        used_counties = {county for county, _, _ in PA_CITIES.values()}
        for county_name in sorted(used_counties):
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=PA_COUNTY_RATE_PCT[county_name],
                effective_from=PA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Pennsylvania",
            )
        for city_name, (county_name, city_rate, _zips) in sorted(PA_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=PA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=county_name,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every PA ZIP. This method ADDS county + city bindings for the
        15 covered cities. ZIPs in covered counties but outside the
        city list keep the Census state-only binding; for the 65 PA
        counties at 0% local that's correct (combined 6.0%). For
        Allegheny County and Philadelphia County a future ratchet
        should extend coverage to suburban municipalities so they
        pick up the +1.0% / +2.0% county tax.
        """
        del source_file, version_label
        for city_name, (county_name, _city_rate, zips) in PA_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="Pennsylvania",
                    authority_type="state",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
                yield BoundaryRow(
                    authority_name=county_name,
                    authority_type="county",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
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
