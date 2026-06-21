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

Combined county rates range from **6%** (Beaufort, Greenville,
Oconee -- the only three verified-zero local-tax counties per SC
DOR ST-500 Rev. 3/9/2026) to **9%** (Berkeley, Charleston, Jasper,
Myrtle Beach municipal area). All 46 SC counties are seeded from
the SC DOR ST-500 rate chart effective May 1, 2026 via
:mod:`opensalestax.states.sc_data`; see that module for the per-
county rates and the 10 covered cities' ZIP coverage.

**Statewide ZIP coverage via Census ZCTA**
(parallels FL/AZ/CA in v0.28 and TX/NY/MO/IL/PA in v0.29).
:meth:`SouthCarolina.parse_boundaries` iterates
:data:`opensalestax.data.zip_county.ZIP_COUNTY` and emits state +
county bindings for every SC ZIP -- not just the ZIPs in the 10
covered cities. Effect: a ZIP in Berkeley County outside the
Goose Creek seed (e.g., Moncks Corner 29461) now picks up the
+3.0% Berkeley local for an 9.0% combined rate, instead of falling
back to state-only at 6.0%.

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

from opensalestax.data.county_names import county_name
from opensalestax.data.zip_county import ZIP_COUNTY
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

        Counties yielded: every county in :data:`SC_COUNTY_RATE_PCT`
        (all 46 SC counties). The ZIP_COUNTY-driven boundary loader
        binds every SC ZIP to its county, so every county must have
        a queryable rate (even the 0% ones -- Beaufort, Greenville,
        Oconee). Cities yielded: every :data:`SC_CITIES` entry; SC
        city rate is 0% in all cases (locals are county-level), so
        the city authority is mainly a friendly anchor for the per-
        city ZIP boundaries.

        ``source_file`` is intentionally ignored -- SC has no SST
        upstream file.
        """
        del source_file, version_label
        yield RateRow(
            authority_name=self.state_name,
            authority_type="state",
            rate_pct=SC_STATE_RATE_PCT,
            effective_from=SC_STATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        # Emit a RateRow for every SC county. The ZIP_COUNTY-driven
        # boundary loader binds every SC ZIP to its county, so every
        # county must have a queryable rate (even the 0% ones).
        for sc_county_name in sorted(SC_COUNTY_RATE_PCT):
            yield RateRow(
                authority_name=sc_county_name,
                authority_type="county",
                rate_pct=SC_COUNTY_RATE_PCT[sc_county_name],
                effective_from=SC_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=self.state_name,
            )
        for city_name, (sc_city_county, city_rate, _zips) in sorted(SC_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=city_rate,
                effective_from=SC_STATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name=sc_city_county,
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, county[, city]) boundary rows for every SC ZIP.

        Two passes:

        1. Iterate :data:`opensalestax.data.zip_county.ZIP_COUNTY` and
           emit state + county bindings for every ZIP intersecting an
           SC county. This covers the entire state -- not just the
           ZIPs in the 10 covered cities -- so a Berkeley County ZIP
           outside Goose Creek (e.g., Moncks Corner 29461) now picks
           up the +3.0% Berkeley local for an 9.0% combined rate
           instead of falling back to state-only at 6.0%.

        2. Fall back to :data:`SC_CITIES` for any city ZIP missed by
           the Census ZCTA pass (USPS-only / PO-box-only ZIPs that
           aren't published as Census ZCTAs), then emit the city
           BoundaryRow on top of the state + county stack so the
           friendly city anchor is preserved.

        Per the FL/AZ/CA pattern, emit at most ONE county per ZIP per
        Census ZCTA, preferring the city-anchor county if the ZIP is
        in :data:`SC_CITIES`. Without this, ZIPs that physically span
        county lines would get bound to BOTH counties and double-count
        the local tax.
        """
        del source_file, version_label
        # Build city-anchor county map for cross-county-line ZIPs.
        # When a ZIP is in SC_CITIES, the city's declared county wins.
        city_county_for_zip: dict[str, str] = {}
        for _cn, (cc, _rate, czs) in SC_CITIES.items():
            for cz in czs:
                city_county_for_zip[cz] = cc

        # Pass 1: state + county for every SC ZIP per Census ZCTA.
        # Emit at most one county per ZIP: prefer the city-anchor
        # county if known, else the first Census-listed SC county
        # in deterministic FIPS-sorted order.
        #
        # ZIP_COUNTY values are frozensets, so iteration order is
        # non-deterministic; we sort by FIPS for stable test results.
        emitted_zips: set[str] = set()
        for zip5, pairs in ZIP_COUNTY.items():
            preferred_county = city_county_for_zip.get(zip5)
            sorted_sc_pairs = sorted(cf for sa, cf in pairs if sa == "SC")
            chosen_county: str | None = None
            for county_fips in sorted_sc_pairs:
                sc_county_name = county_name("SC", county_fips)
                if sc_county_name is None or sc_county_name not in SC_COUNTY_RATE_PCT:
                    continue
                if preferred_county is not None:
                    if sc_county_name == preferred_county:
                        chosen_county = sc_county_name
                        break
                    # keep iterating in hopes of finding the city's county
                    continue
                # No city anchor for this ZIP -- take the first SC county.
                chosen_county = sc_county_name
                break
            if chosen_county is None and preferred_county is not None:
                # ZIP is in a city but Census doesn't list the city's
                # county at all (USPS-only / boundary-mismatch). Trust
                # the city's declared county.
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
            emitted_zips.add(zip5)
        # Pass 2: city BoundaryRows for SC_CITIES. Also emit state +
        # county for any city ZIP missed by the Census pass (USPS-only
        # codes not in ZCTA) so we never regress city coverage.
        for city_name, (sc_city_county, _city_rate, zips) in SC_CITIES.items():
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
                        authority_name=sc_city_county,
                        authority_type="county",
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

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return SC's shipping rule.

        South Carolina treats delivery charges as part of "gross
        proceeds" when the underlying item is taxable; shipping
        follows the taxability of the goods. Practitioner default
        for typical e-commerce.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.CONDITIONAL,
            citation="SC Code 12-36-90",
        )


_PROTOCOL_CHECK: StateModule = SouthCarolina()
del _PROTOCOL_CHECK

SOUTH_CAROLINA = register(SouthCarolina())
