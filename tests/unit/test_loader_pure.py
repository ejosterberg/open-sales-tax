# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Unit tests for the loader's pure-Python helpers (no DB needed)."""

from __future__ import annotations

import pytest

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.data.loader import (
    find_cached_file,
    resolve_filename,
)


def test_resolve_filename_full_label() -> None:
    """Accepts the full SST-style label."""
    assert resolve_filename("MN", "MN-SST-2026Q2FEB18", "R") == "MNR2026Q2FEB18.csv"


def test_resolve_filename_bare_suffix() -> None:
    """Accepts the bare quarterly suffix too."""
    assert resolve_filename("MN", "2026Q2FEB18", "R") == "MNR2026Q2FEB18.csv"


def test_resolve_filename_lowercase_inputs() -> None:
    """Case-insensitive on both state and label."""
    assert resolve_filename("mn", "2026q2feb18", "R") == "MNR2026Q2FEB18.csv"


def test_resolve_filename_boundary() -> None:
    assert resolve_filename("WI", "2026Q2FEB18", "B") == "WIB2026Q2FEB18.csv"


def test_resolve_filename_rejects_bad_kind() -> None:
    with pytest.raises(ValueError, match="kind"):
        resolve_filename("MN", "2026Q2FEB18", "X")


def test_find_cached_file_picks_up_bundled_fixture() -> None:
    """The bundled MN fixture should be findable under the fixtures path."""
    result = find_cached_file("MN", "2026Q2FEB18", "R", cache_dir=state_fixture_dir("MN"))
    assert result is not None
    assert result.name in {"MNR2026Q2FEB18.csv", "MNR2026Q2FEB18.zip"}


def test_find_cached_file_missing_returns_none() -> None:
    result = find_cached_file("MN", "9999Q4JAN01", "R", cache_dir=state_fixture_dir("MN"))
    assert result is None


def test_find_cached_file_handles_missing_cache_dir(tmp_path) -> None:
    nonexistent = tmp_path / "does-not-exist"
    assert find_cached_file("MN", "2026Q2FEB18", "R", cache_dir=nonexistent) is None
