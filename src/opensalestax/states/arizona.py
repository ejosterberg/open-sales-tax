# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Arizona state module (tier 1, non-SST).

AZ is **not** an SST member. The state imposes a **Transaction
Privilege Tax (TPT)** rather than a traditional sales tax -- a
distinction that affects who's legally liable (the seller, not
the buyer) but produces the same dollar result for retail sales.
The statewide TPT base rate is **5.6%** per the Arizona
Department of Revenue (azdor.gov).

**v0.25 ships per-county + 48-city coverage.** All 15 AZ counties
and 48 cities (the original top-20 plus a 2026-05-04 expansion
covering Apache Junction, Bullhead City, Camp Verde, Carefree,
Coolidge, Cottonwood, El Mirage, Eloy, Florence, Globe, Holbrook,
Kingman, Litchfield Park, Maricopa-the-city, Nogales, Page,
Payson, Queen Creek, Sahuarita, San Luis, Sedona, Show Low,
Sierra Vista, Snowflake, Tolleson, Wickenburg, Williams, Winslow)
are seeded from the AZ DOR's monthly TPT Rate Table CSV. ZIPs not
in the city list fall back to state + county where the county is
covered by an explicit city, otherwise state-only via the Census
ZCTA load.

Taxability matrix (per Ariz. Rev. Stat. 42-5061):

- **Clothing** -- TAXABLE.
- **Groceries** -- NON-taxable for "food for home consumption"
  at the state level. Some cities (Tucson is the prominent
  example) tax groceries at the local level; verify per-city.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE.

State maintainer: vacant -- the city-level grocery taxability
divergence is unusual; AZ benefits from a maintainer who can
verify per-locality. See MAINTAINERS.md.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.states.az_data import (
    AZ_CITIES,
    AZ_COUNTY_RATE_PCT,
    AZ_STATE_EFFECTIVE_FROM,
    AZ_STATE_RATE_PCT,
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
        is_taxable=True,
        notes="Clothing is taxable in Arizona.",
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food for home consumption is non-taxable at the state TPT "
            "level. Some cities (e.g. Tucson) tax groceries at the local "
            "level; verify per-city when district rates are loaded in a "
            "future section."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Arizona.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable. AZ's TPT is "
            "imposed on the seller (not the buyer); the math is the same "
            "as a traditional sales tax."
        ),
    ),
}


class Arizona:
    """Arizona state module (tier 1; state + per-county + 48 cities)."""

    state_abbrev: str = "AZ"
    state_name: str = "Arizona"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield AZ's state TPT + per-county + per-city rates.

        All 15 AZ counties from :data:`AZ_COUNTY_RATE_PCT` are emitted
        so the ZIP_COUNTY-driven boundary loader can resolve every AZ
        ZIP to its county authority. Cities yielded: every
        :data:`AZ_CITIES` entry.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Arizona",
            authority_type="state",
            rate_pct=AZ_STATE_RATE_PCT,
            effective_from=AZ_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a county RateRow for every AZ county. The ZIP_COUNTY-
        # driven boundary loader binds every AZ ZIP to its county, so
        # every county must have a queryable rate.
        for az_county_name in sorted(AZ_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=az_county_name,
                authority_type="county",
                rate_pct=AZ_COUNTY_RATE_PCT[az_county_name],
                effective_from=AZ_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Arizona",
            )
        for az_city_name, (az_city_county, city_rate, _zips) in sorted(AZ_CITIES.items()):
            yield RateRow(
                authority_name=az_city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=AZ_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=az_city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, city]) boundary rows for every AZ ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` for
           every ZIP in an AZ county and emit state + county bindings.
           This covers the entire state, not just ZIPs in
           :data:`AZ_CITIES`, so a ZIP outside the top-48 city seed
           still resolves to state + county TPT.

        2. For each :data:`AZ_CITIES` entry, additionally emit a city
           BoundaryRow so the city's TPT portion is layered on top of
           the state + county stack at its ZIPs.

        A ZIP that crosses county lines yields one county BoundaryRow
        per intersecting county.
        """
        del source_file, version_label
        # Build the city-anchor county map first: when a ZIP is in
        # AZ_CITIES, the city's declared county wins over any
        # Census-listed alternate. Prevents double-counting for ZIPs
        # that physically span county lines (e.g. Show Low 85901 lists
        # both Apache and Navajo per Census, but the city is in Navajo).
        city_county_for_zip: dict[str, str] = {}
        for _city_name, (city_county, _rate, city_zips) in AZ_CITIES.items():
            for cz in city_zips:
                city_county_for_zip[cz] = city_county

        # Pass 1: state + county for every AZ ZIP per Census ZCTA.
        # For each ZIP, emit at most one county: prefer the city-anchor
        # county if the ZIP is in AZ_CITIES, otherwise the first
        # Census-listed AZ county.
        zips_with_county_emitted: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            # ZIP_COUNTY values are frozensets; sort by FIPS for stability.
            sorted_az_pairs = sorted(cf for sa, cf in pairs if sa == "AZ")
            for county_fips in sorted_az_pairs:
                az_county_name = county_name("AZ", county_fips)
                if az_county_name is None or az_county_name not in AZ_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if az_county_name == preferred_county:
                        chosen_county = az_county_name
                        break
                    # keep iterating in hopes of finding the city's county
                    continue
                # No city anchor for this ZIP -- take the first AZ county.
                chosen_county = az_county_name
                break
            if chosen_county is None and preferred_county is not None:
                # ZIP is in a city but Census doesn't list the city's
                # county at all (e.g. ZIP entirely on the wrong side per
                # Census). Trust the city's declared county.
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Arizona",
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
            zips_with_county_emitted.add(zip5)
        # Pass 2: city BoundaryRows for AZ_CITIES. Also emit state +
        # county for any city ZIP missed by the Census pass (PO-box-
        # only ZIPs not in ZCTA, etc.) so we never regress city coverage.
        for az_city_name, (az_city_county, _city_rate, zips) in AZ_CITIES.items():
            for zip5 in zips:
                if zip5 not in zips_with_county_emitted:
                    yield BoundaryRow(
                        authority_name="Arizona",
                        authority_type="state",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    yield BoundaryRow(
                        authority_name=az_city_county,
                        authority_type="county",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    zips_with_county_emitted.add(zip5)
                yield BoundaryRow(
                    authority_name=az_city_name,
                    authority_type="city",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Arizona has no annual sales-tax holidays."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = Arizona()
del _PROTOCOL_CHECK

ARIZONA = register(Arizona())
