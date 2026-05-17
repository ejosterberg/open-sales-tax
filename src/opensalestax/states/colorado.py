# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Colorado state module (tier 1, non-SST) -- STATE-PORTION ONLY.

WARNING -- HOME-RULE LIMITATION
-------------------------------
Colorado has the most complex local-tax landscape of any US state outside
of Louisiana. Approximately **70 home-rule cities** -- including Denver,
Aurora, Boulder, Colorado Springs, Fort Collins, Lakewood, Thornton,
Arvada, Pueblo, and Greeley -- **self-administer** their own sales tax
under Article XX of the Colorado Constitution. Each home-rule city
defines its own rate, its own tax base (including categories the state
exempts), and its own filing/registration regime. The Colorado Department
of Revenue (CDOR) does **not** collect on behalf of these cities.

**This module ships ONLY the state-level 2.9% rate and state taxability
matrix.** It does NOT model home-rule cities. API consumers calling
``/v1/calculate`` for an address inside a home-rule city will receive an
**under-collection** of tax -- the city portion is missing entirely, and
the taxability matrix may be wrong (notably, Denver, Boulder, Colorado
Springs, Fort Collins, and most other home-rule cities **tax groceries**
at the local level even though the state exempts them).

The full rationale and the path to correctness lives in
``specs/decisions/04-colorado-home-rule.md``. The short version:
modelling home-rule cities requires either (a) per-jurisdiction
taxability overrides or (b) a new "self-administered sub-jurisdiction"
abstraction. Both are schema changes that v0.7's per-state agent brief
explicitly forbids; both are deferred to v1.0+ when CO, LA (parishes),
and AL (independent locals) all need the same primitive and the
abstraction can be designed once.

State-administered model summary
--------------------------------
Three concurrent regimes operate in Colorado:

1. **State** -- 2.9% per Colo. Rev. Stat. section 39-26-106 since
   2001-01-01 (one of the lowest state-level rates of any taxing US
   state).
2. **State-collected locals** -- counties, special districts (RTD,
   SCFD, Football Stadium District), and most non-home-rule
   municipalities. CDOR collects these on the locality's behalf at
   locally-set rates. **Not modeled in v0.7** (deferred until a CO
   data ingestion path lands; CO has no SST quarterly file and no
   public machine-readable rate-by-ZIP feed comparable to Texas's
   Comptroller file).
3. **Home-rule self-collecting cities** (~70) -- the regime described
   above. **Not modeled in v0.7.**

Combined effective rates therefore range from 2.9% (an unincorporated
area with no county or special-district add-on) to **11.2%+** in some
home-rule cities. The true number for any given address inside a
home-rule jurisdiction cannot be derived from this module alone.

Taxability matrix (statewide rules; per Colo. Rev. Stat. Title 39
Article 26, Part 7)
-------------------------------------------------------------------

- **Clothing** -- TAXABLE. Colorado has no clothing exemption at the
  state level. Some home-rule cities may diverge; see warning above.
- **Groceries (food for home consumption)** -- NON-TAXABLE per
  section 39-26-707(1)(e), exempt since 1980-01-01. **Candy and soft
  drinks** are statutorily carved out of the exemption (taxable) per
  section 39-26-707(1.5) effective 2010-05-01; the engine treats both
  as `prepared_food` / `general` for now -- per-subcategory granularity
  is deferred. **Most home-rule cities tax groceries locally**, so a
  grocery purchase inside Denver/Boulder/Colorado Springs/etc. that
  this module reports as 0% may actually owe ~3-4% to the city.
- **Prescription drugs** -- exempt per section 39-26-717. Insulin,
  oxygen-delivery equipment, and several categories of disposable
  medical supplies dispensed pursuant to a prescription are also
  exempt under the same section.
- **Prepared food** -- TAXABLE. Restaurant meals and hot prepared
  foods do not qualify for the section 39-26-707(1)(e) exemption.
- **Digital goods** -- TAXABLE. House Bill 21-1312 (signed 2021-06-23,
  effective 2021-07-01) amended Colo. Rev. Stat. section
  39-26-102(15)(b.5) to expand the definition of "tangible personal
  property" to include "digital goods" regardless of the method of
  delivery -- electronic downloads and streaming of video, music, and
  electronic books are all taxable. (Note: the orchestrator brief
  mentioned "HB21-1162" affecting sourcing -- HB21-1162 governs
  destination-sourcing transitions; HB21-1312 governs digital goods.
  Both are accurate, separate bills.)

Sales-tax holidays
------------------
Colorado has **NO state-level sales-tax holidays.** Some home-rule
cities have implemented their own local holidays (not modeled here).
``holidays_for(year)`` returns an empty iterator for every year by
design; do not extrapolate.

Loading
-------
The v0.2 loader treats ``Colorado.parse_rates`` as "self-seeded" -- it
returns the single statewide row and ignores the source-file argument.
Use ``opensalestax data load --state CO --version v0.7-statewide`` to
insert it.

State maintainer: vacant -- see MAINTAINERS.md. Colorado is the
**canonical priority candidate** for the v1.0+ self-administered
sub-jurisdiction abstraction; an interested maintainer who knows
DR 1002 + the Denver/Boulder tax codes would be the natural lead.

DISCLAIMER: This is calculation logic, not tax advice. Maintainers and
users are responsible for verifying current CDOR and home-rule-city
guidance before relying on these rules in production.
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
        notes=(
            "Clothing IS taxable in Colorado at the 2.9% state rate "
            "(Colo. Rev. Stat. section 39-26-104). Colorado has NO "
            "clothing exemption. Home-rule cities apply their own rates "
            "and may diverge -- this module models the state portion only. "
            "Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food for home consumption is exempt from the 2.9% state "
            "sales tax per Colo. Rev. Stat. section 39-26-707(1)(e), in "
            "effect since 1980-01-01. WARNING: most Colorado home-rule "
            "cities (Denver, Boulder, Colorado Springs, Fort Collins, "
            "etc.) DO tax groceries at the local level -- this module "
            "does not model home-rule cities, so a grocery purchase the "
            "engine reports as 0% may actually owe local tax. Candy and "
            "soft drinks are taxable per section 39-26-707(1.5) effective "
            "2010-05-01. Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are exempt per Colo. Rev. Stat. section "
            "39-26-717. Insulin, oxygen-delivery equipment, and certain "
            "prescription-dispensed medical supplies are also exempt under "
            "the same section. Calculation only -- not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot prepared foods) is "
            "taxable in Colorado; the section 39-26-707(1)(e) exemption "
            "covers food for home consumption only. Many home-rule cities "
            "impose additional prepared-food/restaurant taxes -- this "
            "module models the state portion only. Calculation only -- "
            "not tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are TAXABLE in Colorado per HB 21-1312 "
            "(effective 2021-07-01), which amended Colo. Rev. Stat. "
            "section 39-26-102(15)(b.5) to expand 'tangible personal "
            "property' to include digital goods regardless of method of "
            "delivery (downloads and streaming of video, music, e-books). "
            "Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at the 2.9% "
            "state rate per Colo. Rev. Stat. section 39-26-104. "
            "WARNING -- Colorado has approximately 70 home-rule "
            "self-collecting cities (Denver, Aurora, Boulder, Colorado "
            "Springs, Fort Collins, Lakewood, etc.) that administer their "
            "own sales taxes with their own rates and bases. This module "
            "does NOT model home-rule cities; combined rates inside those "
            "jurisdictions reach 11%+ and this engine will under-collect. "
            "See specs/decisions/04-colorado-home-rule.md. Calculation "
            "only -- not tax advice."
        ),
    ),
}

# Statewide 2.9% rate took effect 2001-01-01 per Colo. Rev. Stat.
# section 39-26-106(1)(a)(II); the rate has been stable since.
_RATE_EFFECTIVE_FROM = dt.date(2001, 1, 1)


class Colorado:
    """Colorado state module (tier 1; STATE PORTION ONLY in v0.7).

    Home-rule self-collecting cities (~70 of them) are NOT modeled. See
    the module docstring and ``specs/decisions/04-colorado-home-rule.md``
    for the full rationale and the path to correctness.
    """

    state_abbrev: str = "CO"
    state_name: str = "Colorado"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require a
    # cached upstream file. CO's parse_rates returns the same statewide
    # row regardless of source_file (no SST file exists for CO).
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Colorado's statewide 2.9% rate.

        ``source_file`` is intentionally ignored -- CO has no SST
        upstream file. Pass ``None`` from the loader.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Colorado",
            authority_type="state",
            rate_pct=Decimal("2.900"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundaries shipped in v0.7.

        Per-county and per-municipality (state-collected) rates require
        a CO-specific data ingestion path that is deferred until a
        DR 1002 loader lands. Home-rule cities are deferred to a
        future "self-administered sub-jurisdiction" abstraction
        (see ``specs/decisions/04-colorado-home-rule.md``).
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return CO's taxability rule for ``item_category`` (state portion)."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for CO in v0.7."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Colorado has NO state-level sales-tax holidays.

        Some home-rule cities (e.g., certain back-to-school events)
        have local holidays -- those are NOT modeled here because
        home-rule cities themselves are not modeled. ``year`` is
        accepted for Protocol conformance and ignored.
        """
        del year
        return iter(())

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return CO's STATE-LEVEL shipping rule.

        At the state level, separately stated delivery is exempt
        from CO's 2.9% rate. WARNING -- the ~70 home-rule
        self-collecting cities (Denver, Boulder, Colorado Springs,
        Fort Collins, etc.) each set their own shipping rule and
        most of them DO tax shipping; this module models the state
        portion only and the home-rule coverage_warning already
        flags the broader gap (see module docstring).
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.EXEMPT_IF_SEPARATELY_STATED,
            citation=(
                "C.R.S. 39-26-104(1)(a) (state portion only; "
                "home-rule cities apply their own shipping rules)"
            ),
        )


_PROTOCOL_CHECK: StateModule = Colorado()
del _PROTOCOL_CHECK

COLORADO = register(Colorado())
