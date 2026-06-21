# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""District of Columbia state module (tier 1, non-SST).

DC is **not** a Streamlined Sales Tax member. The District is
treated as a "state" by the OpenSalesTax data model -- it has its
own USPS abbreviation (``DC``), its own tax authority (the DC
Office of Tax and Revenue, OTR), and its own Title 47 / Chapter 20
sales-tax statute.

DC has a **single jurisdiction** -- there are no sub-District
counties or cities that levy their own sales tax. The combined
rate at any DC address equals the statewide rate.

## Statewide general rate

- **6.0% effective through Sept. 30, 2026**
- **7.0% effective Oct. 1, 2026**

The rate increase is a confirmed scheduled change per the OTR
"Notice of Oct. 1, 2025 Tax Changes" (https://otr.cfo.dc.gov/release/notice-oct-1-2025-tax-changes).
Both rate rows are emitted with effective-dated bounds so the
engine picks the correct rate for any transaction date.

## DC special-category rates (NOT encoded in v0.6 -- see PR notes)

DC imposes higher sales-tax rates on several non-general categories
under DC Code Sec. 47-2002 and Sec. 47-2002.02:

| Category | Rate | DC Code |
|---|---|---|
| Restaurant meals / prepared food | 10.0% | 47-2002.02(a)(1) |
| On-premises alcoholic beverages | 10.0% | 47-2002.02(a)(2) |
| Off-premises alcoholic beverages | 10.25% | 47-2002(a)(3) |
| Hotel / transient accommodations | 15.95% (through Sept 30, 2027) | 47-2002.02(a)(1) |
| Commercial parking | 18.0% | 47-2002(a)(2) |
| Soft drinks (sweetened beverages) | 8.0% | 47-2002(a)(5) |
| Rental vehicles | 10.25% | 47-2002.02(a)(3) |
| Commercial bingo (since Oct 1, 2025) | 7.5% | -- |

The current OpenSalesTax engine resolves **one rate per
authority per category** -- multiple per-authority special-category
rates would each need their own authority row, or the engine needs
a category-aware authority lookup. This module ships only the
**general 6%/7% statewide rate**; encoding the special rates is
deferred to a future feature parallel to IL's reduced-rate engine
work and the threshold-rules feature on the v0.6+ roadmap.

The taxability matrix below correctly marks ``prepared_food`` as
taxable (so a restaurant meal IS taxed) -- the engine just applies
the 6% (or 7% post-Oct-2026) general rate rather than the 10%
restaurant rate. This is a documented under-collection until the
special-category-rate feature lands.

## Taxability matrix

- **General tangible personal property** -- taxable (DC Code
  Sec. 47-2001(n)(1)).
- **Clothing** -- TAXABLE. DC has no clothing exemption, and the
  back-to-school holiday that previously exempted clothing under
  $100 was **repealed in 2009** (see https://otr.cfo.dc.gov/page/sales-tax-holiday-repealed).
- **Groceries (food for home consumption)** -- NON-taxable.
  Excluded from the definition of "retail sale" by DC Code
  Sec. 47-2001(n)(2)(E), which exempts "sales of food or drink as
  defined in subsection (g)" except for prepared food / food for
  immediate consumption.
- **Prescription drugs** -- NON-taxable per DC Code Sec. 47-2005(14)
  ("sales of medicines, pharmaceuticals, and drugs whether or not
  made on prescriptions of duly licensed physicians").
- **Prepared food** -- taxable (legally at the special 10% rate;
  see special-rate caveat above).
- **Digital goods** -- TAXABLE per DC Code Sec. 47-2001(d-1)
  (definition) and Sec. 47-2001(n)(1)(BB) (imposition); Sec. 337
  of the Fiscal Year 2019 Budget Support Act expanded the
  definition.

## Sales-tax holidays

**None.** DC's August / November back-to-school holiday was
repealed by D.C. Law 18-111 (the Fiscal Year 2010 Budget Support
Act of 2009). No new holiday has been enacted since.

State maintainer: vacant -- see MAINTAINERS.md.
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

# DC taxability matrix per DC Code Title 47, Chapter 20.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in the District of Columbia. DC has no "
            "general clothing exemption. The back-to-school sales-tax "
            "holiday that previously exempted clothing under $100 was "
            "repealed by D.C. Law 18-111 (Fiscal Year 2010 Budget Support "
            "Act of 2009). Calculation only -- not legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food or drink for home consumption is NON-taxable in DC. "
            "Excluded from the definition of 'retail sale' by DC Code "
            "Sec. 47-2001(n)(2)(E), which exempts 'sales of food or "
            "drink as defined in subsection (g)' except for food sold "
            "for immediate consumption (which is taxed at the 10% "
            "restaurant rate). Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are NON-taxable in DC per DC Code "
            "Sec. 47-2005(14) ('sales of medicines, pharmaceuticals, "
            "and drugs whether or not made on prescriptions of duly "
            "licensed physicians'). Calculation only -- not legal or "
            "tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food / restaurant meals are taxable in DC. The "
            "statutory rate is 10% per DC Code Sec. 47-2002.02(a)(1) "
            "(higher than the 6% general rate). The current engine "
            "applies the general statewide rate; the 10% special "
            "rate will be encoded once category-specific rates ship. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are TAXABLE in the District of Columbia per "
            "DC Code Sec. 47-2001(d-1) (definition) and Sec. 47-2001(n)(1)(BB) "
            "(imposition). Coverage was expanded by Sec. 337 of the FY 2019 "
            "Budget Support Act. Calculation only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in DC under "
            "DC Code Sec. 47-2001(n)(1) and Sec. 47-2002. Statewide rate "
            "is 6% through Sept 30, 2026 and 7% effective Oct 1, 2026. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}

# Statewide-rate effective dates per the OTR "Notice of Oct. 1, 2025 Tax
# Changes" (https://otr.cfo.dc.gov/release/notice-oct-1-2025-tax-changes,
# retrieved 2026-05-03). The 6% rate has been in place for many years
# (legacy effective_from used here is the start of the modern OTR rate
# regime); the 7% rate is a confirmed scheduled change.
_GENERAL_RATE_6PCT_EFFECTIVE_FROM = dt.date(2013, 10, 1)
_GENERAL_RATE_6PCT_EFFECTIVE_TO = dt.date(2026, 9, 30)
_GENERAL_RATE_7PCT_EFFECTIVE_FROM = dt.date(2026, 10, 1)


class DistrictOfColumbia:
    """District of Columbia state module (tier 1; statewide rate only)."""

    state_abbrev: str = "DC"
    state_name: str = "District of Columbia"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require
    # a cached upstream file. DC has no SST file; parse_rates returns
    # the same statewide rows regardless of source_file.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield DC's statewide general sales-tax rates.

        Two rows are emitted:

        - 6.0% effective through Sept 30, 2026
        - 7.0% effective Oct 1, 2026 (no end date)

        ``source_file`` is intentionally ignored -- DC has no SST
        upstream file. Pass ``None`` from the loader.
        """
        del source_file, version_label
        yield RateRow(
            authority_name=self.state_name,
            authority_type="state",
            rate_pct=Decimal("6.000"),
            effective_from=_GENERAL_RATE_6PCT_EFFECTIVE_FROM,
            effective_to=_GENERAL_RATE_6PCT_EFFECTIVE_TO,
            parent_authority_name=None,
        )
        yield RateRow(
            authority_name=self.state_name,
            authority_type="state",
            rate_pct=Decimal("7.000"),
            effective_from=_GENERAL_RATE_7PCT_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundary rows shipped in v0.6.

        DC ZIP+4 boundary loading is deferred to the same address-
        level resolution work that other tier-1 modules await
        (Phase 4+).
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return DC's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for DC in v0.6.

        DC's special-category rates (10% restaurant, 18% parking,
        15.95% hotel, 10.25% off-premises liquor, 8% soft drinks,
        7.5% commercial bingo) are documented in the module docstring
        and `specs/research/references.md` for the future
        category-specific-rate engine feature.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """The District of Columbia has no annual sales-tax holidays.

        DC's August / November back-to-school holiday was repealed
        by D.C. Law 18-111 (Fiscal Year 2010 Budget Support Act of
        2009). No replacement holiday has been enacted since.
        """
        del year
        return iter(())

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return DC's shipping rule.

        The District of Columbia treats delivery charges as part
        of "gross receipts" from the sale of tangible personal
        property; shipping is included in the taxable base when
        the underlying item is taxable. Practitioner default for
        typical e-commerce.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.CONDITIONAL,
            citation="DC Code 47-2001(n)(1)",
        )


_PROTOCOL_CHECK: StateModule = DistrictOfColumbia()
del _PROTOCOL_CHECK

DISTRICT_OF_COLUMBIA = register(DistrictOfColumbia())
