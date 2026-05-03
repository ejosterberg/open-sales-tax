# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""California state module (tier 1, non-SST).

CA is **not** a Streamlined Sales Tax member, so no quarterly SST
file. The state base rate is **7.25%** (the highest statewide rate
in the US, per CDTFA -- the California Department of Tax and Fee
Administration).

CA's rate landscape is famously complex: ~1,700 district taxes
overlay the statewide rate, taking combined rates from 7.25% to as
high as 10.75% in some cities. **Phase 2 ships the statewide rate
only;** district-rate loading from CDTFA's downloadable lookup
table is a v0.3 priority.

Taxability matrix:

- **Clothing** -- TAXABLE (no exemption like MN's)
- **Groceries** -- NON-taxable for "food products for human
  consumption" sold for off-premise use (Cal. Rev. & Tax Code §
  6359). Hot prepared food and restaurant meals are taxable.
- **Prescription drugs** -- NON-taxable (§ 6369).
- **Prepared food** -- taxable.
- **Digital goods** -- TAXABLE per AB 147 (2019) and subsequent
  CDTFA guidance.

Loading: the v0.2 loader treats ``California.parse_rates`` as
"self-seeded" -- it returns the single statewide row and ignores
the source-file argument. Use ``opensalestax data load --state CA
--version v0.2-statewide`` to insert it.

State maintainer: vacant -- see MAINTAINERS.md. CA is the highest-
impact state in the US; a maintainer who knows the CDTFA data
should pick this up.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from decimal import Decimal
from pathlib import Path

from opensalestax.states.protocol import (
    BoundaryRow,
    RateRow,
    SpecialCase,
    StateModule,
    StateTier,
    TaxabilityRule,
)
from opensalestax.states.registry import register

# California taxability matrix per Cal. Rev. & Tax Code (statewide rules).
_TAXABILITY: dict[str, TaxabilityRule] = {
    "clothing": TaxabilityRule(
        item_category="clothing",
        is_taxable=True,
        notes=(
            "Clothing IS taxable in California -- CA has no clothing "
            "exemption. (Many states do; CA does not.)"
        ),
    ),
    "groceries": TaxabilityRule(
        item_category="groceries",
        is_taxable=False,
        notes=(
            "Food products for human consumption (Cal. Rev. & Tax Code "
            "section 6359) are non-taxable in California when sold for "
            "off-premise use. Hot prepared food and restaurant meals "
            "are taxable."
        ),
    ),
    "prescription_drugs": TaxabilityRule(
        item_category="prescription_drugs",
        is_taxable=False,
        notes="Prescription drugs are non-taxable (Cal. Rev. & Tax Code section 6369).",
    ),
    "prepared_food": TaxabilityRule(
        item_category="prepared_food",
        is_taxable=True,
        notes="Prepared food is taxable in California.",
    ),
    "digital_goods": TaxabilityRule(
        item_category="digital_goods",
        is_taxable=True,
        notes=(
            "Digital goods are taxable in California per AB 147 (2019) "
            "and subsequent CDTFA guidance."
        ),
    ),
    "general": TaxabilityRule(
        item_category="general",
        is_taxable=True,
        notes="General tangible personal property is taxable.",
    ),
}

# Statewide effective date when the current 7.25% rate took effect.
_RATE_EFFECTIVE_FROM = dt.date(2017, 1, 1)


class California:
    """California state module (tier 1; statewide rate only in v0.2)."""

    state_abbrev: str = "CA"
    state_name: str = "California"
    sst_member: bool = False
    has_sales_tax: bool = True
    tier: StateTier = 1
    # The loader checks this attribute to decide whether to require
    # a cached upstream file. CA's parse_rates returns the same
    # statewide row regardless of source_file, so no file is needed.
    self_seeded: bool = True

    def parse_rates(self, source_file: Path | None, version_label: str) -> Iterable[RateRow]:
        """Yield California's statewide 7.25% rate.

        ``source_file`` is intentionally ignored -- CA has no SST
        upstream file. Pass ``None`` from the loader.
        """
        del source_file, version_label
        yield RateRow(
            authority_name="California",
            authority_type="state",
            rate_pct=Decimal("7.250"),
            effective_from=_RATE_EFFECTIVE_FROM,
            effective_to=None,
            parent_authority_name=None,
        )

    def parse_boundaries(
        self, source_file: Path | None, version_label: str
    ) -> Iterable[BoundaryRow]:
        """No boundaries shipped in v0.2.

        CA has too many ZIP/district mappings to hand-encode; loading
        these is the v0.3 priority once the CDTFA-driven loader
        lands.
        """
        del source_file, version_label
        return iter(())

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return CA's taxability rule for ``item_category``."""
        del effective_date
        return _TAXABILITY.get(item_category)

    def special_cases(self) -> Iterable[SpecialCase]:
        """No special cases tracked for CA in Phase 2."""
        return iter(())


_PROTOCOL_CHECK: StateModule = California()
del _PROTOCOL_CHECK

CALIFORNIA = register(California())
