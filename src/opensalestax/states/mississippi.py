# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Mississippi state module (tier 1, non-SST).

MS is **not** a Streamlined Sales Tax member. The general statewide
rate is **7%** per Miss. Code Ann. section 27-65-17, the highest
single statewide rate in the country and one of only a small number
of states (along with IN, RI, TN, NJ, and CA's pre-district figure)
that sits at or above 7% statewide.

Local-jurisdiction model:

- Mississippi has very few local sales taxes. The state-imposed 7%
  rate is the bulk of what is collected statewide.
- A small handful of municipalities have local "infrastructure"
  taxes on **general retail** (Jackson 1% Special Sales Tax,
  Tupelo 0.25% Water Procurement Facility Tax). These are seeded
  via :mod:`opensalestax.states.ms_data` -- see that module for
  citations and ZIP coverage.
- A larger group of municipalities have **tourism** taxes that
  apply only to hotels, restaurants, and rentals -- NOT general
  retail (Hattiesburg, Gulfport, Biloxi, Tunica County). These
  are NOT modeled because the engine does not yet support
  per-category local taxability overrides; their general-retail
  rate is correctly 7% via the Census ZCTA state-only fallback.
- ZIPs not in a covered city's tuple receive the 7% statewide
  rate, which is the correct answer everywhere outside Jackson
  and Tupelo.

Taxability matrix (per Miss. Code Ann. Title 27, Chapter 65):

- **General tangible personal property** -- TAXABLE at 7% per
  section 27-65-17. The MS rate is high relative to peer states.
- **Clothing** -- TAXABLE year-round (no general clothing
  exemption). The annual back-to-school sales tax holiday (section
  27-65-111(bb)) provides a 3-day window for items < $100.
- **Groceries (SNAP-eligible food)** -- TAXABLE at the **REDUCED
  5% rate** effective July 1, 2025 per H.B. 1, Laws 2025 (which
  amended the rate-imposition provisions). Prior to July 1, 2025
  groceries were taxed at the full 7% statewide rate -- one of
  only a small number of states that historically taxed groceries
  at the full rate. Items NOT eligible for SNAP (candy, soft
  drinks, prepared foods) remain at 7%. The current OpenSalesTax
  engine resolves a single combined rate per authority+category;
  we encode groceries as ``is_taxable=True`` with
  ``rate_modifier=Decimal("5.000")`` to mark the special rate.
  Until the v0.6+ ``rate_modifier`` engine work lands the engine
  will apply the general 7% rate to grocery line items -- this
  over-collects by 2 percentage points for SNAP-eligible food and
  is documented in the API disclaimer. Note: the handful of MS
  cities with tourism or infrastructure taxes may apply those
  separately to groceries; v0.7 does not model per-jurisdiction
  taxability overrides.
- **Prescription drugs** -- exempt per section 27-65-111(h)
  (drugs and medicines prescribed for human treatment by an
  authorized prescriber and dispensed by a pharmacist, OR
  furnished by a licensed physician/surgeon/dentist/podiatrist
  to a patient). The exemption excludes prosthetics, ophthalmic
  devices, dentures, artificial limbs, splints, bandages, and
  the like; those remain taxable as general tangible personal
  property.
- **Prepared food** -- TAXABLE at 7%. The reduced 5% grocery
  rate is for SNAP-eligible food only; restaurant meals,
  hot prepared foods, and ready-to-eat items at delis remain at
  the general 7% rate.
- **Digital goods (specified digital products)** -- TAXABLE at 7%
  per Miss. Code Ann. section 27-65-26 (added by S.B. 2449,
  Laws 2023, effective July 1, 2023). The statute taxes computer
  software, computer software services, specified digital
  products, and other products delivered electronically (music
  downloads, e-books, ringtones, streamed media, etc.) at the
  same rate as tangible personal property.

Sales tax holidays -- MS has TWO annual holidays:

1. **Back-to-School Sales Tax Holiday** (Miss. Code section
   27-65-111(bb))
   - Recurring date: **second Friday in July through following
     Sunday** (3-day window). The pre-2024 statute was "last
     Friday and Saturday in July" (2 days); S.B. 2470, Laws 2024
     (signed April 22, 2024) moved the holiday to the second
     weekend and added Sunday so families could shop before the
     school year starts.
   - Eligible items: clothing, footwear, **and school supplies**;
     each item must be priced **less than $100**.
   - 2026 dates: **July 10 (Friday) - July 12 (Sunday), 2026**
     (second Friday in July 2026 is July 10).

2. **Mississippi Second Amendment Sales Tax Holiday (MSAW)**
   (Miss. Code section 27-65-111(af))
   - Recurring date: **last Friday in August through following
     Sunday** (3-day window).
   - Eligible items: firearms, ammunition, and "hunting supplies"
     -- statutorily defined as "tangible personal property used
     for hunting, including, and limited to, archery equipment,
     firearm and archery cases, firearm and archery accessories,
     hearing protection, holsters, belts and slings."
   - **No per-item dollar cap.**
   - Mail-order, telephone, and internet sales qualify if ordered
     and paid for during the holiday with immediate shipment
     scheduled; layaway sales do not qualify.
   - 2026 dates: **August 28 (Friday) - August 30 (Sunday), 2026**
     (last Friday in August 2026 is August 28).

Loading: the v0.2 loader treats ``Mississippi.parse_rates`` as
"self-seeded" -- it returns the single statewide row and ignores
the source-file argument. Use ``opensalestax data load --state MS
--version v0.7-statewide`` to insert it.

State maintainer: vacant -- see MAINTAINERS.md. MS's per-municipality
local-tax rollup is the natural next contribution; tracking the
biennial legislative session for any rate or holiday changes is a
maintainer responsibility. Notable open question: whether 2026 or
2027 sessions extend the back-to-school list to include computers
or expand the $100 cap (HB 281 / HB 437 in the 2026 session
proposed expansions; status to verify).

DISCLAIMER: This is calculation logic, not tax advice. Maintainers
and users are responsible for verifying current MS DOR guidance
before relying on these rules in production.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.states.ms_data import (
    MS_CITIES,
    MS_COUNTY_RATE_PCT,
    MS_STATE_EFFECTIVE_FROM,
    MS_STATE_RATE_PCT,
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
            "Clothing IS taxable in Mississippi year-round at the general "
            "7% rate (Miss. Code Ann. section 27-65-17). The annual "
            "back-to-school Sales Tax Holiday (section 27-65-111(bb)) "
            "provides a 3-day exemption for items priced less than $100. "
            "Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("5.000"),
        notes=(
            "Groceries (SNAP-eligible food and drink for human "
            "consumption) are taxed at a REDUCED 5% rate effective "
            "July 1, 2025 per H.B. 1, Laws 2025 (Miss. Code Ann. "
            "section 27-65-17). Prior to that date Mississippi taxed "
            "groceries at the full 7% statewide rate -- one of only a "
            "few states that historically did so. Items NOT eligible "
            "for SNAP (candy, soft drinks, prepared foods) remain at "
            "the general 7% rate. The rate_modifier is stored but the "
            "engine applies (as of v0.11.1) it (shipped in v0.11.1); until "
            "then the engine over-collects by 2 percentage points on "
            "SNAP-eligible food. Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs and medicines are exempt per Miss. Code "
            "Ann. section 27-65-111(h) when (i) prescribed for human "
            "treatment by an authorized prescriber and dispensed by a "
            "registered pharmacist, OR (ii) furnished by a licensed "
            "physician, surgeon, dentist or podiatrist to a patient. "
            "The exemption excludes prosthetics, ophthalmic devices, "
            "dentures, artificial limbs, splints, bandages, and similar "
            "non-prescription medical articles -- those remain taxable. "
            "Calculation only -- not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods, ready-to-eat "
            "deli items) is taxable at the general 7% rate per Miss. "
            "Code Ann. section 27-65-17. The reduced 5% grocery rate "
            "(section 27-65-17 as amended by H.B. 1, Laws 2025) applies "
            "only to SNAP-eligible food, which excludes prepared food. "
            "Calculation only -- not tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products and electronically-delivered "
            "computer software are taxable at the general 7% rate per "
            "Miss. Code Ann. section 27-65-26 (added by S.B. 2449, Laws "
            "2023, effective July 1, 2023). Covers downloaded software, "
            "music, e-books, ringtones, streamed media, and similar "
            "electronically-delivered products. Calculation only -- not "
            "tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at the 7% "
            "statewide rate per Miss. Code Ann. section 27-65-17. "
            "Calculation only -- not tax advice."
        ),
    ),
}

# Mississippi's general 7% rate has been in place since the
# 1992 increase from 6% (effective 1992-07-01 per Laws 1992, ch. 484).
# The rate has been stable at 7% since.
_RATE_EFFECTIVE_FROM = dt.date(1992, 7, 1)


class Mississippi:
    """Mississippi state module (tier 1; statewide rate only in v0.7)."""

    state_abbrev: str = "MS"
    state_name: str = "Mississippi"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require a
    # cached upstream file. MS's parse_rates returns the same statewide
    # row regardless of source_file (no SST file exists for MS).
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield MS's state + per-county + per-city general-retail rates.

        Counties yielded: only those touched by an MS_CITIES entry.
        Cities yielded: every MS_CITIES entry. ``source_file`` is
        intentionally ignored -- MS has no SST upstream file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Mississippi",
            authority_type="state",
            rate_pct=MS_STATE_RATE_PCT,
            effective_from=MS_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        used_counties = {county for county, _, _ in MS_CITIES.values()}
        for county_name in sorted(used_counties):
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=MS_COUNTY_RATE_PCT[county_name],
                effective_from=MS_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Mississippi",
            )
        for city_name, (county_name, city_rate, _zips) in sorted(MS_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=MS_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=county_name,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every MS ZIP; this method ADDS county + city bindings for
        Jackson and Tupelo (the only MS cities with general-retail
        local rates). ZIPs outside the covered cities keep the
        Census state-only binding (correct: flat 7%).
        """
        del source_file, version_label
        for city_name, (county_name, _city_rate, zips) in MS_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="Mississippi",
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
        """Return MS's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for MS in v0.7."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Mississippi's two annual sales tax holidays.

        1. Back-to-School (section 27-65-111(bb)) -- second Friday in
           July through Sunday; clothing/footwear/school supplies
           under $100/item.
        2. Second Amendment Weekend (section 27-65-111(af)) -- last
           Friday in August through Sunday; firearms, ammunition,
           and statutorily-defined hunting supplies; no per-item cap.

        2026 dates encoded explicitly per the recurring statutory
        rule. Subsequent years require an explicit data update (do
        NOT extrapolate -- the legislature occasionally adjusts
        dates and category lists, as S.B. 2470 (2024) did).
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Back-to-School Sales Tax Holiday (2026)",
                    starts_on=dt.date(2026, 7, 10),
                    ends_on=dt.date(2026, 7, 12),
                    applicable_categories=("clothing", "school_supplies"),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Miss. Code Ann. section 27-65-111(bb), as "
                        "amended by S.B. 2470, Laws 2024. Three-day "
                        "exemption from the 7% state sales tax for "
                        "clothing, footwear, and school supplies "
                        "priced less than $100 per item. Pre-2024 "
                        "the holiday was 2 days (Friday-Saturday) on "
                        "the LAST weekend in July; the 2024 amendment "
                        "moved it to the SECOND weekend and added "
                        "Sunday. 2026 second Friday in July is July "
                        "10; holiday runs through Sunday July 12. "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Second Amendment Sales Tax Holiday (2026)",
                    starts_on=dt.date(2026, 8, 28),
                    ends_on=dt.date(2026, 8, 30),
                    applicable_categories=(
                        "firearms",
                        "ammunition",
                        "hunting_supplies",
                    ),
                    max_amount_per_item=None,
                    notes=(
                        "Miss. Code Ann. section 27-65-111(af). "
                        "Three-day exemption from the 7% state sales "
                        "tax for firearms, ammunition, and 'hunting "
                        "supplies' (statutorily defined and limited "
                        "to: archery equipment, firearm and archery "
                        "cases, firearm and archery accessories, "
                        "hearing protection, holsters, belts and "
                        "slings). NO per-item dollar cap. Mail-order "
                        "/ telephone / internet sales qualify if "
                        "ordered and paid during the holiday with "
                        "immediate shipment scheduled; layaway does "
                        "not qualify. 2026 last Friday in August is "
                        "August 28; holiday runs through Sunday "
                        "August 30. Calculation only -- not tax "
                        "advice."
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Mississippi()
del _PROTOCOL_CHECK

MISSISSIPPI = register(Mississippi())
