# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the SST fetcher utilities (no network required)."""

from __future__ import annotations

import httpx
import pytest

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.data.sst import (
    SST_BOUNDARY_URL,
    SST_RATES_URL,
    SstFilename,
    download_sst_file,
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


def test_download_sst_file_falls_back_to_zip_on_csv_404(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """SST publishes a state's file as either ``.csv`` or ``.zip`` --
    never both consistently.  When the requested extension 404s, the
    downloader retries the alternate extension and caches it under
    whichever the upstream actually serves.
    """
    csv_url = file_url("KSR2026Q2FEB18.csv")
    zip_url = file_url("KSR2026Q2FEB18.zip")
    served_zip_body = b"PK\x03\x04zip-bytes"

    def handler(request: httpx.Request) -> httpx.Response:
        if str(request.url) == csv_url:
            return httpx.Response(404, content=b"not found")
        if str(request.url) == zip_url:
            return httpx.Response(200, content=served_zip_body)
        raise AssertionError(f"unexpected URL: {request.url}")

    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def mock_client(**kwargs):
        kwargs.pop("transport", None)
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr("opensalestax.data.sst.httpx.Client", mock_client)

    cached = download_sst_file("KSR2026Q2FEB18.csv", dest_dir=tmp_path)
    assert cached.name == "KSR2026Q2FEB18.zip"
    assert cached.read_bytes() == served_zip_body


def test_download_sst_file_propagates_when_both_extensions_404(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When neither the .csv nor .zip variant exists upstream the
    downloader raises rather than failing silently."""
    transport = httpx.MockTransport(lambda req: httpx.Response(404, content=b""))
    real_client = httpx.Client

    def mock_client(**kwargs):
        kwargs.pop("transport", None)
        return real_client(transport=transport, **kwargs)

    monkeypatch.setattr("opensalestax.data.sst.httpx.Client", mock_client)
    with pytest.raises(httpx.HTTPStatusError):
        download_sst_file("XXR2099Q4JAN01.csv", dest_dir=tmp_path)
