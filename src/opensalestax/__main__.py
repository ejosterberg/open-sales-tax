# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Allow ``python -m opensalestax`` to invoke the CLI."""

from opensalestax.cli.main import app

if __name__ == "__main__":
    app()
