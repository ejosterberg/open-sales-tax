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

**Statewide ZIP coverage via Census ZCTA**
(parallels FL/AZ/CA in v0.28). All 102 IL counties are seeded in
:data:`IL_COUNTY_RATE_PCT` and :meth:`Illinois.parse_boundaries`
iterates :data:`opensalestax.data.zip_county.ZIP_COUNTY` to bind
every IL ZIP to its county and the appropriate RTA district (Cook
or Collar) where applicable. The 90 counties added beyond the
original top-12 city seed sit at a 0.000% PLACEHOLDER rate; many
IL counties levy a county school facility tax / public safety tax
(typically 0.25%-1.0%) that a future maintainer should bump out
of the 0% block by auditing the IDOR per-county rate tables.
Until then, those counties under-collect by their county-level
addition (combined remains state 6.25% + 0% = 6.25% for non-city
ZIPs) -- a strict improvement over the prior state-only fallback,
which lost the audit trail entirely.

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

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
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

        Counties yielded: every county in :data:`IL_COUNTY_RATE_PCT`
        (all 102 IL counties). The ZIP_COUNTY-driven boundary loader
        binds every IL ZIP to its county, so every county must have
        a queryable rate (the long tail of 90 outside the original
        seed sit at 0% pending maintainer audit). RTA districts
        yielded: BOTH district authorities so the boundary loader can
        bind the RTA-Cook district to Cook County ZIPs and the
        RTA-Collar district to ZIPs in DuPage / Kane / Lake / McHenry
        / Will. Cities yielded: every IL_CITIES entry. ``source_file``
        is intentionally ignored -- IL is non-SST and has no upstream
        file.
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
        # Emit a county RateRow for every IL county.
        for il_county_name in sorted(IL_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=il_county_name,
                authority_type="county",
                rate_pct=IL_COUNTY_RATE_PCT[il_county_name],
                effective_from=IL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Illinois",
            )
        # Emit BOTH RTA districts (Cook + Collar). The boundary loader
        # binds them to ZIPs based on the ZIP's county.
        for rta_name in sorted(IL_RTA_DISTRICTS):
            yield RateRow(
                authority_name=rta_name,
                authority_type="district",
                rate_pct=IL_RTA_DISTRICTS[rta_name],
                effective_from=IL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Illinois",
            )
        for city_name, (city_county, _rta, city_rate, _zips) in sorted(IL_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=IL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, rta, city]) boundary rows for every IL ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county + (optional) RTA bindings for every
           ZIP intersecting an IL county. This covers the entire
           state -- not just the ZIPs in the top-20 city seed -- so a
           ZIP outside any covered city now resolves to state +
           county (+ RTA where applicable) instead of state-only.

        2. Fall back to :data:`IL_CITIES` for any city ZIP missed by
           the Census pass and emit the city BoundaryRow on top of
           the stack so the city's home-rule portion is layered.

        Per the FL/AZ/CA pattern, emit at most ONE county per ZIP per
        Census ZCTA, preferring the city-anchor county if the ZIP is
        in :data:`IL_CITIES`. The RTA district binding follows the
        chosen county: Cook → ``RTA (Cook County)`` (1.00%), DuPage /
        Kane / Lake / McHenry / Will → ``RTA (Collar Counties)``
        (0.75%), all other counties → no RTA binding.
        """
        del source_file, version_label
        # County → RTA mapping per 70 ILCS 3615/4.03.
        rta_for_county: dict[str, str] = {
            "Cook County": "RTA (Cook County)",
            "DuPage County": "RTA (Collar Counties)",
            "Kane County": "RTA (Collar Counties)",
            "Lake County": "RTA (Collar Counties)",
            "McHenry County": "RTA (Collar Counties)",
            "Will County": "RTA (Collar Counties)",
        }

        # Build city-anchor county map for cross-county-line ZIPs.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, _rta, _r, czs) in IL_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Pass 1: state + county (+ RTA) for every IL ZIP per Census ZCTA.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            # ZIP_COUNTY values are frozensets; sort by FIPS for stability.
            sorted_il_pairs = sorted(cf for sa, cf in pairs if sa == "IL")
            for county_fips in sorted_il_pairs:
                il_county_name = county_name("IL", county_fips)
                if il_county_name is None or il_county_name not in IL_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if il_county_name == preferred_county:
                        chosen_county = il_county_name
                        break
                    continue
                chosen_county = il_county_name
                break
            if chosen_county is None and preferred_county is not None:
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Illinois",
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
            rta = rta_for_county.get(chosen_county)
            if rta is not None:
                yield BoundaryRow(
                    authority_name=rta,
                    authority_type="district",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
            emitted_zips.add(zip5)

        # Pass 2: city BoundaryRows for IL_CITIES.
        for city_name, (city_county, rta_for_city, _city_rate, zips) in IL_CITIES.items():
            for zip5 in zips:
                if zip5 not in emitted_zips:
                    yield BoundaryRow(
                        authority_name="Illinois",
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
                    if rta_for_city is not None:
                        yield BoundaryRow(
                            authority_name=rta_for_city,
                            authority_type="district",
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
