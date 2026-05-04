# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""State-module Protocol and the data carriers it works with.

The architectural keystone of OpenSalesTax (constitution §4): every
US state is a Python module that conforms to :class:`StateModule`.
The core engine never knows or cares about specific states; it
loops over registered modules and asks each one for its data.

State modules MUST NOT import from ``opensalestax.core``,
``opensalestax.api``, or ``opensalestax.db``. The dependency arrow
points one way: ``api -> core -> states -> db.models``. State
modules can use the ORM models for type hints; they cannot
execute queries.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import Iterable
from dataclasses import dataclass, field
from decimal import Decimal
from pathlib import Path
from typing import Literal, Protocol, runtime_checkable

# ---------------------------------------------------------------------------
# Tier semantics
# ---------------------------------------------------------------------------
# tier 0 = unsupported (state has no module; e.g. CA, TX in Phase 1)
# tier 1 = fully maintained (taxability matrix + tests; MN, WI in Phase 1
#          and the 5 no-tax states)
# tier 2 = rate-only via SST data (default taxability matrix; the other 22
#          SST states once Section G2 ships)
StateTier = Literal[0, 1, 2]


# ---------------------------------------------------------------------------
# Data carriers yielded by parsers / returned by accessors
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class RateRow:
    """One rate row yielded by ``StateModule.parse_rates``.

    ``parent_authority_name`` lets a county or city slot under its
    state in the authority hierarchy without the state module
    having to know primary keys.
    """

    authority_name: str
    authority_type: Literal["state", "county", "city", "district"]
    rate_pct: Decimal
    effective_from: dt.date
    effective_to: dt.date | None = None
    parent_authority_name: str | None = None
    applies_to_categories: tuple[str, ...] | None = None  # None = applies to all


@dataclass(frozen=True, slots=True)
class BoundaryRow:
    """One boundary row yielded by ``StateModule.parse_boundaries``.

    Phase 1 uses ZIP+4 ranges. Phase 4 will add geometry; that change
    extends this dataclass without breaking the protocol.
    """

    authority_name: str
    authority_type: Literal["state", "county", "city", "district"]
    zip5: str
    zip4_low: str | None = None
    zip4_high: str | None = None
    address_pattern: str | None = None


ThresholdSemantic = Literal["below_exempt", "above_excess"]
"""Per-item price threshold semantics for taxability rules.

- ``"below_exempt"`` -- if the item's amount is **strictly less than**
  ``taxable_threshold_amount``, the line is fully exempt; at or above
  the threshold the line is fully taxable. New York's $110-or-less
  clothing exemption follows this pattern.
- ``"above_excess"`` -- if the item's amount is **at or below**
  ``taxable_threshold_amount``, the line is fully exempt; above the
  threshold only the **excess** over the threshold is taxable.
  Massachusetts's $175 clothing exemption and Rhode Island's $250
  clothing exemption follow this pattern.
"""


@dataclass(frozen=True, slots=True)
class TaxabilityRule:
    """A per-category taxability rule for a state.

    Distinct from :class:`opensalestax.db.models.TaxabilityRule`,
    which is the persisted ORM row. This dataclass is the
    in-memory contract the state module exposes; data-load code
    converts it into the ORM row.
    """

    item_category: str
    is_taxable: bool
    rate_modifier: Decimal | None = None
    taxable_threshold_amount: Decimal | None = None
    """Per-item price threshold for partial exemption. NULL = no threshold."""

    threshold_semantic: ThresholdSemantic | None = None
    """How ``taxable_threshold_amount`` is applied. NULL when no threshold."""

    notes: str | None = None
    effective_from: dt.date = field(default_factory=lambda: dt.date(1900, 1, 1))
    effective_to: dt.date | None = None


@dataclass(frozen=True, slots=True)
class HolidayWindow:
    """A sales-tax holiday window the engine consults during calculation.

    Holidays exempt specific item categories from tax during a date
    window, sometimes with a per-item price cap. Examples:

    - Texas Back-to-School: clothing/footwear/school supplies under
      $100 per item, first weekend of August.
    - Florida Disaster Preparedness: batteries, generators, etc.,
      no per-item cap, two-week window in late May.

    State modules return one or more :class:`HolidayWindow` instances
    from :meth:`StateModule.holidays_for`. The loader persists them
    as :class:`opensalestax.db.models.HolidayPeriod` rows; the engine
    checks them in ``calculate_tax``.
    """

    name: str
    starts_on: dt.date
    ends_on: dt.date
    applicable_categories: tuple[str, ...] | None = None
    """None = applies to all categories. Tuple = exact category match."""

    max_amount_per_item: Decimal | None = None
    """Per-item price cap. None = no cap."""

    notes: str | None = None


@dataclass(frozen=True, slots=True)
class SpecialCase:
    """A state-specific quirk the calculation engine should consult.

    Phase 1 doesn't actually consume special cases yet; they're
    reserved for Phase 5 when the taxability layer matures (sales-
    tax holidays, exemption certs, etc.). State modules can declare
    them now so their structure is documented in code rather than
    only in prose.
    """

    name: str
    description: str
    applies_from: dt.date | None = None
    applies_to: dt.date | None = None
    affected_categories: tuple[str, ...] = ()


# ---------------------------------------------------------------------------
# The Protocol every state module implements
# ---------------------------------------------------------------------------
@runtime_checkable
class StateModule(Protocol):
    """Contract for a per-state module.

    Implementations are typically small classes registered at import
    time via :func:`opensalestax.states.registry.register`. See
    :mod:`opensalestax.states.no_tax` for the simplest real example.
    """

    state_abbrev: str
    """Two-letter USPS abbreviation, e.g. ``"MN"``."""

    state_name: str
    """Full state name, e.g. ``"Minnesota"``."""

    sst_member: bool
    """True if this state is a Streamlined Sales Tax member."""

    has_sales_tax: bool
    """False for AK, DE, MT, NH, OR -- all other 47 states are True."""

    tier: StateTier
    """Coverage tier: 0 unsupported, 1 fully maintained, 2 rate-only."""

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """Read upstream rate file, yield normalized :class:`RateRow` rows.

        ``source_file`` may be ``None`` (typed as ``Path`` for protocol
        compatibility) for ``self_seeded`` states whose rates come from
        embedded data, not an external file.
        """
        ...

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]:
        """Read upstream boundary file, yield normalized :class:`BoundaryRow` rows.

        ``source_file`` may be ``None`` (typed as ``Path`` for protocol
        compatibility) for ``self_seeded`` states whose boundaries come
        from embedded data, not an external file.
        """
        ...

    def taxability_for(self, item_category: str, effective_date: dt.date) -> TaxabilityRule | None:
        """Return the rule for this category on the given date, or None if unknown.

        ``None`` is the contract for "I don't track this category" and
        the calculation engine treats unknown categories as taxable
        at the standard rate (the most conservative default).
        """
        ...

    def special_cases(self) -> Iterable[SpecialCase]:
        """Yield state-specific quirks the engine may consult.

        Phase 1 returns an empty iterable for every state.
        """
        ...

    def holidays_for(self, year: int) -> Iterable[HolidayWindow]:
        """Yield sales-tax holidays for the given calendar year.

        Default state-module implementations return an empty
        iterator (most states have no annual holidays). States with
        holidays (TX, FL, MA, MD, ...) override this and return
        the year's windows.
        """
        ...
