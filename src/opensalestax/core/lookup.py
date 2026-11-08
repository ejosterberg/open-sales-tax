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

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from opensalestax.data.county_names import county_name as _county_name_lookup
from opensalestax.data.zip_county_dominant import dominant_county
from opensalestax.data.zip_county_overrides import county_override as _county_override
from opensalestax.db.models import Boundary, DataVersion, State, TaxAuthority

# Threshold for the v0.47 "lone type-4-only district" heuristic.
# A solitary type-4-only district is included as a county-wide overlay
# only when its per-ZIP boundary-row count meets this minimum;
# otherwise it's treated as a stray binding (e.g. Fulton TSPLOST
# claiming 7 +4 rows in a Gwinnett-County ZIP). Empirically 20 is
# the right elbow: real GA TSPLOST coverage is ~100+ rows per ZIP;
# stray bindings ship 1-10.
_MIN_LONE_DISTRICT_ROWS = 20

# Decision 10 (iter-62): a type-4 boundary row spanning >= 1000 +4s
# is treated as a "wide-range" / type-z-equivalent record. Some SST
# files encode "this authority covers the whole ZIP" as one such
# row instead of a proper type-z (notably WY counties for synthetic
# +4 lookups). The strict lookup uses this threshold to distinguish
# narrow per-+4 precision (e.g. Natrona 2401-2402 = unincorporated)
# from wide-range claims (Natrona 0000-0999 = whole-ZIP claim).
# Real per-block ranges are < 100 +4s; 1000 is the empirical cutoff.
_WIDE_TYPE4_RANGE_THRESHOLD = 1000

# States whose loaded "district" authorities are mutually-exclusive
# county-level overlays that ALL carry the same rate, so at most one
# applies to any single address. When a ZIP straddles several such
# counties, its SST boundary file binds one district per county-side
# and the naive engine SUMS them -- e.g. West Des Moines 50265 straddles
# Polk + Warren (+ a Dallas sliver on 50266) and returns Polk LOST 1% +
# Union LOST 1% + IA-district-98199 1% = 9% (10% on 50266), well over
# Iowa's 1% cap. For these states the engine keeps only the DOMINANT
# district (most boundary rows for the ZIP) and drops the rest. The fix
# is rate-neutral by construction -- every candidate shares the same
# rate -- so it only removes the erroneous stacking, never changes which
# rate applies.
#   IA: Local Option Sales Tax (LOST) -- uniformly 1%, county-adopted,
#       statutorily capped at 1% by Iowa Code ch. 423B.
# (TN's code-79 IMPROVE Act overlays are collapsed by a separate,
# older mechanism inside ``_pick_one_city_county_per_zip5``; that path
# keys off ``picked_city`` which TN has and IA -- county-level LOST with
# no city authority -- does not, which is why IA needs this dedicated
# post-merge pass that runs on both the strict and loose lookup paths.)
_SINGLE_LOCAL_DISTRICT_STATES = {"IA"}


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
    # Track precise city and county IDs SEPARATELY so the "drop type-z"
    # filter at the merge step only drops the SAME type. Previous
    # behaviour (iter-62 through 2026-11-08) folded both into one
    # `precise_county_city_ids` set, which meant a soft-added dominant
    # city would cause any type-z county binding to be dropped as if
    # the city had superseded it. UT 84601 reproduces this: Provo has
    # only narrow per-+4 rows (none covering synthetic +4 "0001"), so
    # the soft-add path adds Provo, and the old code then dropped the
    # type-z Utah County 2.5% binding, under-collecting by 2.5pp.
    # Same pattern bites MN 55344/55416/55369 (Hennepin County 0.15%
    # dropped) and WY 82601 (Natrona County correctly kept via a
    # different code path, but any peer state with the pattern is
    # exposed).
    precise_city_ids: set[int] = set()
    precise_county_ids: set[int] = set()
    has_narrow_precise = False
    if zip4 is not None:
        precise_stmt = (
            select(TaxAuthority, Boundary.zip4_low, Boundary.zip4_high)
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
        )
        precise_rows = list((await session.execute(precise_stmt)).all())
        precise_authorities = []
        seen: set[int] = set()
        for auth, lo, hi in precise_rows:
            # Track whether any matching row is "narrow" (< 1000 +4s).
            # Decision 10 (iter-62): a narrow type-4 is the SST file's
            # signal that THIS specific +4 is precisely encoded -- e.g.
            # WY Natrona 2401-2402 means "unincorporated, NOT in any
            # city". A wide-range row (Natrona 0000-0999) is a ZIP-wide
            # claim with no per-+4 information. The soft-add-dominant-
            # city path below uses this flag to avoid spuriously adding
            # a city to genuinely unincorporated addresses.
            if lo and hi and (int(hi) - int(lo) + 1) < _WIDE_TYPE4_RANGE_THRESHOLD:
                has_narrow_precise = True
            if auth.id in seen:
                continue
            seen.add(auth.id)
            precise_authorities.append(auth)
            if auth.authority_type == "city":
                precise_city_ids.add(auth.id)
            elif auth.authority_type == "county":
                precise_county_ids.add(auth.id)
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
    #
    # Also pull the matching (zip4_low, zip4_high) for each district
    # row so the cross-county district filter below can detect which
    # county a county-anchored district was co-bound to on each row.
    # SST boundary files for county-anchored district taxes (e.g.
    # OH's COTA LinkUS extension codes 96000=Delaware, 98000=Union,
    # plus COTA 25000=Franklin) emit one boundary row per county side
    # of a cross-county ZIP, pairing district + county on the same
    # (zip5, zip4_low, zip4_high). A naive district query unions
    # every district every ZIP+4 row touches, so Dublin 43017 (which
    # straddles Franklin, Delaware, Union) picks up all three county-
    # anchored districts and stacks their rates -- blowing past Ohio's
    # statutory 8.75% cap (ORC 5739.023) and returning 10.00% for an
    # address OH DOR's Finder reports as 8.00%.
    district_rows: list[tuple[TaxAuthority, str, str]] = []
    if zip4 is not None:
        district_stmt = (
            select(TaxAuthority, Boundary.zip4_low, Boundary.zip4_high)
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
        )
        district_rows = [
            (auth, lo, hi) for auth, lo, hi in (await session.execute(district_stmt)).all()
        ]
    district_authorities: list[TaxAuthority] = []
    seen_d: set[int] = set()
    for auth, _lo, _hi in district_rows:
        if auth.id in seen_d:
            continue
        seen_d.add(auth.id)
        district_authorities.append(auth)

    # Loose fallback: if neither the precise type-4 query NOR
    # the type-z fallback found any city/county binding for this
    # ZIP+4 (e.g. OKC 73102-6107 isn't in any +4 range and the
    # only type-z record was a filtered composite code), fall
    # back to the closest type-4 city/county for the ZIP. Picking
    # the city whose nearest +4 range is closest to the requested
    # +4 avoids OK-style double-counting when a ZIP straddles two
    # cities (e.g. 73069 has Norman ranges starting at +4 1000 and
    # Moore ranges starting at +4 8061; for +4 6107 Norman wins).
    if zip4 is not None and not (precise_city_ids or precise_county_ids):
        local_in_z = any(a.authority_type in ("county", "city") for a in z_authorities)
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
            for auth in precise_authorities:
                if auth.authority_type == "city":
                    precise_city_ids.add(auth.id)
                elif auth.authority_type == "county":
                    precise_county_ids.add(auth.id)

    # Decision 10 (iter-62 third attempt): soft-add the ZIP's dominant
    # city when precise + z + loose all missed one AND no narrow
    # type-4 row covers this +4. WY Casper has 616 narrow type-4
    # ranges for 82601 and zero type-z records; Natrona's wide-range
    # type-4 (0000-0999) covers any synthetic +4 but encodes a
    # ZIP-wide claim, not per-+4 info. The loose-lookup path picks
    # Casper correctly via row-count; this mirrors that signal into
    # the strict path -- but ONLY when no narrow row exists, so
    # genuinely unincorporated +4s (Natrona 2401-2402) keep their
    # state+county-only stack.
    if zip4 is not None and not has_narrow_precise:
        precise_has_city = any(a.authority_type == "city" for a in precise_authorities)
        z_has_city = any(a.authority_type == "city" for a in z_authorities)
        if not precise_has_city and not z_has_city:
            dominant_city_stmt = (
                select(TaxAuthority)
                .join(Boundary, Boundary.authority_id == TaxAuthority.id)
                .where(
                    *base_filter(),
                    Boundary.zip4_low.isnot(None),
                    TaxAuthority.authority_type == "city",
                )
                .group_by(TaxAuthority.id)
                .order_by(func.count(Boundary.id).desc(), TaxAuthority.id.asc())
                .limit(1)
                .options(*options)
            )
            dominant = (await session.execute(dominant_city_stmt)).scalars().first()
            if dominant is not None:
                precise_authorities = [*precise_authorities, dominant]
                precise_city_ids.add(dominant.id)

    # Merge: state always; districts always; county/city prefer
    # type-4 over type-z when both exist for the SAME ZIP+4.
    #
    # The "drop type-z" filter runs per-type: a precise city only
    # supersedes other type-z CITIES (not type-z counties), and
    # vice versa. Folding both into one set (pre 2026-11-08) caused
    # UT 84601 to drop its type-z Utah County binding because the
    # soft-add had added a precise city (Provo), under-collecting
    # 2.5pp. Same bug hit MN 55344/55416/55369 (Hennepin typez
    # dropped when a Minneapolis / Maple Grove / Eden Prairie city
    # bound via precise type-4).
    #
    # EXCEPTION for city-includes-county states (TN, WA): the SST
    # file's city rate ALREADY includes the county portion, so a
    # type-z county binding stacked on top of a precise city would
    # double-collect. When a precise city matches in one of these
    # states, treat the county the same way the pre-2026-11-08
    # code did and drop any type-z county, even though no precise
    # county matched. WA 98402-3502 Tacoma reproduces: Pierce Co
    # has a type-z row + Tacoma has a precise type-4; without this
    # exception Pierce stacks (+3.1pp over-collection). Same bite
    # on TN 37040 Clarksville.
    city_includes_county = False
    if precise_city_ids:
        for auth in precise_authorities:
            if auth.authority_type == "city" and _state_abbrev(auth) in {"TN", "WA"}:
                city_includes_county = True
                break

    seen_ids: set[int] = set()
    merged: list[TaxAuthority] = []
    for auth in [*precise_authorities, *district_authorities, *z_authorities]:
        if auth.id in seen_ids:
            continue
        if auth.authority_type == "city" and precise_city_ids and auth.id not in precise_city_ids:
            continue
        if auth.authority_type == "county":
            if city_includes_county:
                # Drop ALL type-z counties when the state's cities include
                # the county portion (pre 2026-11-08 behaviour for TN/WA).
                continue
            if precise_county_ids and auth.id not in precise_county_ids:
                continue
        seen_ids.add(auth.id)
        merged.append(auth)

    # Type-z fallback dedup: when no precise type-4 match was found,
    # the merged list contains every type-z authority claiming the
    # ZIP. For multi-city/multi-county overlap (e.g. Johnson City
    # 37601 binds to 2 cities + 2 counties via type-z) plus TN's
    # cross-county IMPROVE Act stacking, this stacks 5+ authorities
    # and over-collects. Apply the same loose-lookup dedup so
    # synthetic and real +4 addresses without precise SST coverage
    # behave the same as the zip5-only path.
    #
    # When either precise set IS populated, the precise type-4
    # match has already won for that city/county slot; skip the
    # dedup so per-+4 precision is preserved.
    if not (precise_city_ids or precise_county_ids):
        merged = await _dedup_typez_fallback(session, merged, zip5)

    # Cross-county district filter (ORC 5739.023 / OH COTA LinkUS +
    # any other state whose SST boundary file pairs a county-anchored
    # district onto the same (zip5, zip4_low, zip4_high) row as its
    # anchoring county). Runs AFTER the type-z fallback dedup so the
    # final picked-county set is stable whether the caller supplied
    # a +4 or not. OH ZIP 43017 reproduces: Dublin straddles
    # Franklin + Delaware + Union, and the SST file has one row per
    # county side pairing each county with its own COTA variant
    # (25000 Franklin / 96000 Delaware / 98000 Union) on the same
    # (zip5, zip4_low, zip4_high). With all three type-z district
    # rows the merge otherwise stacks 3 x 1.00% = 3% of transit tax
    # on top of state+county, blowing past Ohio's 8.75% statutory
    # cap (ORC 5739.02 / 5739.023) and returning 10.00%.
    #
    # Algorithm: for each district still in merged, collect the
    # counties co-bound to the SAME (zip5, zip4_low, zip4_high)
    # across the district's type-4 rows for this ZIP (any range,
    # not restricted to the input +4). If the district HAS county
    # pairings and NONE intersect the final picked county set, drop
    # the district as cross-county pollution. Districts with no
    # type-4 county pairings (state-wide transit, metro-wide
    # districts, districts whose SST file doesn't co-bind a county)
    # pass through untouched. Rate-neutral for correctly-bound
    # districts; only drops bindings the SST file implicitly tied
    # to the wrong county.
    merged = await _drop_cross_county_districts(session, merged, zip5)

    # iter-167: cross-state ZIP dedup. Some ZIPs (Pipestone area
    # 56144 / 56164, Sioux Falls 57068) straddle a state line and
    # end up with boundary rows in both states' SST quarterly
    # files. The ZCTA-sourced boundary tells us which state
    # physically owns the ZIP per the Census file; drop
    # authorities from any other state to prevent cross-state
    # rate summing. (Replaces iter-166's count-majority heuristic
    # which mis-picked SD for MN-side ZIP 56144.)
    canonical = await _canonical_state_for_zip(session, zip5)
    merged = _filter_to_canonical_state(merged, canonical)

    # Collapse multi-county same-rate LOST/overlay stacks (IA West Des
    # Moines etc.) to the dominant district. Runs after the merge so it
    # catches both the precise-+4 case (where the typez-fallback dedup
    # is skipped) and the fallback case.
    merged = await _dedup_single_local_districts(session, merged, zip5)

    return _stable_sort(merged)


async def _drop_cross_county_districts(
    session: AsyncSession, authorities: list[TaxAuthority], zip5: str
) -> list[TaxAuthority]:
    """Drop districts whose SST file co-binds them to a county NOT in the picked set.

    See the docstring block in ``lookup_jurisdictions_by_zip`` for
    the OH COTA LinkUS reproduction (Dublin 43017 10% → 8%) and the
    rate-neutrality argument. The algorithm looks at each district's
    type-4 (zip4-range) boundary rows for this ZIP and, for each row,
    checks which county the SST file put on the exact same
    (zip5, zip4_low, zip4_high) tuple. If every such pairing names a
    county NOT in the final picked county set, the district is
    cross-county pollution and is dropped.

    Keeps districts that:
    - have no type-4 county pairings at all (state-wide transit /
      metro districts not anchored to a single county by the SST
      file), OR
    - have at least one type-4 county pairing whose county is in
      the picked set.
    """
    final_county_ids = {a.id for a in authorities if a.authority_type == "county"}
    district_ids = {a.id for a in authorities if a.authority_type == "district"}
    if not (final_county_ids and district_ids):
        return authorities

    pair_stmt = select(Boundary.authority_id, Boundary.zip4_low, Boundary.zip4_high).where(
        Boundary.zip5 == zip5,
        Boundary.zip4_low.isnot(None),
        Boundary.authority_id.in_(district_ids),
    )
    district_t4 = list((await session.execute(pair_stmt)).all())
    range_keys = {(lo, hi) for _aid, lo, hi in district_t4}
    if not range_keys:
        return authorities

    county_pair_stmt = (
        select(TaxAuthority.id, Boundary.zip4_low, Boundary.zip4_high)
        .join(Boundary, Boundary.authority_id == TaxAuthority.id)
        .where(
            Boundary.zip5 == zip5,
            TaxAuthority.authority_type == "county",
            Boundary.zip4_low.in_({lo for lo, _hi in range_keys}),
            Boundary.zip4_high.in_({hi for _lo, hi in range_keys}),
        )
    )
    county_pairs_by_range: dict[tuple[str, str], set[int]] = {}
    for cid, lo, hi in (await session.execute(county_pair_stmt)).all():
        if (lo, hi) in range_keys:
            county_pairs_by_range.setdefault((lo, hi), set()).add(cid)

    district_county_pairs: dict[int, set[int]] = {}
    for aid, lo, hi in district_t4:
        peers = county_pairs_by_range.get((lo, hi))
        if peers:
            district_county_pairs.setdefault(aid, set()).update(peers)

    drop_ids = {
        aid
        for aid in district_ids
        if (peers := district_county_pairs.get(aid)) and not (peers & final_county_ids)
    }
    if not drop_ids:
        return authorities
    return [a for a in authorities if a.id not in drop_ids]


async def _dedup_typez_fallback(
    session: AsyncSession, authorities: list[TaxAuthority], zip5: str
) -> list[TaxAuthority]:
    """Dedup a strict-lookup type-z fallback list to the same shape as the loose lookup.

    Pulls the same ``(authority, zip4_low)`` rows the loose lookup
    uses (any boundary that touches ``zip5`` -- type-z and type-4
    both count) so the dominant-by-row-count tiebreaker gets the
    real per-ZIP coverage. Restricted to the candidate authorities
    already in the merged list so we don't override the strict
    lookup's precise-match selection (Edmond OK 73034-1234 picks
    the Logan County type-4 binding via precise match; widening
    the dedup to ALL ZIP authorities would let Oklahoma County's
    wider boundary outvote it on row count).

    Decision 10 documents the remaining edge case (synthetic +4
    addresses in WY where a wide-range county/state type-4 record
    matches but the city's narrow ranges don't); fixing that
    without regressing OK-style cross-county +4 matches needs a
    more careful design.
    """
    if not authorities:
        return authorities

    candidate_ids = {a.id for a in authorities}
    rows_stmt = (
        select(TaxAuthority, Boundary.zip4_low)
        .join(Boundary, Boundary.authority_id == TaxAuthority.id)
        .where(Boundary.zip5 == zip5, TaxAuthority.id.in_(candidate_ids))
        .options(selectinload(TaxAuthority.state))
    )
    rows = [(row[0], row[1]) for row in (await session.execute(rows_stmt)).all()]

    coverage_stmt = (
        select(Boundary.authority_id, func.count(Boundary.zip5.distinct()))
        .where(Boundary.authority_id.in_(candidate_ids))
        .group_by(Boundary.authority_id)
    )
    total_zip_counts: dict[int, int] = {}
    for aid, zip_count in (await session.execute(coverage_stmt)).all():
        total_zip_counts[aid] = zip_count
    return _pick_one_city_county_per_zip5(rows, total_zip_counts=total_zip_counts, zip5=zip5)


def _collapse_single_local_districts(
    authorities: list[TaxAuthority],
    zip_counts: dict[int, int],
    total_counts: dict[int, int],
    local_state: str | None,
) -> list[TaxAuthority]:
    """Pure core of the single-local-district dedup (see async wrapper).

    For a state in :data:`_SINGLE_LOCAL_DISTRICT_STATES`, keep only the
    dominant district and drop the others. Dominance is decided by, in
    order: most boundary rows for THIS ZIP (the county-side the ZIP
    mostly sits in), then most total ZIPs claimed (regional-fit signal),
    then lowest authority id (stable tiebreaker). Rate-neutral -- every
    candidate district shares the same rate, so this never changes the
    tax, only stops the multi-county stack from summing.

    A no-op when there is at most one district or the address's local
    state does not need the dedup. Kept pure (no DB) so it is unit-
    testable with stub authorities.
    """
    districts = [a for a in authorities if a.authority_type == "district"]
    if len(districts) <= 1 or local_state not in _SINGLE_LOCAL_DISTRICT_STATES:
        return authorities
    dominant = max(
        districts,
        key=lambda d: (zip_counts.get(d.id, 0), total_counts.get(d.id, 0), -d.id),
    )
    return [a for a in authorities if a.authority_type != "district" or a is dominant]


async def _dedup_single_local_districts(
    session: AsyncSession, authorities: list[TaxAuthority], zip5: str
) -> list[TaxAuthority]:
    """Collapse stacked same-rate LOST/overlay districts to the dominant one.

    Runs on the final merged authority list from BOTH the strict
    (ZIP+4) and loose (ZIP5) lookup paths. For states whose districts
    are mutually-exclusive county overlays sharing one rate
    (:data:`_SINGLE_LOCAL_DISTRICT_STATES`), a ZIP that straddles
    several counties otherwise sums one district per county-side and
    over-collects (IA West Des Moines 50265 -> 9%, 50266 -> 10%; correct
    7%). This keeps only the district with the most boundary rows for
    ``zip5`` and drops the rest.

    Cheap by design: zero DB work unless the list has >1 district AND
    the address's local state is one that needs the dedup, so it never
    touches lookups for the other 48 states.
    """
    districts = [a for a in authorities if a.authority_type == "district"]
    if len(districts) <= 1:
        return authorities

    # Local state = the county/city the ZIP resolved to (IA LOST is
    # county-level with no city authority, so county is the signal);
    # fall back to the districts' own state if somehow no county/city.
    local_state = next(
        (
            abbrev
            for a in authorities
            if a.authority_type in ("county", "city") and (abbrev := _state_abbrev(a)) is not None
        ),
        None,
    ) or _state_abbrev(districts[0])
    if local_state not in _SINGLE_LOCAL_DISTRICT_STATES:
        return authorities

    district_ids = {d.id for d in districts}
    zip_count_stmt = (
        select(Boundary.authority_id, func.count(Boundary.id))
        .where(Boundary.zip5 == zip5, Boundary.authority_id.in_(district_ids))
        .group_by(Boundary.authority_id)
    )
    zip_counts = dict((await session.execute(zip_count_stmt)).tuples().all())
    total_stmt = (
        select(Boundary.authority_id, func.count(Boundary.zip5.distinct()))
        .where(Boundary.authority_id.in_(district_ids))
        .group_by(Boundary.authority_id)
    )
    total_counts = dict((await session.execute(total_stmt)).tuples().all())

    return _collapse_single_local_districts(authorities, zip_counts, total_counts, local_state)


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

    # iter-167: cross-state ZIP dedup. Filter rows down to the
    # canonical state's authorities so cross-state ZIPs
    # (Pipestone-area MN/SD) don't return both states' rates.
    # The canonical state comes from the ZCTA-sourced boundary
    # (geographic ground truth), not from authority counts.
    if rows:
        canonical = await _canonical_state_for_zip(session, zip5)
        canonical_authorities = _filter_to_canonical_state([r[0] for r in rows], canonical)
        canonical_ids = {a.id for a in canonical_authorities}
        rows = [r for r in rows if r[0].id in canonical_ids]

    # Total ZIP coverage per candidate authority -- used as a
    # tiebreaker so the more-specific authority wins (e.g. Winooski
    # 85150 covers ZIP 05404 only, while Colchester 14875 covers
    # several northern Chittenden County ZIPs). Without this signal,
    # both bind to ZIP 05404 with row count = 1 and the lower-id
    # authority wins arbitrarily; the curated-name tiebreaker doesn't
    # help when both are curated.
    candidate_ids = {auth.id for auth, _ in rows}
    total_zip_counts: dict[int, int] = {}
    if candidate_ids:
        coverage_stmt = (
            select(Boundary.authority_id, func.count(Boundary.zip5.distinct()))
            .where(Boundary.authority_id.in_(candidate_ids))
            .group_by(Boundary.authority_id)
        )
        for aid, zip_count in (await session.execute(coverage_stmt)).all():
            total_zip_counts[aid] = zip_count

    picked = _pick_one_city_county_per_zip5(rows, total_zip_counts=total_zip_counts, zip5=zip5)
    # Collapse multi-county same-rate LOST/overlay stacks (IA) to the
    # dominant district; no-op for states that don't need it.
    return await _dedup_single_local_districts(session, picked, zip5)


def _is_placeholder_name(auth: TaxAuthority) -> bool:
    """Return True if ``auth.name`` is the loader's ``XX-type-NNNNN`` fallback.

    Authorities whose state module's ``_authority_name`` couldn't
    map the SST jurisdiction code to a friendly name fall back to
    ``"{state_abbrev}-{authority_type}-{code}"`` (e.g.
    ``VT-city-66175``). These represent codes that no maintainer has
    vetted -- often broad regional / county-overlay zones that
    incidentally claim the same ZIPs as the more specific city
    authority. When two candidates tie on all other signals, prefer
    the one with a curated name as a proxy for "vetted by a state
    module maintainer".
    """
    state_abbrev = _state_abbrev(auth)
    if not state_abbrev:
        return False
    return auth.name.startswith(f"{state_abbrev}-{auth.authority_type}-")


def _pick_one_city_county_per_zip5(
    rows: list[tuple[TaxAuthority, str | None]],
    total_zip_counts: dict[int, int] | None = None,
    *,
    zip5: str | None = None,
) -> list[TaxAuthority]:
    """Collapse multi-city / multi-county ZIPs to one authority per type.

    For each (authority_type, authority_id), compute (has_typez,
    row_count). For city/county types, pick the dominant authority
    using these tiebreakers in order:

    1. Highest boundary-row count for THIS ZIP (most coverage wins).
       Catches GA Roswell 30075 -- Cobb has 1 typez + 18 type4 (=19),
       Fulton has 0 typez + 107 type4. Per USPS Roswell is in Fulton;
       picking by row count gives the correct county (whereas the
       previous "has-typez first" pick gave Cobb because of one stray
       zip-wide binding).
    2. Has a type-z record (zip-wide claim is a secondary signal).
       Used as a tiebreaker when row counts are equal.
    3. Has a curated friendly name (placeholder ``XX-city-NNNNN``
       loses to a vetted name). Catches VT 05401 where the SST
       address-level data binds the ZIP to both city ``10675``
       (= "Burlington", curated) and a regional code ``66175``
       (placeholder, covers 38 ZIPs). The vetted name corresponds
       to the dominant city; the placeholder is a broader overlay.
    4. Fewer total ZIPs claimed by the authority across the boundary
       table -- the more-specific city wins. Catches Winooski 05404,
       where Winooski (85150) covers ZIP 05404 only while Colchester
       (14875) covers several Chittenden County ZIPs; both are
       curated, both have row_count=1 for 05404, but Winooski is
       clearly the right city for that ZIP.
    5. Lowest authority id (stable tiebreaker for testability).

    State and district authorities pass through unchanged.

    ``total_zip_counts`` is the ``{authority_id: distinct zip5 count}``
    map from the boundary table; when not supplied (e.g. unit tests
    that build rows from in-memory stubs), the fewer-ZIPs tiebreaker
    is a no-op (everyone counts as 0).
    """
    if total_zip_counts is None:
        total_zip_counts = {}
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
    picked_city: TaxAuthority | None = None
    picked_county: TaxAuthority | None = None
    # Hard-override for the county slot: Census area-majority wins over
    # SST row-count. GA 30601 reproduces why: ZIP 30601's USPS place is
    # Athens (Athens-Clarke County). The GA Q4 SST boundary file binds
    # 30601 to Clarke, Jackson, AND Madison, with Madison carrying one
    # more row (15) than Clarke (14) -- so the row-count tiebreak picked
    # Madison, over-collecting the wrong county and dropping Athens-
    # Clarke entirely. `dominant_county` returns the FIPS whose
    # AREALAND_PART is largest per the Census ZCTA relationship file;
    # that is the same rule `choose_county_name` already uses for
    # self-seeded modules, lifted here for SST states too.
    dominant_county_name: str | None = None
    if zip5 is not None and by_type.get("county"):
        sample_auth = seen_authorities[by_type["county"][0]]
        sample_state = _state_abbrev(sample_auth)
        if sample_state is not None:
            # Hand-curated override wins over Census area-majority. See
            # zip_county_overrides.py: Census land-area is a proxy for
            # "where the addresses are" and fails for a city that sits
            # in a geographically small county next to a large rural
            # neighbour (e.g. OK 74003 Bartlesville: Osage 113 wins by
            # acreage but the city is in Washington 147).
            dom_fips = _county_override(zip5, sample_state) or dominant_county(zip5, sample_state)
            if dom_fips is not None:
                dominant_county_name = _county_name_lookup(sample_state, dom_fips)

    for auth_type, aids in by_type.items():
        if auth_type in ("city", "county"):
            # If Census tells us the dominant county for this ZIP AND a
            # candidate matches that name, that pick is final.
            overridden_id: int | None = None
            if auth_type == "county" and dominant_county_name is not None:
                for aid in aids:
                    if seen_authorities[aid].name == dominant_county_name:
                        overridden_id = aid
                        break
            # Otherwise: dominant authority wins by the usual sort chain.
            #   1. most rows for THIS ZIP (typez+type4 combined)
            #   2. type-z first (True > False) -- secondary signal
            #   3. non-placeholder name (True > False -- vetted name wins)
            #   4. fewer total ZIPs (more-specific authority wins;
            #      negate so max() picks the smallest)
            #   5. lowest id (stable tiebreaker)
            best_id = (
                overridden_id
                if overridden_id is not None
                else max(
                    aids,
                    key=lambda aid: (
                        counts.get(aid, 0),
                        has_typez.get(aid, False),
                        not _is_placeholder_name(seen_authorities[aid]),
                        -total_zip_counts.get(aid, 0),
                        -aid,
                    ),
                )
            )
            chosen = seen_authorities[best_id]
            if auth_type == "city":
                picked_city = chosen
            else:
                picked_county = chosen
            out.append(chosen)
        elif auth_type == "district":
            # Districts with a type-z (zip-wide) record genuinely apply
            # to every address in the ZIP -- include all (e.g. MN's 3
            # metro transit districts at Minneapolis 55401).
            #
            # Districts with ONLY type-4 records fall into three camps:
            #
            # 1. Multiple competing CIDs (Community Improvement
            #    Districts, STAR Bond, TIF) on the same ZIP. The SST
            #    file lists every CID overlapping the ZIP; summing
            #    them over-collects by 3-4% in KS / OK / TN. Without
            #    a ZIP+4 we can't pick a single correct one, so drop
            #    them all.
            #
            # 2. A SINGLE county-wide district whose SST encoding uses
            #    per-+4 records to cover every address (e.g. Fulton
            #    County TSPLOST at GA Roswell 30075 has 107 type-4
            #    records all pointing at the one TSPLOST authority).
            #    Dropping it under-collects by the district rate.
            #
            # 3. A SINGLE stray binding -- the SST file lists a
            #    district claim on a ZIP that's actually outside the
            #    district's geographic area, with only a handful of
            #    type-4 records (e.g. Fulton TSPLOST at Suwanee 30024
            #    in Gwinnett County has 7 stray type-4 rows). The
            #    district doesn't actually apply.
            #
            # Heuristic: include a lone type-4-only district only if
            # its per-ZIP row count is at least ``_MIN_LONE_DISTRICT_ROWS``
            # (proxy for "covers most of the ZIP, not just a few stray
            # +4 ranges"). 20 is empirically the right elbow: real GA
            # county-wide TSPLOSTs ship ~100+ type-4 rows per covered
            # ZIP; stray bindings ship 1-10.
            typez_aids = [aid for aid in aids if has_typez.get(aid, False)]
            type4_only_aids = [aid for aid in aids if not has_typez.get(aid, False)]
            for aid in typez_aids:
                out.append(seen_authorities[aid])
            if (
                len(type4_only_aids) == 1
                and counts.get(type4_only_aids[0], 0) >= _MIN_LONE_DISTRICT_ROWS
            ):
                out.append(seen_authorities[type4_only_aids[0]])
            # iter-169 OH COTA bug: when MULTIPLE type-4-only districts
            # exist (e.g. OH Dublin 43017 = COTA 260 rows + OH-district-
            # 96000 71 rows + OH-district-98000 28 rows), the original
            # lone-district rule dropped ALL of them. But COTA is the
            # right answer; the other two are unmodeled special districts
            # with placeholder names. Include the dominant CURATED
            # type-4-only district when it has >= _MIN_LONE_DISTRICT_ROWS
            # AND dominates the runner-up by 2x. The "curated name"
            # filter naturally excludes the KS/OK/TN competing-CID case
            # (placeholder TIF/CID names) while letting OH transit
            # authorities through.
            elif len(type4_only_aids) > 1:
                curated_with_counts = sorted(
                    (
                        (aid, counts.get(aid, 0))
                        for aid in type4_only_aids
                        if not _is_placeholder_name(seen_authorities[aid])
                    ),
                    key=lambda x: -x[1],
                )
                if curated_with_counts:
                    top_aid, top_count = curated_with_counts[0]
                    runner_up_count = max(
                        (counts.get(aid, 0) for aid in type4_only_aids if aid != top_aid),
                        default=0,
                    )
                    if top_count >= _MIN_LONE_DISTRICT_ROWS and top_count >= 2 * max(
                        runner_up_count, 1
                    ):
                        out.append(seen_authorities[top_aid])
        else:
            # state: pass through.
            out.extend(seen_authorities[aid] for aid in aids)

    # State-specific exclusivity: in TN and WA the SST 'city' code
    # already includes the local county portion (TN: city = county
    # rate uniformly; WA: city = combined city+county+transit). When
    # both a city and a county come back for the same ZIP, dropping
    # the county avoids double-collecting that local rate.
    #
    # OK / KS / etc. genuinely separate city + county (county 0.125-1%,
    # city 1-4% on top), so we ONLY apply this filter for the few
    # states with the city-includes-county pattern.
    if (
        picked_city is not None
        and picked_county is not None
        and _state_abbrev(picked_city) in {"TN", "WA"}
    ):
        out = [a for a in out if a is not picked_county]

    # State-specific district dedup: in TN, the only district codes
    # that load (code 79) are county-level IMPROVE Act / transit
    # overlays. A ZIP that physically straddles multiple counties
    # (e.g. Brentwood 37027 spanning Williamson + Davidson + bordering
    # counties) collects type-z bindings to every county's IMPROVE Act,
    # which would stack 4x at 0.5% each (= 2% extra) on top of the
    # already-correct city local rate. Pick the dominant one (most
    # rows for THIS ZIP, then most total ZIPs as a regional-fit signal).
    state_abbrev = _state_abbrev(picked_city)
    if state_abbrev == "TN":
        district_authorities = [a for a in out if a.authority_type == "district"]
        if len(district_authorities) > 1:
            best = max(
                district_authorities,
                key=lambda a: (
                    counts.get(a.id, 0),
                    total_zip_counts.get(a.id, 0),
                    -a.id,
                ),
            )
            out = [a for a in out if a.authority_type != "district" or a is best]

    return _stable_sort(out)


_TYPE_ORDER = {"state": 0, "county": 1, "city": 2, "district": 3}


def _stable_sort(authorities: list[TaxAuthority]) -> list[TaxAuthority]:
    """Sort authorities into a predictable jurisdiction-stack order."""
    return sorted(
        authorities,
        key=lambda a: (_TYPE_ORDER.get(a.authority_type, 99), a.name),
    )


def _state_abbrev(auth: TaxAuthority | None) -> str | None:
    """Safely extract ``auth.state.abbrev``.

    The :class:`TaxAuthority` ORM model has ``state`` as an eager-loaded
    relationship; in some unit-test fixtures the attribute may be
    missing entirely. Using ``getattr`` with defaults keeps the lookup
    engine resilient to either shape.
    """
    if auth is None:
        return None
    state = getattr(auth, "state", None)
    if state is None:
        return None
    return getattr(state, "abbrev", None)


async def _canonical_state_for_zip(session: AsyncSession, zip5: str) -> str | None:
    """Return the state abbrev that canonically owns ``zip5`` per the ZCTA loader.

    Iter-167: cross-state ZIP dedup truth-source.

    The Census ZCTA file binds every US ZIP to a single state (the
    state with the most county-row intersections per
    :func:`opensalestax.data.zcta_loader.parse_zcta_state_rows`).
    That binding is loaded as a ``DataVersion`` whose ``source``
    starts with ``zcta`` (e.g. ``zcta-census-2020``) and a state-
    level ``TaxAuthority`` boundary. This boundary represents the
    geographic ground truth for "which state does this ZIP
    physically sit in," independent of what multiple states' SST
    quarterly files might claim.

    Returns ``None`` when no ZCTA-sourced boundary exists for the
    ZIP (e.g. some PO-box-only ZIPs that even the USPS supplement
    didn't fill, or a state whose ZCTA load was skipped).
    """
    stmt = (
        select(State.abbrev)
        .join(DataVersion, DataVersion.state_id == State.id)
        .join(Boundary, Boundary.data_version_id == DataVersion.id)
        .where(
            Boundary.zip5 == zip5,
            DataVersion.source.like("zcta%"),
        )
        .limit(1)
    )
    return (await session.execute(stmt)).scalar_one_or_none()


def _filter_to_canonical_state(
    authorities: list[TaxAuthority],
    canonical_abbrev: str | None,
) -> list[TaxAuthority]:
    """Filter authorities to those whose state matches ``canonical_abbrev``.

    Iter-167 fix for the cross-state ZIP bug (handoff iter-163..166).
    Some ZIPs straddle a state line and end up with boundary rows
    in BOTH states' SST quarterly files. The lookup engine
    previously returned all authorities -- including TWO state
    authorities -- and the rate calculator summed both states'
    rates.

    For ZIP 56164 (Pipestone, MN) the pre-fix engine emitted
    Minnesota AND South Dakota state authorities and summed
    6.875% + 4.2% = 11.075%.

    Iter-166 picked the state with the most authorities, but that
    backfired on ZIPs like 56144 where SD's SST file bound more
    rows than MN's, even though the ZIP is physically in MN per
    the Census ZCTA file.

    Iter-167 instead defers to :func:`_canonical_state_for_zip`,
    which queries the ZCTA-sourced boundary -- the geographic
    ground truth. If no canonical state can be determined
    (no ZCTA boundary loaded for this ZIP), this function
    falls back to authority-count majority for compatibility.

    Authorities without a ``.state`` (shouldn't happen but
    defensive) pass through unchanged.
    """
    if not authorities:
        return authorities

    # Find every state present in the candidate authorities.
    present_states: set[str] = {
        abbrev for auth in authorities if (abbrev := _state_abbrev(auth)) is not None
    }

    if len(present_states) <= 1:
        # Single state (or no state info) -- no filtering needed.
        return authorities

    target = canonical_abbrev
    if target is None or target not in present_states:
        # Fall back to majority-by-count when we have no ZCTA truth
        # OR the canonical state has no authorities in the candidate
        # pool (e.g. ZCTA says MN but only SD authorities loaded).
        counts: dict[str, int] = {}
        for auth in authorities:
            abbrev = _state_abbrev(auth)
            if abbrev:
                counts[abbrev] = counts.get(abbrev, 0) + 1
        if not counts:
            return authorities
        # Sort by (-count, abbrev): most authorities wins, alphabetical tiebreak.
        target = min(counts.keys(), key=lambda a: (-counts[a], a))

    return [auth for auth in authorities if _state_abbrev(auth) in (None, target)]


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
