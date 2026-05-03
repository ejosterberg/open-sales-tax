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

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from opensalestax.db.models import Boundary, TaxAuthority


async def lookup_jurisdictions_by_zip(
    session: AsyncSession,
    zip5: str,
    zip4: str | None = None,
) -> list[TaxAuthority]:
    """Return the tax authorities that apply to ``zip5`` (+ optional ``zip4``).

    A boundary matches when:

    1. ``zip5`` matches exactly, AND
    2. Either the boundary specifies no ZIP+4 range (applies to the whole ZIP5),
       OR the supplied ``zip4`` falls within ``[zip4_low, zip4_high]``.

    If no ``zip4`` is supplied, only boundaries with no ZIP+4 range
    are returned -- a deliberately conservative default. Callers
    that want a "best-effort" match for a ZIP5 alone (returning
    every authority touching the ZIP5 regardless of +4) can call
    :func:`lookup_jurisdictions_by_zip5_loose`.

    Returns deduplicated authorities, ordered by a stable priority
    (state -> county -> city -> district) so callers get a
    predictable jurisdiction stack.
    """
    if zip4 is not None and not zip4.isdigit():
        # Defense in depth -- the API layer validates, but never trust it.
        raise ValueError(f"zip4 must be 4 digits, got {zip4!r}")
    if not zip5.isdigit() or len(zip5) != 5:
        raise ValueError(f"zip5 must be 5 digits, got {zip5!r}")

    no_range_match = Boundary.zip4_low.is_(None)
    in_range_match = (
        (Boundary.zip4_low.isnot(None))
        & (Boundary.zip4_high.isnot(None))
        & (Boundary.zip4_low <= zip4)
        & (zip4 <= Boundary.zip4_high)
        if zip4 is not None
        else None
    )

    if in_range_match is not None:
        boundary_filter = or_(no_range_match, in_range_match)
    else:
        boundary_filter = no_range_match

    stmt = (
        select(TaxAuthority)
        .join(Boundary, Boundary.authority_id == TaxAuthority.id)
        .where(Boundary.zip5 == zip5, boundary_filter)
        .options(selectinload(TaxAuthority.state))
        .distinct()
    )

    result = await session.execute(stmt)
    authorities = list(result.scalars().all())
    return _stable_sort(authorities)


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
