# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Census ZCTA->state boundary parser."""

from __future__ import annotations

from opensalestax.data.zcta_loader import parse_zcta_state_rows

_HEADER = (
    "OID_ZCTA5_20|GEOID_ZCTA5_20|NAMELSAD_ZCTA5_20|AREALAND_ZCTA5_20|"
    "AREAWATER_ZCTA5_20|MTFCC_ZCTA5_20|CLASSFP_ZCTA5_20|FUNCSTAT_ZCTA5_20|"
    "OID_COUNTY_20|GEOID_COUNTY_20|NAMELSAD_COUNTY_20|AREALAND_COUNTY_20|"
    "AREAWATER_COUNTY_20|MTFCC_COUNTY_20|CLASSFP_COUNTY_20|FUNCSTAT_COUNTY_20|"
    "AREALAND_PART|AREAWATER_PART"
)


def _write_fixture(tmp_path, rows: list[str]):
    fixture = tmp_path / "zcta.txt"
    fixture.write_text(_HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return fixture


def test_parse_emits_one_row_per_zip_state(tmp_path) -> None:
    """Each (ZCTA, state) pair is emitted exactly once even when the
    Census file lists the ZIP across multiple counties of the same state.
    """
    rows = [
        # ZCTA 32401 in two FL counties (state FIPS 12)
        "|32401|||||||" + "|12005|||||||100|0",
        "|32401|||||||" + "|12013|||||||50|0",
        # ZCTA 55401 in one MN county (state FIPS 27)
        "|55401|||||||" + "|27053|||||||200|0",
    ]
    fixture = _write_fixture(tmp_path, rows)
    # Filter to FL+MN only so the iter-68 USPS PO-box supplement
    # (which adds MA / RI / CT / NJ ZIPs unconditionally) doesn't
    # interfere with this test's specific assertion.
    parsed = list(parse_zcta_state_rows(fixture, abbrev_filter={"FL", "MN"}))
    pairs = sorted((p.zip5, p.state_abbrev) for p in parsed)
    assert pairs == [("32401", "FL"), ("55401", "MN")]


def test_parse_skips_county_only_rows(tmp_path) -> None:
    """Rows where the ZCTA column is empty (county-only entries) are skipped."""
    rows = [
        # County row with no ZCTA -- must be ignored
        "|||||||| 27590114112812|01003|||||||100|0",
        # Real ZCTA->county row for Alabama
        "|36101|||||||" + "|01101|||||||100|0",
    ]
    fixture = _write_fixture(tmp_path, rows)
    # Filter to AL only so the USPS PO-box supplement doesn't interfere.
    parsed = list(parse_zcta_state_rows(fixture, abbrev_filter={"AL"}))
    assert [(p.zip5, p.state_abbrev) for p in parsed] == [("36101", "AL")]


def test_parse_respects_abbrev_filter(tmp_path) -> None:
    """The ``abbrev_filter`` arg restricts the output to a subset of states.

    Note: with the iter-68 USPS PO-box supplement, MA-filtered output
    also includes the four PO-box-only Springfield ZIPs from
    USPS_PO_BOX_ZIPS. Filter to NY only here to keep the assertion
    free of supplement noise.
    """
    rows = [
        "|55401|||||||" + "|27053|||||||100|0",  # MN
        "|10001|||||||" + "|36061|||||||100|0",  # NY
        "|02101|||||||" + "|25025|||||||100|0",  # MA
    ]
    fixture = _write_fixture(tmp_path, rows)
    parsed = list(parse_zcta_state_rows(fixture, abbrev_filter={"NY"}))
    pairs = sorted((p.zip5, p.state_abbrev) for p in parsed)
    assert pairs == [("10001", "NY")]


def test_parse_ignores_unknown_state_fips(tmp_path) -> None:
    """A state FIPS not in the canonical table is silently skipped."""
    rows = [
        "|55401|||||||" + "|99999|||||||100|0",  # bogus state FIPS 99
        "|55401|||||||" + "|27053|||||||100|0",  # real MN row
    ]
    fixture = _write_fixture(tmp_path, rows)
    # Filter to MN only so USPS PO-box supplement doesn't interfere.
    parsed = list(parse_zcta_state_rows(fixture, abbrev_filter={"MN"}))
    assert [(p.zip5, p.state_abbrev) for p in parsed] == [("55401", "MN")]


def test_parse_appends_usps_po_box_supplement(tmp_path) -> None:
    """USPS PO-box-only ZIPs (not in Census ZCTA) are appended to the output.

    Pre-iter-68 the engine returned 0% for any GET /v1/calculate on a
    PO-box-only ZIP in a flat-rate state (MA Springfield 01101, NJ
    Newark 07101, etc.) because those ZIPs aren't in Census ZCTA and
    no other binding existed. This test pins the supplement.
    """
    rows = [
        # Real Census row for Boston (which IS in ZCTA)
        "|02108|||||||" + "|25025|||||||100|0",
    ]
    fixture = _write_fixture(tmp_path, rows)
    pairs = {(p.zip5, p.state_abbrev) for p in parse_zcta_state_rows(fixture)}
    assert ("02108", "MA") in pairs  # from Census
    # Springfield PO-box ZIPs from the supplement
    assert ("01101", "MA") in pairs
    assert ("01102", "MA") in pairs
    assert ("01115", "MA") in pairs
    assert ("01199", "MA") in pairs
    # NJ / RI / CT confirmed examples
    assert ("07101", "NJ") in pairs
    assert ("08601", "NJ") in pairs
    assert ("02901", "RI") in pairs
    assert ("06101", "CT") in pairs


def test_parse_supplement_respects_abbrev_filter(tmp_path) -> None:
    """USPS PO-box supplement also respects abbrev_filter."""
    rows = [
        "|55401|||||||" + "|27053|||||||100|0",  # MN
    ]
    fixture = _write_fixture(tmp_path, rows)
    pairs = {(p.zip5, p.state_abbrev) for p in parse_zcta_state_rows(fixture, abbrev_filter={"MN"})}
    # Only MN row from Census; no supplement entries since MN isn't in
    # the PO-box ZIP table.
    assert pairs == {("55401", "MN")}
