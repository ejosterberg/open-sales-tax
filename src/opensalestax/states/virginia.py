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
  :mod:`opensalestax.states.va_data`. Per-jurisdiction coverage
  via :data:`opensalestax.states.va_data.VA_COUNTY_DISTRICT` (v0.31
  ratchet) covers all 133 VA jurisdictions; the v0.25 top-12 city
  seed is preserved as a friendly-anchor layer.
- **Historic Triangle (Williamsburg city, James City County, York
  County): +1.0%** -- now seeded in v0.31 via
  :data:`VA_HISTORIC_TRIANGLE` as a SECOND district layer that
  stacks ON TOP of Hampton Roads for the three overlapping
  jurisdictions, yielding state 5.3% + HR 0.7% + Triangle 1.0% =
  **7.0%** combined.
- **Selected Southside localities (Charlotte, Danville, Gloucester,
  Halifax, Henry, Northampton, Patrick, Pittsylvania): +1.0%**
  additional local -> combined 6.3%. NOT modeled in v0.31; these
  locality-specific +1.0% surcharges are filed under Va. Code
  section 58.1-602 as "additional local" rather than a regional
  district. A future ratchet should add them as per-county
  ``district`` authorities (parallels the Historic Triangle
  pattern).
- Roanoke and Lynchburg are top-12 cities seeded with NO regional
  add-on; they correctly land at 5.3% via the state authority.

**Statewide ZIP coverage via Census ZCTA**
(v0.31 ratchet, parallels FL/AZ/CA in v0.28 and TX/NY/MO/IL/PA
in v0.29). :meth:`Virginia.parse_boundaries` iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` and emits state +
county + (district if mapped) bindings for every VA ZIP -- not
just the ZIPs in the top-12 city seed. Effect: every Hampton Roads
suburb in Isle of Wight County (e.g., Smithfield 23430) now picks
up the +0.7% Hampton Roads district, and every Loudoun / Prince
William / Fairfax County ZIP in Northern Virginia picks up the
+0.7% NoVA district -- instead of falling back to state-only.

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

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
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
    VA_COUNTY_DISTRICT,
    VA_COUNTY_RATE_PCT,
    VA_DISTRICT_RATE_PCT,
    VA_HISTORIC_TRIANGLE,
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
        """Yield VA's state + per-district + per-county + per-city rates.

        Districts yielded: ALL four regional districts (Hampton Roads,
        Northern Virginia, Central Virginia at 0.7%; Historic Triangle
        at 1.0%). Counties yielded: ALL 133 VA jurisdictions (95
        counties + 38 independent cities) at 0% -- the mandatory 1%
        local is folded into the 5.3% state rate, so the county layer
        exists ONLY to give every VA ZIP a county-level authority for
        binding. Cities yielded: every :data:`VA_CITIES` entry; the
        city rate is 0% in all cases (the engine treats the city
        authority as a friendly anchor for per-ZIP boundaries).

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
        # Emit ALL four regional districts (the v0.25 set was the
        # three +0.7% regions; v0.31 adds Historic Triangle at +1.0%
        # for James City / York / Williamsburg).
        for district_name in sorted(VA_DISTRICT_RATE_PCT):
            yield RateRow(
                authority_name=district_name,
                authority_type="district",
                rate_pct=VA_DISTRICT_RATE_PCT[district_name],
                effective_from=VA_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Virginia",
            )
        # Emit a RateRow for every VA jurisdiction (county or
        # independent city). The ZIP_COUNTY-driven boundary loader
        # binds every VA ZIP to its jurisdiction, so every one must
        # have a queryable rate (uniformly 0% per the local-1%-in-
        # state-rate fold).
        for va_county_name in sorted(VA_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=va_county_name,
                authority_type="county",
                rate_pct=VA_COUNTY_RATE_PCT[va_county_name],
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
        """Yield (state, county[, district[, district2]][, city]) rows for every VA ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county + (district if mapped) + (Historic
           Triangle district if applicable) bindings for every ZIP
           intersecting a VA jurisdiction. This covers the entire
           state -- not just the ZIPs in the top-12 city seed -- so
           every Loudoun / Prince William / Fairfax / Isle of Wight
           ZIP picks up the appropriate +0.7% regional district
           binding instead of falling back to state-only at 5.3%.

        2. Fall back to :data:`VA_CITIES` for any city ZIP missed by
           the Census ZCTA pass and emit the friendly-anchor city
           BoundaryRow on top of the state + county + district stack.

        Per the FL/AZ/CA pattern, emit at most ONE county per ZIP per
        Census ZCTA, preferring the city-anchor jurisdiction if the
        ZIP is in :data:`VA_CITIES` (mapped via the city's declared
        district -> jurisdictions). Without this, ZIPs that physically
        span jurisdiction lines would get bound to BOTH and could
        double-count any regional district add-on.
        """
        del source_file, version_label

        # Build city-anchor jurisdiction map for ZIPs that span lines.
        # When a ZIP is in VA_CITIES, prefer the city's home jurisdiction
        # (the FIPS county-equivalent name in VA_COUNTY_RATE_PCT).
        # The mapping uses the friendly city name -> "<Name> city"
        # canonical FIPS suffix that matches county_names.
        city_to_jurisdiction: dict[str, str] = {
            "Virginia Beach": "Virginia Beach city",
            "Norfolk": "Norfolk city",
            "Chesapeake": "Chesapeake city",
            "Newport News": "Newport News city",
            "Hampton": "Hampton city",
            "Portsmouth": "Portsmouth city",
            "Suffolk": "Suffolk city",
            "Arlington": "Arlington County",
            "Alexandria": "Alexandria city",
            "Richmond": "Richmond city",
            "Roanoke": "Roanoke city",
            "Lynchburg": "Lynchburg city",
        }
        city_county_for_zip: dict[str, str] = {}
        for cn, (_district, czs) in VA_CITIES.items():
            jurisdiction = city_to_jurisdiction.get(cn)
            if jurisdiction is None:
                continue
            for cz in czs:
                city_county_for_zip[cz] = jurisdiction

        # Pass 1: state + county + district for every VA ZIP per
        # Census ZCTA. Emit at most one county per ZIP: prefer the
        # city-anchor jurisdiction if known, else the first
        # Census-listed VA jurisdiction.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            chosen_county: str | None = None
            for state_abbrev, county_fips in pairs:
                if state_abbrev != "VA":
                    continue
                va_county_name = county_name("VA", county_fips)
                if va_county_name is None or va_county_name not in VA_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if va_county_name == preferred_county:
                        chosen_county = va_county_name
                        break
                    continue
                chosen_county = va_county_name
                break
            if chosen_county is None and preferred_county is not None:
                chosen_county = preferred_county
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Virginia",
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
            district = VA_COUNTY_DISTRICT.get(chosen_county)
            if district is not None:
                yield BoundaryRow(
                    authority_name=district,
                    authority_type="district",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
            # Historic Triangle stacks on TOP of Hampton Roads for the
            # three overlap jurisdictions (James City / York / Williamsburg).
            if chosen_county in VA_HISTORIC_TRIANGLE:
                yield BoundaryRow(
                    authority_name="Historic Triangle Region",
                    authority_type="district",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
            emitted_zips.add(zip5)

        # Pass 2: city BoundaryRows for VA_CITIES. Also emit state +
        # county + district for any city ZIP missed by the Census
        # pass (USPS-only / PO-box-only ZIPs not in ZCTA).
        for city_name, (district_name, zips) in VA_CITIES.items():
            jurisdiction = city_to_jurisdiction.get(city_name)
            for zip5 in zips:
                if zip5 not in emitted_zips and jurisdiction is not None:
                    yield BoundaryRow(
                        authority_name="Virginia",
                        authority_type="state",
                        zip5=zip5,
                        zip4_low=None,
                        zip4_high=None,
                    )
                    yield BoundaryRow(
                        authority_name=jurisdiction,
                        authority_type="county",
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
                    if jurisdiction in VA_HISTORIC_TRIANGLE:
                        yield BoundaryRow(
                            authority_name="Historic Triangle Region",
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
