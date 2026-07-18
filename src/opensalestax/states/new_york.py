# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""New York state module (tier 1, non-SST).

NY is **not** an SST member. Statewide rate is **4%** per
NY DTF (tax.ny.gov). Local additions vary widely; the MCTD
(Metropolitan Commuter Transportation District) surcharge of
**0.375%** applies in NYC plus 7 surrounding counties (Nassau,
Suffolk, Westchester, Rockland, Dutchess, Orange, Putnam --
12 counties total counting NYC's five), and ~57 counties +
~18 cities impose their own local rates. Combined rates range
from 7% (a couple of upstate counties) to 8.875% (NYC and
Yonkers).

**Statewide coverage shipped.** All 62 NY counties seeded with
their per-county portion from NY DTF Publication 718 (retrieved
2026-05-04), and the boundary loader iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` to bind every NY
ZIP to its county (and the MCTD 0.375% district surcharge in the
12 MCTD counties), parallelling the FL/AZ/CA pattern shipped in
v0.28. Effect: any upstate NY ZIP outside the top-30 city seed
now resolves to state + county (+ MCTD where applicable) instead
of falling back to state-only at 4.0%. New York City is shipped
as ONE city entry "New York City" with parent county "New York
County" (Manhattan); the ZIP list covers all five boroughs
(Manhattan, Bronx, Brooklyn, Queens, Staten Island), all of which
share the 8.875% combined rate. See
:mod:`opensalestax.states.ny_data` for the per-city rates and
ZIP coverage.

Taxability matrix (per N.Y. Tax Law Article 28):

- **Clothing** -- TAXABLE with a state-level threshold:
  clothing/footwear priced under $110 per item is exempt from
  the state 4% rate (N.Y. Tax Law section 1115(a)(30)). The
  ``below_exempt`` semantic encodes this. The MCTD 0.375%
  surcharge follows the same threshold; local jurisdictions may
  opt back in (NY DTF Publication 718-C lists current local
  treatment). v0.26 ships the state-portion threshold; per-
  locality re-imposition lands when the threshold-rule engine
  expands to per-authority overrides.
- **Groceries** -- NON-taxable for "food and food products"
  (sec 1115(a)(1)). Candy, soda, prepared food: taxable.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE for prewritten software (sec
  1101(b)(6)); the rule for streamed/digital media is more
  nuanced.

State maintainer: vacant -- see MAINTAINERS.md. NY's clothing
rule is one of the more complex in the US; promoting this to a
fully-correct tier-1 needs a NY-resident maintainer who can
verify against DTF guidance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.states.ny_data import (
    NY_CITIES,
    NY_COUNTY_RATE_PCT,
    NY_MCTD_COUNTIES,
    NY_MCTD_DISTRICT_NAME,
    NY_MCTD_RATE,
    NY_STATE_EFFECTIVE_FROM,
    NY_STATE_RATE_PCT,
)
from opensalestax.states.protocol import (
    BoundaryRow,
    HolidayWindow,
    RateRow,
    ShippingRule,
    ShippingRuleSet,
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
        taxable_threshold_amount=Decimal("110.00"),
        threshold_semantic="below_exempt",
        notes=(
            "New York: clothing/footwear under $110 per item is exempt "
            "from the state 4% rate (N.Y. Tax Law section 1115(a)(30)). "
            "Items at or above $110 are fully taxable. The MCTD 0.375% "
            "surcharge follows the same threshold; local jurisdictions "
            "may opt back in -- see NY DTF Publication 718-C."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food products are non-taxable (N.Y. Tax Law "
            "section 1115(a)(1)). Candy, soda, prepared food are taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable in New York.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food (restaurant meals, etc.) is taxable.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Prewritten software is taxable (N.Y. Tax Law section "
            "1101(b)(6)). The rule for streamed/digital media is more "
            "nuanced; verify case-by-case."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class NewYork:
    """New York state module (tier 1; state + per-county + MCTD + top-30 cities)."""

    state_abbrev: str = "NY"
    state_name: str = "New York"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield NY's state + per-county + MCTD + per-city rates.

        Counties yielded: every county in :data:`NY_COUNTY_RATE_PCT`
        (all 62 NY counties). The ZIP_COUNTY-driven boundary loader
        binds every NY ZIP to its county, so every county must have a
        queryable rate. Cities yielded: every NY_CITIES entry. The
        MCTD surcharge is emitted once as a single ``district``
        authority that sits under the state; per-county MCTD
        applicability is encoded via the boundary table.

        ``source_file`` is intentionally ignored -- NY is non-SST and
        has no machine-readable upstream rate file in v0.26.
        """
        del source_file, version_label
        # State row -- 4.0%.
        yield RateRow(
            authority_name=self.state_name,
            authority_type="state",
            rate_pct=NY_STATE_RATE_PCT,
            effective_from=NY_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # MCTD row -- 0.375% district surcharge. Always emitted now
        # that the boundary loader binds the MCTD district to every
        # ZIP in an MCTD county (not just the cities in NY_CITIES).
        yield RateRow(
            authority_name=NY_MCTD_DISTRICT_NAME,
            authority_type="district",
            rate_pct=NY_MCTD_RATE,
            effective_from=NY_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=self.state_name,
        )
        # Per-county rows -- every NY county. The ZIP_COUNTY-driven
        # boundary loader binds every NY ZIP to its county, so every
        # county must have a queryable rate (even the 0% NYC ones).
        for ny_county_name in sorted(NY_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=ny_county_name,
                authority_type="county",
                rate_pct=NY_COUNTY_RATE_PCT[ny_county_name],
                effective_from=NY_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=self.state_name,
            )
        # Per-city rows. Most cities have a 0% city rate; only NYC
        # (4.5%), Yonkers (1.5%), New Rochelle / Mount Vernon /
        # White Plains (1.0% each) impose their own city sales tax.
        for city_name, (city_county, city_rate, _zips) in sorted(NY_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=NY_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, MCTD?, city) boundary rows for every NY ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county + (optional) MCTD bindings for every
           ZIP intersecting an NY county. This covers the entire state
           -- not just the ZIPs in the top-30 city seed -- so any
           upstate ZIP outside the city list now resolves to its
           county portion (and MCTD surcharge in the 12 MCTD counties)
           instead of falling back to state-only at 4.0%.

        2. Fall back to :data:`NY_CITIES` for any city ZIP missed by
           the Census pass and emit the city BoundaryRow on top of
           the stack so the city's tax (NYC 4.5%, Yonkers 0.5%, etc.)
           is layered correctly.

        Per the FL/AZ/CA pattern, emit at most ONE county per ZIP per
        Census ZCTA, preferring the city-anchor county if the ZIP is
        in :data:`NY_CITIES`. Without this, ZIPs that physically span
        county lines would get bound to BOTH counties and double-count
        the local tax.
        """
        del source_file, version_label
        # Build city-anchor county map for cross-county-line ZIPs.
        # When a ZIP is in NY_CITIES, the city's declared county wins.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, _rate, czs) in NY_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Pass 1: state + county (+ MCTD) for every NY ZIP per Census ZCTA.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            # ZIP_COUNTY values are frozensets; sort by FIPS for stability.
            sorted_ny_pairs = sorted(cf for sa, cf in pairs if sa == "NY")
            for county_fips in sorted_ny_pairs:
                ny_county_name = county_name("NY", county_fips)
                if ny_county_name is None or ny_county_name not in NY_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if ny_county_name == preferred_county:
                        chosen_county = ny_county_name
                        break
                    # keep iterating in hopes of finding the city's county
                    continue
                # No city anchor -- take the first NY county.
                chosen_county = ny_county_name
                break
            if chosen_county is None and preferred_county is not None:
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name=self.state_name,
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
            if chosen_county in NY_MCTD_COUNTIES:
                yield BoundaryRow(
                    authority_name=NY_MCTD_DISTRICT_NAME,
                    authority_type="district",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
            emitted_zips.add(zip5)

        # Pass 2: city BoundaryRows for NY_CITIES. Also emit state +
        # county (+ MCTD) for any city ZIP missed by the Census pass
        # (USPS-only / PO-box-only ZIPs not in ZCTA) so we never
        # regress city coverage.
        for city_name, (city_county, _city_rate, zips) in NY_CITIES.items():
            mctd_applies = city_county in NY_MCTD_COUNTIES
            for zip5 in zips:
                if zip5 not in emitted_zips:
                    yield BoundaryRow(
                        authority_name=self.state_name,
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
                    if mctd_applies:
                        yield BoundaryRow(
                            authority_name=NY_MCTD_DISTRICT_NAME,
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
        """New York has no annual sales-tax holidays at the state level."""
        del year
        return iter(())

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return NY's shipping rule.

        New York treats delivery charges as part of the taxable
        receipt when the underlying item is taxable; shipping is
        included in the taxable base when the goods are taxable
        and excluded when the goods are exempt. Practitioner
        default for typical e-commerce.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.CONDITIONAL,
            citation="NY Tax Bulletin ST-838",
        )


_PROTOCOL_CHECK: StateModule = NewYork()
del _PROTOCOL_CHECK

NEW_YORK = register(NewYork())
