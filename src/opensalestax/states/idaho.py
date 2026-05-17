# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Idaho state module (tier 1, non-SST).

ID is **not** a Streamlined Sales Tax member (verified 2026-05-03
against the SST member roster on streamlinedsalestax.org). The
statewide rate is **6%** per **Idaho Code section 63-3619**, which
took its current 6% form effective **October 1, 2006** under House
Bill 82 from the 2006 First Extraordinary Legislative Session
(prior rate: 5%).

Idaho's local-jurisdiction landscape is **narrow**. There is no
county-level sales tax. A small number of "resort cities" with
populations not exceeding 10,000 are authorized under
**Idaho Code section 50-1044** (and the related municipal-finance
statute section 50-1046) to impose, by 60% voter approval,
local-option non-property taxes that may include a sales tax,
typically 1-3%.

iter-75 ships the 6 highest-population 3% resort cities (Sun
Valley, Ketchum, McCall, Stanley, Donnelly, Cascade) via
:data:`opensalestax.states.id_data.ID_RESORT_CITIES`. Each emits
a city RateRow with ``parent_authority_name='Idaho'`` and a city
BoundaryRow per covered ZIP, so the engine returns combined 9.0%
in those municipalities. Smaller resort cities (Salmon 0.5%,
Sandpoint 1%, Driggs 1%, Riggins 1%, Lava Hot Springs 1%) can be
added in a follow-up ratchet by extending ID_RESORT_CITIES.

Taxability matrix (per Idaho Code Title 63, Chapter 36):

- **General tangible personal property** -- TAXABLE at 6%
  (Idaho Code section 63-3619; section 63-3612 defines "sale";
  section 63-3616 defines "tangible personal property").
- **Clothing** -- TAXABLE. Idaho has **no clothing exemption** in
  Chapter 36; clothing and footwear are general tangible personal
  property and tax at 6%.
- **Groceries** -- TAXABLE at 6%. Idaho is one of the few states
  that fully taxes groceries at the state sales-tax rate. Chapter
  36 contains no grocery exemption; instead, the state offsets the
  burden with a separate **non-refundable income-tax credit**
  (commonly called the "Idaho grocery credit") under the state
  income-tax statutes -- not a reduction of the sales tax. The
  sales-tax engine therefore correctly applies the full 6% to
  unprepared food sales. (Source: Idaho State Tax Commission,
  "Idaho Food Tax Credit" guidance.)
- **Prescription drugs** -- EXEMPT per **Idaho Code section
  63-3622N** ("PRESCRIPTIONS"), which exempts drugs, hypodermic
  syringes, insulin, insulin syringes, artificial eyes,
  eyeglasses/component parts, contact lenses, hearing aids and
  hearing-aid parts/accessories when administered or distributed
  by a practitioner or purchased under a prescription.
- **Prepared food** -- TAXABLE. Idaho Code section 63-3612 includes
  the furnishing of meals among taxable retail sales; IDAPA
  35.01.02.041 ("FOOD, MEALS, OR DRINKS") confirms that the sale
  of food, meals, and drinks is taxable.
- **Digital goods** -- **TAXABLE in the dominant case** under
  **Idaho Code section 63-3616(b)**, which classifies as tangible
  personal property both (a) prewritten ("canned") computer
  software regardless of delivery method, and (b) digital music,
  digital books, digital videos, and digital games sold with a
  **permanent right to use**. **Excluded** from the TPP definition
  -- and therefore NOT taxable -- are (i) custom computer programs,
  (ii) computer software delivered electronically with no permanent
  right to use (i.e. subscription/SaaS / "remotely accessed"
  software), and (iii) digital media sold without a permanent
  right to use. The engine encodes ``digital_goods=is_taxable=True``
  for the dominant case (downloaded canned software + permanent-
  right digital media); the SaaS / subscription exception is
  documented in notes for follow-up if/when a sub-category split
  ships. (Note: this differs from the per-state research brief's
  initial sketch, which treated SaaS as taxable -- corrected here
  per direct reading of section 63-3616(b).)

Sales-tax holidays:

- **NONE.** Idaho has never enacted a recurring sales-tax holiday.
  Confirmed 2026-05-03 via the Idaho State Tax Commission's
  filing/holiday pages and multiple cross-references; no
  back-to-school, no disaster prep, no Energy Star holiday in
  Chapter 36 or in published commission guidance.

State maintainer: vacant -- see MAINTAINERS.md. Resort-city rate
loading and any future digital-goods sub-category split are the
most likely sources of follow-up work.

Disclaimer: this module computes tax; it does not provide legal or
tax advice. Verify against the Idaho State Tax Commission for any
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

# Idaho taxability matrix per Idaho Code Title 63, Chapter 36.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Idaho at the 6% state rate. Idaho "
            "Code Title 63, Chapter 36 contains no clothing exemption; "
            "clothing and footwear are general tangible personal "
            "property under Idaho Code section 63-3616 and tax at the "
            "rate set by section 63-3619. Idaho has no annual "
            "back-to-school sales-tax holiday. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=True,
        notes=(
            "Groceries ARE taxable in Idaho at the full 6% state sales-"
            "tax rate. Idaho is one of the few states that fully taxes "
            "groceries; Idaho Code Title 63, Chapter 36 contains no "
            "grocery exemption. The state offsets the burden with a "
            "separate non-refundable INCOME-TAX credit (the 'Idaho "
            "grocery credit', administered under the state income-tax "
            "statutes, NOT under Chapter 36) -- this is a credit on the "
            "state income-tax return, not a reduction of the sales tax "
            "owed at the register. The sales-tax engine therefore "
            "correctly applies the full 6% to unprepared-food sales. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT in Idaho per Idaho Code "
            "section 63-3622N ('PRESCRIPTIONS'). The exemption covers "
            "drugs, hypodermic syringes, insulin, insulin syringes, "
            "artificial eyes, eyeglasses and eyeglass component parts, "
            "contact lenses, hearing aids, and hearing-aid parts and "
            "accessories when administered or distributed by a "
            "practitioner OR purchased by/on behalf of an individual "
            "under a prescription or work order. Animal-use medical "
            "products are NOT covered (section 63-3622N expressly "
            "limits the exemption to use in humans). Calculation only "
            "-- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food / meals / drinks are TAXABLE in Idaho at the "
            "6% state rate. Idaho Code section 63-3612 (definition of "
            "'sale') includes the furnishing of meals among taxable "
            "retail sales; IDAPA 35.01.02.041 ('FOOD, MEALS, OR "
            "DRINKS') confirms the sale of food, meals, and drinks is "
            "taxable. Service charges added to the price of meals are "
            "part of the taxable sales price. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are TAXABLE in the dominant case under "
            "Idaho Code section 63-3616(b), which classifies as "
            "tangible personal property: (a) prewritten 'canned' "
            "computer software regardless of delivery method (download "
            "or physical media), and (b) digital music, digital books, "
            "digital videos, and digital games sold with a PERMANENT "
            "RIGHT to use. EXCLUDED from the TPP definition (and "
            "therefore NOT taxable) are: custom computer programs; "
            "remotely accessed software / SaaS where the user holds "
            "only license or subscription rights; the 'load and leave' "
            "installation method without transfer of tangible media; "
            "and digital media sold without a permanent right to use "
            "(subscription streaming etc.). The OpenSalesTax engine "
            "currently maps every 'digital_goods' line item to the "
            "dominant-case taxable rule; callers shipping SaaS or "
            "subscription-only digital media to Idaho should "
            "categorize those line items differently or apply an "
            "exemption until a sub-category split lands. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable in Idaho at "
            "6% per Idaho Code section 63-3619 (rate) and section "
            "63-3616 (definition of 'tangible personal property'). "
            "Calculation only -- not legal or tax advice."
        ),
    ),
}

# Statewide-rate effective date: October 1, 2006. The 6% rate took
# effect under House Bill 82 from the 2006 First Extraordinary
# Legislative Session, which raised the statewide rate from 5% to
# 6% (Idaho Code section 63-3619 as amended by Chapter 1, Section 18,
# 2006 1st Extra. Sess.).
_RATE_EFFECTIVE_FROM = dt.date(2006, 10, 1)


class Idaho:
    """Idaho state module (tier 1; statewide 6% rate only in v0.6)."""

    state_abbrev: str = "ID"
    state_name: str = "Idaho"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # Idaho has no SST upstream file; parse_rates returns the same row
    # regardless of source_file, so the loader must skip the cache-file
    # requirement for ID.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Idaho's statewide 6% rate plus resort-city overlays.

        ``source_file`` is intentionally ignored -- ID is non-SST and
        has no upstream file. Pass ``None`` from the loader.

        Resort-city local-option sales taxes (Idaho Code section
        50-1044) are sourced from
        :data:`opensalestax.states.id_data.ID_RESORT_CITIES`. Each
        resort city emits a city RateRow with
        ``parent_authority_name='Idaho'``.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Idaho",
            authority_type="state",
            rate_pct=Decimal("6.000"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )
        from opensalestax.states.id_data import ID_RESORT_CITIES

        for city_name, (rate, _zips) in sorted(ID_RESORT_CITIES.items()):
            yield RateRow(
                authority_name=city_name,
                authority_type="city",
                rate_pct=rate,
                effective_from=_RATE_EFFECTIVE_FROM,
                effective_to=None,
                parent_authority_name="Idaho",
            )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """Yield (state, city) boundaries for ID resort-city ZIPs.

        Idaho has no county-level sales tax. Resort cities under
        Idaho Code section 50-1044 emit state + city BoundaryRows
        for each covered ZIP. ZIPs not in any resort city get
        state-only bindings via the ZCTA loader fallback (which
        matches the user-facing rate of 6% statewide for
        non-resort-city addresses).
        """
        del source_file, version_label
        from opensalestax.states.id_data import ID_RESORT_CITIES

        for city_name, (_rate, zips) in sorted(ID_RESORT_CITIES.items()):
            for zip5 in sorted(zips):
                yield BoundaryRow(
                    authority_name="Idaho",
                    authority_type="state",
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
        """Return Idaho's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases consumed by the engine in v0.6.

        Resort-city local-option taxes (section 50-1044) and the
        digital-goods sub-category split (SaaS vs. permanent-right
        canned software) are documented in this module's docstring
        and ``specs/research/references.md`` for future feature work.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Idaho has no annual sales-tax holidays.

        Confirmed 2026-05-03 against the Idaho State Tax Commission's
        filing/holiday pages: there is no back-to-school holiday, no
        disaster-prep holiday, no Energy Star holiday, and no other
        recurring exemption window in Idaho Code Title 63, Chapter
        36 or in published commission guidance. Returns an empty
        iterator for every year.
        """
        del year
        return iter(())

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return ID's shipping rule.

        Separately stated freight / delivery charges are exempt;
        bundled freight is taxable as part of the sales price.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.EXEMPT_IF_SEPARATELY_STATED,
            citation="IDAPA 35.01.02.045",
        )


_PROTOCOL_CHECK: StateModule = Idaho()
del _PROTOCOL_CHECK

IDAHO = register(Idaho())
