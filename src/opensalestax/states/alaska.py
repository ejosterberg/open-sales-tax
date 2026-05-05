# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Alaska state module (tier 1; cities-only MVP via ARSSTC data).

Replaces the v0.1 ``NoTaxState("AK")`` registration with a real
state module that emits 0% state + per-city local rates for the
~20 largest sales-tax-collecting AK municipalities. See
:mod:`opensalestax.states.ak_data` for the data table and the
known-gaps catalogue (boroughs not modeled, Anchorage retained
at 0% per common in-state-retail practice, seasonal-rate
simplification, etc.).

Source data captured 2026-05-05 from the Alaska Remote Seller
Sales Tax Commission (ARSSTC) member jurisdictions list:
https://arsstc.org/business-sellers/member-jurisdictions/

Pre-v0.49 OpenSalesTax modeled AK as no-tax everywhere, missing
real local collections in Juneau / Sitka / Kodiak / Bethel /
Wasilla / Petersburg / etc. This ratchet brings the populated
ZIPs into compliance; unincorporated AK ZIPs and the long tail
of small AK municipalities continue to return 0% (per the
documented MVP scope).
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from opensalestax.states.ak_data import AK_CITIES, AK_STATE_RATE_PCT
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

# All AK rates in this ratchet are pinned to a single effective
# date. The ARSSTC list captures whatever rate is currently in
# effect for each member jurisdiction; without per-jurisdiction
# effective dates from ARSSTC we treat them as effective from
# AK's pre-statehood (functionally "always" for current use).
_RATE_EFFECTIVE_FROM = dt.date(1959, 1, 3)  # AK statehood

# Default taxability matrix for AK -- the state has no general
# sales tax, so per-category taxability defaults from the
# state's perspective are non-taxable. Local jurisdictions
# define their own taxability matrices (e.g. Juneau exempts
# food, Bethel taxes alcohol at 15%); modeling those per-
# jurisdiction is deferred to later ratchets. v0.49 marks
# every category as taxable at the local rate so the engine
# correctly applies city tax to general retail.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "Alaska has NO statewide sales tax (one of 5 no-state-tax "
            "jurisdictions). ~110 AK municipalities levy local sales "
            "tax at rates 0%-7.5%; OpenSalesTax v0.49 ships ~20 of the "
            "largest via the Alaska Remote Seller Sales Tax Commission "
            "(ARSSTC) data set. Anchorage Municipality has no general "
            "sales tax and returns 0% in this engine; ARSSTC's "
            "Anchorage 5% entry is a remote-seller-only rate (Wayfair "
            "post-decision) not collected at brick-and-mortar retail. "
            "Borough rates and the long tail of unmodeled AK cities "
            "continue to under-collect. See ak_data.py for the full "
            "MVP scope. Calculation only -- not legal or tax advice."
        ),
    ),
}


class Alaska:
    """Alaska state module (tier 1; cities-only ARSSTC MVP).

    Replaces the previous ``NoTaxState("AK")`` registration. Yields
    a 0% state RateRow plus per-city RateRows for every covered
    municipality in :data:`AK_CITIES`. Emits state + city boundary
    rows for the cities' covered ZIPs only -- ZIPs in unincorporated
    borough areas (or in cities not yet in the MVP table) get
    state-only 0% bindings via the engine's standard "no city"
    fallback, which matches the user-facing rate of 0% for an
    unmodeled AK address.
    """

    state_abbrev: str = "AK"
    state_name: str = "Alaska"
    sst_member: bool = False
    has_sales_tax: bool = True  # local-only, but the state does collect via cities
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Alaska's 0% state row + per-city rates from AK_CITIES."""
        del source_file, version_label
        yield RateRow(
            authority_name="Alaska",
            authority_type="state",
            rate_pct=AK_STATE_RATE_PCT,
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        for city_name, (_borough, city_rate, _zips) in sorted(AK_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=_RATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Alaska",
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, city) boundary rows for every covered AK city ZIP.

        Cities-only MVP: state row is emitted for each city ZIP so the
        engine resolves the rate stack correctly; borough rows are
        deliberately NOT emitted (per the per-borough exclusivity
        deferral documented in ``ak_data.py``).
        """
        del source_file, version_label
        for city_name, (_borough, _city_rate, zips) in sorted(AK_CITIES.items()):
            for zip5 in sorted(zips):
                yield BoundaryRow(
                    authority_name="Alaska",
                    authority_type="state",
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
        """Return Alaska's taxability rule for ``item_category`` (general only)."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No SpecialCase entries tracked for AK in this MVP."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """No statewide sales-tax holidays in Alaska."""
        del year
        return iter(())


# Compile-time check: Alaska satisfies the StateModule Protocol.
_PROTOCOL_CHECK: StateModule = Alaska()
del _PROTOCOL_CHECK

ALASKA = register(Alaska())
