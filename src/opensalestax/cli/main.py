# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""OpenSalesTax CLI entry point (Typer).

Subcommands:

- ``opensalestax version`` -- print the installed version.
- ``opensalestax serve``   -- run the API server (uvicorn).
- ``opensalestax data fetch``  -- download an SST file (by filename or --state/--version).
- ``opensalestax data load``   -- load a cached SST file into the database.
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
    list_loaded_versions,
    load_state_data,
    purge_data_version,
    resolve_filename,
)
from opensalestax.data.sst import (
    SstFilename,
    default_data_dir,
    download_sst_file,
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
                )
            except LoaderError as exc:
                typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
                raise typer.Exit(code=1) from exc
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
