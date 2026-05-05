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

    # Loose fallback: if neither the precise type-4 query NOR
    # the type-z fallback found any city/county binding for this
    # ZIP+4 (e.g. OKC 73102-6107 isn't in any +4 range and the
    # only type-z record was a filtered composite code), fall
    # back to the closest type-4 city/county for the ZIP. Picking
    # the city whose nearest +4 range is closest to the requested
    # +4 avoids OK-style double-counting when a ZIP straddles two
    # cities (e.g. 73069 has Norman ranges starting at +4 1000 and
    # Moore ranges starting at +4 8061; for +4 6107 Norman wins).
    if zip4 is not None and not precise_county_city_ids:
        local_in_z = any(
            a.authority_type in ("county", "city") for a in z_authorities
        )
        if not local_in_z:
            loose_stmt = (
                select(
                    TaxAuthority,
                    Boundary.zip4_low,
                    Boundary.zip4_high,
                )
                .join(Boundary, Boundary.authority_id == TaxAuthority.id)
                .where(
                    *base_filter(),
                    Boundary.zip4_low.isnot(None),
                    TaxAuthority.authority_type.in_(("county", "city")),
                )
                .options(*options)
            )
            loose_rows = list((await session.execute(loose_stmt)).all())
            precise_authorities = _pick_closest_per_type(loose_rows, zip4)

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
    """Return one-city/one-county-per-ZIP authorities touching ``zip5``.

    Used by the calculation engine when the caller didn't supply a
    ZIP+4. The challenge: real-world ZIPs sometimes have multiple
    overlapping authority claims in the SST source data (e.g. NE
    68046 has La Vista as a type-z zip-wide record AND Papillion as
    type-4 per-+4 records AND a single Omaha type-4 record). Returning
    every authority would stack their tax rates and over-collect by
    several percent.

    The pragmatic compromise: pick at most ONE city and ONE county
    per ZIP, by total boundary coverage (most rows wins). Always
    include the state and any districts (those apply zip-wide).

    A ZIP that genuinely splits between two cities (e.g. 68046's
    Papillion vs La Vista border) will pick whichever has the larger
    geographic share. Callers wanting per-address precision should
    pass ZIP+4 to the strict lookup.
    """
    if not zip5.isdigit() or len(zip5) != 5:
        raise ValueError(f"zip5 must be 5 digits, got {zip5!r}")

    # Pull (authority, type-z-flag, row-count) so we can pick the
    # dominant city/county per ZIP. We can't easily ORDER BY a window
    # function here without breaking MariaDB compat, so we collect
    # all rows and pick in Python.
    stmt = (
        select(TaxAuthority, Boundary.zip4_low)
        .join(Boundary, Boundary.authority_id == TaxAuthority.id)
        .where(Boundary.zip5 == zip5)
        .options(selectinload(TaxAuthority.state))
    )
    rows = [(row[0], row[1]) for row in (await session.execute(stmt)).all()]
    return _pick_one_city_county_per_zip5(rows)


def _pick_one_city_county_per_zip5(
    rows: list[tuple[TaxAuthority, str | None]],
) -> list[TaxAuthority]:
    """Collapse multi-city / multi-county ZIPs to one authority per type.

    For each (authority_type, authority_id), compute (has_typez,
    row_count). For city/county types, pick the dominant authority
    using these tiebreakers in order:

    1. Has a type-z record (zip-wide claim wins over per-+4 only).
    2. Highest boundary-row count (most precise/extensive coverage).
    3. Lowest authority id (stable tiebreaker for testability).

    State and district authorities pass through unchanged.
    """
    seen_authorities: dict[int, TaxAuthority] = {}
    has_typez: dict[int, bool] = {}
    counts: dict[int, int] = {}
    for auth, zip4_low in rows:
        seen_authorities[auth.id] = auth
        if zip4_low is None:
            has_typez[auth.id] = True
        has_typez.setdefault(auth.id, False)
        counts[auth.id] = counts.get(auth.id, 0) + 1

    by_type: dict[str, list[int]] = {}
    for aid, auth in seen_authorities.items():
        by_type.setdefault(auth.authority_type, []).append(aid)

    out: list[TaxAuthority] = []
    for auth_type, aids in by_type.items():
        if auth_type in ("city", "county"):
            # Dominant authority wins. Sort key: type-z first (True > False),
            # then most rows, then lowest id.
            best_id = max(
                aids,
                key=lambda aid: (
                    has_typez.get(aid, False),
                    counts.get(aid, 0),
                    -aid,
                ),
            )
            out.append(seen_authorities[best_id])
        elif auth_type == "district":
            # Districts with a type-z (zip-wide) record genuinely apply
            # to every address in the ZIP -- include all (e.g. MN's 3
            # metro transit districts at Minneapolis 55401).
            #
            # Districts with ONLY type-4 records are address-specific
            # (Community Improvement Districts, STAR Bond, TIF, etc.):
            # only one applies per address, but the SST file lists every
            # CID overlapping the ZIP, so summing them all over-collects
            # by 3-4% in KS, OK, TN. Without zip4, drop these entirely
            # rather than pick an arbitrary one -- the rate would still
            # be wrong for most addresses in the ZIP. Callers wanting
            # CID precision should pass ZIP+4 to the strict lookup.
            for aid in aids:
                if has_typez.get(aid, False):
                    out.append(seen_authorities[aid])
        else:
            # state: pass through.
            out.extend(seen_authorities[aid] for aid in aids)
    return _stable_sort(out)


_TYPE_ORDER = {"state": 0, "county": 1, "city": 2, "district": 3}


def _stable_sort(authorities: list[TaxAuthority]) -> list[TaxAuthority]:
    """Sort authorities into a predictable jurisdiction-stack order."""
    return sorted(
        authorities,
        key=lambda a: (_TYPE_ORDER.get(a.authority_type, 99), a.name),
    )


def _pick_closest_per_type(rows, zip4: str) -> list[TaxAuthority]:
    """For each authority_type, pick the single authority whose +4 range is closest.

    The loose fallback can return multiple cities (or counties) when
    a ZIP straddles two municipalities. Picking ALL of them would
    double-count the local rate. Instead, we pick the one authority
    per type whose nearest +4 range is closest in numeric distance
    to the requested +4. Adjacent +4s usually belong to the same
    municipality, so distance is a strong signal.
    """
    requested = int(zip4)
    best: dict[str, tuple[int, TaxAuthority]] = {}
    for auth, low, high in rows:
        if low is None or high is None:
            continue
        try:
            low_i = int(low)
            high_i = int(high)
        except (TypeError, ValueError):
            continue
        if low_i <= requested <= high_i:
            distance = 0
        else:
            distance = min(abs(requested - low_i), abs(requested - high_i))
        prior = best.get(auth.authority_type)
        if prior is None or distance < prior[0]:
            best[auth.authority_type] = (distance, auth)
    return [auth for _, auth in best.values()]
