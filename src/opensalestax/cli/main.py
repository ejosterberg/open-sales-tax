# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""OpenSalesTax CLI entry point.

Stub implementation for Phase 1 scaffolding. Subcommands
(``data fetch``, ``data list-versions``, ``data activate``) are
added in Section H of the Phase 1 task list.
"""

import typer

from opensalestax import __version__

app = typer.Typer(
    name="opensalestax",
    help="OpenSalesTax — open-source US sales tax calculation API.",
    no_args_is_help=True,
)


@app.command()
def version() -> None:
    """Print the installed OpenSalesTax version."""
    typer.echo(__version__)


if __name__ == "__main__":
    app()
