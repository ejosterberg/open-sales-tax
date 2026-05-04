# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Virginia state module (tier 1, non-SST).

VA is **not** a Streamlined Sales Tax member. The Virginia Retail
Sales and Use Tax has a layered structure (Va. Code Title 58.1,
Chapter 6):

- **State portion: 4.3%** (Va. Code section 58.1-603) -- the
  "license or privilege tax" imposed on every retail sale.
- **Mandatory local 1%** (Va. Code sections 58.1-605, 58.1-606)
  -- every Virginia locality imposes the 1% local option, so it
  functions as a statewide floor.
- **Combined statewide minimum: 5.3%** -- the headline rate
  consumers see in localities without a regional add-on.

Regional add-ons:

- **Central Virginia, Hampton Roads, Northern Virginia: +0.7%**
  regional transportation tax -> combined 6.0%. Modeled as
  ``district`` authorities seeded from
  :mod:`opensalestax.states.va_data`. Top-12-city coverage in v0.25:
  Virginia Beach / Norfolk / Chesapeake / Newport News / Hampton /
  Portsmouth / Suffolk (Hampton Roads); Arlington / Alexandria
  (Northern Virginia); Richmond (Central Virginia).
- **Historic Triangle (Williamsburg, James City County, York
  County): +1.0%** -- documented in :mod:`va_data` but NOT seeded
  in v0.25 (none of the top-12 cities are in the Triangle).
- **Selected Southside localities (Charlotte, Danville, Gloucester,
  Halifax, Henry, Northampton, Patrick, Pittsylvania): +1.0%**
  additional local -> combined 6.3%. Not seeded in v0.25.
- Roanoke and Lynchburg are top-12 cities seeded with NO regional
  add-on; they correctly land at 5.3% via the state authority.

ZIPs not in any covered city's tuple fall back to state-only at
5.3% via the Census ZCTA load.

Taxability matrix (per Va. Code Chapter 6):

- **Clothing** -- TAXABLE year-round (no general clothing
  exemption). The annual August Sales Tax Holiday (Va. Code
  section 58.1-639.1) temporarily exempts qualifying clothing
  and footwear at $100 or less per item.
- **Groceries (food for human consumption) and essential
  personal hygiene products** -- the **state 4.3% portion was
  eliminated effective January 1, 2023** (Va. Code section
  58.1-611.1). The mandatory **local 1% still applies**, so
  the effective rate is **1%** statewide. Encoded with
  ``rate_modifier=Decimal("1.000")`` mirroring the IL grocery
  pattern; the engine will apply the modifier in v0.6+.
- **Prescription drugs** -- NON-taxable (Va. Code section
  58.1-609.10, subdivisions 9 and 22).
- **Nonprescription drugs and proprietary medicines** --
  NON-taxable (Va. Code section 58.1-609.10, subdivision 14).
  Mapped under prescription_drugs since the engine doesn't
  yet have a separate OTC category.
- **Prepared food** -- TAXABLE at the standard combined rate
  (and most localities also impose a separate meals tax that
  is administered locally and not modeled here).
- **Digital goods** -- **Generally NON-taxable** when delivered
  electronically with no tangible medium. Long-standing Virginia
  Tax Commissioner policy (rulings 05-44, 14-178, 16-135) treats
  electronically-delivered prewritten software and digital
  downloads as not constituting tangible personal property under
  Va. Code section 58.1-602. Tangible-media sales remain taxable.

Sales-tax holiday:

VA has a single combined 3-day August Sales Tax Holiday per Va.
Code section 58.1-639.1 (effective until July 1, 2030). It begins
the first Friday in August at 12:01 a.m. and ends the following
Sunday at 11:59 p.m. The holiday covers four scopes with distinct
per-item caps:

- **School supplies** -- $20 or less per item
- **Clothing and footwear** -- $100 or less per item
- **Energy Star / WaterSense products** for noncommercial home or
  personal use -- $2,500 or less per item
- **Hurricane / emergency preparedness items** -- portable
  generators $1,000 or less; gas-powered chainsaws $350 or less;
  chainsaw accessories and other qualifying preparedness items
  $60 or less

Per-item caps are encoded in ``HolidayWindow.max_amount_per_item``
where one cap covers the scope; multi-tiered caps within a single
scope (e.g., the hurricane scope's three different caps) are
documented in the ``notes`` field and will be enforced when the
threshold-rule engine work lands in v0.6+.

State maintainer: vacant -- see MAINTAINERS.md.

Disclaimer: this module is calculation infrastructure, not tax
advice. Verify every rule against the Virginia Department of
Taxation (https://www.tax.virginia.gov) before relying on it for
compliance.
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
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register
from opensalestax.states.va_data import (
    VA_CITIES,
    VA_DISTRICT_RATE_PCT,
    VA_STATE_EFFECTIVE_FROM,
    VA_STATE_RATE_PCT,
)

# Virginia taxability matrix per Va. Code Title 58.1, Chapter 6.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Virginia year-round (no general "
            "clothing exemption). The annual August Sales Tax Holiday "
            "(Va. Code section 58.1-639.1) temporarily exempts "
            "qualifying clothing and footwear $100 or less per item; "
            "the per-item cap will be enforced when the threshold-rule "
            "engine work lands in v0.6+. Calculation only -- not tax "
            "advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        rate_modifier=Decimal("1.000"),
        notes=(
            "Food purchased for human consumption and essential personal "
            "hygiene products are taxed at a REDUCED 1% rate in Virginia "
            "(Va. Code section 58.1-611.1). The state 4.3% portion was "
            "eliminated effective January 1, 2023; only the mandatory "
            "1% local option still applies. v0.6 reports this as taxable "
            "with rate_modifier=1.000; the engine applies (as of v0.11.1) "
            "rate_modifier. Retailers selling groceries in VA should "
            "verify with the Virginia Department of Taxation until v0.6+ "
            "wires the modifier through. Calculation only -- not tax "
            "advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are non-taxable in Virginia (Va. Code "
            "section 58.1-609.10, subdivisions 9 and 22). Nonprescription "
            "drugs and proprietary medicines are also non-taxable per "
            "subdivision 14 of the same section. Calculation only -- "
            "not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food is taxable at the standard combined Virginia "
            "rate. Most Virginia localities also impose a separate meals "
            "tax that is administered locally and not modeled in this "
            "module. Calculation only -- not tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=False,
        notes=(
            "Digital goods (electronically-delivered prewritten software, "
            "downloads) are generally NON-taxable in Virginia per "
            "long-standing Virginia Tax Commissioner policy (rulings "
            "05-44, 14-178, 16-135) interpreting Va. Code section "
            "58.1-602 -- electronic delivery without any tangible medium "
            "does not constitute a sale of tangible personal property. "
            "Sales delivered on physical media remain taxable. "
            "Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at the "
            "Virginia combined rate (Va. Code section 58.1-603). The "
            "v0.6 module ships the 5.3% statewide minimum (4.3% state + "
            "1% mandatory local); regional add-ons (Central VA, Hampton "
            "Roads, Northern VA, Historic Triangle, Southside) are "
            "deferred to per-locality boundary loading."
        ),
    ),
}

# Virginia's current 4.3% state portion took effect 2013-07-01 when
# the General Assembly (HB 2313) raised the state portion from 4.0%
# to 4.3% and added the regional transportation taxes for Northern
# Virginia and Hampton Roads.
_RATE_EFFECTIVE_FROM = dt.date(2013, 7, 1)

# Statewide minimum combined rate: 4.3% state + 1% mandatory local = 5.3%.
# This is the headline rate consumers see in any Virginia locality
# that is NOT in a regional-add-on area.
_STATEWIDE_MINIMUM_RATE_PCT = Decimal("5.300")


class Virginia:
    """Virginia state module (tier 1; statewide minimum rate only in v0.6)."""

    state_abbrev: str = "VA"
    state_name: str = "Virginia"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require
    # a cached upstream file. VA is not an SST member and has no
    # quarterly upstream file; parse_rates returns the statewide
    # minimum row regardless of source_file.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield VA's state + per-district + per-city rates.

        Districts yielded: only those touched by a covered city
        (Hampton Roads, Northern Virginia, Central Virginia).
        Cities yielded: every VA_CITIES entry. The city rate is 0%
        in all cases -- the city authority is purely a friendly
        anchor for per-ZIP boundaries; the math comes from
        state 5.3% + district 0.7% (where applicable).

        ``source_file`` is intentionally ignored -- VA has no SST
        upstream file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Virginia",
            authority_type="state",
            rate_pct=VA_STATE_RATE_PCT,
            effective_from=VA_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        used_districts = {
            district for district, _ in VA_CITIES.values() if district is not None
        }
        for district_name in sorted(used_districts):
            yield RateRow(
                authority_name=district_name,
                authority_type="district",
                rate_pct=VA_DISTRICT_RATE_PCT[district_name],
                effective_from=VA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Virginia",
            )
        for city_name, (city_district, _zips) in sorted(VA_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=Decimal("0.000"),
                effective_from=VA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                # Cities sit under their district when one applies, else
                # under the state. The engine's authority-stacking layer
                # uses parent_authority_name only as a label; rate math
                # comes from authority lookups via boundary bindings.
                parent_authority_name=city_district or "Virginia",
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, district?, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every VA ZIP; this method ADDS district + city bindings for the
        12 covered cities. Cities outside a regional-add-on region
        (Roanoke, Lynchburg) get state + city bindings only -- no
        district -- so their combined rate is 5.3% (state) + 0% (city).
        """
        del source_file, version_label
        for city_name, (district_name, zips) in VA_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="Virginia",
                    authority_type="state",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
                if district_name is not None:
                    yield BoundaryRow(
                        authority_name=district_name,
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
        """Return VA's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for VA in v0.6."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Virginia's combined 3-day August Sales Tax Holiday.

        Per Va. Code section 58.1-639.1 (effective until July 1,
        2030), the holiday begins the first Friday in August at
        12:01 a.m. and ends the following Sunday at 11:59 p.m.

        For 2026 the first Friday of August is August 7, so the
        holiday runs August 7-9, 2026.

        The single statutory holiday covers four scopes; each is
        encoded as a separate :class:`HolidayWindow` so the engine
        can match per-category. Per-item caps are encoded in
        ``max_amount_per_item`` where one cap covers the whole
        scope; the hurricane scope has three tiered caps that are
        documented in ``notes`` and will be enforced once the
        threshold-rule engine work lands in v0.6+.
        """
        if year != 2026:
            return iter(())
        # 2026 dates: first Friday of August is August 7;
        # holiday ends the following Sunday, August 9.
        starts_on = dt.date(2026, 8, 7)
        ends_on = dt.date(2026, 8, 9)
        return iter(
            [
                HolidayWindow(
                    name="Virginia Sales Tax Holiday -- School Supplies (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("school_supplies",),
                    max_amount_per_item=Decimal("20.00"),
                    notes=(
                        "Va. Code section 58.1-639.1: qualifying school "
                        "supplies (dictionaries, notebooks, pens, pencils, "
                        "paper, calculators, etc.) $20 or less per item. "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Virginia Sales Tax Holiday -- Clothing & Footwear (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Va. Code section 58.1-639.1: qualifying clothing "
                        "and footwear designed for human wear $100 or less "
                        "per item. Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Virginia Sales Tax Holiday -- Energy Star & WaterSense (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("energy_star", "water_efficient"),
                    max_amount_per_item=Decimal("2500.00"),
                    notes=(
                        "Va. Code section 58.1-639.1: qualifying Energy "
                        "Star or WaterSense products purchased for "
                        "noncommercial home or personal use $2,500 or "
                        "less per item. Calculation only -- not tax "
                        "advice."
                    ),
                ),
                HolidayWindow(
                    name="Virginia Sales Tax Holiday -- Hurricane Preparedness (2026)",
                    starts_on=starts_on,
                    ends_on=ends_on,
                    applicable_categories=("emergency_supplies",),
                    # Use the lowest tier ($60) as the engine-level cap
                    # so a naive engine doesn't over-exempt; the higher
                    # generator/chainsaw tiers are documented in notes
                    # for the v0.6+ threshold-rule work.
                    max_amount_per_item=Decimal("60.00"),
                    notes=(
                        "Va. Code section 58.1-639.1: hurricane and "
                        "emergency preparedness items with TIERED caps -- "
                        "portable generators $1,000 or less; gas-powered "
                        "chainsaws $350 or less; chainsaw accessories and "
                        "other qualifying preparedness items (batteries, "
                        "ice, CO detectors, fuel tanks, coolers, radios, "
                        "tarps, tie-downs) $60 or less per item. The "
                        "$60 cap is used as the conservative engine-level "
                        "default; the $350 and $1,000 tiers will be "
                        "enforced when the threshold-rule engine work "
                        "lands in v0.6+. Calculation only -- not tax "
                        "advice."
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Virginia()
del _PROTOCOL_CHECK

VIRGINIA = register(Virginia())
