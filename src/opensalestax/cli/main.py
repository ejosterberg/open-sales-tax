# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""OpenSalesTax CLI entry point (Typer).

Subcommands:

- ``opensalestax version`` -- print the installed version.
- ``opensalestax serve``   -- run the API server (uvicorn).
- ``opensalestax data fetch``  -- download an SST file (by filename or --state/--version).
- ``opensalestax data load``   -- load a cached SST file into the database.
- ``opensalestax data restore``-- fast install: pull a pre-loaded dump from
  the latest GitHub release and restore it into the local DB. Two-minute
  alternative to the ~50-minute manual fetch+load loop.
- ``opensalestax data status`` -- show what's loaded per state.
- ``opensalestax data purge``  -- delete a specific data version.
- ``opensalestax data list-versions`` -- list cached SST files (not yet loaded).

Run ``opensalestax --help`` for the full menu.
"""

from __future__ import annotations

import asyncio
import datetime as dt
from pathlib import Path

import typer

from opensalestax import __version__
from opensalestax.data.loader import (
    LoaderError,
    LoadSummary,
    ZctaLoadSummary,
    list_loaded_versions,
    load_state_data,
    load_zcta_state_boundaries,
    purge_data_version,
    resolve_filename,
)
from opensalestax.data.restore import (
    RestoreError,
    RestoreSummary,
    download_dump,
    get_current_alembic_revision,
    is_postgres_dsn,
    read_dump_sample,
    resolve_source,
    sniff_alembic_version,
    stream_dump_to_psql,
    validate_schema_compatibility,
)
from opensalestax.data.sst import (
    SstFilename,
    default_data_dir,
    download_sst_file,
)
from opensalestax.data.zcta_loader import (
    ZCTA_COUNTY_FILENAME,
    download_zcta_county_file,
)

app = typer.Typer(
    name="opensalestax",
    help="OpenSalesTax -- open-source US sales tax calculation API.",
    no_args_is_help=True,
)
data_app = typer.Typer(help="Manage SST data files.", no_args_is_help=True)
app.add_typer(data_app, name="data")
keys_app = typer.Typer(help="Manage API keys (api_key auth mode).", no_args_is_help=True)
app.add_typer(keys_app, name="keys")


# ---------------------------------------------------------------------------
# top-level commands
# ---------------------------------------------------------------------------
@app.command()
def version() -> None:
    """Print the installed OpenSalesTax version."""
    typer.echo(__version__)


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind interface."),  # noqa: S104
    port: int = typer.Option(8080, help="Bind port."),
    reload: bool = typer.Option(False, help="Auto-reload on code change (dev only)."),
) -> None:
    """Run the API server via uvicorn.

    Equivalent to::

        uvicorn --factory opensalestax.app:create_app --host <HOST> --port <PORT>

    Requires ``OPENSALESTAX_DATABASE_URL`` to be set.
    """
    import uvicorn

    uvicorn.run(
        "opensalestax.app:create_app",
        host=host,
        port=port,
        reload=reload,
        factory=True,
    )


# ---------------------------------------------------------------------------
# data subcommands
# ---------------------------------------------------------------------------
@data_app.command("fetch")
def data_fetch(
    filename: str | None = typer.Argument(
        None,
        help=(
            "SST filename, e.g. MNR2026Q2FEB18.zip. "
            "Omit and use --state + --version to construct it."
        ),
    ),
    state: str | None = typer.Option(
        None, "--state", "-s", help="USPS state abbreviation (e.g. MN)."
    ),
    version: str | None = typer.Option(
        None,
        "--version",
        "-v",
        help="Quarter suffix (e.g. 2026Q2FEB18). Used with --state.",
    ),
    kind: str = typer.Option(
        "R",
        "--kind",
        "-k",
        help="'R' for rates, 'B' for boundary. Only used with --state/--version.",
    ),
    dest_dir: Path | None = typer.Option(
        None, help="Override default cache directory (~/.opensalestax/data)."
    ),
) -> None:
    """Download and cache an SST quarterly file.

    Two invocation styles:

    \b
    1. Direct filename:
        opensalestax data fetch MNR2026Q2FEB18.zip

    2. State + version (constructs the filename):
        opensalestax data fetch --state MN --version 2026Q2FEB18
    """
    resolved = filename
    if resolved is None:
        if not state or not version:
            typer.secho(
                "error: provide either FILENAME or --state and --version",
                fg=typer.colors.RED,
                err=True,
            )
            raise typer.Exit(code=2)
        try:
            resolved = resolve_filename(state, version, kind.upper())
        except ValueError as exc:
            typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=2) from exc

    try:
        path = download_sst_file(resolved, dest_dir)
    except (ValueError, OSError) as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"cached: {path}")


@data_app.command("list-versions")
def data_list_versions(
    cache_dir: Path | None = typer.Option(None, help="Override default cache directory."),
) -> None:
    """List cached SST files on disk (not necessarily loaded into the DB)."""
    target = cache_dir or default_data_dir()
    if not target.exists():
        typer.echo(f"(empty cache: {target} doesn't exist)")
        raise typer.Exit(code=0)

    found = []
    for path in sorted(target.iterdir()):
        if path.is_file():
            try:
                parsed = SstFilename.parse(path.name)
                found.append((parsed.version_label, parsed.kind, path))
            except ValueError:
                continue

    if not found:
        typer.echo(f"(no SST files in {target})")
        return

    typer.echo(f"cache: {target}")
    typer.echo(f"{'version':35s} {'kind':5s}  path")
    for label, kind, path in found:
        typer.echo(f"{label:35s} {kind:5s}  {path}")


@data_app.command("load")
def data_load(
    state: str = typer.Option(..., "--state", "-s", help="USPS state abbreviation."),
    version: str = typer.Option(
        ...,
        "--version",
        "-v",
        help="Version label (e.g. 2026Q2FEB18 or MN-SST-2026Q2FEB18).",
    ),
    boundary_version: str | None = typer.Option(
        None,
        "--boundary-version",
        "-b",
        help=(
            "Boundary file version label, when SST publishes the "
            "boundary file under a different release date than "
            "rates (common). Defaults to --version."
        ),
    ),
    cache_dir: Path | None = typer.Option(None, help="Override default cache directory."),
    skip_boundaries: bool = typer.Option(
        False,
        "--skip-boundaries",
        help="Skip boundary loading (faster; rate calculations still work for seeded ZIPs).",
    ),
) -> None:
    """Load a state's cached SST data into the database.

    Idempotent: re-running drops any existing DataVersion with the
    same label and inserts fresh rows.
    """
    summary = asyncio.run(
        _load_async(
            state=state,
            version=version,
            cache_dir=cache_dir,
            load_boundaries=not skip_boundaries,
            boundary_version=boundary_version,
        )
    )
    typer.echo(
        f"loaded: {summary.state_abbrev} {summary.version_label}\n"
        f"  data_version_id:  {summary.data_version_id}\n"
        f"  authorities:      {summary.authorities_created}\n"
        f"  rates:            {summary.rates_loaded}\n"
        f"  boundaries:       {summary.boundaries_loaded}\n"
        f"  taxability rules: {summary.taxability_rules_loaded}"
    )


@data_app.command("load-zcta")
def data_load_zcta(
    cache_dir: Path | None = typer.Option(
        None, help="Override default cache directory (~/.opensalestax/data)."
    ),
    only: str | None = typer.Option(
        None,
        "--only",
        help=(
            "Comma-separated list of state abbrevs to seed (e.g. "
            "'CA,TX,NY'). Default: every state in the catalog."
        ),
    ),
    skip: str | None = typer.Option(
        None,
        "--skip",
        help=(
            "Comma-separated list of state abbrevs to exclude (e.g. "
            "the SST states whose own boundary file is already loaded)."
        ),
    ),
) -> None:
    """Seed ZIP -> state boundaries from the Census ZCTA -> County file.

    Downloads the ~3 MB national ZCTA-to-county relationship file
    once (cached in the data dir) and inserts a ZIP -> state
    boundary row for every US ZIP that maps to a state with a
    registered module. Idempotent: re-running drops any prior
    ``zcta-census-2020`` DataVersion per state.

    The state-level binding is what unblocks the engine for the 23
    self-seeded modules (CA, TX, NY, FL, ...) that ship rates but
    no SST boundary file. Per-county/sub-state boundaries for those
    states wait on the SubJurisdiction Protocol work.
    """
    only_tuple = tuple(s.strip().upper() for s in only.split(",") if s.strip()) if only else None
    skip_tuple = tuple(s.strip().upper() for s in skip.split(",") if s.strip()) if skip else ()
    summary = asyncio.run(_load_zcta_async(cache_dir=cache_dir, only=only_tuple, skip=skip_tuple))
    typer.echo(
        f"ZCTA boundaries seeded:\n"
        f"  states_seeded:    {summary.states_seeded}\n"
        f"  boundaries_added: {summary.boundaries_loaded}"
    )
    if summary.skipped_states:
        typer.echo(f"  skipped (no module): {', '.join(summary.skipped_states)}")


@data_app.command("status")
def data_status() -> None:
    """List every (state, version) pair currently loaded into the database."""
    rows = asyncio.run(_status_async())
    if not rows:
        typer.echo("(no data versions loaded)")
        return
    typer.echo(f"{'state':6s} {'version':40s} fetched_at")
    for state_abbrev, label, fetched_at in rows:
        typer.echo(f"{state_abbrev:6s} {label:40s} {fetched_at.isoformat()}")


@data_app.command("restore")
def data_restore(
    release: str | None = typer.Option(
        None,
        "--release",
        help=(
            "Release tag to pull the dump from (e.g. v0.23.0). "
            "Default: latest release. Mutually exclusive with --file."
        ),
    ),
    file: Path | None = typer.Option(
        None,
        "--file",
        exists=False,  # we surface a friendlier error than typer's
        help="Local path to a .sql.gz dump. Mutually exclusive with --release.",
    ),
    cache_dir: Path | None = typer.Option(
        None,
        "--cache-dir",
        help="Where to cache downloaded dumps (default: ~/.opensalestax/data).",
    ),
    skip_schema_check: bool = typer.Option(
        False,
        "--skip-schema-check",
        help=(
            "Bypass the alembic-revision compatibility check. Use with care; "
            "the consumer database must be at a compatible head."
        ),
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Resolve the source and validate the dump's schema, but do not apply it.",
    ),
) -> None:
    """Restore a pre-loaded data dump (the recommended fast install path).

    By default this fetches the latest published GitHub release dump,
    validates that its schema head matches the consumer database, then
    pipes the gzipped SQL through ``psql``. Net effect: a fresh local
    install is fully populated with all 24 SST states + AZ in under
    two minutes, instead of the ~50-minute manual fetch+load loop.

    PostgreSQL only -- the dump uses pg_dump's COPY format. MariaDB
    deployments must use ``opensalestax data load`` per state.
    """
    # Engine guard first; everything else is wasted effort on MariaDB.
    from opensalestax.settings import get_settings

    settings = get_settings()
    if not is_postgres_dsn(settings.database_dsn):
        typer.secho(
            "Restore from PostgreSQL dump only; for MariaDB, use the manual data load path:",
            fg=typer.colors.YELLOW,
            err=True,
        )
        typer.echo(
            "    opensalestax data fetch --state <ST> --version <VER>\n"
            "    opensalestax data load  --state <ST> --version <VER>",
            err=True,
        )
        raise typer.Exit(code=2)

    try:
        source = resolve_source(release=release, file=file)
    except RestoreError as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"source: {source.display}")

    # Materialize the dump locally if we resolved to a URL.
    if source.is_local:
        dump_path = source.local_path
        assert dump_path is not None
    else:
        target_dir = cache_dir or default_data_dir()
        target_dir.mkdir(parents=True, exist_ok=True)
        dump_path = target_dir / Path(source.url or "").name
        typer.echo(f"downloading -> {dump_path}")
        try:
            download_dump(source.url or "", dump_path)
        except RestoreError as exc:
            typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from exc

    # Schema-version check: refuse to apply a dump that pins a head
    # different from the one Alembic just produced. A workflow-built
    # dump excludes alembic_version data and so this is a no-op there.
    if not skip_schema_check:
        try:
            sample = read_dump_sample(dump_path)
            dump_rev = sniff_alembic_version(sample)
            current_rev = get_current_alembic_revision()
            validate_schema_compatibility(dump_rev, current_rev)
        except RestoreError as exc:
            typer.secho(f"schema check failed: {exc}", fg=typer.colors.RED, err=True)
            raise typer.Exit(code=1) from exc

    if dry_run:
        typer.secho("dry-run: skipping psql apply", fg=typer.colors.YELLOW)
        raise typer.Exit(code=0)

    typer.echo("applying dump (piping through psql)...")
    try:
        stream_dump_to_psql(dump_path, settings.database_dsn)
    except RestoreError as exc:
        typer.secho(f"restore failed: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc

    summary = asyncio.run(_restore_summary_async(source.display))
    typer.secho(
        f"Restored {summary.states} states, {summary.rates} rates, "
        f"{summary.boundaries} boundaries from {summary.source}",
        fg=typer.colors.GREEN,
    )


async def _restore_summary_async(source: str) -> RestoreSummary:
    """Query post-restore counts so the CLI can echo a one-line summary."""
    from sqlalchemy import func, select
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.db.models import Boundary, Rate, State, TaxAuthority
    from opensalestax.db.session import get_engine, reset_engine

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            states = (await session.execute(select(func.count()).select_from(State))).scalar_one()
            rates = (await session.execute(select(func.count()).select_from(Rate))).scalar_one()
            bounds = (
                await session.execute(select(func.count()).select_from(Boundary))
            ).scalar_one()
            auths = (
                await session.execute(select(func.count()).select_from(TaxAuthority))
            ).scalar_one()
            return RestoreSummary(
                states=int(states),
                rates=int(rates),
                boundaries=int(bounds),
                authorities=int(auths),
                source=source,
            )
    finally:
        await reset_engine()


@data_app.command("purge")
def data_purge(
    state: str = typer.Option(..., "--state", "-s", help="USPS state abbreviation."),
    version: str = typer.Option(..., "--version", "-v", help="Version label to delete."),
) -> None:
    """Delete a specific (state, version) data version + cascade dependent rows."""
    deleted = asyncio.run(_purge_async(state, version))
    if deleted:
        typer.echo(f"purged: {state.upper()} {version}")
    else:
        typer.secho(
            f"not found: {state.upper()} {version}",
            fg=typer.colors.YELLOW,
            err=True,
        )
        raise typer.Exit(code=1)


# ---------------------------------------------------------------------------
# Async helpers (Typer commands are sync; we bridge with asyncio.run)
# ---------------------------------------------------------------------------
async def _load_async(
    state: str,
    version: str,
    cache_dir: Path | None,
    load_boundaries: bool,
    boundary_version: str | None = None,
) -> LoadSummary:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.db.session import get_engine, reset_engine

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            try:
                return await load_state_data(
                    session,
                    state_abbrev=state,
                    version_label=version,
                    cache_dir=cache_dir,
                    load_boundaries=load_boundaries,
                    boundary_version_label=boundary_version,
                )
            except LoaderError as exc:
                typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
                raise typer.Exit(code=1) from exc
    finally:
        await reset_engine()


async def _load_zcta_async(
    cache_dir: Path | None,
    only: tuple[str, ...] | None,
    skip: tuple[str, ...],
) -> ZctaLoadSummary:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.db.session import get_engine, reset_engine

    target_dir = cache_dir or default_data_dir()
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / ZCTA_COUNTY_FILENAME
    if not target_path.exists():
        typer.echo(f"downloading ZCTA file -> {target_path}...")
        download_zcta_county_file(dest_dir=target_dir)

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            return await load_zcta_state_boundaries(
                session,
                source_file=target_path,
                only_states=only,
                skip_states=skip,
            )
    finally:
        await reset_engine()


async def _status_async() -> list[tuple[str, str, dt.datetime]]:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.db.session import get_engine, reset_engine

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            return await list_loaded_versions(session)
    finally:
        await reset_engine()


async def _purge_async(state: str, version: str) -> bool:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.db.session import get_engine, reset_engine

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            return await purge_data_version(session, state, version)
    finally:
        await reset_engine()


# ---------------------------------------------------------------------------
# keys subcommands -- API-key management for api_key auth mode
# ---------------------------------------------------------------------------
@keys_app.command("create")
def keys_create(
    label: str = typer.Argument(
        ..., help="Human-readable label (e.g. 'eric-laptop', 'scbooks-prod')."
    ),
    rate_limit_per_minute: int | None = typer.Option(
        None,
        "--rate-limit",
        help="Override the default rate limit for this key.",
    ),
    notes: str | None = typer.Option(None, "--notes", help="Free-form notes for the key."),
) -> None:
    """Mint a fresh API key.

    The plaintext is printed ONCE -- save it now. The database
    only ever stores the hash. The label can be reused for "rotate
    and revoke" workflows.
    """
    minted = asyncio.run(_keys_create_async(label, rate_limit_per_minute, notes))
    typer.secho(f"created key id={minted.db_id}, label={minted.label!r}", fg=typer.colors.GREEN)
    typer.echo("plaintext (save now; not retrievable):")
    typer.secho(f"  {minted.plaintext}", bold=True)


@keys_app.command("list")
def keys_list() -> None:
    """List active (non-revoked) API keys."""
    rows = asyncio.run(_keys_list_async())
    if not rows:
        typer.echo("(no active API keys)")
        return
    typer.echo(f"{'id':>4s}  {'label':30s} {'created_at':25s} last_used_at")
    for row in rows:
        last = row.last_used_at.isoformat() if row.last_used_at else "never"
        typer.echo(f"{row.id:>4d}  {row.label:30s} {row.created_at.isoformat():25s} {last}")


@keys_app.command("revoke")
def keys_revoke(
    label: str = typer.Argument(..., help="Revoke every active key with this label."),
) -> None:
    """Revoke every active API key matching ``label``."""
    n = asyncio.run(_keys_revoke_async(label))
    if n == 0:
        typer.secho(f"no active keys with label {label!r}", fg=typer.colors.YELLOW)
        raise typer.Exit(code=1)
    typer.secho(f"revoked {n} key(s)", fg=typer.colors.GREEN)


# ---------------------------------------------------------------------------
# keys async bridges
# ---------------------------------------------------------------------------
async def _keys_create_async(
    label: str,
    rate_limit_per_minute: int | None,
    notes: str | None,
):
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.auth import create_api_key
    from opensalestax.db.session import get_engine, reset_engine

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            return await create_api_key(
                session,
                label=label,
                rate_limit_per_minute=rate_limit_per_minute,
                notes=notes,
            )
    finally:
        await reset_engine()


async def _keys_list_async():
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.auth import list_active_api_keys
    from opensalestax.db.session import get_engine, reset_engine

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            return await list_active_api_keys(session)
    finally:
        await reset_engine()


async def _keys_revoke_async(label: str) -> int:
    from sqlalchemy.ext.asyncio import async_sessionmaker

    from opensalestax.auth import revoke_api_key
    from opensalestax.db.session import get_engine, reset_engine

    engine = get_engine()
    sessionmaker = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with sessionmaker() as session:
            return await revoke_api_key(session, label)
    finally:
        await reset_engine()


if __name__ == "__main__":
    app()
