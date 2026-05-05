# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the generic SST CSV parser using real MN fixtures."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.data.sst import open_sst_csv
from opensalestax.data.sst_parser import (
    SstBoundaryRecord,
    SstRateRecord,
    active_only,
    parse_boundary_csv,
    parse_rates_csv,
)


# ---------------------------------------------------------------------------
# Rates parser
# ---------------------------------------------------------------------------
def test_parse_rates_yields_records() -> None:
    """The full MN rates fixture parses into 147 records."""
    fixture = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    records = list(parse_rates_csv(open_sst_csv(fixture)))
    assert len(records) == 148  # known from the upstream file


def test_parse_rates_extracts_mn_state_base() -> None:
    """The MN state-level rate row (type 45) shows 6.875%."""
    fixture = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    records = list(parse_rates_csv(open_sst_csv(fixture)))

    state_rows = [r for r in records if r.jurisdiction_type == "45"]
    assert len(state_rows) == 1
    state_row = state_rows[0]
    assert state_row.state_fips == "27"
    assert state_row.jurisdiction_code == "27"
    assert state_row.general_rate == Decimal("0.06875")
    assert state_row.effective_from == dt.date(2009, 7, 1)
    assert state_row.effective_to is None  # 29991231 -> None


def test_parse_rates_handles_open_ended_dates() -> None:
    """The 29991231 sentinel maps to None for effective_to."""
    fixture = state_fixture_dir("MN") / "MNR2026Q2FEB18.csv"
    records = list(parse_rates_csv(open_sst_csv(fixture)))
    open_ended = [r for r in records if r.effective_to is None]
    expired = [r for r in records if r.effective_to is not None]
    # MN file has both currently-active rates and historical ones
    assert open_ended
    assert expired


def test_parse_rates_skips_blank_lines() -> None:
    records = list(parse_rates_csv(["", "  ", "\n"]))
    assert records == []


def test_parse_rates_skips_malformed_rows(caplog) -> None:
    """A row with the wrong column count is logged and skipped."""
    bad_lines = [
        "27,01,12345",  # too few cols
        "27,45,27,0.06875,0.06875,0.06875,0.06875,20090701,29991231",  # good
        "27,45,27,not-a-decimal,0,0,0,20090701,29991231",  # bad rate
    ]
    records = list(parse_rates_csv(bad_lines))
    # Only the one good row survives
    assert len(records) == 1
    assert records[0].general_rate == Decimal("0.06875")
    # And we logged the failures
    assert any("3 columns" in m or "skipping" in m for m in caplog.messages)


# ---------------------------------------------------------------------------
# Boundary parser
# ---------------------------------------------------------------------------
def test_parse_boundary_yields_records() -> None:
    """The 100-row MN boundary sample parses cleanly."""
    fixture = state_fixture_dir("MN") / "MNB2026Q2FEB18-sample.csv"
    records = list(parse_boundary_csv(open_sst_csv(fixture)))
    # All 100 lines should parse (they're real production rows)
    assert len(records) == 100
    assert all(isinstance(r, SstBoundaryRecord) for r in records)


def test_parse_boundary_extracts_zip_range() -> None:
    fixture = state_fixture_dir("MN") / "MNB2026Q2FEB18-sample.csv"
    records = list(parse_boundary_csv(open_sst_csv(fixture)))
    # Every record in MN's file is for state FIPS 27
    for r in records:
        assert r.state_fips == "27"
    # Several records cover real MN ZIPs in the 55xxx range
    zip_lows = {r.zip5_low for r in records if r.zip5_low.startswith("55")}
    assert zip_lows  # non-empty


def test_parse_boundary_record_types() -> None:
    """Sample includes both 'z' and possibly '4' record types."""
    fixture = state_fixture_dir("MN") / "MNB2026Q2FEB18-sample.csv"
    records = list(parse_boundary_csv(open_sst_csv(fixture)))
    types = {r.record_type for r in records}
    # The first 100 lines of MN's boundary file are all 'z' records
    assert "z" in types


def test_parse_boundary_normalizes_record_type_case(tmp_path) -> None:
    """SST publishes record-type codes inconsistently ('z' / 'Z' / '4').

    The parser normalizes the case so downstream consumers can
    compare against a single lowercase code. RI / KY / MI / WV
    publish uppercase Z records that earlier silently dropped.
    """
    from opensalestax.data.sst_parser import BOUNDARY_COLUMNS

    csv = tmp_path / "ZZB2025Q1JAN1.csv"
    # One '4' (FIPS+ZIP9) record + one 'Z' (uppercase) ZIP-range record.
    # Format mirrors the real SST file shape (89 columns).
    base_cols = [""] * BOUNDARY_COLUMNS
    base_cols[1] = "20070101"
    base_cols[2] = "29991231"
    base_cols[17] = "02801"
    base_cols[19] = "02940"
    base_cols[22] = "44"
    record_4 = ",".join(["4", *base_cols[1:]])
    record_z = ",".join(["Z", *base_cols[1:]])
    csv.write_text(record_4 + "\n" + record_z + "\n")

    records = list(parse_boundary_csv(open_sst_csv(csv)))
    types = sorted(r.record_type for r in records)
    assert types == ["4", "z"], f"expected normalized ['4', 'z']; got {types}"


def test_parse_boundary_handles_address_level_records(tmp_path) -> None:
    """Type-'A' (address-level) records used by VT must parse.

    Vermont's SST boundary file ships address-level rows where zip5
    is at col 15 (instead of col 17 for 'z'/'4' records) and zip4 at
    col 16. The parser must collapse 'A' rows to a zip5-wide binding
    (zip4_low/high left None) so the loose lookup picks them up the
    same as 'z' rows -- otherwise per-street rows would either be
    silently dropped (status quo before this test) or bloat the DB
    with millions of single-address boundaries.

    Regression for ``specs/decisions/08-vt-address-record-format.md``.
    """
    from opensalestax.data.sst_parser import BOUNDARY_COLUMNS

    csv = tmp_path / "VTB2026Q2FEB20.csv"
    base_cols = [""] * BOUNDARY_COLUMNS
    base_cols[1] = "20250101"
    base_cols[2] = "29991231"
    base_cols[14] = "BURLINGTON"  # city/place name (informational)
    base_cols[15] = "05401"  # zip5 (NOT col 17 like 'z'/'4' rows)
    base_cols[16] = "1234"  # zip4 (informational; not loaded as range)
    base_cols[22] = "50"  # state FIPS
    # county_fips at col 24 left blank (VT 'A' rows omit it)
    base_cols[25] = "10675"  # FIPS Place 10675 = Burlington
    record_a_upper = ",".join(["A", *base_cols[1:]])
    record_a_lower = ",".join(["a", *base_cols[1:]])
    csv.write_text(record_a_upper + "\n" + record_a_lower + "\n")

    records = list(parse_boundary_csv(open_sst_csv(csv)))
    assert len(records) == 2
    for rec in records:
        assert rec.record_type == "a"
        assert rec.zip5_low == "05401"
        assert rec.zip5_high == "05401"
        # zip4 must be None so the loose lookup treats this as a
        # zip-wide binding rather than a single-address record.
        assert rec.zip4_low is None
        assert rec.zip4_high is None
        assert rec.state_fips == "50"
        assert rec.city_code == "10675"


def test_parse_boundary_zero_pads_zip4_ranges(tmp_path) -> None:
    """Type-4 records with un-padded +4 ranges (e.g. "1" instead of "0001")
    must be zero-padded so downstream string comparison behaves numerically.

    Without padding, OK 73072-1015 was matched against ranges low="1"
    high="7" (lex: "1"<="1015"<="7"), spuriously binding the ZIP to
    Norman + Newcastle + Cleveland + McClain and tripling the city tax.
    """
    from opensalestax.data.sst_parser import BOUNDARY_COLUMNS

    csv = tmp_path / "OKB2026Q2APR01.csv"
    base_cols = [""] * BOUNDARY_COLUMNS
    base_cols[1] = "20070101"
    base_cols[2] = "29991231"
    base_cols[17] = "73072"
    base_cols[18] = "1"  # +4 low — un-padded
    base_cols[19] = "73072"
    base_cols[20] = "7"  # +4 high — un-padded
    base_cols[22] = "40"
    record_4 = ",".join(["4", *base_cols[1:]])
    csv.write_text(record_4 + "\n")

    records = list(parse_boundary_csv(open_sst_csv(csv)))
    assert len(records) == 1
    assert records[0].zip4_low == "0001"
    assert records[0].zip4_high == "0007"


# ---------------------------------------------------------------------------
# active_only filter
# ---------------------------------------------------------------------------
def test_active_only_drops_expired() -> None:
    """Records with effective_to in the past are filtered out."""
    expired = SstRateRecord(
        state_fips="27",
        jurisdiction_type="01",
        jurisdiction_code="12345",
        general_rate=Decimal("0.005"),
        food_rate=Decimal("0.005"),
        drug_rate=Decimal("0.005"),
        residential_utility_rate=Decimal("0.005"),
        effective_from=dt.date(2010, 1, 1),
        effective_to=dt.date(2020, 12, 31),
    )
    current = SstRateRecord(
        state_fips="27",
        jurisdiction_type="45",
        jurisdiction_code="27",
        general_rate=Decimal("0.06875"),
        food_rate=Decimal("0.06875"),
        drug_rate=Decimal("0.06875"),
        residential_utility_rate=Decimal("0.06875"),
        effective_from=dt.date(2009, 7, 1),
        effective_to=None,
    )
    future = SstRateRecord(
        state_fips="27",
        jurisdiction_type="01",
        jurisdiction_code="99999",
        general_rate=Decimal("0.005"),
        food_rate=Decimal("0.005"),
        drug_rate=Decimal("0.005"),
        residential_utility_rate=Decimal("0.005"),
        effective_from=dt.date(2099, 1, 1),
        effective_to=None,
    )
    active = list(active_only([expired, current, future], as_of=dt.date(2026, 5, 3)))
    # only 'current' is active on 2026-05-03
    assert active == [current]
