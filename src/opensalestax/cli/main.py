# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""OpenSalesTax CLI entry point (Typer).

Subcommands:

- ``opensalestax version`` -- print the installed version.
- ``opensalestax serve``   -- run the API server (uvicorn).
- ``opensalestax data fetch <state> <filename>`` -- download an SST file.
- ``opensalestax data list-versions``            -- show cached versions.

Run ``opensalestax --help`` for the full menu.
"""

from __future__ import annotations

from pathlib import Path

import typer

from opensalestax import __version__
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
    filename: str = typer.Argument(..., help="SST filename, e.g. MNR2026Q2FEB18.zip"),
    dest_dir: Path | None = typer.Option(
        None, help="Override default cache directory (~/.opensalestax/data)."
    ),
) -> None:
    """Download and cache an SST quarterly file.

    Validates the filename, picks the right SST URL (rates vs
    boundary), downloads via httpx, and stores in the cache. If
    the file already exists in the cache it's reused (no re-download).
    """
    try:
        path = download_sst_file(filename, dest_dir)
    except (ValueError, OSError) as exc:
        typer.secho(f"error: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(f"cached: {path}")


@data_app.command("list-versions")
def data_list_versions(
    cache_dir: Path | None = typer.Option(None, help="Override default cache directory."),
) -> None:
    """List cached SST data versions."""
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


if __name__ == "__main__":
    app()
