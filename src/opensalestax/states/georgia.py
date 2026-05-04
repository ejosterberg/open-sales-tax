# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Georgia state module (tier 1).

Georgia (GA) is a Streamlined Sales Tax full member state (full
membership effective 2011-07-01 after associate membership
effective 2011-01-01). The statewide general sales-tax rate is
**4.0%** per O.C.G.A. section 48-8-30, one of the lower
state-only rates in the United States. The combined state +
local rate at any given GA address typically falls between **7%
and 9%** depending on the stack of county and special-district
taxes layered on top.

Local-jurisdiction model:

- **Counties** levy a 1% Local Option Sales Tax (LOST) under
  O.C.G.A. section 48-8-80 et seq., plus optional 1% Special
  Purpose Local Option Sales Tax (SPLOST) under section 48-8-110
  et seq., and other optional layers including Educational
  SPLOST (ELOST) under section 48-8-141 et seq., Homestead
  Option Sales Tax (HOST) under section 48-8-100 et seq., and
  Transportation SPLOST (TSPLOST) under section 48-8-240 et seq.
- **City of Atlanta** levies the Municipal Option Sales Tax
  (MOST) under section 48-8-200 et seq.
- These local layers stack; a typical county yields LOST + a
  SPLOST + an ELOST for a 3% local addition; some metro counties
  add HOST and/or TSPLOST for as much as 5% local on top of the
  state's 4%.

The GA SST rate file uses these jurisdiction-type codes (column
2), validated against ``GAR2026Q2FEB19.csv``:

- ``45`` = state (single row carrying 0.04 / 4.0%)
- ``00`` = county (LOST + SPLOST + ELOST + HOST stack folded
  into a single per-county figure)
- ``01`` = city / local (e.g., the City of Atlanta MOST)
- ``63`` = special district (TSPLOST regional districts and the
  MARTA district)

The GA file's distribution -- 1 state row, 432 county rows
(159 GA counties times historical effective-date ranges), 12
city rows, 4 special-district rows -- matches the published GA
DOR rate-chart structure. Most GA local taxation lives in the
``00`` (county) rows because the bulk of GA local-option
taxation is county-level rather than municipal.

Taxability matrix (per O.C.G.A. Title 48, Chapter 8):

- **General tangible personal property** -- TAXABLE at 4% per
  O.C.G.A. section 48-8-30.
- **Clothing** -- TAXABLE year-round. Georgia has no general
  clothing exemption. The annual back-to-school sales-tax
  holiday that previously exempted clothing under $100 was
  **last in effect in 2016**; the General Assembly has not
  re-enacted any sales-tax holiday since (per the GA DOR press
  releases history; see also GBPI, 11alive, and Tax Foundation
  reporting cited in ``specs/research/references.md``).
- **Groceries (food and food ingredients for off-premises
  consumption)** -- exempt **at the state level** (the 4%
  state portion) per O.C.G.A. section 48-8-3(57). The exemption
  expressly does **NOT** apply to local sales and use taxes:
  "the exemption provided for in this paragraph shall not apply
  to any local sales and use tax levied or imposed at any time"
  (with a narrow exception for counties imposing the equalized
  homestead-option tax under section 48-8-104). Most GA
  groceries therefore bear ~3% local sales tax even though the
  4% state portion is exempt.

  This module marks groceries ``is_taxable=False`` consistent
  with the engine's single-combined-rate evaluation; a future
  per-jurisdiction taxability override would let us model the
  state-vs-local split precisely (mirrors the Louisiana
  precedent in ``louisiana.py``). Until that lands, the engine
  will under-collect on GA grocery line items by the local
  portion (~3%); the API disclaimer covers this.
- **Prescription drugs** -- exempt per O.C.G.A. section
  48-8-3(54). Note that the GA SST rate file column 6 (drug
  rate) is ``0`` for the state-base row (``13,45,13,0.04,0.04,
  0,0,...``), confirming the state-level drug exemption in the
  upstream data.
- **Prepared food (restaurant meals, hot prepared food,
  ready-to-eat deli items)** -- TAXABLE at the full combined
  rate. The food-for-home-consumption exemption in section
  48-8-3(57) explicitly excludes prepared food.
- **Digital goods (specified digital products, other digital
  goods, digital codes)** -- TAXABLE at the same 4% state rate
  as tangible personal property **effective 2024-01-01** per
  Ga. Comp. R. & Regs. R. 560-12-2-.118 (adopted under SUT
  2024-001) implementing H.B. 170, Laws 2023. The tax requires
  the End User to receive a permanent right of use; SaaS and
  similar conditional-payment models remain non-taxable as of
  this writing.

Sales-tax holidays -- **NONE in 2026 or any year after 2016**.

Georgia's last sales-tax holiday occurred in 2016 (clothing /
school supplies / computers on July 30-31 and energy-efficient
products on September 30 - October 2). The General Assembly let
the holiday expire after 2016 and has not re-enacted it as of
the 2025 Regular Session (S.B. 115, S.B. 527, S.B. 555 each
introduced in 2024-2025 sessions but did not pass). The GA DOR
"2016 Sales Tax Holidays" press release remains the most recent
official holiday notice.

This module returns an empty iterable from ``holidays_for(year)``
for **every** year. Should the General Assembly re-authorize a
holiday in a future session, a maintainer must explicitly add
the year's data; the empty iterable is intentional regression
protection (the 2024-2025 reauthorization bills failed and the
project does not pre-encode speculative future legislation).

State maintainer: vacant -- see MAINTAINERS.md.

DISCLAIMER: This module is calculation infrastructure, not tax
advice. Maintainers and users are responsible for verifying
current GA DOR guidance and jurisdiction-specific ordinances
before relying on these rules in production.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from pathlib import Path

from opensalestax.data.sst import open_sst_csv
from opensalestax.data.sst_parser import parse_boundary_csv, parse_rates_csv
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

# ---------------------------------------------------------------------------
# GA-specific SST jurisdiction-type code mapping
# ---------------------------------------------------------------------------
# Validated against ``GAR2026Q2FEB19.csv`` (449 rows): 1 row of type 45,
# 432 rows of type 00, 12 rows of type 01, 4 rows of type 63. Same scheme
# as MN and WI; documented separately so that any future divergence (a
# new GA-specific code) can be encoded without affecting other states.
_JURISDICTION_TYPE: dict[str, str] = {
    "45": "state",
    "00": "county",
    "01": "city",
    "63": "district",
}

# Static taxability matrix per O.C.G.A. Title 48, Chapter 8.
# Categories not listed default to taxable (the engine's behavior).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Georgia year-round at the full "
            "combined state + local rate per O.C.G.A. section 48-8-30. "
            "Georgia has no general clothing exemption. The back-to-"
            "school sales-tax holiday that previously exempted "
            "clothing under $100 was last in effect in 2016 (per "
            "Ga. Comp. R. and Regs. R. 560-12-2-.110 historical "
            "applicability and the GA DOR 2016 Sales Tax Holidays "
            "press release); the General Assembly has not re-enacted "
            "any sales-tax holiday since. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food and food ingredients sold to natural persons for "
            "off-premises consumption are EXEMPT from the Georgia "
            "state 4% sales tax per O.C.G.A. section 48-8-3(57). The "
            "exemption expressly does NOT extend to LOCAL sales and "
            "use taxes (LOST, SPLOST, ELOST, HOST, TSPLOST, MOST), "
            "which generally still apply to grocery purchases unless "
            "the county imposes the equalized homestead-option tax "
            "under section 48-8-104. v0.7 marks groceries non-taxable "
            "at the combined-rate level consistent with the engine's "
            "single-rate-per-authority evaluation; future per-"
            "jurisdiction taxability overrides will model the state-"
            "vs-local split precisely (mirrors the Louisiana approach "
            "for state-only-exempt categories). Until then the engine "
            "under-collects on GA groceries by the local portion. "
            "Calculation only -- not legal or tax advice."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes=(
            "Prescription drugs are EXEMPT from Georgia sales and "
            "use tax per O.C.G.A. section 48-8-3(54). The exemption "
            "is reflected in the SST rate file, where GA's state-"
            "base row carries 0 in the drug-rate column. Calculation "
            "only -- not legal or tax advice."
        ),
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes=(
            "Prepared food (restaurant meals, hot prepared food, "
            "ready-to-eat deli items) is TAXABLE at the full Georgia "
            "combined state + local rate. The food-for-home-"
            "consumption exemption in O.C.G.A. section 48-8-3(57) "
            "explicitly excludes prepared food, drugs, and over-the-"
            "counter drugs. Calculation only -- not legal or tax "
            "advice."
        ),
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Specified digital products, other digital goods, and "
            "digital codes sold to an End User who receives a "
            "permanent right of use are TAXABLE in Georgia at the "
            "same rate as tangible personal property effective "
            "2024-01-01 per Ga. Comp. R. and Regs. R. 560-12-2-.118 "
            "(SUT 2024-001), implementing H.B. 170, Laws 2023, under "
            "O.C.G.A. section 48-8-30. Pre-2024 digital products "
            "were generally non-taxable in Georgia. Conditional-"
            "payment models (SaaS without a permanent right of use) "
            "remain non-taxable as of 2026. Calculation only -- not "
            "legal or tax advice."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes=(
            "General tangible personal property is TAXABLE in "
            "Georgia at the 4% state rate per O.C.G.A. section "
            "48-8-30, plus stacked local sales taxes (LOST, SPLOST, "
            "ELOST, HOST, TSPLOST, MOST) authorized under O.C.G.A. "
            "sections 48-8-80 et seq., 48-8-100 et seq., 48-8-110 "
            "et seq., 48-8-141 et seq., 48-8-200 et seq., and "
            "48-8-240 et seq. Combined GA rates typically fall "
            "between 7% and 9%. Calculation only -- not legal or "
            "tax advice."
        ),
    ),
}


class Georgia:
    """Georgia state module (tier 1; SST member)."""

    state_abbrev: str = "GA"
    state_name: str = "Georgia"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """Parse a Georgia SST rates file into normalized RateRow records.

        Skips rows whose jurisdiction-type isn't in the known mapping
        -- they won't be loaded into the rate engine but the rest of
        the file is still ingested. Future quarters that introduce a
        new GA-specific type code will surface as gaps in coverage
        rather than silent miscalculations.
        """
        del version_label  # per-row version comes from the data_version row
        for record in parse_rates_csv(open_sst_csv(source_file)):
            authority_type = _JURISDICTION_TYPE.get(record.jurisdiction_type)
            if authority_type is None:
                continue
            yield RateRow(
                authority_name=_authority_name(record.jurisdiction_code, authority_type),
                authority_type=authority_type,  # type: ignore[arg-type]
                rate_pct=record.general_rate * 100,  # SST stores 0.04, we want 4.00
                effective_from=record.effective_from,
                effective_to=record.effective_to,
                parent_authority_name="Georgia" if authority_type != "state" else None,
            )

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]:
        """Parse a Georgia SST boundary file into normalized BoundaryRow records.

        Emits multiple bindings per ZIP (state always; county / city /
        district where the SST file records them) using both type-z
        ZIP-wide records and type-4 ZIP+4-precision records, matching
        the modern SstStateModule.parse_boundaries logic. Without
        this, Atlanta 30303 returned only state + Fulton County
        (7.0%) and missed the 1.9% Atlanta city tax (which lives in
        type-4 records' city_code column).
        """
        del version_label
        from opensalestax.data.zip_state import zip_in_state
        from opensalestax.states._sst_base import _expand_zip5_range

        seen: set[tuple[str, str, str, str | None, str | None]] = set()
        for record in parse_boundary_csv(open_sst_csv(source_file)):
            if record.record_type not in {"z", "4"}:
                continue
            if not record.zip5_low:
                continue
            zip4_low = record.zip4_low if record.record_type == "4" else None
            zip4_high = record.zip4_high if record.record_type == "4" else None

            for zip5 in _expand_zip5_range(record.zip5_low, record.zip5_high):
                if zip_in_state(zip5, "GA") is False:
                    continue
                bindings: list[tuple[str, str]] = [("state", "Georgia")]
                if record.county_fips:
                    bindings.append(
                        ("county", _authority_name(record.county_fips, "county"))
                    )
                if record.city_code:
                    bindings.append(("city", _authority_name(record.city_code, "city")))
                if record.district_code:
                    bindings.append(
                        ("district", _authority_name(record.district_code, "district"))
                    )
                for authority_type, authority_name in bindings:
                    key = (authority_type, authority_name, zip5, zip4_low, zip4_high)
                    if key in seen:
                        continue
                    seen.add(key)
                    yield BoundaryRow(
                        authority_name=authority_name,
                        authority_type=authority_type,  # type: ignore[arg-type]
                        zip5=zip5,
                        zip4_low=zip4_low,
                        zip4_high=zip4_high,
                    )

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return GA's taxability rule for ``item_category`` on ``effective_date``.

        ``effective_date`` is accepted for the Protocol but v0.7
        treats every rule as currently in force; pre-2024 callers
        evaluating digital goods will get the wrong answer (digital
        goods became taxable 2024-01-01) and must be revisited when
        the legislative-history layer lands.
        """
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No SpecialCase entries tracked for GA in v0.7.

        The state-vs-local grocery exemption split is documented
        in the module docstring and in the grocery TaxabilityRule
        notes; per-jurisdiction taxability is reserved for a future
        engine feature paralleling LA's parish work.
        """
        return iter(())

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Georgia has no annual sales-tax holidays.

        Georgia's last sales-tax holiday was in 2016 (clothing /
        school supplies / computers on July 30-31 and energy-
        efficient products on September 30 - October 2). The
        General Assembly let the holiday expire after 2016 and
        has not re-enacted one since. Reauthorization bills
        introduced in 2024-2025 (S.B. 115, S.B. 527, S.B. 555)
        did not pass. This method returns the empty iterable for
        every year intentionally; should a future session re-
        authorize a holiday, a maintainer must explicitly add the
        year's data (no extrapolation -- legislation is required).
        """
        del year
        return iter(())


def _authority_name(code: str, authority_type: str) -> str:
    """Build a deterministic authority name from a SST jurisdiction code.

    Phase 1 doesn't have a code -> human-name lookup table (that's
    Phase 5 work). Names follow ``GA-<TYPE>-<CODE>`` so the engine
    can group authorities consistently and integrators can join
    against external code lists when needed.
    """
    if authority_type == "state":
        return "Georgia"
    return f"GA-{authority_type}-{code}"


# Compile-time check + register
_PROTOCOL_CHECK: StateModule = Georgia()
del _PROTOCOL_CHECK

GEORGIA = register(Georgia())
