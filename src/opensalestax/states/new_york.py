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

**v0.26 ships state + per-county + MCTD-as-district +
top-30-city coverage** seeded from NY DTF Publication 718
(retrieved 2026-05-04). New York City is shipped as ONE city
entry "New York City" with parent county "New York County"
(Manhattan); the ZIP list covers all five boroughs (Manhattan,
Bronx, Brooklyn, Queens, Staten Island), all of which share
the 8.875% combined rate. ZIPs not in the city list fall back
to state-only at 4.0% via the Census ZCTA load -- a future
ratchet should iterate Census ZCTA->county data for all 62 NY
counties to pick up the correct county portion (and MCTD
surcharge in the 12 MCTD counties) statewide. See
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

        Counties yielded: only those touched by an NY_CITIES entry.
        Cities yielded: every NY_CITIES entry. The MCTD surcharge is
        emitted once as a single ``district`` authority that sits
        under the state; per-county MCTD applicability is encoded via
        the boundary table.

        ``source_file`` is intentionally ignored -- NY is non-SST and
        has no machine-readable upstream rate file in v0.26.
        """
        del source_file, version_label
        # State row -- 4.0%.
        yield RateRow(
            authority_name="New York",
            authority_type="state",
            rate_pct=NY_STATE_RATE_PCT,
            effective_from=NY_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # MCTD row -- 0.375% district surcharge. Emitted once if any
        # covered city sits in an MCTD county; the boundary table binds
        # the district to specific ZIPs.
        used_counties = {county for county, _, _ in NY_CITIES.values()}
        if used_counties & NY_MCTD_COUNTIES:
            yield RateRow(
                authority_name=NY_MCTD_DISTRICT_NAME,
                authority_type="district",
                rate_pct=NY_MCTD_RATE,
                effective_from=NY_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="New York",
            )
        # Per-county rows -- only counties touched by a covered city.
        for county_name in sorted(used_counties):
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=NY_COUNTY_RATE_PCT[county_name],
                effective_from=NY_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="New York",
            )
        # Per-city rows. Most cities have a 0% city rate; only NYC
        # (4.5%), Yonkers (1.5%), New Rochelle / Mount Vernon /
        # White Plains (1.0% each) impose their own city sales tax.
        for city_name, (county_name, city_rate, _zips) in sorted(NY_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=NY_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=county_name,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, MCTD?, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every NY ZIP; this method ADDS county + city bindings (and the
        MCTD district binding when the county is one of the 12 MCTD
        counties) for the 30 covered cities. ZIPs in covered counties
        but outside the city list keep the Census state-only binding;
        a future ratchet should extend coverage to all 62 NY counties
        and all MCTD ZIPs.
        """
        del source_file, version_label
        for city_name, (county_name, _city_rate, zips) in NY_CITIES.items():
            mctd_applies = county_name in NY_MCTD_COUNTIES
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="New York",
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
                if mctd_applies:
                    yield BoundaryRow(
                        authority_name=NY_MCTD_DISTRICT_NAME,
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
        """New York has no annual sales-tax holidays at the state level."""
        del year
        return iter(())


_PROTOCOL_CHECK: StateModule = NewYork()
del _PROTOCOL_CHECK

NEW_YORK = register(NewYork())
