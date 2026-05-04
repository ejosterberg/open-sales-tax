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

    def base_filter():
        return [Boundary.zip5 == zip5]

    # Type-4 (precise per-+4) county/city bindings, when caller
    # supplied a +4 AND any type-4 record covers it. For TN-style
    # encoding ("this +4 is in city X" vs "this +4 is in
    # unincorporated county Y") the type-4 row is the precise
    # truth and the type-z fallback would double-count.
    precise_county_city_ids: set[int] = set()
    if zip4 is not None:
        precise_stmt = (
            select(TaxAuthority)
            .join(Boundary, Boundary.authority_id == TaxAuthority.id)
            .where(
                *base_filter(),
                Boundary.zip4_low.isnot(None),
                Boundary.zip4_high.isnot(None),
                Boundary.zip4_low <= zip4,
                zip4 <= Boundary.zip4_high,
                TaxAuthority.authority_type.in_(("county", "city")),
            )
            .options(*options)
            .distinct()
        )
        precise_authorities = list(
            (await session.execute(precise_stmt)).scalars().all()
        )
        precise_county_city_ids = {a.id for a in precise_authorities}
    else:
        precise_authorities = []

    # Type-z (NULL +4) bindings -- catches the always-applies
    # state row, the metro / transit districts that aren't bound
    # per-+4, and (when no precise type-4 row covered the +4) the
    # zip-wide county/city fallback.
    z_stmt = (
        select(TaxAuthority)
        .join(Boundary, Boundary.authority_id == TaxAuthority.id)
        .where(
            *base_filter(),
            Boundary.zip4_low.is_(None),
        )
        .options(*options)
        .distinct()
    )
    z_authorities = list((await session.execute(z_stmt)).scalars().all())

    # Districts ALWAYS apply (state-only / state+county / metro /
    # transit) regardless of record type; pull them from the
    # type-4 layer too so districts encoded only on per-+4 rows
    # don't get dropped.
    district_authorities: list[TaxAuthority] = []
    if zip4 is not None:
        district_stmt = (
            select(TaxAuthority)
            .join(Boundary, Boundary.authority_id == TaxAuthority.id)
            .where(
                *base_filter(),
                Boundary.zip4_low.isnot(None),
                Boundary.zip4_high.isnot(None),
                Boundary.zip4_low <= zip4,
                zip4 <= Boundary.zip4_high,
                TaxAuthority.authority_type == "district",
            )
            .options(*options)
            .distinct()
        )
        district_authorities = list(
            (await session.execute(district_stmt)).scalars().all()
        )

    # Merge: state always; districts always; county/city prefer
    # type-4 over type-z when both exist for the SAME ZIP+4.
    seen_ids: set[int] = set()
    merged: list[TaxAuthority] = []
    for auth in [*precise_authorities, *district_authorities, *z_authorities]:
        if auth.id in seen_ids:
            continue
        # Drop type-z county/city when a precise type-4 county/
        # city was found (TN-style alternation).
        if (
            auth.authority_type in ("county", "city")
            and precise_county_city_ids
            and auth.id not in precise_county_city_ids
        ):
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
