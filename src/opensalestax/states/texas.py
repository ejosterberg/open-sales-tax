# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Texas state module (tier 1, non-SST).

TX is **not** an SST member. Statewide rate is **6.25%** per the
Texas Comptroller (comptroller.texas.gov). Local jurisdictions
(cities, counties, transit authorities, special-purpose districts)
can add up to **2.0%** combined, capping the maximum combined rate
at **8.25%** per Tex. Tax Code section 321.101(f).

**v0.26 ships top-50-city coverage.** All 49 covered cities (the top
50 by 2020 census population, minus Atascocita CDP) are seeded from
:mod:`opensalestax.states.tx_data`, sourced from the Texas
Comptroller's "City Sales and Use Tax Rates" + "Local Sales and Use
Tax Rates" publications and cross-checked against Avalara per-city
rate pages on 2026-05-04. The module emits four authority types:

- **state** (Texas, 6.25%)
- **county** (per-county portion; 0% for most TX counties, 0.5% for
  El Paso County)
- **district** (Metropolitan Transit Authority -- Houston METRO,
  Dallas DART, Austin Capital Metro, San Antonio VIA+ATD, Fort
  Worth FWTA, El Paso Sun Metro, Corpus Christi RTA)
- **city** (combined municipal portion: city tax + EDC 4A/4B +
  crime control + street maintenance + MDD, etc.)

**Statewide ZIP coverage via Census ZCTA**
(parallels FL/AZ/CA in v0.28). All 254 TX counties are seeded in
:data:`TX_COUNTY_RATE_PCT` and :meth:`Texas.parse_boundaries`
iterates :data:`opensalestax.data.zip_county.ZIP_COUNTY` to bind
every TX ZIP to its county. The vast majority of TX counties sit
at 0% county sales tax (TX is a city-tax state under Tex. Tax
Code Chapter 321), so a non-city TX ZIP resolves to state 6.25%
+ county 0% = 6.25% combined -- the same dollar result as the
prior state-only fallback, but with the audit trail recording
which county the ZIP physically sits in. The single non-zero
county today is El Paso (0.5%); a future maintainer should audit
the Texas Comptroller's quarterly tables and bump any other
non-zero counties.

**Sourcing model -- IMPORTANT:** Texas uses **origin-based
sourcing** for in-state sellers (Tex. Tax Code section 321.203).
The ZIP-based boundary table here is a **delivery-address
approximation** that produces the correct rate for a buyer at that
ZIP buying from a seller at the same ZIP -- the dominant case for
brick-and-mortar retail and direct-to-consumer e-commerce delivered
in-state. A future ratchet should expose the seller-vs-buyer
distinction so the API caller can pick the right rule.

Taxability matrix (per Tex. Tax Code Chapter 151):

- **Clothing** -- TAXABLE (no exemption). Three annual sales-tax
  holidays modify this temporarily; modeled below in
  :meth:`Texas.holidays_for`.
- **Groceries** -- NON-taxable for "food products" sold for off-
  premise consumption (Tex. Tax Code section 151.314).
- **Prescription drugs** -- NON-taxable (Tex. Tax Code section
  151.313).
- **Prepared food** -- TAXABLE.
- **Digital goods** -- TAXABLE for downloaded software, music,
  ringtones, etc.

Special note: TX has 3 annual sales-tax holidays (emergency
preparation in April, Energy Star + WaterSense in May, back-to-
school in August).

State maintainer: vacant -- see MAINTAINERS.md.

Disclaimer: this module is calculation infrastructure, not tax
advice. Origin sourcing, single-purpose districts (TIF, MUD, etc.),
and the local-cap interaction can produce surprising results at
specific addresses. Verify against the Comptroller's Sales Tax
Rate Locator before relying on these rates for compliance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
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
from opensalestax.states.tx_data import (
    TX_CITIES,
    TX_COUNTY_RATE_PCT,
    TX_STATE_EFFECTIVE_FROM,
    TX_STATE_RATE_PCT,
    TX_TRANSIT_DISTRICTS,
)

_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Texas year-round; the August "
            "back-to-school sales-tax holiday provides a temporary "
            "exemption (modeled when the holidays feature lands)."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food products for off-premise consumption are non-taxable "
            "(Tex. Tax Code section 151.314). Prepared food is taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable (Tex. Tax Code section 151.313).",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food (restaurant meals, hot foods) is taxable.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods (downloaded software, music, etc.) are taxable in Texas.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Texas:
    """Texas state module (tier 1; state + county + transit + city in v0.26)."""

    state_abbrev: str = "TX"
    state_name: str = "Texas"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield TX's state + per-county + per-transit + per-city rates.

        Counties yielded: every county in :data:`TX_COUNTY_RATE_PCT`
        (all 254 TX counties). The ZIP_COUNTY-driven boundary loader
        binds every TX ZIP to its county, so every county must have
        a queryable rate (almost all are 0% since TX is a city-tax
        state, but the 0% rows preserve the audit trail).
        Transit districts yielded: only those touched by a covered
        city. Cities yielded: every TX_CITIES entry. ``source_file``
        is intentionally ignored -- TX is non-SST and has no upstream
        file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Texas",
            authority_type="state",
            rate_pct=TX_STATE_RATE_PCT,
            effective_from=TX_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a RateRow for every TX county. The ZIP_COUNTY-driven
        # boundary loader binds every TX ZIP to its county, so every
        # county must have a queryable rate (even 0% ones).
        for tx_county_name in sorted(TX_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=tx_county_name,
                authority_type="county",
                rate_pct=TX_COUNTY_RATE_PCT[tx_county_name],
                effective_from=TX_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Texas",
            )
        used_transits = {transit for _, transit, _, _ in TX_CITIES.values() if transit is not None}
        for transit_name in sorted(used_transits):
            yield RateRow(
                authority_name=transit_name,
                authority_type="district",
                rate_pct=TX_TRANSIT_DISTRICTS[transit_name],
                effective_from=TX_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Texas",
            )
        for city_name, (city_county, _transit, city_rate, _zips) in sorted(TX_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=TX_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, transit, city]) boundary rows for every TX ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county bindings for every ZIP intersecting a
           TX county. This covers the entire state -- not just the
           ZIPs in the top-49 city seed list -- so a ZIP outside any
           covered city still resolves to state + county (combined
           6.25% almost everywhere since most TX counties have no
           county sales tax) instead of falling back to state-only.

        2. Fall back to :data:`TX_CITIES` for any city ZIP missed by
           the Census pass and emit transit + city BoundaryRows on
           top of the state + county stack so the city's portion (and
           transit district where applicable) is layered correctly.

        Per the FL/AZ/CA pattern, emit at most ONE county per ZIP per
        Census ZCTA, preferring the city-anchor county if the ZIP is
        in :data:`TX_CITIES`. Without this, ZIPs that physically span
        county lines would get bound to BOTH counties and could
        double-count any county tax.
        """
        del source_file, version_label
        # Build city-anchor county map for cross-county-line ZIPs.
        # When a ZIP is in TX_CITIES, the city's declared county wins.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, _t, _r, czs) in TX_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Pass 1: state + county for every TX ZIP per Census ZCTA.
        # Emit at most one county per ZIP: prefer the city-anchor
        # county if known, else the first Census-listed TX county.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            # ZIP_COUNTY values are frozensets; sort by FIPS for stability.
            sorted_tx_pairs = sorted(cf for sa, cf in pairs if sa == "TX")
            for county_fips in sorted_tx_pairs:
                tx_county_name = county_name("TX", county_fips)
                if tx_county_name is None or tx_county_name not in TX_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if tx_county_name == preferred_county:
                        chosen_county = tx_county_name
                        break
                    continue
                chosen_county = tx_county_name
                break
            if chosen_county is None and preferred_county is not None:
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Texas",
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

        # Pass 2: transit + city BoundaryRows for TX_CITIES. Also
        # emit state + county for any city ZIP missed by the Census
        # pass (USPS-only / PO-box-only ZIPs not in ZCTA).
        for city_name, (city_county, transit_name, _city_rate, zips) in TX_CITIES.items():
            for zip5 in zips:
                if zip5 not in emitted_zips:
                    yield BoundaryRow(
                        authority_name="Texas",
                        authority_type="state",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    yield BoundaryRow(
                        authority_name=city_county,
                        authority_type="county",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    emitted_zips.add(zip5)
                if transit_name is not None:
                    yield BoundaryRow(
                        authority_name=transit_name,
                        authority_type="district",
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
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Texas has 3 annual sales-tax holidays per Tex. Tax Code Chapter 151.

        Dates rotate each year (last Saturday of April, etc.); 2026
        dates encoded explicitly. Add subsequent years as legislation
        is published.
        """
        if year != 2026:
            return iter(())
        # Per https://comptroller.texas.gov/taxes/publications/
        return iter(
            [
                HolidayWindow(
                    name="Emergency Preparation Supplies (2026)",
                    starts_on=dt.date(2026, 4, 25),
                    ends_on=dt.date(2026, 4, 27),
                    applicable_categories=("emergency_supplies",),
                    max_amount_per_item=Decimal("3000.00"),
                    notes="Generators <$3000, hurricane shutters, batteries, etc.",
                ),
                HolidayWindow(
                    name="Energy Star + Water-Efficient Products (2026)",
                    starts_on=dt.date(2026, 5, 23),
                    ends_on=dt.date(2026, 5, 25),
                    applicable_categories=("energy_star", "water_efficient"),
                    max_amount_per_item=None,
                    notes="Memorial Day weekend; Energy Star + WaterSense items.",
                ),
                HolidayWindow(
                    name="Back-to-School (2026)",
                    starts_on=dt.date(2026, 8, 7),
                    ends_on=dt.date(2026, 8, 9),
                    applicable_categories=("clothing", "school_supplies"),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "First weekend of August; clothing, footwear, "
                        "school supplies and backpacks under $100/item."
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Texas()
del _PROTOCOL_CHECK

TEXAS = register(Texas())
