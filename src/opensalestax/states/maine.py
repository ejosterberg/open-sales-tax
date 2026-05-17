# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Maine state module (tier 1, non-SST).

ME is **not** a Streamlined Sales Tax member (verified 2026-05-03
against the SST member roster on streamlinedsalestax.org -- Maine
runs its own audit/compliance program through Maine Revenue
Services and is not on the SST membership list).

## NOTABLE STRUCTURE: NO LOCAL SALES TAX

Maine is a **state-only** sales-tax jurisdiction: there are NO
county or municipal general sales taxes. The 5.5% state rate is
the entire combined rate at every Maine address. This puts ME in
the small "no-local-tax" club alongside Indiana (7.0%), Kentucky
(6.0%), Michigan (6.0%), and Rhode Island (7.0%).

The statewide general sales tax rate is **5.5%** per Me. Rev.
Stat. tit. 36, section 1811(1). The 5.5% rate took effect
**2013-10-01** as a temporary increase under PL 2013, c. 368,
Part M (raised from 5.0%) and was made **permanent** by PL 2015,
c. 267, Part OOOO. The module pins ``effective_from`` to the
2013-10-01 implementation date because that is when the current
5.5% rate first applied to taxable transactions.

## CATEGORY-SPECIFIC HIGHER RATES (deferred from v1)

In addition to the 5.5% general rate, Me. Rev. Stat. tit. 36
section 1811 imposes several higher rates on specific
transaction categories that the OpenSalesTax engine does **not
yet model** as of this state-module ship. The category-aware-rate
engine extension required to apply different rates to different
line-item categories has not yet landed; the module documents
the higher rates here and applies the 5.5% general rate to all
taxable categories until the engine catches up:

- **8% on prepared food** (section 1811(1) third paragraph) --
  the prepared_food taxability rule is encoded as
  ``is_taxable=True``; the engine applies 5.5% rather than the
  statutory 8%, **under-collecting by 2.5 percentage points** on
  prepared-food line items until category-aware rates ship.
- **9% on lodging** (section 1811(1) fourth paragraph; was 8% from
  2013-10-01 through 2015-12-31, raised to 9% effective 2016-01-01
  by PL 2015, c. 267, Part OOOO). Not modeled -- there is no
  "lodging" category in the v1 baseline taxability matrix.
- **10% on short-term automobile rental** (section 1811(1) fifth
  paragraph -- rentals less than one year). Not modeled -- there
  is no "auto_rental" category in the v1 baseline taxability
  matrix.
- **14% on adult-use cannabis** sales for sales on or after
  2026-01-01 (PL 2025, c. 87 §7; PL 2025, c. 388, Pt. F §1, §5).
  Not modeled -- cannabis is outside the v1 baseline taxability
  matrix.

When the category-aware-rate engine extension lands, this module
should be revisited to emit the 8%/9%/10% rates as
``RateRow`` instances with ``applies_to_categories`` set, and the
prepared_food taxability rule should be updated to point at the
8% rate instead of falling through to the 5.5% general rate.

Taxability matrix (per Me. Rev. Stat. tit. 36, Part 3):

- **General tangible personal property** -- TAXABLE at 5.5%
  (Me. Rev. Stat. tit. 36, section 1811(1); section 1752(17)
  defines "tangible personal property").
- **Clothing** -- TAXABLE at 5.5%. Maine has no general clothing
  exemption; clothing and footwear are general tangible personal
  property and tax at the 5.5% rate. (Me. Rev. Stat. tit. 36
  section 1760's enumerated exemptions do not include clothing.)
- **Groceries** -- EXEMPT as "grocery staples" per Me. Rev. Stat.
  tit. 36 section 1760(3). The "grocery staples" definition in
  section 1752(3-B) excludes alcohol, candy, soft drinks, dietary
  supplements, marijuana products, prepared food, and several
  snack categories -- those remain taxable.
- **Prescription drugs** -- EXEMPT per Me. Rev. Stat. tit. 36
  section 1760(5) ("Prescription drugs"), which exempts sales of
  medicines for human beings sold on a doctor's prescription.
- **Prepared food** -- TAXABLE. **Statutory rate is 8%** under
  Me. Rev. Stat. tit. 36 section 1811(1), but v1 applies the
  5.5% general rate pending category-aware-rate engine support
  (see notes above).
- **Digital goods** -- TAXABLE at 5.5%. Me. Rev. Stat. tit. 36
  section 1752(17) defines "tangible personal property" to
  expressly INCLUDE "any product transferred electronically",
  language added in 2009 (PL 2009, c. 211) effective 2010 and
  subsequently broadened. Maine further expanded its taxable
  digital base effective 2026-01-01 to cover subscription-based
  streaming/audio/ebook services that lack a permanent right to
  use (LD 210 of 2025, signed June 2025) -- the 5.5%
  digital_goods rule already covers both the permanent-right and
  subscription cases under the unified TPP definition.

Sales-tax holidays:

- **NONE.** Maine has no enacted sales-tax holiday. Bills to
  establish a back-to-school holiday have been introduced
  (HP0227 / LD 318 in the 126th Legislature; HP0512 / LD 759 in
  the 127th Legislature) but none have been passed into law.
  Confirmed 2026-05-03 against Maine Revenue Services published
  guidance and current statute. The module's
  ``holidays_for(year)`` returns an empty iterator for every
  year, with a regression test that exercises 2024-2030.

State maintainer: vacant -- see MAINTAINERS.md. The most likely
sources of follow-up work are (a) the category-aware-rate
extension to encode the 8% prepared-food / 9% lodging / 10%
auto-rental / 14% cannabis rates and (b) any future Maine
sales-tax holiday if the legislature enacts one.

Disclaimer: this module computes tax; it does not provide legal
or tax advice. Verify against Maine Revenue Services for any
compliance decision.
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

# Maine taxability matrix per Me. Rev. Stat. tit. 36, Part 3.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Maine at the 5.5% state rate. Me. "
            "Rev. Stat. tit. 36 section 1760's enumerated exemptions do "
            "not include clothing; clothing and footwear are general "
            "tangible personal property under section 1752(17) and tax "
            "at the rate set by section 1811(1). Maine has no enacted "
            "annual back-to-school clothing holiday (a holiday bill has "
            "been introduced multiple sessions but never enacted). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "'Grocery staples' are EXEMPT in Maine per Me. Rev. Stat. "
            "tit. 36 section 1760(3). The 'grocery staples' definition "
            "in section 1752(3-B) covers food products ordinarily "
            "consumed for human nourishment but EXCLUDES spirituous/"
            "malt/vinous liquors, medicines, water, soft drinks, "
            "candy, confectionery, dietary supplements, marijuana and "
            "marijuana products, prepared food, and various snack "
            "categories -- those remain taxable (snacks/soft drinks/"
            "candy at the 5.5% general rate; prepared food at the "
            "statutory 8% rate documented under prepared_food). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Maine per Me. Rev. Stat. "
            "tit. 36 section 1760(5) ('Prescription drugs'), which "
            "exempts sales of medicines for human beings sold on a "
            "doctor's prescription. The exemption does NOT extend to "
            "cannabis products even when recommended by a physician "
            "(section 1760(5) explicitly excludes cannabis sales). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food / meals are TAXABLE in Maine. The STATUTORY "
            "rate is 8% under Me. Rev. Stat. tit. 36 section 1811(1) "
            "third paragraph, but the OpenSalesTax engine applies the "
            "5.5% general rate to this category in v1, UNDER-COLLECTING "
            "by 2.5 percentage points on prepared-food line items "
            "pending the category-aware-rate engine extension. "
            "'Prepared food' is defined in section 1752(8-A) and "
            "includes meals served on or off the premises and food/"
            "drinks prepared by the retailer ready for consumption "
            "without further preparation. Service charges added to the "
            "price of meals are part of the taxable sales price. "
            "Callers needing exact prepared-food tax amounts should "
            "apply an 8%/5.5% adjustment factor until category rates "
            "ship. Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are TAXABLE in Maine at 5.5%. Me. Rev. "
            "Stat. tit. 36 section 1752(17) defines 'tangible personal "
            "property' to expressly INCLUDE 'any product transferred "
            "electronically' -- the digital-products inclusion was "
            "added by PL 2009, c. 211 effective 2010 and broadened "
            "since. Maine further expanded the taxable digital base "
            "effective 2026-01-01 (LD 210 of 2025, signed June 2025) "
            "to cover subscription-based streaming/audio/ebook/app "
            "services that lack a permanent right to use; the unified "
            "TPP definition means both downloaded-with-permanent-right "
            "AND subscription-based digital media now fall under the "
            "5.5% general rate without a sub-category split. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Maine at "
            "5.5% per Me. Rev. Stat. tit. 36 section 1811(1) (rate) "
            "and section 1752(17) (definition of 'tangible personal "
            "property'). Maine levies NO general local (county or "
            "municipal) sales tax -- the 5.5% state rate is the entire "
            "combined rate at every Maine address (mirrors IN/KY/MI/"
            "RI). Calculation only -- not legal or tax advice."
        ),
    ),
}

# Statewide-rate effective date: October 1, 2013. The 5.5% rate took
# effect under PL 2013, c. 368, Part M (originally a temporary
# increase from 5.0% scheduled to sunset 2015-06-30). PL 2015, c. 267,
# Part OOOO eliminated the sunset and made 5.5% permanent.
_RATE_EFFECTIVE_FROM = dt.date(2013, 10, 1)


class Maine:
    """Maine state module (tier 1; statewide 5.5% rate; no local tax)."""

    state_abbrev: str = "ME"
    state_name: str = "Maine"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # Maine has no SST upstream file; parse_rates returns the same row
    # regardless of source_file, so the loader must skip the cache-file
    # requirement for ME.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Maine's statewide 5.5% rate.

        ``source_file`` is intentionally ignored -- ME is non-SST and
        has no upstream file. Pass ``None`` from the loader.

        Maine has NO general local sales tax (no county or municipal
        sales tax), so this method yields exactly one state-level row.
        The category-specific higher rates documented in this module's
        docstring (8% prepared food, 9% lodging, 10% short-term auto
        rental, 14% cannabis) are NOT yet emitted as RateRow instances
        because the engine does not yet support per-category rate
        application; once that extension lands, additional rows with
        ``applies_to_categories`` set should be emitted here.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Maine",
            authority_type="state",
            rate_pct=Decimal("5.500"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundary rows shipped: Maine is a state-only jurisdiction.

        Maine imposes no county or municipal sales tax, so a single
        state-level authority covers every Maine address. There is
        nothing to attach via boundaries.
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return Maine's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases consumed by the engine in v1.

        The category-specific higher rates (8% prepared food, 9%
        lodging, 10% short-term auto rental, 14% adult-use cannabis)
        are documented in this module's docstring and
        ``specs/research/references.md`` for follow-up work once the
        category-aware-rate engine extension lands.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Maine has no enacted sales-tax holidays.

        Confirmed 2026-05-03 against Maine Revenue Services published
        guidance and the current text of Me. Rev. Stat. tit. 36, Part
        3. Several bills to establish a back-to-school holiday have
        been introduced (HP0227/LD 318 in the 126th Legislature;
        HP0512/LD 759 in the 127th Legislature) but none have passed.
        Returns an empty iterator for every year.
        """
        del year
        return iter(())

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return ME's shipping rule.

        Separately stated transportation charges are excluded from
        "sale price"; bundled transportation is taxable.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.EXEMPT_IF_SEPARATELY_STATED,
            citation="36 MRSA 1752(14)(B)",
        )


_PROTOCOL_CHECK: StateModule = Maine()
del _PROTOCOL_CHECK

MAINE = register(Maine())
