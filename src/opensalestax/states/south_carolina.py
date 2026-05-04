# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""South Carolina state module (tier 1, non-SST).

SC is **not** a Streamlined Sales Tax member. The statewide rate is
**6%** per S.C. Code Ann. section 12-36-910(A), effective
**June 1, 2007** (the additional 1% surcharge under
section 12-36-1110 took the combined statewide rate from 5% to 6%
on that date and it has been stable since).

Local-jurisdiction model:

- **Local Option (LO)** -- 1%, county-level
- **Capital Project (CP)** -- 1%, county-level
- **Education Capital Improvement (ECI)** -- 1%, county-level
- **School District (SD)** -- 1%, county-level
- **Transportation Tax (TT)** -- 1%, county-level
- **Tourism Development (TD)** -- 1%, certain municipalities
  (Myrtle Beach is the only one currently active)

Combined county rates range from **6%** (Greenville, Oconee, Beaufort
-- no local tax) to **9%** (Berkeley, Charleston, Jasper, Myrtle Beach
municipal area). All 46 SC counties are seeded from the SC DOR
ST-500 rate chart effective May 1, 2026 via
:mod:`opensalestax.states.sc_data`; see that module for the per-
county rates and the 10 covered cities' ZIP coverage.

Taxability matrix (per S.C. Code Ann. Title 12, Chapter 36):

- **Clothing** -- TAXABLE year-round. The annual August Tax Free
  Weekend (section 12-36-2120(57)) provides a 72-hour exemption.
- **Groceries (unprepared food)** -- exempt from the **state 6%**
  per section 12-36-2120(75). Important quirk: local sales taxes
  may STILL apply to groceries unless the specific local tax
  ordinance also exempts them. This v0.6 module marks groceries
  ``is_taxable=False`` with a notes-field caveat about local taxes,
  consistent with how the engine evaluates a single combined rate;
  a future "per-jurisdiction taxability override" feature would
  let us model this precisely.
- **Prescription drugs** -- exempt per section 12-36-2120(28).
- **Prepared food** -- TAXABLE (the section 12-36-2120(75)
  exemption is for **unprepared** food only).
- **Digital goods** -- **NOT TAXABLE** when delivered purely
  electronically. Per SC Revenue Ruling #03-5 and section 12-36-60,
  software/digital products delivered via download are treated as
  intangible and not subject to sales tax. Software delivered on
  physical media (diskette, magnetic tape) IS taxable. This is
  unusual relative to most peer states -- maintainers should track
  any legislative shift here, since SC has had multiple bills
  proposing to extend tax to digital goods.

Sales tax holiday (section 12-36-2120(57)):

The Tax Free Weekend runs **72 hours** beginning at 12:01 a.m. on
the **first Friday in August** through midnight the following
**Sunday**. There are **no per-item dollar caps** -- both the 6%
state rate and any applicable local sales/use tax are suspended
during the window for qualifying categories:

- Clothing, clothing accessories, footwear
- School supplies (pens, pencils, paper, binders, notebooks,
  bookbags, lunchboxes, calculators)
- Computers, printers, printer supplies, computer software
- Certain bed and bath items (sheet sets, towels, pillows,
  comforters, etc.)
- Books used for school assignments
- Musical instruments used for school assignments

**2026 dates:** August 7 through August 9, 2026 (verified against
SC DOR's published statutory schedule on 2026-05-03). A pending
2025-2026 Bill 728 ("Tax Free Month") would extend the holiday to
the entire month of August but has not been enacted; encode the
72-hour holiday consistent with current statute.

Loading: the v0.2 loader treats ``SouthCarolina.parse_rates`` as
"self-seeded" -- it returns the single statewide row and ignores
the source-file argument. Use ``opensalestax data load --state SC
--version v0.6-statewide`` to insert it.

State maintainer: vacant -- see MAINTAINERS.md. SC's per-county
local-tax rollup is the natural next contribution; tracking the
annual general assembly tax-relief bill (and Bill 728's progress
in particular) is a maintainer responsibility.

DISCLAIMER: This is calculation logic, not tax advice. Maintainers
and users are responsible for verifying current SC DOR guidance
before relying on these rules in production.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
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
from opensalestax.states.sc_data import (
    SC_CITIES,
    SC_COUNTY_RATE_PCT,
    SC_STATE_EFFECTIVE_FROM,
    SC_STATE_RATE_PCT,
)

_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in South Carolina year-round (S.C. Code "
            "Ann. section 12-36-910). The annual August Tax Free Weekend "
            "(section 12-36-2120(57)) provides a 72-hour exemption with "
            "no per-item cap. Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Unprepared food is exempt from the 6% state sales tax per "
            "S.C. Code Ann. section 12-36-2120(75). LOCAL TAXES may still "
            "apply to groceries unless the specific local-tax ordinance "
            "also exempts them; v0.6 does not model per-jurisdiction "
            "taxability overrides. Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are exempt per S.C. Code Ann. section "
            "12-36-2120(28). Calculation only -- not tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot foods) is taxable in "
            "South Carolina; the section 12-36-2120(75) exemption "
            "covers unprepared food only. Calculation only -- not tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=False,
        notes=(
            "Digital goods delivered purely electronically (downloaded "
            "software, digital downloads) are NOT taxable in South "
            "Carolina per SC Revenue Ruling 03-5 and S.C. Code Ann. "
            "section 12-36-60. Software delivered on physical media "
            "(diskette/tape) IS taxable. This treatment is unusual vs "
            "peer states; maintainers should track legislative changes. "
            "Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable per S.C. Code "
            "Ann. section 12-36-910. Calculation only -- not tax advice."
        ),
    ),
}

# Statewide rate took its current 6% form on 2007-06-01 when the 1%
# surcharge under S.C. Code Ann. section 12-36-1110 was added on top
# of the long-standing 5% under section 12-36-910(A).
_RATE_EFFECTIVE_FROM = dt.date(2007, 6, 1)


class SouthCarolina:
    """South Carolina state module (tier 1; statewide rate only in v0.6)."""

    state_abbrev: str = "SC"
    state_name: str = "South Carolina"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require a
    # cached upstream file. SC's parse_rates returns the same statewide
    # row regardless of source_file (no SST file exists for SC).
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield SC's state + per-county + per-city rates.

        Counties yielded: only those touched by an SC_CITIES entry
        (mirrors the AZ pattern of not loading rates for counties
        without any covered city). Cities yielded: every SC_CITIES
        entry; SC city rate is 0% in all cases (locals are
        county-level), so the city authority is mainly a friendly
        anchor for the per-city ZIP boundaries.

        ``source_file`` is intentionally ignored -- SC has no SST
        upstream file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="South Carolina",
            authority_type="state",
            rate_pct=SC_STATE_RATE_PCT,
            effective_from=SC_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        used_counties = {county for county, _, _ in SC_CITIES.values()}
        for county_name in sorted(used_counties):
            yield RateRow(
                authority_name=county_name,
                authority_type="county",
                rate_pct=SC_COUNTY_RATE_PCT[county_name],
                effective_from=SC_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="South Carolina",
            )
        for city_name, (county_name, city_rate, _zips) in sorted(SC_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=SC_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=county_name,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county, city) boundary rows for each covered ZIP.

        The Census ZCTA load already provides state-level binding for
        every SC ZIP. This method ADDS county + city bindings for the
        10 covered cities (Columbia, Charleston, Mount Pleasant,
        North Charleston, Rock Hill, Greenville, Summerville,
        Spartanburg, Sumter, Goose Creek). ZIPs in covered counties
        but outside the city list keep the Census state-only binding
        -- a future ratchet should iterate the Census ZCTA->county
        data for SC to add county-only bindings across the rest of
        the state.
        """
        del source_file, version_label
        for city_name, (county_name, _city_rate, zips) in SC_CITIES.items():
            for zip5 in zips:
                yield BoundaryRow(
                    authority_name="South Carolina",
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
        """Return SC's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for SC in v0.6."""
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """South Carolina's annual Tax Free Weekend (section 12-36-2120(57)).

        Statutorily the holiday runs 12:01 a.m. on the **first Friday
        in August** through midnight the following Sunday (a 72-hour
        window). 2026 dates encoded explicitly per SC DOR's published
        schedule; subsequent years require an explicit data update (do
        not extrapolate -- the legislature occasionally adjusts dates
        and a pending 2025-2026 Bill 728 would extend the window to a
        full month).
        """
        if year != 2026:
            return iter(())
        # 2026: first Friday of August is August 7; ends Sunday August 9.
        return iter(
            [
                HolidayWindow(
                    name="Tax Free Weekend (2026)",
                    starts_on=dt.date(2026, 8, 7),
                    ends_on=dt.date(2026, 8, 9),
                    applicable_categories=(
                        "clothing",
                        "school_supplies",
                        "computers",
                        "bed_and_bath",
                    ),
                    max_amount_per_item=None,
                    notes=(
                        "S.C. Code Ann. section 12-36-2120(57). 72-hour "
                        "exemption from state 6% AND any applicable local "
                        "sales/use tax for clothing, clothing accessories, "
                        "footwear, school supplies, computers, printers, "
                        "computer software, certain bed and bath items, "
                        "books for school assignments, and musical "
                        "instruments for school assignments. NO per-item "
                        "dollar cap. Calculation only -- not tax advice."
                    ),
                ),
            ]
        )


_PROTOCOL_CHECK: StateModule = SouthCarolina()
del _PROTOCOL_CHECK

SOUTH_CAROLINA = register(SouthCarolina())
