# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Missouri state module (tier 1, non-SST).

MO is **not** a Streamlined Sales Tax member (verified 2026-05-03
against the SST member roster -- Missouri does not appear among the
23 full members or the lone associate member, Tennessee). The
statewide sales-tax rate is **4.225%** per the Missouri Department
of Revenue (https://dor.mo.gov), composed of:

- **3.000%** general revenue (Mo. Rev. Stat. section 144.020)
- **1.000%** education (Proposition C, Mo. Rev. Stat. section
  144.701)
- **0.125%** state parks and soils conservation (Mo. Const.
  art. IV, section 47(a))
- **0.100%** conservation (Mo. Const. art. IV, section 43(a))

Local jurisdictions -- Missouri counties, cities, fire districts,
ambulance districts, transit authorities, and tourism community
enhancement districts (TCEDs) may each levy their own sales tax
under various enabling acts. Combined statewide-plus-local rates
range from **4.225% to over 11.0%** in some areas (e.g., Branson,
the Branson Lakes Area Convention and Visitors Bureau district).
**Per-jurisdiction local rates are NOT modeled in v0.7** -- there
is no SST file (MO is not an SST member) and no public per-ZIP
machine-readable feed comparable to the Texas Comptroller's. MO
DOR does publish a Sales/Use Tax Rate Tables PDF and an Excel
download, but ingesting and normalizing that data is deferred to a
future state-data-loader phase. The module ships the 4.225%
statewide rate only, mirroring how CA defers its CDTFA districts,
SC defers its county/municipal rates, and VA defers its regional
add-ons.

Taxability matrix (per Mo. Rev. Stat. Title X, Chapter 144 --
sales/use tax):

- **Clothing** -- TAXABLE year-round (no general clothing
  exemption). The annual Back-to-School Sales Tax Holiday (Mo.
  Rev. Stat. section 144.049) temporarily exempts qualifying
  clothing $100 or less per item.
- **Groceries (food for home consumption)** -- TAXABLE at a
  REDUCED state rate of **1.225%** (instead of the general
  4.225%) per Mo. Rev. Stat. section 144.014. The 3.000% general
  revenue portion does not apply to qualifying food; the 0.100%
  conservation, 0.125% parks/soils, and 1.000% Proposition C
  education portions do, totaling 1.225%. **Important caveat:**
  the reduced state rate applies ONLY to the state portion --
  city, county, and other local sales taxes apply to groceries
  at the FULL local rate. Encoded with
  ``rate_modifier=Decimal("1.225")`` mirroring the Illinois /
  Virginia pattern; the engine does not yet apply rate_modifier
  (deferred to v0.6+), so retailers selling groceries in MO
  should verify with the Missouri Department of Revenue until
  the modifier is wired through.
- **Prescription drugs** -- NON-taxable (Mo. Rev. Stat. section
  144.030.2(18)).
- **Prepared food** -- TAXABLE at the full statewide rate. Some
  Missouri municipalities also impose a separate restaurant or
  meals tax administered locally; not modeled here.
- **Digital goods** -- NON-taxable. Missouri's sales tax applies
  only to "tangible personal property" per Mo. Rev. Stat. section
  144.020, and the Missouri Department of Revenue has historically
  taken the position that electronically delivered digital goods
  (downloaded software, music, ebooks, streaming) are not tangible
  personal property and therefore not subject to sales tax. SB
  153 (2021) -- enacted as Mo. Rev. Stat. sections 144.605 and
  144.752 -- established a remote-seller and marketplace-
  facilitator economic-nexus regime ($100,000 in gross receipts)
  effective 2023-01-01; SB 153 did NOT change the underlying
  tangibility-based scope of the sales tax, so digital goods
  remain non-taxable in v0.7. Tangible-media sales (e.g., a
  boxed CD) remain taxable.
- **General** -- TAXABLE at 4.225% (Mo. Rev. Stat. section
  144.020).

Sales-tax holidays:

Missouri has TWO annual sales-tax holidays codified in Chapter
144:

- **Show-Me Green Sales Tax Holiday** (Mo. Rev. Stat. section
  144.526) -- begins at 12:01 a.m. on April 19 and ends at
  midnight on April 25 each year (fixed calendar dates, NOT
  weekday-relative). Exempts qualifying Energy Star certified
  new appliances $1,500 or less per item. The state-level
  exemption applies automatically; cities and counties may opt
  out, in which case local sales tax still applies.
- **Back-to-School Sales Tax Holiday** (Mo. Rev. Stat. section
  144.049) -- begins at 12:01 a.m. on the first Friday in August
  and ends at midnight on the Sunday following. Exempts:
  - Clothing $100 or less per item
  - School supplies $50 or less per purchase
  - Personal computers $1,500 or less
  - Computer peripheral devices $1,500 or less
  - Computer software $350 or less

  As of 2023 (HB 154 of 2021, codified at section 144.049.10),
  cities and counties no longer have the option to opt out --
  the back-to-school holiday is mandatory at all jurisdiction
  levels.

Each holiday is encoded as one or more :class:`HolidayWindow`
instances. The back-to-school holiday's clothing/school
supplies/computers/peripherals/software scopes are encoded as
separate windows so the engine can match per-category with the
correct per-item cap.

State maintainer: vacant -- see MAINTAINERS.md. The biggest
follow-up is local-rate ingestion: MO DOR publishes a quarterly
Sales/Use Tax Rate Tables file that needs a custom loader (no
SST data path).

Disclaimer: this module is calculation infrastructure, not tax
advice. Verify every rule against the Missouri Department of
Revenue (https://dor.mo.gov) before relying on it for compliance.
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

# Missouri taxability matrix per Mo. Rev. Stat. Title X, Chapter 144.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Missouri year-round (no general "
            "clothing exemption; Mo. Rev. Stat. section 144.020 imposes "
            "the 4.225% sales tax on tangible personal property). The "
            "annual Back-to-School Sales Tax Holiday (Mo. Rev. Stat. "
            "section 144.049) temporarily exempts qualifying clothing "
            "$100 or less per item; see holidays_for(). The per-item "
            "cap will be enforced when the threshold-rule engine work "
            "lands in v0.6+. Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        # Encoded as the absolute reduced state rate as a percentage,
        # mirroring how Illinois encodes its 1% reduced grocery rate
        # and Virginia encodes its 1% reduced grocery rate. The
        # engine does not yet apply rate_modifier (deferred to v0.6+).
        rate_modifier=Decimal("1.225"),
        notes=(
            "Food qualifying as 'food for home consumption' is taxed at "
            "a REDUCED state rate of 1.225% in Missouri (per Mo. Rev. "
            "Stat. section 144.014) instead of the general 4.225%. "
            "The 3.000% general revenue portion does not apply to "
            "qualifying food; the 0.100% conservation, 0.125% parks/"
            "soils, and 1.000% Proposition C education portions do, "
            "totaling 1.225%. CAVEAT: the reduced rate applies to the "
            "state portion only -- city, county, and other local sales "
            "taxes apply to groceries at the FULL local rate. v0.7 "
            "reports this as taxable with rate_modifier=1.225; the "
            "engine doesn't yet apply rate_modifier. Retailers selling "
            "groceries in MO should verify with the Missouri Department "
            "of Revenue until v0.6+ wires the modifier through. "
            "Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are non-taxable in Missouri (Mo. Rev. "
            "Stat. section 144.030.2(18) -- exemption for drugs and "
            "medical equipment dispensed pursuant to a prescription). "
            "Calculation only -- not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (meals sold by restaurants and similar "
            "establishments) is taxable at the full Missouri state rate "
            "of 4.225% (Mo. Rev. Stat. section 144.020) plus applicable "
            "local rates. The reduced 1.225% food rate of section "
            "144.014 is limited to 'food for home consumption' and "
            "does not apply to prepared food. Many Missouri "
            "municipalities also impose a separate restaurant or meals "
            "tax administered locally and not modeled in this module. "
            "Calculation only -- not tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=False,
        notes=(
            "Digital goods (downloaded software, music, ebooks, "
            "streaming) are generally NON-taxable in Missouri. The "
            "Missouri sales tax applies to 'tangible personal property' "
            "per Mo. Rev. Stat. section 144.020, and the Missouri "
            "Department of Revenue has historically treated "
            "electronically delivered digital products as not "
            "constituting tangible personal property. SB 153 (2021), "
            "codified as Mo. Rev. Stat. sections 144.605 and 144.752, "
            "established a remote-seller and marketplace-facilitator "
            "economic-nexus regime effective 2023-01-01 but did NOT "
            "change the underlying tangibility-based scope of the sales "
            "tax. Tangible-media sales (e.g., a boxed CD) remain "
            "taxable. Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at the "
            "Missouri statewide rate of 4.225% (Mo. Rev. Stat. section "
            "144.020). The v0.7 module ships the statewide rate only; "
            "city, county, and special-district local rates are "
            "deferred to a future state-data-loader phase (no SST file "
            "and no public per-ZIP machine-readable feed). Calculation "
            "only -- not tax advice."
        ),
    ),
}

# Statewide effective date: Missouri's combined statewide rate has
# been 4.225% since the 0.10% Conservation Sales Tax took effect
# 1977-07-01 (Mo. Const. art. IV, section 43(a)) layered atop the
# 1.0% Proposition C education tax (1982) plus the 3.0% general-
# revenue rate plus the 0.125% parks/soils tax (1984, Mo. Const.
# art. IV, section 47(a)). The current 4.225% composition has been
# stable since 1984.
_RATE_EFFECTIVE_FROM = dt.date(1984, 1, 1)


class Missouri:
    """Missouri state module (tier 1; statewide 4.225% rate only in v0.7)."""

    state_abbrev: str = "MO"
    state_name: str = "Missouri"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # MO has no SST upstream file; parse_rates returns the same row
    # regardless of source_file, so the loader must skip the cache-
    # file requirement.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Missouri's statewide 4.225% rate.

        ``source_file`` is intentionally ignored -- MO is non-SST and
        has no upstream file. Pass ``None`` from the loader.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Missouri",
            authority_type="state",
            rate_pct=Decimal("4.225"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundaries shipped in v0.7.

        Missouri's per-county/per-city local rates require a custom
        MO DOR loader (no SST file path); deferred to a future phase.
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return MO's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases consumed by the engine in v0.7.

        Local-jurisdiction opt-out behavior for the Show-Me Green
        holiday and the (now-mandatory) back-to-school holiday are
        documented in the module docstring and would become
        SpecialCase entries once the engine layer that reads them
        lands.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Missouri's two annual sales-tax holidays.

        - **Show-Me Green** (Mo. Rev. Stat. section 144.526): April
          19-25 each year (fixed calendar dates), Energy Star
          appliances $1,500 or less per item.
        - **Back-to-School** (Mo. Rev. Stat. section 144.049): first
          Friday in August through the following Sunday. Five
          per-category caps encoded as separate windows.

        Per Missouri statute, the holiday windows are not legislated
        annually but are codified in Chapter 144 with statutory
        date formulas. We still encode each year explicitly so a
        future maintainer can audit the chosen dates against the
        DOR's published announcement.

        For 2026:
        - Show-Me Green: Sun April 19 -- Sat April 25, 2026.
        - Back-to-School: first Friday of August 2026 is August 7;
          holiday runs Aug 7 (Fri) -- Aug 9 (Sun), 2026.
        """
        if year != 2026:
            return iter(())

        show_me_green_start = dt.date(2026, 4, 19)
        show_me_green_end = dt.date(2026, 4, 25)
        back_to_school_start = dt.date(2026, 8, 7)
        back_to_school_end = dt.date(2026, 8, 9)
        return iter(
            [
                HolidayWindow(
                    name="Missouri Show-Me Green Sales Tax Holiday (2026)",
                    starts_on=show_me_green_start,
                    ends_on=show_me_green_end,
                    applicable_categories=("energy_star",),
                    max_amount_per_item=Decimal("1500.00"),
                    notes=(
                        "Mo. Rev. Stat. section 144.526: Energy Star "
                        "certified new appliances (refrigerators, "
                        "freezers, dishwashers, clothes washers, air "
                        "conditioners, furnaces, heat pumps, etc.) "
                        "priced $1,500 or less per item are exempt "
                        "from the state 4.225% sales tax from 12:01 "
                        "a.m. April 19 through midnight April 25 each "
                        "year. Cities and counties may opt out, in "
                        "which case local sales tax still applies. "
                        "The engine-level cap is the statutory $1,500. "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Missouri Back-to-School Sales Tax Holiday -- Clothing (2026)",
                    starts_on=back_to_school_start,
                    ends_on=back_to_school_end,
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Mo. Rev. Stat. section 144.049: qualifying "
                        "clothing (defined to include footwear and "
                        "items intended to be worn on or about the "
                        "human body) priced $100 or less per item is "
                        "exempt from sales tax during the holiday. "
                        "Excludes accessories, watches, jewelry, "
                        "umbrellas, handbags, and items containing "
                        "fur. Per HB 154 (2021), the holiday is "
                        "mandatory at all jurisdiction levels (cities "
                        "and counties may no longer opt out). "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Missouri Back-to-School Sales Tax Holiday -- School Supplies (2026)",
                    starts_on=back_to_school_start,
                    ends_on=back_to_school_end,
                    applicable_categories=("school_supplies",),
                    max_amount_per_item=Decimal("50.00"),
                    notes=(
                        "Mo. Rev. Stat. section 144.049: qualifying "
                        "school supplies up to $50 per purchase are "
                        "exempt during the holiday. The $50 cap is "
                        "PER PURCHASE under the statute (not strictly "
                        "per item) -- the engine encodes it as a per-"
                        "item cap pending threshold-rule support that "
                        "can model purchase-level caps. Includes "
                        "notebooks, paper, pens, pencils, art supplies, "
                        "lunch boxes, and required class graphing "
                        "calculators. Calculation only -- not tax "
                        "advice."
                    ),
                ),
                HolidayWindow(
                    name="Missouri Back-to-School Sales Tax Holiday -- Personal Computers (2026)",
                    starts_on=back_to_school_start,
                    ends_on=back_to_school_end,
                    applicable_categories=("computers",),
                    max_amount_per_item=Decimal("1500.00"),
                    notes=(
                        "Mo. Rev. Stat. section 144.049: personal "
                        "computers (laptops, desktops, tablets) priced "
                        "$1,500 or less are exempt during the holiday. "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name=(
                        "Missouri Back-to-School Sales Tax Holiday "
                        "-- Computer Peripherals (2026)"
                    ),
                    starts_on=back_to_school_start,
                    ends_on=back_to_school_end,
                    applicable_categories=("computer_peripherals",),
                    max_amount_per_item=Decimal("1500.00"),
                    notes=(
                        "Mo. Rev. Stat. section 144.049: computer "
                        "peripheral devices (monitors, keyboards, "
                        "mice, printers, modems, routers, speakers, "
                        "external drives) priced $1,500 or less per "
                        "item are exempt during the holiday. "
                        "Calculation only -- not tax advice."
                    ),
                ),
                HolidayWindow(
                    name="Missouri Back-to-School Sales Tax Holiday -- Computer Software (2026)",
                    starts_on=back_to_school_start,
                    ends_on=back_to_school_end,
                    applicable_categories=("computer_software",),
                    max_amount_per_item=Decimal("350.00"),
                    notes=(
                        "Mo. Rev. Stat. section 144.049: prewritten "
                        "computer software priced $350 or less per "
                        "item is exempt during the holiday. "
                        "Calculation only -- not tax advice."
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = Missouri()
del _PROTOCOL_CHECK

MISSOURI = register(Missouri())
