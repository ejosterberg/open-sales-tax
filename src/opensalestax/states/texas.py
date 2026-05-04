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

ZIPs not in :data:`tx_data.TX_CITIES` fall back to state-only at
6.25% via the Census ZCTA load. This is a significant under-
collection for suburban / unincorporated Texas; a future ratchet
should add per-county boundary seeds for non-zero counties (today
only El Paso County) and per-county fallback bindings for the
~250 Texas counties with no county sales tax.

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

        Counties yielded: only those touched by a covered city.
        Transit districts yielded: only those touched by a covered city.
        Cities yielded: every TX_CITIES entry. ``source_file`` is
        intentionally ignored -- TX is non-SST and has no upstream file.
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
        used_counties = {county for county, _, _, _ in TX_CITIES.values()}
        for county_name in sorted(used_counties):
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=TX_COUNTY_RATE_PCT[county_name],
                effective_from=TX_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Texas",
            )
        used_transits = {
            transit for _, transit, _, _ in TX_CITIES.values() if transit is not None
        }
        for transit_name in sorted(used_transits):
            yield RateRow(
                authority_name=transit_name,
                authority_type="district",
                rate_pct=TX_TRANSIT_DISTRICTS[transit_name],
                effective_from=TX_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Texas",
            )
        for city_name, (county_name, _transit, city_rate, _zips) in sorted(TX_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=TX_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=county_name,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, transit?, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every TX ZIP. This method ADDS county + (optional) transit +
        city bindings for the 49 covered cities. ZIPs in covered
        counties but outside the city list keep the Census state-only
        binding (under-collects local tax for any address in an
        incorporated city not on the seed list).
        """
        del source_file, version_label
        for city_name, (county_name, transit_name, _city_rate, zips) in TX_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="Texas",
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
