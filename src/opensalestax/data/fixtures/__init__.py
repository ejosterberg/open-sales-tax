# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Bundled SST data fixtures for tests.

Subdirectories per state contain real upstream SST files (or
trimmed samples) from a specific quarterly release. Files are
public-domain US government data; no licensing concerns with
bundling them.
"""

from pathlib import Path

FIXTURES_DIR = Path(__file__).parent
"""Absolute path to the fixtures directory."""


def state_fixture_dir(abbrev: str) -> Path:
    """Return the fixture directory for a given state's abbreviation."""
    return FIXTURES_DIR / abbrev.lower()
