# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Resolve applicable rates for a set of jurisdictions on a date.

Given a list of :class:`TaxAuthority` rows (typically returned by
:func:`opensalestax.core.lookup.lookup_jurisdictions_by_zip`), this
module finds the active :class:`Rate` for each authority on the
effective date and category.

A rate is "active" when:

- ``effective_from <= date``, AND
- ``effective_to`` is NULL OR ``date <= effective_to``, AND
- ``applies_to_categories`` is NULL (applies to all) OR contains
  the requested category.

Multiple rates may exist per authority (effective-dated history);
this function returns the single active one. If two rates appear
to overlap for the same authority + category, the most recently
``effective_from`` wins -- protects against stale historical rows.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.db.models import Rate, TaxAuthority


@dataclass(frozen=True, slots=True)
class ResolvedRate:
    """A jurisdiction + the rate that applies to it on the effective date."""

    authority: TaxAuthority
    rate: Rate

    @property
    def rate_pct(self) -> Decimal:
        """Convenience accessor for the rate percentage."""
        return self.rate.rate_pct


async def resolve_rates_for_authorities(
    session: AsyncSession,
    authorities: list[TaxAuthority],
    effective_date: dt.date,
    item_category: str = "general",
) -> list[ResolvedRate]:
    """Return the active rate for each authority on ``effective_date``.

    Authorities with no active rate for this category are silently
    omitted -- the calculation engine treats their contribution as
    zero, which matches reality (no rate on the books = no tax
    from that jurisdiction).

    The query loads all candidate rates in a single round-trip and
    picks winners in Python rather than using a SQL window function.
    Window functions are portable but their syntax across PG and
    MariaDB has subtle differences; doing the picking in Python keeps
    constitution §10 rule 1 (no engine branches) trivially satisfied.
    """
    if not authorities:
        return []

    authority_ids = [a.id for a in authorities]
    by_id = {a.id: a for a in authorities}

    stmt = select(Rate).where(
        Rate.authority_id.in_(authority_ids),
        Rate.effective_from <= effective_date,
    )
    result = await session.execute(stmt)
    candidate_rates = list(result.scalars().all())

    # Pick the most recently effective rate per authority that
    # (a) hasn't expired and (b) applies to this category.
    winners: dict[int, Rate] = {}
    for rate in candidate_rates:
        if rate.effective_to is not None and rate.effective_to < effective_date:
            continue
        if not _category_applies(rate, item_category):
            continue
        existing = winners.get(rate.authority_id)
        if existing is None or rate.effective_from > existing.effective_from:
            winners[rate.authority_id] = rate

    return [ResolvedRate(authority=by_id[aid], rate=rate) for aid, rate in winners.items()]


def _category_applies(rate: Rate, item_category: str) -> bool:
    """Return True if this rate applies to ``item_category``.

    A rate with ``applies_to_categories`` of None applies to every
    category (the common case). A rate with a list applies only to
    listed categories.
    """
    cats = rate.applies_to_categories
    if cats is None:
        return True
    # JSON column may round-trip as list, tuple, or string -- be defensive.
    if isinstance(cats, list | tuple):
        return item_category in cats
    if isinstance(cats, str):
        return item_category == cats
    return False


def combined_rate_pct(resolved: list[ResolvedRate]) -> Decimal:
    """Sum the percentages from a list of resolved rates."""
    total = Decimal("0")
    for r in resolved:
        total += r.rate_pct
    return total
