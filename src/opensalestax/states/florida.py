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

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
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

        All 67 FL counties from :data:`FL_COUNTY_SURTAX_PCT` are
        emitted -- including the zero-surtax counties (e.g. Citrus) --
        so that any FL ZIP bound to a county via the Census ZCTA->county
        relationship can resolve cleanly. Zero-rate authorities sum to
        no effect but preserve the rate-stack audit trail. Florida has
        no city-level sales tax, so no city ``RateRow`` rows are
        emitted.

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
        # Emit a RateRow for every FL county. The ZIP_COUNTY-driven
        # boundary loader binds every FL ZIP to its county/counties, so
        # every county must have a queryable rate (even the 0% ones).
        for fl_county_name in sorted(FL_COUNTY_SURTAX_PCT):
            yield RateRow(
                authority_name=fl_county_name,
                authority_type="county",
                rate_pct=FL_COUNTY_SURTAX_PCT[fl_county_name],
                effective_from=FL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Florida",
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county) boundary rows for every FL ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county bindings for every ZIP intersecting an
           FL county. This covers the entire state, not just the ZIPs
           in the :data:`FL_CITIES` top-30 seed list -- so Miami Beach
           (33139), Key West (33040), Naples (34102), and every other
           FL ZIP resolves to its county's discretionary surtax
           instead of falling back to state-only.

        2. Fall back to :data:`FL_CITIES` for any city ZIP missed by
           the Census ZCTA pass (USPS-only / PO-box-only ZIPs that
           aren't published as Census ZCTAs, e.g. Jacksonville's
           32099). This guards against city-coverage regressions.

        A ZIP that crosses county lines yields one county BoundaryRow
        per intersecting county; the engine picks the highest-precision
        match at lookup time.

        Florida has no city-level sales tax, so NO city
        ``BoundaryRow`` rows are emitted -- :data:`FL_CITIES` is used
        only as a regression-guard fallback and does not become a
        city authority.
        """
        del source_file, version_label
        # Build city-anchor county map for cross-county-line ZIPs.
        # When a ZIP is in FL_CITIES, the city's declared county wins.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, czs) in FL_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Emit at most one county per ZIP per Census ZCTA: prefer the
        # city-anchor county if known, else first Census-listed county.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            # ZIP_COUNTY values are frozensets, so iteration order is
            # non-deterministic; sort by FIPS so cross-county ZIPs pick
            # the same county across Python interpreter restarts.
            sorted_fl_pairs = sorted(cf for sa, cf in pairs if sa == "FL")
            for county_fips in sorted_fl_pairs:
                fl_county_name = county_name("FL", county_fips)
                if fl_county_name is None or fl_county_name not in FL_COUNTY_SURTAX_PCT:
                    continue
                if preferred_county is not None:
                    if fl_county_name == preferred_county:
                        chosen_county = fl_county_name
                        break
                    continue
                chosen_county = fl_county_name
                break
            if chosen_county is None and preferred_county is not None:
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Florida",
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
        # Fallback pass: city ZIPs that aren't in Census ZCTA (USPS-only
        # codes like Jacksonville's 32099). Use FL_CITIES' county
        # binding so the city's ZIPs always resolve to a county.
        for _city_name, (fl_city_county, zips) in FL_CITIES.items():
            for zip5 in zips:
                if zip5 in emitted_zips:
                    continue
                yield BoundaryRow(
                    authority_name="Florida",
                    authority_type="state",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
                yield BoundaryRow(
                    authority_name=fl_city_county,
                    authority_type="county",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
                emitted_zips.add(zip5)

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
