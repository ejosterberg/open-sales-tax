# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""California state module (tier 1, non-SST).

CA is **not** a Streamlined Sales Tax member, so no quarterly SST
file. The state base rate is **7.25%** (the highest statewide rate
in the US, per the CDTFA -- the California Department of Tax and Fee
Administration).

CA's rate landscape is famously complex: ~1,700 district taxes
overlay the statewide rate, taking combined rates from 7.25% (rural
counties with no local overlay) up to **10.75%** (Hayward in Alameda
County, plus a handful of LA County suburbs not in this seed --
Pico Rivera and Santa Fe Springs).

**v0.27 ships state + per-county-district + top-50-city coverage.**
All 50 covered cities (the top 50 by 2020 census population, with
East Los Angeles included as the unincorporated CDP that carries the
LA County rate) are seeded from :mod:`opensalestax.states.ca_data`,
sourced from the CDTFA's "California City and County Sales and Use
Tax Rates" publication effective April 1, 2026 (Q2 2026) and cross-
checked against Avalara's per-city rate pages on 2026-05-04. The
module emits three authority types:

- **state** (California, 7.25%)
- **county** (per-county district overlay; 0% for Kern/Ventura,
  2.250% for LA, 2.000% for Alameda, etc.)
- **city** (city-only district portion; 0% for many cities --
  Anaheim, Irvine, Fontana, Ontario, Roseville, etc. -- and up to
  2.000% for Oxnard or 1.875% for Vallejo)

ZIPs not in :data:`ca_data.CA_CITIES` fall back to state-only at
7.25% via the Census ZCTA load. This is a significant under-
collection for suburban / unincorporated California; a future
ratchet should ingest the CDTFA address-level Tax Rate Area dataset
to extend coverage statewide.

**Sourcing model -- IMPORTANT:** California uses a hybrid sourcing
rule. The **state + uniform 1.25%** portion is sourced to the
seller's location for in-state sales; the **district tax** portions
(county + city) are sourced to the **delivery address** per Cal.
Rev. & Tax Code section 7261. The ZIP-based boundary table here is
a delivery-address approximation that produces the correct combined
rate at the centroid of any covered ZIP. A future ratchet should
expose the seller-vs-buyer distinction so the API caller can pick
the right rule.

Taxability matrix:

- **Clothing** -- TAXABLE (no exemption like MN's).
- **Groceries** -- NON-taxable for "food products for human
  consumption" sold for off-premise use (Cal. Rev. & Tax Code
  section 6359). Hot prepared food and restaurant meals are
  taxable.
- **Prescription drugs** -- NON-taxable (section 6369).
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE per AB 147 (2019) and subsequent
  CDTFA guidance.

State maintainer: vacant -- see MAINTAINERS.md. CA is the highest-
impact state in the US; a maintainer who knows the CDTFA address-
level dataset should pick this up.

Disclaimer: this module is calculation infrastructure, not tax
advice. CA's special districts (Tax Rate Areas, BIDs, etc.) and
hybrid sourcing rule can produce surprising results at specific
addresses. Verify against the CDTFA tax-rate lookup before relying
on these rates for compliance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from opensalestax.states.ca_data import (
    CA_CITIES,
    CA_COUNTY_RATE_PCT,
    CA_STATE_EFFECTIVE_FROM,
    CA_STATE_RATE_PCT,
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

# California taxability matrix per Cal. Rev. & Tax Code (statewide rules).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in California -- CA has no clothing "
            "exemption. (Many states do; CA does not.)"
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food products for human consumption (Cal. Rev. & Tax Code "
            "section 6359) are non-taxable in California when sold for "
            "off-premise use. Hot prepared food and restaurant meals "
            "are taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable (Cal. Rev. & Tax Code section 6369).",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in California.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are taxable in California per AB 147 (2019) "
            "and subsequent CDTFA guidance."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class California:
    """California state module (tier 1; state + per-county + top-50 cities in v0.27)."""

    state_abbrev: str = "CA"
    state_name: str = "California"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require
    # a cached upstream file. CA's parse_rates returns embedded data
    # regardless of source_file, so no file is needed.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield CA's state + per-county-district + per-city rates.

        Counties yielded: only those touched by a CA_CITIES entry.
        Cities yielded: every CA_CITIES entry. ``source_file`` is
        intentionally ignored -- CA is non-SST and has no machine-
        readable upstream rate file in v0.27.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="California",
            authority_type="state",
            rate_pct=CA_STATE_RATE_PCT,
            effective_from=CA_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a county RateRow for every county touched by a covered
        # city. Counties not used by any city are skipped to avoid
        # loading rates without any matching boundary.
        used_counties = {county for county, _, _ in CA_CITIES.values()}
        for county_name in sorted(used_counties):
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=CA_COUNTY_RATE_PCT[county_name],
                effective_from=CA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="California",
            )
        for city_name, (county_name, city_rate, _zips) in sorted(CA_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=CA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=county_name,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every CA ZIP. This method ADDS county + city bindings for the
        50 covered cities. ZIPs in covered counties but outside the
        city list keep the Census state-only binding (under-collects
        local tax for any address in an incorporated city not on the
        seed list, of which there are many in CA's ~480 incorporated
        municipalities).
        """
        del source_file, version_label
        for city_name, (county_name, _city_rate, zips) in CA_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="California",
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
        """Return CA's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for CA in Phase 2."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """California has no annual sales-tax holidays."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = California()
del _PROTOCOL_CHECK

CALIFORNIA = register(California())
