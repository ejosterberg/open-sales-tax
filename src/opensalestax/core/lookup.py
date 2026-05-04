# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Address-to-jurisdictions lookup.

Phase 1 resolves a ZIP+4 to the set of :class:`TaxAuthority` rows
that apply at that address. Phase 4 will add address-level
geometry resolution (PostGIS / R-tree); the function signatures
here will accept lat/lon then.

The query is portable across PostgreSQL and MariaDB -- it uses
only the boundary table's existing B-tree index on
(zip5, zip4_low, zip4_high) and SQLAlchemy generic comparison
operators. Constitution §10 rule 1 (no engine branches in
business logic) is satisfied.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from opensalestax.db.models import Boundary, TaxAuthority


async def lookup_jurisdictions_by_zip(
    session: AsyncSession,
    zip5: str,
    zip4: str | None = None,
) -> list[TaxAuthority]:
    """Return the tax authorities that apply to ``zip5`` (+ optional ``zip4``).

    Precedence:

    1. **State authorities are always included.** They're the most-
       general binding and don't conflict with city/county/district.
    2. **If ``zip4`` is supplied AND any boundary records explicitly
       cover that +4 range (zip4_low/high not NULL), use those
       records' bindings exclusively** (excluding state). The SST
       file uses type-4 records to encode per-+4 precision; for
       states like TN that mark "this +4 is in city X" via type-4
       and "this +4 is in unincorporated county Y" via type-z, we
       must NOT mix the two -- doing so double-counts (city +
       county both summed).
    3. **Otherwise fall back to the type-z (NULL ZIP+4) bindings.**

    Returns deduplicated authorities, ordered by a stable priority
    (state -> county -> city -> district) so callers get a
    predictable jurisdiction stack.
    """
    if zip4 is not None and not zip4.isdigit():
        # Defense in depth -- the API layer validates, but never trust it.
        raise ValueError(f"zip4 must be 4 digits, got {zip4!r}")
    if not zip5.isdigit() or len(zip5) != 5:
        raise ValueError(f"zip5 must be 5 digits, got {zip5!r}")

    options = (selectinload(TaxAuthority.state),)

    # State authorities always apply -- pull them via the type-z
    # (NULL +4) bindings since states are emitted at that level.
    state_stmt = (
        select(TaxAuthority)
        .join(Boundary, Boundary.authority_id == TaxAuthority.id)
        .where(
            Boundary.zip5 == zip5,
            Boundary.zip4_low.is_(None),
            TaxAuthority.authority_type == "state",
        )
        .options(*options)
        .distinct()
    )
    state_authorities = list((await session.execute(state_stmt)).scalars().all())

    local_authorities: list[TaxAuthority] = []
    if zip4 is not None:
        # Try the precise type-4 lookup first; if it returns
        # anything, use it exclusively for the local layer.
        precise_stmt = (
            select(TaxAuthority)
            .join(Boundary, Boundary.authority_id == TaxAuthority.id)
            .where(
                Boundary.zip5 == zip5,
                Boundary.zip4_low.isnot(None),
                Boundary.zip4_high.isnot(None),
                Boundary.zip4_low <= zip4,
                zip4 <= Boundary.zip4_high,
                TaxAuthority.authority_type != "state",
            )
            .options(*options)
            .distinct()
        )
        local_authorities = list((await session.execute(precise_stmt)).scalars().all())

    if not local_authorities:
        # Fall back to type-z (no +4) local bindings.
        fallback_stmt = (
            select(TaxAuthority)
            .join(Boundary, Boundary.authority_id == TaxAuthority.id)
            .where(
                Boundary.zip5 == zip5,
                Boundary.zip4_low.is_(None),
                TaxAuthority.authority_type != "state",
            )
            .options(*options)
            .distinct()
        )
        local_authorities = list((await session.execute(fallback_stmt)).scalars().all())

    # De-dup across the two queries (state could be in both, paranoia).
    seen_ids: set[int] = set()
    merged: list[TaxAuthority] = []
    for auth in [*state_authorities, *local_authorities]:
        if auth.id in seen_ids:
            continue
        seen_ids.add(auth.id)
        merged.append(auth)
    return _stable_sort(merged)


async def lookup_jurisdictions_by_zip5_loose(
    session: AsyncSession, zip5: str
) -> list[TaxAuthority]:
    """Return every authority touching ``zip5`` regardless of ZIP+4.

    Use with care: a ZIP5 can span multiple cities with different
    rates. Callers that get back >1 city-level authority should
    treat the result as ambiguous and ask the user for ZIP+4.
    """
    if not zip5.isdigit() or len(zip5) != 5:
        raise ValueError(f"zip5 must be 5 digits, got {zip5!r}")

    stmt = (
        select(TaxAuthority)
        .join(Boundary, Boundary.authority_id == TaxAuthority.id)
        .where(Boundary.zip5 == zip5)
        .options(selectinload(TaxAuthority.state))
        .distinct()
    )
    result = await session.execute(stmt)
    return _stable_sort(list(result.scalars().all()))


_TYPE_ORDER = {"state": 0, "county": 1, "city": 2, "district": 3}


def _stable_sort(authorities: list[TaxAuthority]) -> list[TaxAuthority]:
    """Sort authorities into a predictable jurisdiction-stack order."""
    return sorted(
        authorities,
        key=lambda a: (_TYPE_ORDER.get(a.authority_type, 99), a.name),
    )
