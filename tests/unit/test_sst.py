# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the SST fetcher utilities (no network required)."""

from __future__ import annotations

import pytest

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.data.sst import (
    SST_BOUNDARY_URL,
    SST_RATES_URL,
    SstFilename,
    file_url,
    open_sst_csv,
)


def test_parse_filename_rates() -> None:
    parsed = SstFilename.parse("MNR2026Q2FEB18.zip")
    assert parsed.state == "MN"
    assert parsed.kind == "R"
    assert parsed.year == 2026
    assert parsed.quarter == 2
    assert parsed.month == "FEB"
    assert parsed.day == 18
    assert parsed.ext == "zip"


def test_parse_filename_boundary() -> None:
    parsed = SstFilename.parse("WIB2026Q3OCT01.csv")
    assert parsed.state == "WI"
    assert parsed.kind == "B"
    assert parsed.ext == "csv"


def test_parse_filename_is_case_insensitive() -> None:
    parsed = SstFilename.parse("mnr2026q2feb18.zip")
    assert parsed.state == "MN"
    assert parsed.kind == "R"
    assert parsed.month == "FEB"


def test_version_label_is_deterministic() -> None:
    parsed = SstFilename.parse("MNR2026Q2FEB18.zip")
    assert parsed.version_label == "MN-SST-2026Q2FEB18"


@pytest.mark.parametrize(
    "bad",
    ["MN-2026.csv", "MNR2026.csv", "MNR2026Q2.csv", "MNX2026Q2FEB18.zip", ""],
)
def test_parse_filename_rejects_malformed(bad: str) -> None:
    with pytest.raises(ValueError):
        SstFilename.parse(bad)


def test_file_url_routes_to_rates_or_boundary() -> None:
    assert file_url("MNR2026Q2FEB18.zip") == SST_RATES_URL + "MNR2026Q2FEB18.zip"
    assert file_url("MNB2026Q2FEB18.zip") == SST_BOUNDARY_URL + "MNB2026Q2FEB18.zip"


def test_open_sst_csv_reads_plain_csv() -> None:
    """The fetcher should yield lines from a plain CSV file."""
    fixture_path = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    lines = list(open_sst_csv(fixture_path))
    assert len(lines) == 148  # known from the upstream file (147 rows + final EOL)
    assert lines[0].startswith("27,")  # MN FIPS code in column 1


def test_open_sst_csv_unzips_archive() -> None:
    """The fetcher should transparently unzip a single-CSV archive."""
    fixture_path = state_fixture_dir("MN") / "MNR2026Q2FEB18.zip"
    lines = list(open_sst_csv(fixture_path))
    # ZIP yields the same line count as the unwrapped CSV
    assert len(lines) == 148
    assert lines[0].startswith("27,")


def test_open_sst_csv_rejects_unsupported_extension(tmp_path) -> None:
    bogus = tmp_path / "data.txt"
    bogus.write_text("ignored")
    with pytest.raises(ValueError, match="unsupported"):
        list(open_sst_csv(bogus))
