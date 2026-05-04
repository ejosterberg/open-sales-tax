# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Florida state module (tier 1, non-SST).

FL is **not** an SST member. Statewide rate is **6%** per the
Florida Department of Revenue (floridarevenue.com). Counties may
add a discretionary sales surtax (Form DR-15DSS) of 0% to 1.5%;
combined statewide-plus-county rates therefore range **6.0%-7.5%**.

Florida has **NO city-level general sales tax** anywhere in the
state. The only modeled layers are state + county; cities are used
purely as ZIP-binding anchors to produce friendly receipt
descriptions. See :mod:`opensalestax.states.fl_data` for the per-
county surtax table (all 67 counties) and the 30 covered cities.

Taxability matrix (per Fla. Stat. Chapter 212):

- **Clothing** -- TAXABLE (no general exemption). FL runs annual
  sales-tax holidays (Back to School, Disaster Preparedness,
  Tool Time, Freedom Month) that temporarily exempt qualifying
  items; modeled when the holidays feature lands.
- **Groceries** -- NON-taxable for "groceries" (Fla. Stat.
  212.08(1)). Prepared food, candy, soda: taxable.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE for downloaded software and
  digital content.

NOT modeled in this loader:

- The **$5,000 single-item discretionary-surtax cap** (Fla. Stat.
  212.054(2)(b)) -- the county surtax applies only to the first
  $5,000 of any single item; the state 6% applies to the full
  amount. Future enhancement once the engine supports per-
  jurisdiction caps.
- **Tourist Development Tax (TDT)** -- transient-rental tax,
  separate from general sales tax.

State maintainer: vacant -- see MAINTAINERS.md. FL's annual
sales-tax holidays are extensive (typically 4-5 per year, set
by annual legislation); a maintainer who tracks legislative
sessions is ideal.

DISCLAIMER: This is calculation infrastructure, not tax advice.
Verify every rule against the current FL DOR DR-15DSS publication
and Form DR-15 schedule before relying on it for compliance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.states.fl_data import (
    FL_CITIES,
    FL_COUNTY_SURTAX_PCT,
    FL_STATE_EFFECTIVE_FROM,
    FL_STATE_RATE_PCT,
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
        notes=(
            "Clothing IS taxable in Florida year-round. Annual "
            "back-to-school sales-tax holidays temporarily exempt "
            "qualifying items; modeled when the holidays feature lands."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Groceries are non-taxable in Florida (Fla. Stat. 212.08(1)). "
            "Prepared food, candy, and soda are taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable in Florida.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in Florida.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Florida.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Florida:
    """Florida state module (tier 1; state 6% + per-county discretionary surtax)."""

    state_abbrev: str = "FL"
    state_name: str = "Florida"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield FL's state + per-county discretionary-surtax rates.

        Counties yielded: every county with a non-zero surtax PLUS
        every county touched by a covered ``FL_CITIES`` entry (so that
        zero-surtax counties hosting covered cities still get a county
        authority for boundary binding). Florida has no city-level
        sales tax, so no city ``RateRow`` rows are emitted.

        ``source_file`` is intentionally ignored -- FL is non-SST and
        has no upstream rate file consumed by this module.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Florida",
            authority_type="state",
            rate_pct=FL_STATE_RATE_PCT,
            effective_from=FL_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Counties to emit: any county with a non-zero surtax (so the
        # rate is queryable for any ZIP later bound to it) plus any
        # county touched by a covered city (so ZIPs in our city list
        # can resolve to a county authority even where the surtax is
        # zero, e.g. Citrus County).
        cities_counties = {county for county, _ in FL_CITIES.values()}
        nonzero_counties = {
            name for name, rate in FL_COUNTY_SURTAX_PCT.items() if rate > 0
        }
        emitted = sorted(cities_counties | nonzero_counties)
        for county_name in emitted:
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=FL_COUNTY_SURTAX_PCT[county_name],
                effective_from=FL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Florida",
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every FL ZIP. This method ADDS county bindings (and reaffirms
        the state binding) for ZIPs in the 30 covered cities. Florida
        has no city-level sales tax, so NO city ``BoundaryRow`` rows
        are emitted -- the city is purely an organizational concept
        in :mod:`fl_data` and does not become an authority.

        ZIPs in covered counties but outside the city list keep the
        Census state-only binding -- a future ratchet should iterate
        the Census ZCTA->county data for FL to add county-only
        bindings across the rest of the state.
        """
        del source_file, version_label
        for _city_name, (county_name, zips) in FL_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="Florida",
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

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Florida runs 4-5 annual sales-tax holidays set by legislation.

        2026 dates encoded explicitly. Add subsequent years as the
        Florida Legislature's annual tax-relief bill is published.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Disaster Preparedness (2026)",
                    starts_on=dt.date(2026, 6, 1),
                    ends_on=dt.date(2026, 6, 14),
                    applicable_categories=("emergency_supplies",),
                    max_amount_per_item=None,
                    notes="Batteries, generators, ice chests, etc.",
                ),
                HolidayWindow(
                    name="Freedom Month (2026)",
                    starts_on=dt.date(2026, 7, 1),
                    ends_on=dt.date(2026, 7, 31),
                    applicable_categories=("recreation", "entertainment"),
                    max_amount_per_item=None,
                    notes="Outdoor recreation gear, event admissions, etc.",
                ),
                HolidayWindow(
                    name="Back-to-School (2026)",
                    starts_on=dt.date(2026, 8, 1),
                    ends_on=dt.date(2026, 8, 14),
                    applicable_categories=("clothing", "school_supplies", "computers"),
                    max_amount_per_item=Decimal("100.00"),
                    notes="Clothing $100/less, supplies $50/less, computers $1500/less.",
                ),
                HolidayWindow(
                    name="Tool Time (2026)",
                    starts_on=dt.date(2026, 9, 5),
                    ends_on=dt.date(2026, 9, 11),
                    applicable_categories=("tools",),
                    max_amount_per_item=None,
                    notes="Tools and shop supplies for skilled trade workers.",
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Florida()
del _PROTOCOL_CHECK

FLORIDA = register(Florida())
