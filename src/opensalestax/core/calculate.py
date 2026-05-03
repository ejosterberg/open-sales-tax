# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tax calculation -- the engine's top-level entry point.

Given a ZIP+4 address and a list of line items, produce a per-line
tax decomposition with jurisdictional detail. Combines:

- :mod:`opensalestax.core.lookup`  -- ZIP -> tax authorities
- :mod:`opensalestax.core.resolve` -- authorities -> active rates
- per-state taxability rules from the database

Currency math: every monetary value is :class:`decimal.Decimal`.
We never use floats for money. Tax amounts round to 4 decimal
places (HALF_UP) -- callers are responsible for any further
rounding when presenting to a customer.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.core.disclaimer import disclaimer
from opensalestax.core.lookup import lookup_jurisdictions_by_zip
from opensalestax.core.resolve import (
    combined_rate_pct,
    resolve_rates_for_authorities,
)
from opensalestax.db.models import State, TaxabilityRule

# Tax amounts round to 4 dp internally. Display rounding is the
# caller's job.
TAX_QUANTUM = Decimal("0.0001")


@dataclass(frozen=True, slots=True)
class LineItem:
    """A single product/service line being taxed."""

    amount: Decimal
    category: str = "general"

    def __post_init__(self) -> None:
        if self.amount < 0:
            raise ValueError(f"amount must be non-negative, got {self.amount}")


@dataclass(frozen=True, slots=True)
class JurisdictionResult:
    """One authority's contribution to the tax on a single line."""

    name: str
    type: str
    rate_pct: Decimal


@dataclass(frozen=True, slots=True)
class CalculatedLine:
    """The result of taxing one :class:`LineItem`."""

    amount: Decimal
    category: str
    tax: Decimal
    rate_pct: Decimal
    jurisdictions: list[JurisdictionResult] = field(default_factory=list)
    note: str | None = None


@dataclass(frozen=True, slots=True)
class CalculationResult:
    """Top-level result of :func:`calculate_tax`."""

    subtotal: Decimal
    tax_total: Decimal
    lines: list[CalculatedLine]
    disclaimer: str
    data_versions: dict[str, str] = field(default_factory=dict)
    """Map of state abbrev -> active data version label, for traceability."""


async def calculate_tax(
    session: AsyncSession,
    zip5: str,
    line_items: list[LineItem],
    zip4: str | None = None,
    effective_date: dt.date | None = None,
) -> CalculationResult:
    """Tax a list of line items at a given address.

    Returns a :class:`CalculationResult` with per-line decomposition
    and a constitution-§13 disclaimer field. If the ZIP doesn't
    match any known jurisdiction, every line gets ``tax=0`` with a
    ``note`` explaining why -- the call doesn't fail.
    """
    if not line_items:
        return CalculationResult(
            subtotal=Decimal("0"),
            tax_total=Decimal("0"),
            lines=[],
            disclaimer=disclaimer(),
        )

    eff_date = effective_date or dt.date.today()
    authorities = await lookup_jurisdictions_by_zip(session, zip5, zip4)
    state_abbrev = _resolve_state_abbrev(authorities)
    no_jurisdiction_note = _no_jurisdiction_note(zip5, zip4) if not authorities else None

    lines_out: list[CalculatedLine] = []
    subtotal = Decimal("0")
    tax_total = Decimal("0")

    for item in line_items:
        subtotal += item.amount
        line = await _tax_one_line(
            session,
            item,
            authorities,
            state_abbrev,
            eff_date,
            no_jurisdiction_note,
        )
        tax_total += line.tax
        lines_out.append(line)

    return CalculationResult(
        subtotal=subtotal,
        tax_total=tax_total,
        lines=lines_out,
        disclaimer=disclaimer(),
    )


def _resolve_state_abbrev(authorities: list) -> str | None:
    """Pick the state abbreviation from a list of authorities.

    Prefers the state-typed authority; falls back to the first
    authority's state. Returns None if the list is empty.
    """
    if not authorities:
        return None
    for a in authorities:
        if a.authority_type == "state":
            return str(a.state.abbrev)
    return str(authorities[0].state.abbrev)


def _no_jurisdiction_note(zip5: str, zip4: str | None) -> str:
    """Format the explanatory note for ZIPs with no boundaries on file."""
    suffix = f"-{zip4}" if zip4 else ""
    return f"No jurisdictions found for ZIP {zip5}{suffix}; tax assumed zero."


async def _tax_one_line(
    session: AsyncSession,
    item: LineItem,
    authorities: list,
    state_abbrev: str | None,
    eff_date: dt.date,
    no_jurisdiction_note: str | None,
) -> CalculatedLine:
    """Compute the :class:`CalculatedLine` for a single :class:`LineItem`."""
    if not authorities:
        return _zero_line(item, note=no_jurisdiction_note)

    # Taxability check -- a per-category rule may zero out this line.
    if state_abbrev is not None:
        rule = await _taxability_rule(session, state_abbrev, item.category, eff_date)
        if rule is not None and not rule.is_taxable:
            note = rule.notes or f"{item.category} is non-taxable in {state_abbrev}."
            return _zero_line(item, note=note)

    resolved = await resolve_rates_for_authorities(session, authorities, eff_date, item.category)
    rate_pct = combined_rate_pct(resolved)
    line_tax = (item.amount * rate_pct / Decimal("100")).quantize(
        TAX_QUANTUM, rounding=ROUND_HALF_UP
    )

    return CalculatedLine(
        amount=item.amount,
        category=item.category,
        tax=line_tax,
        rate_pct=rate_pct,
        jurisdictions=[
            JurisdictionResult(
                name=r.authority.name,
                type=r.authority.authority_type,
                rate_pct=r.rate_pct,
            )
            for r in resolved
        ],
    )


def _zero_line(item: LineItem, note: str | None) -> CalculatedLine:
    """Build a CalculatedLine with zero tax (used for non-taxable + missing-juris cases)."""
    return CalculatedLine(
        amount=item.amount,
        category=item.category,
        tax=Decimal("0"),
        rate_pct=Decimal("0"),
        jurisdictions=[],
        note=note,
    )


async def _taxability_rule(
    session: AsyncSession,
    state_abbrev: str,
    item_category: str,
    effective_date: dt.date,
) -> TaxabilityRule | None:
    """Look up the active taxability rule for a state + category + date."""
    stmt = (
        select(TaxabilityRule)
        .join(State, State.id == TaxabilityRule.state_id)
        .where(
            State.abbrev == state_abbrev,
            TaxabilityRule.item_category == item_category,
            TaxabilityRule.effective_from <= effective_date,
        )
    )
    result = await session.execute(stmt)
    candidates = list(result.scalars().all())

    # Pick the most recently effective rule that hasn't expired.
    winner: TaxabilityRule | None = None
    for rule in candidates:
        if rule.effective_to is not None and rule.effective_to < effective_date:
            continue
        if winner is None or rule.effective_from > winner.effective_from:
            winner = rule
    return winner
