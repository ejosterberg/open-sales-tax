# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Louisiana state module (tier 1, non-SST).

LA is **not** a Streamlined Sales Tax member. The current statewide
rate is **5.000%** effective **2025-01-01**, established by Act 11
of the 2024 3rd Extraordinary Session (HB 10). The 5% rate is a
**temporary** increase from the prior 4.45% combined statutory rate;
under the same Act it is scheduled to step down to **4.75% on
2030-01-01** absent further legislative action. The 5% rate is the
sum of multiple statutory layers: La. R.S. 47:302 (the original 2%),
47:321 (an additional 1%), 47:321.1 (a temporary 0.45% historically
plus the new Act-11 increment), 47:331 (an additional 0.97%, of
which a portion is dedicated), and 47:332 (a 0.03% Tourism Promotion
levy). LDR publishes the combined 5% headline rate; this module
encodes that headline rate.

------------------------------------------------------------------
PARISH-LEVEL TAXATION IS **NOT MODELED** IN v0.7
------------------------------------------------------------------

Louisiana's local sales tax landscape is uniquely fragmented in the
United States. Each of the **64 Louisiana parishes** independently
administers its own local sales and use tax (and often the
sub-municipal and special-district taxes layered on top) through a
parish Sales and Use Tax Commission or comparable body, under La.
R.S. 47:337.1 et seq. ("Uniform Local Sales Tax Code"). Combined
state + parish + municipal + special-district rates can exceed
**12%** in some inhabited corners of LA -- among the highest
combined sales-tax rates in the United States.

LA has taken **partial** consolidation steps:

- The **Louisiana Sales and Use Tax Commission for Remote Sellers**
  (La. R.S. 47:339.1, established 2018) collects state + local on
  remote-seller transactions -- but does **not** unify in-state
  rates.
- The **Parish E-File** portal lets in-state retailers file most
  parishes through one online interface; the underlying rates and
  ordinances remain parish-specific.
- A 2026 combined state-and-parish return form is rolling out per
  LDR -- still does not change rate authority.

**v0.7 ships the state 5% portion only.** Per-parish, per-municipal,
and per-special-district rates require per-parish data ingestion
that does not exist as a single machine-readable feed comparable to
SST. See `specs/decisions/05-louisiana-parishes.md` for the full
trade-off analysis (Options A / B / C considered; Option A --
state-only with prominent deferral -- chosen for v0.7).

------------------------------------------------------------------

Taxability matrix (state portion only -- parishes generally tax
groceries / residential utilities / prescription drugs differently
from the state):

- **Clothing** -- TAXABLE year-round (no clothing exemption in
  Louisiana; the back-to-school holiday that previously exempted
  clothing has been suspended since 2018 and was NOT reauthorized
  in the 2025 Regular Session -- HB 551 died on 2025-06-12).
- **Groceries (food sold for preparation and consumption in the
  home)** -- exempt from the **state 5%** per La. R.S. 47:305(D)
  (subdivisions covering bakery products, fresh fruit/vegetables,
  packaged foods requiring further preparation; renumbered in 2025
  by Act 11 reorganization). The exemption is preserved by La.
  Const. Art. VII section 2.2 against legislative repeal of the
  state portion. **Parishes generally still tax groceries unless
  the parish ordinance also exempts them.** This module marks
  groceries ``is_taxable=False`` consistent with the engine's
  single-combined-rate evaluation; a future per-jurisdiction
  taxability override would let us model the parish deviation
  precisely.
- **Prescription drugs** -- exempt from the state 5% per La. R.S.
  47:305(D) and La. R.S. 47:305.10 (drugs prescribed by physician
  or dentist). Constitutional protection per Art. VII section 2.2.
  Parish treatment varies; La. R.S. 47:337.11.1 conditions parish
  taxation of prescription drugs on local-board procedures.
- **Residential utilities (steam, water, electric power, natural
  gas)** -- exempt from the state 5% (the residential carve-out
  to La. R.S. 47:305(D)(1)(g), which exempts non-residential
  utilities; residential is exempted by separate provision plus
  the La. Const. Art. VII section 2.2 protection). Mapped in the
  engine under no current category; documented here for the
  maintainer who eventually adds a ``residential_utilities``
  category to the engine.
- **Prepared food** -- TAXABLE at the state 5% (the food-at-home
  exemption explicitly excludes "prepared meals furnished to and
  consumed by employees of restaurants" and similar). Most LA
  parishes layer additional restaurant / hospitality taxes that
  are administered locally and not modeled here.
- **Digital goods (digital audiovisual works, digital audio,
  digital books, digital games, digital codes, digital
  periodicals, and remotely accessed software / SaaS)** --
  TAXABLE at the state 5% effective **2025-01-01** per Act 10 of
  the 2024 3rd Extraordinary Session (HB 8) and the LDR Digital
  Products Guidance (LDR document 11.20.25). Pre-2025 digital
  products were generally non-taxable in Louisiana; agents
  encountering pre-2025 calculations must use a different rule
  set. The current module encodes the **post-2025-01-01** state.

Sales-tax holiday(s) in 2026:

LA has historically had three annual sales-tax holidays:

1. **Annual Louisiana Sales Tax Holiday** (originally R.S. 47:305.54,
   "Annual" general back-to-school / general-merchandise) --
   **SUSPENDED** since 2018 budget actions; reauthorization HB 551
   (2025 Reg. Sess.) **died** on 2025-06-12. NOT in effect for 2026.
2. **Annual Louisiana Hurricane Preparedness Sales Tax Holiday**
   (R.S. 47:305.58) -- SUSPENDED; no 2026 reauthorization. NOT in
   effect for 2026.
3. **Annual Louisiana Second Amendment Weekend Holiday** (R.S.
   47:305.62) -- **ACTIVE**. The statute defines the holiday as
   "the first consecutive Friday through Sunday of September" each
   calendar year, exempting firearms, ammunition, and hunting
   supplies (including archery, accessories, apparel, footwear,
   bags, binoculars, tools, and related gear) for personal use.
   The exemption applies to **state AND local** ("levied by the
   state of Louisiana and its political subdivisions"). No
   per-item dollar cap. Excluded: animal feed, ATVs, airboats,
   float tubes, business-use purchases. LDR confirmed 2025 dates
   (Sept 5-7, 2025) per RIB 25-017; 2026 dates per the statutory
   formula are **September 4-6, 2026** (Sept 1, 2026 falls on a
   Tuesday, so the first Friday is September 4).

This module encodes the Second Amendment Weekend Holiday for 2026
as the ONLY currently-active LA holiday; subsequent years require
explicit data updates per the project convention (no extrapolation
of statutory dates -- legislatures occasionally amend or suspend).

Loading: the v0.2 loader treats ``Louisiana.parse_rates`` as
"self-seeded" -- it returns the single statewide row and ignores
the source-file argument. Use ``opensalestax data load --state LA
--version v0.7-statewide`` to insert it.

State maintainer: vacant -- see MAINTAINERS.md. LA's per-parish
local-tax rollup is the natural next contribution and the most
impactful single piece of state-buildout work remaining: 64 parish
commissions, each with their own rate and ordinance schedule, plus
the Constitutional Amendment 2 (passed November 2025) and ongoing
LDR consolidation work that may further reshape the local
landscape.

DISCLAIMER: This module is calculation infrastructure, not tax
advice. Maintainers and users are responsible for verifying current
LDR guidance and parish-commission ordinances before relying on
these rules in production. Parish portions are NOT modeled in v0.7
and a v0.7 caller will under-collect tax on every LA address; see
the module docstring section above and `specs/decisions/05-louisiana-parishes.md`.
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

# Louisiana taxability matrix per La. R.S. Title 47 (state portion only).
# Parish taxability varies independently and is NOT captured here -- see
# `specs/decisions/05-louisiana-parishes.md`.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Louisiana year-round at the state "
            "5% rate per La. R.S. 47:301 et seq. There is no general "
            "clothing exemption; the prior back-to-school holiday "
            "(R.S. 47:305.54) has been suspended since 2018 and was "
            "NOT reauthorized in the 2025 Regular Session (HB 551 "
            "died on 2025-06-12). Calculation only -- not tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food sold for preparation and consumption in the home "
            "(bakery products, fresh fruit and vegetables, packaged "
            "foods requiring further preparation) is exempt from the "
            "Louisiana state 5% sales tax per La. R.S. 47:305(D), with "
            "constitutional protection under La. Const. Art. VII "
            "section 2.2. PARISH AND LOCAL SALES TAXES generally STILL "
            "APPLY to groceries unless the specific parish ordinance "
            "also exempts them; v0.7 does not model per-jurisdiction "
            "taxability overrides and does not model parish rates at "
            "all (see specs/decisions/05-louisiana-parishes.md). "
            "Calculation only -- not tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Drugs prescribed by a licensed physician or dentist are "
            "exempt from the Louisiana state 5% sales tax per La. R.S. "
            "47:305(D) and La. R.S. 47:305.10, with constitutional "
            "protection under La. Const. Art. VII section 2.2. Parish "
            "treatment varies under La. R.S. 47:337.11.1 (parish "
            "taxation of prescription drugs is conditioned on parish "
            "local-board procedures). Calculation only -- not tax "
            "advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot food, ready-to-eat "
            "deli items) is taxable at the Louisiana state 5% rate; "
            "the food-for-home-consumption exemption in La. R.S. "
            "47:305(D) does not extend to prepared food. Most "
            "Louisiana parishes layer additional restaurant or "
            "hospitality taxes that are administered locally and not "
            "modeled in this module. Calculation only -- not tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital products (digital audiovisual works, digital "
            "audio, digital books, digital games, digital codes, "
            "digital periodicals, and remotely accessed software / "
            "SaaS) are TAXABLE at the Louisiana state 5% rate "
            "effective 2025-01-01 per Act 10 of the 2024 3rd "
            "Extraordinary Session (HB 8) and the LDR Digital Products "
            "Guidance (LDR document 11.20.25). Pre-2025 digital "
            "products were generally non-taxable in Louisiana. "
            "Calculation only -- not tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is taxable at the "
            "Louisiana state 5% rate per La. R.S. 47:301 et seq. "
            "(combined statutory layers under sections 47:302, "
            "47:321, 47:321.1, 47:331, 47:332). The 5% rate is "
            "TEMPORARY per Act 11 of the 2024 3rd Extraordinary "
            "Session (HB 10) -- effective 2025-01-01 through "
            "2029-12-31, then scheduled to step down to 4.75% on "
            "2030-01-01 absent further legislative action. v0.7 does "
            "NOT model parish, municipal, or special-district rates "
            "(see specs/decisions/05-louisiana-parishes.md). "
            "Calculation only -- not tax advice."
        ),
    ),
}

# Louisiana's current 5% state portion took effect 2025-01-01 under
# Act 11 of the 2024 3rd Extraordinary Session (HB 10).
_RATE_EFFECTIVE_FROM = dt.date(2025, 1, 1)

# The 5% rate sunsets 2029-12-31 per Act 11; on 2030-01-01 it is
# scheduled to step down to 4.75%. We encode the effective_to as
# 2029-12-31 so the v0.7 row correctly self-expires; a future module
# update will add the 4.75% successor row when 2030 approaches and
# the legislature has confirmed (or amended) the step-down.
_RATE_EFFECTIVE_TO = dt.date(2029, 12, 31)

# Headline statewide rate per LDR FAQ "What is the state sales tax rate?"
# (https://revenue.la.gov/tax-education-and-faqs/faqs/sales-tax-reform/
# what-is-the-state-sales-tax-rate/), retrieved 2026-05-03.
_RATE_PCT = Decimal("5.000")


class Louisiana:
    """Louisiana state module (tier 1; statewide rate only in v0.7).

    PARISH-LEVEL TAXATION IS NOT MODELED in v0.7. See module
    docstring for the full deferral rationale and
    `specs/decisions/05-louisiana-parishes.md` for the trade-off
    analysis.
    """

    state_abbrev: str = "LA"
    state_name: str = "Louisiana"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require
    # a cached upstream file. LA is not an SST member and has no
    # quarterly upstream file; parse_rates returns the same
    # statewide row regardless of source_file.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield Louisiana's statewide 5.000% rate.

        ``source_file`` is intentionally ignored -- LA has no SST
        upstream file. Pass ``None`` from the loader. The 5.000%
        rate is per Act 11 of the 2024 3rd Extraordinary Session
        (HB 10) and is encoded with ``effective_to=2029-12-31`` so
        it self-expires when the statutory sunset takes effect.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="Louisiana",
            authority_type="state",
            rate_pct=_RATE_PCT,
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=_RATE_EFFECTIVE_TO,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundaries shipped in v0.7.

        LA's 64 parishes plus their municipal and special-district
        sub-jurisdictions are not loaded; see the module docstring
        and ``specs/decisions/05-louisiana-parishes.md``.
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return LA's state-portion taxability rule for ``item_category``.

        Note: parishes commonly tax groceries / residential
        utilities / prescription drugs even though the state does
        not. v0.7 only encodes the state-portion answer.
        """
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No SpecialCase entries tracked for LA in v0.7.

        The parish-administration topology is documented in the
        module docstring and decision doc; the SpecialCase API is
        reserved for engine-consumed quirks (Phase 5+).
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Louisiana's annual Second Amendment Weekend Holiday.

        Per La. R.S. 47:305.62 ("Annual Louisiana Second Amendment
        Weekend Holiday Act"), the exemption applies on **the first
        consecutive Friday through Sunday of September** each
        calendar year. The exemption applies to state AND local
        sales/use tax ("taxes levied by the state of Louisiana and
        its political subdivisions") on firearms, ammunition, and
        hunting supplies for personal use. No per-item dollar cap.
        Excluded items: animal feed, ATVs, airboats, float tubes,
        business-use purchases.

        For 2026 the first Friday of September is **September 4**
        (Sept 1 is a Tuesday), so the holiday runs September 4-6,
        2026.

        Two other LA holidays (back-to-school under R.S. 47:305.54
        and hurricane preparedness under R.S. 47:305.58) have been
        suspended since 2018 and were NOT reauthorized in the 2025
        Regular Session (HB 551 died on 2025-06-12). They are
        intentionally NOT yielded here.

        Subsequent years require an explicit data update; do not
        extrapolate the statutory formula -- the legislature has a
        documented history of suspending or amending these
        holidays in budget cycles.
        """
        if year != 2026:
            return iter(())
        return iter(
            [
                HolidayWindow(
                    name="Louisiana Second Amendment Weekend Holiday (2026)",
                    starts_on=dt.date(2026, 9, 4),
                    ends_on=dt.date(2026, 9, 6),
                    applicable_categories=(
                        "firearms",
                        "ammunition",
                        "hunting_supplies",
                    ),
                    max_amount_per_item=None,
                    notes=(
                        "La. R.S. 47:305.62 (Annual Louisiana Second "
                        "Amendment Weekend Holiday Act). Three-day "
                        "exemption from STATE 5% AND any applicable "
                        "parish/local sales tax on firearms (shotguns, "
                        "rifles, pistols, revolvers, handguns), "
                        "ammunition, and hunting supplies including "
                        "archery, pirogues, accessories, apparel, "
                        "shoes, bags, binoculars, and tools. NO "
                        "per-item dollar cap. Excludes animal feed, "
                        "ATVs, airboats, float tubes, and business-use "
                        "purchases. Calculation only -- not tax "
                        "advice."
                    ),
                ),
            ]
        )

    def shipping_rule_set(self) -> ShippingRuleSet:
        """Return LA's shipping rule (state portion only).

        Louisiana treats delivery charges as part of the "sales
        price" when the underlying item is taxable; shipping
        follows the taxability of the goods. Practitioner default
        for typical e-commerce.

        PARISH-LEVEL CAVEAT: Louisiana's ~64 parishes administer
        their own sales taxes independently (see module docstring
        and ``specs/decisions/05-louisiana-parishes.md``); parish
        treatment of shipping may diverge from the state rule. v1
        P1 ships only the state-portion shipping rule -- callers
        with parish exposure should consult local ordinances.
        """
        return ShippingRuleSet(
            default_rule=ShippingRule.CONDITIONAL,
            citation="LA RS 47:301(13)",
        )


_PROTOCOL_CHECK: StateModule = Louisiana()
del _PROTOCOL_CHECK

LOUISIANA = register(Louisiana())
