# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Illinois state module (tier 1, non-SST).

IL is **not** an SST member. State Retailer's Occupation Tax base
rate is **6.25%** per the Illinois Department of Revenue
(tax.illinois.gov). Many home-rule cities add their own rates;
combined rates range 6.25%-11%.

**Top-20-city coverage shipped.** All 20 covered cities (the top 20
IL cities by 2020 census population) are seeded from
:mod:`opensalestax.states.il_data`, sourced from the IDOR Tax Rate
Database / Tax Rate Finder publications and cross-checked against
Avalara per-city rate pages on 2026-05-04. The module emits four
authority types:

- **state** (Illinois, 6.25%)
- **county** (per-county portion; e.g. Cook 1.75%, Sangamon 1.0%,
  Winnebago 1.5%, Champaign 1.25%, Macon 1.5%, Peoria 1.0%; 0% for
  most other IL counties)
- **district** (Regional Transportation Authority -- two authorities:
  ``RTA (Cook County)`` at 1.00% and ``RTA (Collar Counties)`` at
  0.75%, the latter covering DuPage, Kane, Lake, McHenry, Will)
- **city** (combined municipal portion: city sales tax + home-rule
  + non-home-rule municipal taxes)

ZIPs not in :data:`il_data.IL_CITIES` fall back to state-only at
6.25% via the Census ZCTA load. This is a significant under-
collection for suburban / unincorporated Illinois; a future ratchet
should ingest the IDOR Tax Rate Database CSV directly.

Taxability matrix (per IL Retailer's Occupation Tax Act -- 35 ILCS
120):

- **Clothing** -- TAXABLE in Illinois (no general exemption).
- **Groceries** -- **TAXABLE at a reduced 1% state rate.** This is
  unusual: most states either fully exempt groceries or fully
  tax them. Encoded with ``rate_modifier=Decimal("1.000")``;
  the engine applies rate_modifier (since v0.11.1). Local
  portions still apply at the regular local rate.
- **Prescription drugs** -- TAXABLE at the reduced 1% state rate
  (same caveat as groceries).
- **Prepared food** -- taxable at the standard rate.
- **Digital goods** -- TAXABLE.

State maintainer: vacant -- see MAINTAINERS.md.

Disclaimer: this module is calculation infrastructure, not tax
advice. Special Service Areas (SSAs), business-improvement districts,
and the home-rule local-rate landscape can produce surprising
results at specific +4 addresses. Verify against the IDOR Tax
Rate Finder before relying on these rates for compliance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.states.il_data import (
    IL_CITIES,
    IL_COUNTY_RATE_PCT,
    IL_RTA_DISTRICTS,
    IL_STATE_EFFECTIVE_FROM,
    IL_STATE_RATE_PCT,
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
        notes="Clothing IS taxable in Illinois (no general exemption).",
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("1.000"),
        notes=(
            "Groceries are taxable at a REDUCED 1% rate in Illinois. "
            "v0.4 reports them as taxable with rate_modifier=1.0; the "
            "engine applies rate_modifier (since v0.11.1). Retailers selling "
            "groceries in IL should verify with IDOR as of v0.11.1 the engine wires "
            "the modifier through."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=True,
        rate_modifier=Decimal("1.000"),
        notes="Prescription drugs taxed at reduced 1% rate (same caveat as groceries).",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food taxed at the standard 6.25% rate plus local additions.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Illinois.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Illinois:
    """Illinois state module (tier 1; state + county + RTA + city)."""

    state_abbrev: str = "IL"
    state_name: str = "Illinois"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield IL's state + per-county + per-RTA + per-city rates.

        Counties yielded: only those touched by a covered city.
        RTA districts yielded: only those touched by a covered city.
        Cities yielded: every IL_CITIES entry. ``source_file`` is
        intentionally ignored -- IL is non-SST and has no upstream file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Illinois",
            authority_type="state",
            rate_pct=IL_STATE_RATE_PCT,
            effective_from=IL_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        used_counties = {county for county, _, _, _ in IL_CITIES.values()}
        for county_name in sorted(used_counties):
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=IL_COUNTY_RATE_PCT[county_name],
                effective_from=IL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Illinois",
            )
        used_rtas = {
            rta for _, rta, _, _ in IL_CITIES.values() if rta is not None
        }
        for rta_name in sorted(used_rtas):
            yield RateRow(
                authority_name=rta_name,
                authority_type="district",
                rate_pct=IL_RTA_DISTRICTS[rta_name],
                effective_from=IL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Illinois",
            )
        for city_name, (county_name, _rta, city_rate, _zips) in sorted(IL_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=IL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=county_name,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, rta?, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every IL ZIP. This method ADDS county + (optional) RTA + city
        bindings for the 20 covered cities. ZIPs in covered counties
        but outside the city list keep the Census state-only binding
        (under-collects local tax for any address in an incorporated
        city not on the seed list).
        """
        del source_file, version_label
        for city_name, (county_name, rta_name, _city_rate, zips) in IL_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="Illinois",
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
                if rta_name is not None:
                    yield BoundaryRow(
                        authority_name=rta_name,
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
        """Illinois has no recurring annual sales-tax holiday in the current law."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = Illinois()
del _PROTOCOL_CHECK

ILLINOIS = register(Illinois())
