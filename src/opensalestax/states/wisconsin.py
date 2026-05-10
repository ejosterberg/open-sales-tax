# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Wisconsin state module (tier 1).

WI is a Streamlined Sales Tax member. State base rate is 5.0%
(confirmed via the WI DOR and the SST quarterly file, which
shows ``55,45,55,0.05,0.05,0.05,0.05,19800101,99991231`` --
the 5.0% state rate effective since 1980).

WI's SST rate file uses the standard
:data:`~opensalestax.states._sst_base._DEFAULT_JURISDICTION_TYPE`
mapping (45=state, 00=county, 01=city, 63=district), so the
inherited :class:`SstStateModule` parsers handle the quarterly
file unmodified.

Two notable WI rate-file properties handled by the shared SST
parser:

- **Open-end date sentinel is ``99991231``** (not MN's ``29991231``).
  The shared SST parser handles both via
  :data:`~opensalestax.data.sst_parser.NO_END_DATE_SENTINELS`.
- **Rate file is plain CSV, not ZIP.** Filename pattern is
  ``WIR<...>.csv`` rather than ``WIR<...>.zip``.

iter-63 audit: WI was historically wired with a hand-rolled
``parse_boundaries`` that emitted only state + county bindings
and dropped ``4`` (ZIP+4) records entirely. Milwaukee City's 2%
sales tax (WI Act 12, effective 2024-01-01, encoded in the SST
rate file as ``55,01,53000,0.02,...``) loaded into the rate
table but was unreachable because the boundary parser never
linked ZIP 53202 -> Milwaukee City. Same root cause for several
counties whose binding was carried by ``4`` records (Eau Claire,
Rock, Columbia). Switching WI to inherit from
:class:`SstStateModule` picks up the modern boundary parser,
which emits state + county + city + district bindings, expands
ZIP5 ranges, handles ``z``/``4``/``a`` records, and applies the
cross-border ZIP filter -- consistent with every other SST
member state.

Taxability deviations from MN -- the architectural keystone for
tier-1 contrast:

- **Clothing** -- TAXABLE in WI (Wisconsin has no clothing exemption).
  This is the single most-cited contrast with MN.
- **Groceries** -- non-taxable (food and food ingredients exempt).
- **Prescription drugs** -- non-taxable.
- **Prepared food** -- taxable.
- **Digital goods** -- taxable.

State maintainer: vacant -- see MAINTAINERS.md.
"""

from __future__ import annotations

from opensalestax.states._sst_base import SstStateModule
from opensalestax.states.protocol import (
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# Wisconsin taxability matrix per Wisconsin Statutes ch. 77.
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in Wisconsin -- WI has no clothing exemption. "
            "(Contrast with MN, where clothing is non-taxable.)"
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes="Food and food ingredients are non-taxable in WI (Wis. Stat. 77.54(20n)).",
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable in Wisconsin.",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in Wisconsin.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes="Digital goods are taxable in Wisconsin.",
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}


class Wisconsin(SstStateModule):
    """Wisconsin state module (tier 1, SST member).

    Subclass of :class:`SstStateModule` that overrides only the
    metadata (state abbrev / name / FIPS), the taxability matrix,
    and the city-friendly-name lookup. Rate parsing, boundary
    parsing, special cases, and the empty-holidays default are
    all inherited.

    See module docstring for the iter-63 audit that prompted the
    conversion from a hand-rolled parser.
    """

    state_abbrev: str = "WI"
    state_name: str = "Wisconsin"
    state_fips: str = "55"
    sst_member: bool = True
    has_sales_tax: bool = True
    tier: StateTier = 1

    taxability: dict[str, TaxabilityRule] = _TAXABILITY

    def _authority_name(self, code: str, authority_type: str) -> str:
        """Use the curated WI city-name table; fall back to placeholder."""
        from opensalestax.states.wi_names import city_name as _wi_city

        if authority_type == "city":
            friendly = _wi_city(code)
            if friendly is not None:
                return friendly
        return super()._authority_name(code, authority_type)


_PROTOCOL_CHECK: StateModule = Wisconsin()
del _PROTOCOL_CHECK

WISCONSIN = register(Wisconsin())
