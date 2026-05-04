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

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
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

        Counties yielded: every county in :data:`CA_COUNTY_RATE_PCT`
        so the ZIP_COUNTY-driven boundary loader can resolve any CA
        ZIP in a covered county to its county district authority,
        not just the ZIPs in the top-50 city seed. ZIPs in CA counties
        not yet in :data:`CA_COUNTY_RATE_PCT` (a long tail of small /
        rural counties) keep state-only binding from the Census ZCTA
        load -- a future ratchet should expand the county table.
        Cities yielded: every :data:`CA_CITIES` entry.

        ``source_file`` is intentionally ignored -- CA is non-SST and
        has no machine-readable upstream rate file in v0.27.
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
        # Emit a RateRow for every county in CA_COUNTY_RATE_PCT, not
        # just those touched by a covered city. The ZIP_COUNTY-driven
        # boundary loader binds every ZIP in these counties to the
        # county authority, so every county must have a queryable rate.
        for ca_county_name in sorted(CA_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=ca_county_name,
                authority_type="county",
                rate_pct=CA_COUNTY_RATE_PCT[ca_county_name],
                effective_from=CA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="California",
            )
        for ca_city_name, (ca_city_county, city_rate, _zips) in sorted(CA_CITIES.items()):
            yield RateRow(
                authority_name=ca_city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=CA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=ca_city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, city]) boundary rows for every CA ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` for
           every ZIP in a CA county that's in :data:`CA_COUNTY_RATE_PCT`
           and emit state + county bindings. This extends county-level
           coverage well beyond the top-50 city seed -- e.g., Encinitas
           (92024) in San Diego County now resolves to state 7.25% +
           SD County 0.5% = 7.75% instead of state-only 7.25%.

        2. For each :data:`CA_CITIES` entry, additionally emit a city
           BoundaryRow so the city's district portion is layered on top
           of the state + county stack at its ZIPs.

        ZIPs in CA counties not yet in :data:`CA_COUNTY_RATE_PCT` (a
        long tail of small / rural counties) keep state-only binding
        from the Census ZCTA load. A future ratchet should expand
        :data:`CA_COUNTY_RATE_PCT` to all 58 CA counties using the
        CDTFA address-level Tax Rate Area dataset.

        A ZIP that crosses county lines yields one county BoundaryRow
        per intersecting county.
        """
        del source_file, version_label
        # Build city-anchor county map: when a ZIP is in CA_CITIES, the
        # city's declared county wins over Census alternates. Prevents
        # double-counting for ZIPs spanning county lines.
        city_county_for_zip: dict[str, str] = {}
        for _city_name, (city_county, _rate, city_zips) in CA_CITIES.items():
            for cz in city_zips:
                city_county_for_zip[cz] = city_county

        # Pass 1: state + county for every CA ZIP per Census ZCTA.
        # Emit at most one county per ZIP: prefer the city-anchor
        # county if known, else the first Census-listed CA county.
        zips_with_county_emitted: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            # ZIP_COUNTY values are frozensets; sort by FIPS for stability.
            sorted_ca_pairs = sorted(cf for sa, cf in pairs if sa == "CA")
            for county_fips in sorted_ca_pairs:
                ca_county_name = county_name("CA", county_fips)
                if ca_county_name is None or ca_county_name not in CA_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if ca_county_name == preferred_county:
                        chosen_county = ca_county_name
                        break
                    continue
                chosen_county = ca_county_name
                break
            if chosen_county is None and preferred_county is not None:
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="California",
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
        # Pass 2: city BoundaryRows for CA_CITIES. Also emit state +
        # county for any city ZIP missed by the Census pass (PO-box-
        # only ZIPs not in ZCTA, etc.) so we never regress city coverage.
        for ca_city_name, (ca_city_county, _city_rate, zips) in CA_CITIES.items():
            for zip5 in zips:
                if zip5 not in zips_with_county_emitted:
                    yield BoundaryRow(
                        authority_name="California",
                        authority_type="state",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    yield BoundaryRow(
                        authority_name=ca_city_county,
                        authority_type="county",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    zips_with_county_emitted.add(zip5)
                yield BoundaryRow(
                    authority_name=ca_city_name,
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
