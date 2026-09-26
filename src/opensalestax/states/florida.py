# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Florida state module (tier 1, non-SST).

FL is **not** an SST member. Statewide rate is **6%** per the
Florida Department of Revenue (floridarevenue.com). Counties may
add a discretionary sales surtax (Form DR-15DSS) of 0% to 1.5%;
combined statewide-plus-county rates therefore range **6.0%-7.5%**.

Florida has **NO city-level general sales tax** anywhere in the
state. The only modeled layers are state + county; cities are used
purely as ZIP-binding anchors to produce friendly receipt
descriptions. See :mod:`opensalestax.states.fl_data` for the per-
county surtax table (all 67 counties) and the 30 covered cities.

Taxability matrix (per Fla. Stat. Chapter 212):

- **Clothing** -- TAXABLE (no general exemption). The annual
  back-to-school holiday (Fla. Stat. 212.08(20)) temporarily
  exempts qualifying items; see :meth:`Florida.holidays_for`.
- **Groceries** -- NON-taxable for "groceries" (Fla. Stat.
  212.08(1)). Prepared food, candy, soda: taxable.
- **Prescription drugs** -- NON-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE for downloaded software and
  digital content.

NOT modeled in this loader:

- The **$5,000 single-item discretionary-surtax cap** (Fla. Stat.
  212.054(2)(b)) -- the county surtax applies only to the first
  $5,000 of any single item; the state 6% applies to the full
  amount. Future enhancement once the engine supports per-
  jurisdiction caps.
- **Tourist Development Tax (TDT)** -- transient-rental tax,
  separate from general sales tax.

State maintainer: vacant -- see MAINTAINERS.md. FL's annual
back-to-school holiday is permanent in statute, but other
holidays come and go with each year's tax package; a maintainer
who tracks legislative sessions is ideal.

DISCLAIMER: This is calculation infrastructure, not tax advice.
Verify every rule against the current FL DOR DR-15DSS publication
and Form DR-15 schedule before relying on it for compliance.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.data.county_choice import choose_county_name
from opensalestax.data.zip_county import ZIP_COUNTY
from opensalestax.states.fl_data import (
    FL_CITIES,
    FL_COUNTY_SURTAX_PCT,
    FL_STATE_EFFECTIVE_FROM,
    FL_STATE_RATE_PCT,
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
        notes=(
            "Clothing IS taxable in Florida year-round. The annual "
            "back-to-school sales-tax holiday (Fla. Stat. 212.08(20)) "
            "temporarily exempts qualifying items."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Groceries are non-taxable in Florida (Fla. Stat. 212.08(1)). "
            "Prepared food, candy, and soda are taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable in Florida.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in Florida.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Florida.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Florida:
    """Florida state module (tier 1; state 6% + per-county discretionary surtax)."""

    state_abbrev: str = "FL"
    state_name: str = "Florida"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield FL's state + per-county discretionary-surtax rates.

        All 67 FL counties from :data:`FL_COUNTY_SURTAX_PCT` are
        emitted -- including the zero-surtax counties (e.g. Citrus) --
        so that any FL ZIP bound to a county via the Census ZCTA->county
        relationship can resolve cleanly. Zero-rate authorities sum to
        no effect but preserve the rate-stack audit trail. Florida has
        no city-level sales tax, so no city ``RateRow`` rows are
        emitted.

        ``source_file`` is intentionally ignored -- FL is non-SST and
        has no upstream rate file consumed by this module.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Florida",
            authority_type="state",
            rate_pct=FL_STATE_RATE_PCT,
            effective_from=FL_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a RateRow for every FL county. The ZIP_COUNTY-driven
        # boundary loader binds every FL ZIP to its county/counties, so
        # every county must have a queryable rate (even the 0% ones).
        for fl_county_name in sorted(FL_COUNTY_SURTAX_PCT):
            yield RateRow(
                authority_name=fl_county_name,
                authority_type="county",
                rate_pct=FL_COUNTY_SURTAX_PCT[fl_county_name],
                effective_from=FL_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Florida",
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county) boundary rows for every FL ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county bindings for every ZIP intersecting an
           FL county. This covers the entire state, not just the ZIPs
           in the :data:`FL_CITIES` top-30 seed list -- so Miami Beach
           (33139), Key West (33040), Naples (34102), and every other
           FL ZIP resolves to its county's discretionary surtax
           instead of falling back to state-only.

        2. Fall back to :data:`FL_CITIES` for any city ZIP missed by
           the Census ZCTA pass (USPS-only / PO-box-only ZIPs that
           aren't published as Census ZCTAs, e.g. Jacksonville's
           32099). This guards against city-coverage regressions.

        A ZIP that crosses county lines yields one county BoundaryRow
        per intersecting county; the engine picks the highest-precision
        match at lookup time.

        Florida has no city-level sales tax, so NO city
        ``BoundaryRow`` rows are emitted -- :data:`FL_CITIES` is used
        only as a regression-guard fallback and does not become a
        city authority.
        """
        del source_file, version_label
        # Build city-anchor county map for cross-county-line ZIPs.
        # When a ZIP is in FL_CITIES, the city's declared county wins.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, czs) in FL_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Emit at most one county per ZIP per Census ZCTA: prefer the
        # city-anchor county if known, else the Census land-area-majority
        # county. See choose_county_name().
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            chosen_county = choose_county_name(
                "FL",
                zip5,
                pairs,
                FL_COUNTY_SURTAX_PCT,
                preferred=city_county_for_zip.get(zip5),
            )
            if chosen_county is None:
                continue
            yield BoundaryRow(
                authority_name="Florida",
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
            emitted_zips.add(zip5)
        # Fallback pass: city ZIPs that aren't in Census ZCTA (USPS-only
        # codes like Jacksonville's 32099). Use FL_CITIES' county
        # binding so the city's ZIPs always resolve to a county.
        for _city_name, (fl_city_county, zips) in FL_CITIES.items():
            for zip5 in zips:
                if zip5 in emitted_zips:
                    continue
                yield BoundaryRow(
                    authority_name="Florida",
                    authority_type="state",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
                yield BoundaryRow(
                    authority_name=fl_city_county,
                    authority_type="county",
                    zip5=zip5,
                    zip4_low=None,
                    zip4_high=None,
                )
                emitted_zips.add(zip5)

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Florida's sales-tax holidays for the years encoded in this module.

        - Back-to-school (Fla. Stat. 212.08(20)): July 20 through
          August 20 each year. Permanent since ch. 2025-208; section
          27 of ch. 2026-239 set the current dates. One window per cap.
        - Hunting, fishing, and camping (section 43 of ch. 2026-239,
          uncodified): September 1 through December 31, 2026 only.

        Disaster-preparedness items have been exempt year-round since
        August 1, 2025 (ch. 2025-208), so they are no longer a holiday,
        and 2026 has no Freedom Month or Tool Time holiday. Other
        temporary holidays come from each year's tax package; add them
        as they are enacted.
        """
        if year not in (2026, 2027):
            return iter(())
        windows = _back_to_school(year)
        if year == 2026:
            windows.extend(_HUNTING_FISHING_CAMPING_2026)
        return iter(windows)

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return FL's shipping rule.

        Shipping is exempt when it is (a) separately stated and
        (b) the customer has the option to pick up the item. The
        e-commerce default ordinarily satisfies both conditions;
        the county discretionary surtax follows the same rule.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.EXEMPT_IF_SEPARATELY_STATED,
            citation="FL Rule 12A-1.045",
        )


def _back_to_school(year: int) -> list[HolidayWindow]:
    """Fla. Stat. 212.08(20)(a): one window per statutory price cap."""
    starts_on, ends_on = dt.date(year, 7, 20), dt.date(year, 8, 20)
    common = (
        "Fla. Stat. 212.08(20). Not available for rentals, repairs, or "
        "sales within a theme park or entertainment complex, public "
        "lodging establishment, or airport; dealers cannot opt out."
    )
    return [
        HolidayWindow(
            name=f"Back-to-School -- Clothing, Footwear, Wallets, and Bags ({year})",
            starts_on=starts_on,
            ends_on=ends_on,
            applicable_categories=("clothing", "backpacks", "handbags", "wallets"),
            max_amount_per_item=Decimal("100.00"),
            notes=(
                "Clothing, footwear, wallets, and bags (handbags, backpacks, "
                "fanny packs, diaper bags) priced $100 or less per item; "
                "briefcases, suitcases, garment bags, watches, jewelry, "
                "umbrellas, skis, swim fins, roller blades, and skates are "
                f"excluded. {common}"
            ),
        ),
        HolidayWindow(
            name=f"Back-to-School -- School Supplies ({year})",
            starts_on=starts_on,
            ends_on=ends_on,
            applicable_categories=("school_supplies",),
            max_amount_per_item=Decimal("50.00"),
            notes=f"School supplies priced $50 or less per item. {common}",
        ),
        HolidayWindow(
            name=f"Back-to-School -- Learning Aids and Jigsaw Puzzles ({year})",
            starts_on=starts_on,
            ends_on=ends_on,
            applicable_categories=("learning_aids", "jigsaw_puzzles"),
            max_amount_per_item=Decimal("30.00"),
            notes=f"Learning aids and jigsaw puzzles priced $30 or less. {common}",
        ),
        HolidayWindow(
            name=f"Back-to-School -- Personal Computers ({year})",
            starts_on=starts_on,
            ends_on=ends_on,
            applicable_categories=("computers",),
            max_amount_per_item=Decimal("1500.00"),
            notes=(
                "Personal computers and computer-related accessories priced "
                "$1,500 or less, for noncommercial home or personal use; "
                "cellular telephones, video game consoles, and digital media "
                f"receivers are excluded. {common}"
            ),
        ),
    ]


def _hunting_fishing_camping(
    label: str, categories: tuple[str, ...], cap: str | None, notes: str
) -> HolidayWindow:
    return HolidayWindow(
        name=f"Hunting, Fishing, and Camping -- {label} (2026)",
        starts_on=dt.date(2026, 9, 1),
        ends_on=dt.date(2026, 12, 31),
        applicable_categories=categories,
        max_amount_per_item=None if cap is None else Decimal(cap),
        notes=f"{notes} Section 43, ch. 2026-239, Laws of Florida.",
    )


_HUNTING_FISHING_CAMPING_2026: tuple[HolidayWindow, ...] = (
    _hunting_fishing_camping(
        "Firearms, Ammunition, and Archery",
        ("firearms", "ammunition", "hunting_supplies"),
        None,
        "Firearms, ammunition, the listed firearm accessories, bows, "
        "crossbows, and the listed archery accessories; no price cap.",
    ),
    _hunting_fishing_camping("Tents", ("tents",), "200.00", "Tents priced $200 or less."),
    _hunting_fishing_camping(
        "Camping Gear",
        ("sleeping_bags", "portable_hammocks", "camping_stoves", "camping_chairs"),
        "50.00",
        "Sleeping bags, portable hammocks, camping stoves, and collapsible "
        "camping chairs priced $50 or less.",
    ),
    _hunting_fishing_camping(
        "Lanterns and Flashlights",
        ("camping_lanterns", "flashlights"),
        "30.00",
        "Camping lanterns and flashlights priced $30 or less.",
    ),
    _hunting_fishing_camping(
        "Rods and Reels",
        ("fishing_rods", "fishing_reels"),
        "75.00",
        "Rods and reels priced $75 or less sold individually; not for " "commercial fishing.",
    ),
    _hunting_fishing_camping(
        "Rod and Reel Sets",
        ("fishing_rod_and_reel_sets",),
        "150.00",
        "Rods and reels sold as a set priced $150 or less; not for " "commercial fishing.",
    ),
    _hunting_fishing_camping(
        "Tackle Boxes",
        ("tackle_boxes",),
        "30.00",
        "Tackle boxes or bags priced $30 or less; not for commercial fishing.",
    ),
    _hunting_fishing_camping(
        "Bait and Tackle",
        ("fishing_bait", "fishing_tackle"),
        "10.00",
        "Bait or fishing tackle priced $10 or less sold individually; not "
        "for commercial fishing.",
    ),
    _hunting_fishing_camping(
        "Bait and Tackle Sold Together",
        ("fishing_tackle_sets",),
        "20.00",
        "Bait or fishing tackle sold together as multiple items priced "
        "$20 or less; not for commercial fishing.",
    ),
)

_PROTOCOL_CHECK: StateModule = Florida()
del _PROTOCOL_CHECK

FLORIDA = register(Florida())
