# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Connecticut state module (tier 1, non-SST).

CT is **not** a Streamlined Sales Tax member (verified 2026-05-03
against the SST member roster). The general statewide rate is
**6.35%** effective **2011-07-01** when the General Assembly raised
it from 6.0% (Conn. Gen. Stat. section 12-408(1)(A)).

Connecticut is a **state-only** sales-tax jurisdiction: per Conn.
Gen. Stat. section 12-408 there are **no** county or municipal
sales taxes -- the entire 6.35% combined rate is the state portion,
nothing is added at the local level anywhere in the state. This is
unusual; only a handful of states (RI 7%, IN 7%, KY 6%, MI 6%, NJ
6.625%) share the no-local-sales-tax pattern. The flat statewide
rate applies in every CT ZIP code; a future maintainer adding
"local" CT rates would be making a mistake. The only sub-state
taxing authority is the **Mashantucket Pequot Tribal Nation**
reservation, whose retail sales fall outside CT's sales-tax regime
under the 1983 federal settlement act and tribal-state compact --
a special case the engine does not yet model.

In addition to the 6.35% general rate, section 12-408(1) imposes
several CATEGORY-SPECIFIC rates that are **not modeled in v0.6**
(documented here so a future maintainer knows the landscape):

- 7.75% luxury rate on motor vehicles > $50,000, jewelry > $5,000,
  and clothing/footwear/handbag/luggage/umbrella/wallet/watch >
  $1,000 (section 12-408(1)(H)).
- 7.35% on meals and beverages sold by eating establishments,
  caterers, or grocery stores (the 6.35% general rate plus the
  additional 1% in section 12-408(1)(I)).
- 15% on hotel/lodging-house occupancy, 11% on B&B occupancy
  (section 12-408(1)(B)).
- 9.35% on short-term passenger-vehicle rental (section
  12-408(1)(G)).
- 1% on computer and data processing services (section
  12-408(1)(D)(i)).
- 2.99% on vessels and vessel motors (section 12-408(1)(E)(ii)).

Modeling these requires either rate-modifier engine support or
threshold-rule support, both of which are deferred to a later
phase. The v0.6 module ships the 6.35% general rate plus a
6-category taxability matrix.

Taxability matrix (per Conn. Gen. Stat. chapter 219):

- **Clothing** -- TAXABLE at 6.35%. CT eliminated its clothing
  exemption in 2011 (P.A. 11-6) and the briefly-restored under-$50
  exemption was repealed effective 2015-07-01 (P.A. 15-244).
  Section 12-407e exempts clothing/footwear under $100 only during
  the annual third-Sunday-in-August holiday week (modeled in
  ``holidays_for``).
- **Groceries** -- NON-taxable as "food products for human
  consumption" (section 12-412(13)).
- **Prescription drugs** -- NON-taxable (section 12-412(4)).
- **Prepared food** -- TAXABLE. CT applies the 7.35% combined rate
  via section 12-408(1)(I); v0.6 ships the rule with a notes-only
  caveat pending rate-modifier engine support.
- **Digital goods** -- TAXABLE. P.A. 19-117 amended section
  12-407(a)(13) to include digital goods and electronically
  accessed canned/prewritten software in "tangible personal
  property" effective 2019-10-01.
- **General** -- TAXABLE at 6.35%.

Sales-tax holidays:

- **Sales Tax Free Week** -- annual back-to-school holiday running
  the third Sunday in August through the following Saturday,
  inclusive (section 12-407e). Exempts clothing and footwear under
  $100 per item; excludes athletic wear, jewelry, handbags,
  luggage, umbrellas, wallets, and watches. The under-$300
  threshold that ran 2004-2015 was reduced to under-$100 effective
  2015-07-01 by P.A. 15-244. 2026 dates: August 16 (Sunday) through
  August 22 (Saturday).

State maintainer: vacant -- see MAINTAINERS.md. CT's category
rates and the Mashantucket Pequot reservation case are the most
likely sources of follow-up work.

Disclaimer: this module computes tax; it does not provide legal or
tax advice. Verify against the Connecticut Department of Revenue
Services (DRS) for any compliance decision.
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

# Connecticut taxability matrix per Conn. Gen. Stat. chapter 219.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Connecticut at 6.35% (Conn. Gen. Stat. "
            "section 12-408(1)(A)). The under-$50 clothing exemption was "
            "eliminated effective 2015-07-01 by P.A. 15-244. Items priced "
            "over $1,000 fall under the 7.75% luxury rate per section "
            "12-408(1)(H) -- not modeled in v0.6 pending threshold-rule "
            "support. The annual Sales Tax Free Week (third Sunday in "
            "August through following Saturday) exempts clothing/footwear "
            "under $100 per item; see holidays_for(). Calculation only -- "
            "not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food products for human consumption are non-taxable (Conn. "
            "Gen. Stat. section 12-412(13)). Statutory definition excludes "
            "spirituous/malt/vinous liquors, soft drinks, candy, "
            "confectionery, dietary supplements, and meals sold by an "
            "eating establishment or caterer (those are taxable under the "
            "prepared_food category). Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription medicine, syringes, and needles are non-taxable "
            "(Conn. Gen. Stat. section 12-412(4)). Calculation only -- not "
            "tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Meals sold by eating establishments, caterers, or grocery "
            "stores are taxable. Conn. Gen. Stat. section 12-408(1)(I) "
            "imposes an additional 1% on top of the 6.35% general rate "
            "for a combined 7.35% meals rate; v0.6 applies the 6.35% "
            "general rate only, pending rate-modifier engine support. "
            "Calculation only -- not tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods and electronically accessed canned/prewritten "
            "software are TAXABLE at 6.35% per Conn. Gen. Stat. section "
            "12-407(a)(13), as amended by Public Act 19-117 effective "
            "2019-10-01. Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at 6.35% (Conn. "
            "Gen. Stat. section 12-408(1)(A)). Calculation only -- not tax "
            "advice."
        ),
    ),
}

# Statewide effective date when the current 6.35% rate took effect:
# P.A. 11-6 raised the rate from 6.0% effective 2011-07-01.
_RATE_EFFECTIVE_FROM = dt.date(2011, 7, 1)

# Annual Sales Tax Free Week: third Sunday of August through following Saturday.
# 2026: third Sunday is August 16; week runs through Saturday August 22.
_HOLIDAY_2026_START = dt.date(2026, 8, 16)
_HOLIDAY_2026_END = dt.date(2026, 8, 22)


class Connecticut:
    """Connecticut state module (tier 1; statewide 6.35% rate only in v0.6)."""

    state_abbrev: str = "CT"
    state_name: str = "Connecticut"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # CT has no SST upstream file; parse_rates returns the same row regardless
    # of source_file, so the loader must skip the cache-file requirement.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Connecticut's statewide 6.35% rate.

        ``source_file`` is intentionally ignored -- CT is non-SST and
        has no upstream file. Pass ``None`` from the loader.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Connecticut",
            authority_type="state",
            rate_pct=Decimal("6.350"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundaries shipped: CT is a state-only jurisdiction.

        Connecticut imposes no county or municipal sales tax, so a
        single state-level authority suffices. The Mashantucket Pequot
        reservation is a special case not modeled here.
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return CT's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases consumed by the engine in v0.6.

        The Mashantucket Pequot reservation regime, the 7.75% luxury
        rate, the 7.35% meals rate, the 15% hotel rate, and the 9.35%
        short-term-rental rate are documented in this module's
        docstring and will become SpecialCase entries once the engine
        layer that reads them lands.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Connecticut's annual Sales Tax Free Week.

        Codified as a recurring holiday by Conn. Gen. Stat. section
        12-407e: third Sunday in August through following Saturday,
        inclusive. Exempts clothing and footwear under $100 per item;
        excludes athletic wear, jewelry, handbags, luggage, umbrellas,
        wallets, and watches.

        The under-$300 threshold that ran 2004-2015 was reduced to
        under-$100 effective 2015-07-01 by P.A. 15-244. 2026 dates
        encoded explicitly; future years require updating once DRS
        publishes the official window.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Sales Tax Free Week (2026)",
                    starts_on=_HOLIDAY_2026_START,
                    ends_on=_HOLIDAY_2026_END,
                    applicable_categories=("clothing",),
                    max_amount_per_item=Decimal("100.00"),
                    notes=(
                        "Clothing and footwear under $100/item exempt "
                        "(Conn. Gen. Stat. section 12-407e). Excludes "
                        "athletic wear designed primarily for sports, "
                        "jewelry, handbags, luggage, umbrellas, wallets, "
                        "and watches. Third Sunday of August through "
                        "following Saturday."
                    ),
                ),
            ]
        )

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return CT's shipping rule.

        Connecticut treats delivery charges as part of the "sales
        price" of tangible personal property; shipping is included
        in the taxable base when the underlying item is taxable
        and excluded when the item is exempt. Practitioner default
        for typical e-commerce.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.CONDITIONAL,
            citation="Conn. Gen. Stat. 12-407(a)(2)",
        )


_PROTOCOL_CHECK: StateModule = Connecticut()
del _PROTOCOL_CHECK

CONNECTICUT = register(Connecticut())
