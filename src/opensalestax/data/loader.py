# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Load parsed SST data into the database.

The missing piece between :mod:`opensalestax.data.sst` (fetcher),
:mod:`opensalestax.data.sst_parser` (raw parser), the per-state
modules in :mod:`opensalestax.states`, and the ORM tables in
:mod:`opensalestax.db.models`.

Workflow (see ``cli/main.py`` ``data load`` for the entry point):

1. Resolve a state abbrev + version label to the cached file
2. Get the state module from the registry
3. Stream RateRow / BoundaryRow records from the module's parsers
4. Open a DB session and:
   - Find or create the State row
   - Drop any existing DataVersion with the same label (idempotency)
   - Create a fresh DataVersion row
   - Find or create TaxAuthority rows for each unique
     (state, name, type)
   - Insert Rate rows linked to authorities + data version
   - Insert Boundary rows linked to authorities + data version
   - Insert TaxabilityRule rows from the state module's matrix
"""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.data.sst import SstFilename, default_data_dir, file_url
from opensalestax.db.models import (
    Boundary,
    DataVersion,
    HolidayPeriod,
    Rate,
    State,
    TaxabilityRule,
    TaxAuthority,
)
from opensalestax.states.protocol import StateModule
from opensalestax.states.registry import get_state_module

logger = logging.getLogger(__name__)

# The default categories the loader populates per state from the
# state module's taxability_for() method. Categories not in this
# list aren't pre-populated; the engine falls back to "taxable
# unless the rule says otherwise" anyway.
DEFAULT_CATEGORIES: tuple[str, ...] = (
    "general",
    "clothing",
    "groceries",
    "prescription_drugs",
    "prepared_food",
    "digital_goods",
)


@dataclass(frozen=True, slots=True)
class LoadSummary:
    """Result of a successful load operation."""

    state_abbrev: str
    version_label: str
    data_version_id: int
    rates_loaded: int
    boundaries_loaded: int
    taxability_rules_loaded: int
    authorities_created: int
    holidays_loaded: int = 0


class LoaderError(Exception):
    """Top-level error raised by the loader."""


def resolve_filename(state_abbrev: str, version_label: str, kind: str) -> str:
    """Build the SST filename for a state + version + kind ('R' or 'B').

    ``version_label`` may be either the bare quarterly suffix
    (``"2026Q2FEB18"``) OR the full SST-style label
    (``"MN-SST-2026Q2FEB18"``). Both are accepted for ergonomics.
    """
    if kind not in {"R", "B"}:
        raise ValueError(f"kind must be 'R' or 'B', got {kind!r}")

    suffix = version_label.upper()
    if "-" in suffix:
        # Full label like 'MN-SST-2026Q2FEB18'; take the last segment
        suffix = suffix.split("-")[-1]

    state = state_abbrev.upper()
    # Try the .csv form first; SST sometimes publishes only one variant
    return f"{state}{kind}{suffix}.csv"


def find_cached_file(
    state_abbrev: str,
    version_label: str,
    kind: str,
    cache_dir: Path | None = None,
) -> Path | None:
    """Look for a cached SST file matching ``state_abbrev`` + ``version_label`` + ``kind``.

    Tries both ``.csv`` and ``.zip`` extensions; returns the first
    matching path or None if neither exists.
    """
    cache = cache_dir or default_data_dir()
    if not cache.exists():
        return None

    target_csv = resolve_filename(state_abbrev, version_label, kind)
    target_zip = target_csv[:-4] + ".zip"

    for name in (target_csv, target_zip):
        candidate = cache / name
        if candidate.is_file():
            return candidate
    return None


async def load_state_data(
    session: AsyncSession,
    state_abbrev: str,
    version_label: str,
    cache_dir: Path | None = None,
    *,
    load_boundaries: bool = True,
    boundary_version_label: str | None = None,
) -> LoadSummary:
    """Load a state's SST data from the cache into the database.

    Idempotent: if a :class:`DataVersion` with the same label
    already exists for this state + source, it (and all rows that
    reference it via cascade) is dropped before the fresh insert.
    Re-running the same command produces the same DB state.

    ``load_boundaries=False`` is a convenience for the SST states
    where the boundary file is too large to keep in test fixtures
    (most of them); skipping doesn't affect rate calculations as
    long as boundaries are loaded by some other path.

    ``boundary_version_label`` lets the caller point at a boundary
    file with a different release date than the rate file -- common
    in the SST publishing schedule (e.g. GA rates 2026Q2FEB19 +
    GA boundaries 2026Q2FEB16). If omitted, the rate
    ``version_label`` is reused.

    Raises :class:`LoaderError` if the state isn't registered or
    the cache file isn't found.
    """
    state_abbrev = state_abbrev.upper()
    state_module = _require_state_module(state_abbrev)
    self_seeded = bool(getattr(state_module, "self_seeded", False))
    rates_file = _resolve_rates_file(state_abbrev, version_label, cache_dir, self_seeded)

    full_label = _full_label(state_abbrev, version_label)
    state_row = await _get_or_create_state(session, state_module)
    await _drop_existing_data_version(session, state_row.id, full_label)
    data_version = await _create_data_version(session, state_row.id, full_label)

    authority_cache: dict[tuple[str, str], TaxAuthority] = {}
    rates_loaded = await _load_rates(
        session,
        state_module,
        rates_file,
        full_label,
        state_row.id,
        data_version.id,
        authority_cache,
    )
    boundaries_loaded = await _maybe_load_boundaries(
        session,
        state_module,
        state_abbrev,
        boundary_version_label or version_label,
        cache_dir,
        full_label,
        state_row.id,
        data_version.id,
        authority_cache,
        load_boundaries=load_boundaries,
        self_seeded=self_seeded,
    )
    taxability_loaded = await _load_taxability(session, state_module, state_row.id)
    holidays_loaded = await _load_holidays(session, state_module, state_row.id)

    await session.commit()

    summary = LoadSummary(
        state_abbrev=state_abbrev,
        version_label=full_label,
        data_version_id=data_version.id,
        rates_loaded=rates_loaded,
        boundaries_loaded=boundaries_loaded,
        taxability_rules_loaded=taxability_loaded,
        authorities_created=len(authority_cache),
        holidays_loaded=holidays_loaded,
    )
    logger.info("loader: %s", summary)
    return summary


# ---------------------------------------------------------------------------
# load_state_data helpers (kept module-private for clarity)
# ---------------------------------------------------------------------------
def _require_state_module(state_abbrev: str) -> StateModule:
    state_module = get_state_module(state_abbrev)
    if state_module is None:
        raise LoaderError(
            f"No state module registered for {state_abbrev!r}; "
            f"cannot load. Add a module under opensalestax/states/ "
            f"and register it via the registry."
        )
    return state_module


def _resolve_rates_file(
    state_abbrev: str,
    version_label: str,
    cache_dir: Path | None,
    self_seeded: bool,
) -> Path | None:
    """Return the cached rates file path, or None for self-seeded states."""
    if self_seeded:
        return None
    rates_file = find_cached_file(state_abbrev, version_label, "R", cache_dir)
    if rates_file is None:
        suggested = resolve_filename(state_abbrev, version_label, "R")
        raise LoaderError(
            f"No cached rates file found for {state_abbrev} {version_label}. "
            f"Try `opensalestax data fetch {suggested}` first "
            f"(or .zip variant)."
        )
    return rates_file


async def _create_data_version(
    session: AsyncSession, state_id: int, full_label: str
) -> DataVersion:
    data_version = DataVersion(
        state_id=state_id,
        source="sst",
        version_label=full_label,
        notes=f"Loaded by opensalestax data load on {dt.datetime.now(tz=dt.UTC).isoformat()}",
    )
    session.add(data_version)
    await session.flush()
    return data_version


async def _load_rates(
    session: AsyncSession,
    state_module: StateModule,
    rates_file: Path | None,
    full_label: str,
    state_id: int,
    data_version_id: int,
    authority_cache: dict[tuple[str, str], TaxAuthority],
) -> int:
    """Insert rate rows yielded by the state module; return the count."""
    rate_rows = list(state_module.parse_rates(rates_file, full_label))  # type: ignore[arg-type]
    rates_loaded = 0
    for row in rate_rows:
        authority = await _get_or_create_authority(
            session, authority_cache, state_id, row.authority_name, row.authority_type
        )
        session.add(
            Rate(
                authority_id=authority.id,
                rate_pct=row.rate_pct,
                effective_from=row.effective_from,
                effective_to=row.effective_to,
                applies_to_categories=(
                    list(row.applies_to_categories)
                    if row.applies_to_categories is not None
                    else None
                ),
                data_version_id=data_version_id,
            )
        )
        rates_loaded += 1
    return rates_loaded


async def _maybe_load_boundaries(
    session: AsyncSession,
    state_module: StateModule,
    state_abbrev: str,
    version_label: str,
    cache_dir: Path | None,
    full_label: str,
    state_id: int,
    data_version_id: int,
    authority_cache: dict[tuple[str, str], TaxAuthority],
    *,
    load_boundaries: bool,
    self_seeded: bool,
) -> int:
    """Insert boundary rows if a file exists and loading isn't suppressed."""
    if not load_boundaries or self_seeded:
        return 0
    boundary_file = find_cached_file(state_abbrev, version_label, "B", cache_dir)
    if boundary_file is None:
        return 0

    boundaries_loaded = 0
    for brow in state_module.parse_boundaries(boundary_file, full_label):
        authority = await _get_or_create_authority(
            session, authority_cache, state_id, brow.authority_name, brow.authority_type
        )
        session.add(
            Boundary(
                authority_id=authority.id,
                zip5=brow.zip5,
                zip4_low=brow.zip4_low,
                zip4_high=brow.zip4_high,
                address_pattern=brow.address_pattern,
                data_version_id=data_version_id,
            )
        )
        boundaries_loaded += 1
    return boundaries_loaded


async def _load_holidays(session: AsyncSession, state_module: StateModule, state_id: int) -> int:
    """Replace the state's holiday windows for the current year.

    Loads only the current year for v0.5; multi-year history can
    be added later by extending this loop.
    """
    current_year = dt.date.today().year
    # Drop existing holidays for this state to keep load idempotent.
    existing = list(
        (await session.execute(select(HolidayPeriod).where(HolidayPeriod.state_id == state_id)))
        .scalars()
        .all()
    )
    for old in existing:
        await session.delete(old)
    if existing:
        await session.flush()

    holidays_loaded = 0
    for window in state_module.holidays_for(current_year):
        cats = (
            list(window.applicable_categories) if window.applicable_categories is not None else None
        )
        session.add(
            HolidayPeriod(
                state_id=state_id,
                name=window.name,
                starts_on=window.starts_on,
                ends_on=window.ends_on,
                applicable_categories=cats,
                max_amount_per_item=window.max_amount_per_item,
                notes=window.notes,
            )
        )
        holidays_loaded += 1
    return holidays_loaded


async def _load_taxability(session: AsyncSession, state_module: StateModule, state_id: int) -> int:
    """Replace the state's taxability matrix with what the module reports today."""
    today = dt.date.today()
    await _drop_existing_taxability(session, state_id)
    taxability_loaded = 0
    for category in DEFAULT_CATEGORIES:
        rule = state_module.taxability_for(category, today)
        if rule is None:
            continue
        session.add(
            TaxabilityRule(
                state_id=state_id,
                item_category=rule.item_category,
                is_taxable=rule.is_taxable,
                rate_modifier=rule.rate_modifier,
                taxable_threshold_amount=rule.taxable_threshold_amount,
                threshold_semantic=rule.threshold_semantic,
                notes=rule.notes,
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
            )
        )
        taxability_loaded += 1
    return taxability_loaded


async def purge_data_version(
    session: AsyncSession,
    state_abbrev: str,
    version_label: str,
) -> bool:
    """Delete a specific DataVersion + the rows it brought in.

    The schema has ``Rate.data_version_id`` as ``ondelete=SET NULL``
    (rates can semantically outlive their data version). Purge
    semantics are different -- we want a quarterly refresh's rows
    GONE so the next refresh starts clean. So we explicitly delete
    rates with this ``data_version_id`` before deleting the
    version itself; ``Boundary`` already cascades.

    Returns True if a matching version was found and deleted;
    False if no matching version existed (nothing to purge).
    """
    state_abbrev = state_abbrev.upper()
    full_label = _full_label(state_abbrev, version_label)

    state_row = (
        await session.execute(select(State).where(State.abbrev == state_abbrev))
    ).scalar_one_or_none()
    if state_row is None:
        return False

    existing = (
        await session.execute(
            select(DataVersion).where(
                DataVersion.state_id == state_row.id,
                DataVersion.version_label == full_label,
            )
        )
    ).scalar_one_or_none()

    if existing is None:
        return False

    # Explicitly delete rates linked to this data version.
    # (Cascade-on-delete would do this automatically if the schema
    # used ondelete=CASCADE, but we kept SET NULL on Rate so that
    # data versions can be archived without losing rate history.
    # Purge is different from archive.)
    rates_to_drop = (
        (await session.execute(select(Rate).where(Rate.data_version_id == existing.id)))
        .scalars()
        .all()
    )
    for rate in rates_to_drop:
        await session.delete(rate)
    if rates_to_drop:
        await session.flush()

    await session.delete(existing)
    await session.commit()
    return True


@dataclass(frozen=True, slots=True)
class ZctaLoadSummary:
    """Result of a successful ZCTA boundary load."""

    states_seeded: int
    boundaries_loaded: int
    skipped_states: tuple[str, ...] = ()


async def load_zcta_state_boundaries(
    session: AsyncSession,
    source_file: Path,
    *,
    only_states: tuple[str, ...] | None = None,
    skip_states: tuple[str, ...] = (),
) -> ZctaLoadSummary:
    """Seed ZIP -> state boundaries from the Census ZCTA->county file.

    Idempotent at the (state, source) level: any prior DataVersion
    row for the same state with ``source='zcta-census-2020'`` is
    dropped before re-seeding. Existing SST-source DataVersions
    are untouched -- the engine de-dupes authorities via the
    ``DISTINCT`` clause in
    :func:`opensalestax.core.lookup.lookup_jurisdictions_by_zip`,
    so layering ZCTA on top of SST data is safe.

    ``only_states`` lets a caller restrict the load (e.g. just the
    23 self-seeded modules); when None every state in the catalog
    that has a registered module is seeded.

    ``skip_states`` excludes specific abbrevs (e.g. SST member
    states whose own quarterly boundary file is already loaded).
    """
    from opensalestax.data.zcta_loader import parse_zcta_state_rows

    only_set = {s.upper() for s in only_states} if only_states else None
    skip_set = {s.upper() for s in skip_states}

    # Group ZCTA rows by state so we can attribute boundaries to a
    # per-state DataVersion (keeps the data lineage clean).
    zips_by_state: dict[str, list[str]] = {}
    for row in parse_zcta_state_rows(source_file):
        if only_set is not None and row.state_abbrev not in only_set:
            continue
        if row.state_abbrev in skip_set:
            continue
        zips_by_state.setdefault(row.state_abbrev, []).append(row.zip5)

    states_seeded = 0
    boundaries_loaded = 0
    skipped: list[str] = []

    for abbrev in sorted(zips_by_state.keys()):
        state_module = get_state_module(abbrev)
        if state_module is None:
            skipped.append(abbrev)
            continue

        state_row = await _get_or_create_state(session, state_module)
        full_label = _zcta_label(abbrev)
        await _drop_existing_data_version(session, state_row.id, full_label)
        # Use a non-SST source string so this DataVersion lives
        # alongside any SST DataVersion for the same state.
        data_version = DataVersion(
            state_id=state_row.id,
            source="zcta-census-2020",
            version_label=full_label,
            notes="Census 2020 ZCTA->county relationship file (state-level binding only).",
        )
        session.add(data_version)
        await session.flush()

        # Find or create the state-level TaxAuthority once per state.
        state_auth = await _get_or_create_authority(
            session,
            cache={},
            state_id=state_row.id,
            name=state_module.state_name,
            authority_type="state",
        )

        for zip5 in zips_by_state[abbrev]:
            session.add(
                Boundary(
                    authority_id=state_auth.id,
                    zip5=zip5,
                    data_version_id=data_version.id,
                )
            )
            boundaries_loaded += 1
        states_seeded += 1

    await session.commit()
    return ZctaLoadSummary(
        states_seeded=states_seeded,
        boundaries_loaded=boundaries_loaded,
        skipped_states=tuple(skipped),
    )


def _zcta_label(state_abbrev: str) -> str:
    """Canonical DataVersion label for a ZCTA-sourced load."""
    return f"{state_abbrev.upper()}-ZCTA-2020"


async def list_loaded_versions(
    session: AsyncSession,
) -> list[tuple[str, str, dt.datetime]]:
    """Return ``[(state_abbrev, version_label, fetched_at), ...]`` for every loaded version."""
    stmt = (
        select(State.abbrev, DataVersion.version_label, DataVersion.fetched_at)
        .join(DataVersion, DataVersion.state_id == State.id)
        .order_by(State.abbrev, DataVersion.fetched_at.desc())
    )
    result = await session.execute(stmt)
    return [(row[0], row[1], row[2]) for row in result.all()]


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------
def _full_label(state_abbrev: str, version_label: str) -> str:
    """Normalize a version label to the canonical ``<STATE>-<SOURCE>-<SUFFIX>`` form.

    Accepts:

    - A bare suffix (``"2026Q2FEB18"``, ``"v0.2-statewide"``) -- prepends
      ``<STATE>-SST-``. Hyphens inside the suffix are kept.
    - An already-canonical label that starts with ``<STATE>-`` -- returned
      uppercased as-is.

    The previous implementation treated any hyphen as "already canonical,"
    which mangled labels like ``"v0.2-statewide"`` for non-SST states.
    """
    state = state_abbrev.upper()
    label = version_label.upper()
    if label.startswith(f"{state}-"):
        return label
    return f"{state}-SST-{label}"


async def _get_or_create_state(session: AsyncSession, state_module: StateModule) -> State:
    existing = (
        await session.execute(select(State).where(State.abbrev == state_module.state_abbrev))
    ).scalar_one_or_none()
    if existing is not None:
        return existing

    state = State(
        abbrev=state_module.state_abbrev,
        name=state_module.state_name,
        sst_member=state_module.sst_member,
        has_sales_tax=state_module.has_sales_tax,
    )
    session.add(state)
    await session.flush()
    return state


async def _drop_existing_data_version(
    session: AsyncSession, state_id: int, full_label: str
) -> None:
    """Drop a prior DataVersion + dependent rates and boundaries.

    The DB-level FK on ``boundaries.data_version_id`` is
    ``ondelete=CASCADE``, but SQLAlchemy's session-level dependency
    flushing tries to NULL the FK first before the cascade runs --
    which violates the NOT NULL constraint. Explicitly deleting
    boundaries (and rates, whose FK is ``ondelete=SET NULL``)
    before the DataVersion sidesteps both issues.
    """
    existing = (
        await session.execute(
            select(DataVersion).where(
                DataVersion.state_id == state_id,
                DataVersion.version_label == full_label,
            )
        )
    ).scalar_one_or_none()
    if existing is None:
        return

    boundaries_to_drop = list(
        (await session.execute(select(Boundary).where(Boundary.data_version_id == existing.id)))
        .scalars()
        .all()
    )
    for boundary in boundaries_to_drop:
        await session.delete(boundary)
    if boundaries_to_drop:
        await session.flush()

    rates_to_drop = list(
        (await session.execute(select(Rate).where(Rate.data_version_id == existing.id)))
        .scalars()
        .all()
    )
    for rate in rates_to_drop:
        await session.delete(rate)
    if rates_to_drop:
        await session.flush()
    await session.delete(existing)
    await session.flush()


async def _drop_existing_taxability(session: AsyncSession, state_id: int) -> None:
    existing = (
        (await session.execute(select(TaxabilityRule).where(TaxabilityRule.state_id == state_id)))
        .scalars()
        .all()
    )
    for rule in existing:
        await session.delete(rule)
    if existing:
        await session.flush()


async def _get_or_create_authority(
    session: AsyncSession,
    cache: dict[tuple[str, str], TaxAuthority],
    state_id: int,
    name: str,
    authority_type: str,
) -> TaxAuthority:
    """Find or create a TaxAuthority, with an in-load cache to avoid round-trips."""
    key = (name, authority_type)
    if key in cache:
        return cache[key]

    existing = (
        await session.execute(
            select(TaxAuthority).where(
                TaxAuthority.state_id == state_id,
                TaxAuthority.name == name,
                TaxAuthority.authority_type == authority_type,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
        cache[key] = existing
        return existing

    authority = TaxAuthority(state_id=state_id, name=name, authority_type=authority_type)
    session.add(authority)
    await session.flush()
    cache[key] = authority
    return authority


# Re-export file_url for the CLI's "where would this file come from?" hint
__all__ = [
    "DEFAULT_CATEGORIES",
    "LoadSummary",
    "LoaderError",
    "find_cached_file",
    "list_loaded_versions",
    "load_state_data",
    "purge_data_version",
    "resolve_filename",
    "file_url",
    "SstFilename",
]
