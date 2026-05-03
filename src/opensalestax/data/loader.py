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

    Raises :class:`LoaderError` if the state isn't registered or
    the cache file isn't found.
    """
    state_abbrev = state_abbrev.upper()
    state_module = get_state_module(state_abbrev)
    if state_module is None:
        raise LoaderError(
            f"No state module registered for {state_abbrev!r}; "
            f"cannot load. Add a module under opensalestax/states/ "
            f"and register it via the registry."
        )

    rates_file = find_cached_file(state_abbrev, version_label, "R", cache_dir)
    if rates_file is None:
        suggested = resolve_filename(state_abbrev, version_label, "R")
        raise LoaderError(
            f"No cached rates file found for {state_abbrev} {version_label}. "
            f"Try `opensalestax data fetch {suggested}` first "
            f"(or .zip variant)."
        )

    full_label = _full_label(state_abbrev, version_label)

    # 1) State row -- find or create
    state_row = await _get_or_create_state(session, state_module)

    # 2) Idempotency: drop any pre-existing DataVersion with this label.
    #    Cascade rules on rates / boundaries handle the dependent rows.
    await _drop_existing_data_version(session, state_row.id, full_label)

    # 3) Fresh DataVersion
    data_version = DataVersion(
        state_id=state_row.id,
        source="sst",
        version_label=full_label,
        notes=f"Loaded by opensalestax data load on {dt.datetime.now(tz=dt.UTC).isoformat()}",
    )
    session.add(data_version)
    await session.flush()

    # 4) Rates -- group by authority and insert
    rate_rows = list(state_module.parse_rates(rates_file, full_label))
    authority_cache: dict[tuple[str, str], TaxAuthority] = {}
    rates_loaded = 0
    for row in rate_rows:
        authority = await _get_or_create_authority(
            session,
            authority_cache,
            state_row.id,
            row.authority_name,
            row.authority_type,
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
                data_version_id=data_version.id,
            )
        )
        rates_loaded += 1

    # 5) Boundaries (optional)
    boundaries_loaded = 0
    if load_boundaries:
        boundary_file = find_cached_file(state_abbrev, version_label, "B", cache_dir)
        if boundary_file is not None:
            for brow in state_module.parse_boundaries(boundary_file, full_label):
                authority = await _get_or_create_authority(
                    session,
                    authority_cache,
                    state_row.id,
                    brow.authority_name,
                    brow.authority_type,
                )
                session.add(
                    Boundary(
                        authority_id=authority.id,
                        zip5=brow.zip5,
                        zip4_low=brow.zip4_low,
                        zip4_high=brow.zip4_high,
                        address_pattern=brow.address_pattern,
                        data_version_id=data_version.id,
                    )
                )
                boundaries_loaded += 1

    # 6) Taxability matrix -- pre-populate the categories the state
    #    module knows about.
    today = dt.date.today()
    await _drop_existing_taxability(session, state_row.id)
    taxability_loaded = 0
    for category in DEFAULT_CATEGORIES:
        rule = state_module.taxability_for(category, today)
        if rule is None:
            continue
        session.add(
            TaxabilityRule(
                state_id=state_row.id,
                item_category=rule.item_category,
                is_taxable=rule.is_taxable,
                rate_modifier=rule.rate_modifier,
                notes=rule.notes,
                effective_from=rule.effective_from,
                effective_to=rule.effective_to,
            )
        )
        taxability_loaded += 1

    await session.commit()

    summary = LoadSummary(
        state_abbrev=state_abbrev,
        version_label=full_label,
        data_version_id=data_version.id,
        rates_loaded=rates_loaded,
        boundaries_loaded=boundaries_loaded,
        taxability_rules_loaded=taxability_loaded,
        authorities_created=len(authority_cache),
    )
    logger.info("loader: %s", summary)
    return summary


async def purge_data_version(
    session: AsyncSession,
    state_abbrev: str,
    version_label: str,
) -> bool:
    """Delete a specific DataVersion + cascade dependent rows.

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

    await session.delete(existing)
    await session.commit()
    return True


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
    """Normalize a version label to the canonical 'MN-SST-2026Q2FEB18' form."""
    label = version_label.upper()
    if "-" in label:
        return label
    return f"{state_abbrev.upper()}-SST-{label}"


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
    existing = (
        await session.execute(
            select(DataVersion).where(
                DataVersion.state_id == state_id,
                DataVersion.version_label == full_label,
            )
        )
    ).scalar_one_or_none()
    if existing is not None:
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
