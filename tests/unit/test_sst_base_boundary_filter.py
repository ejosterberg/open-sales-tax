# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the effective-date filter in :class:`SstStateModule.parse_boundaries`.

The SST quarterly boundary file retains years of historical
records in the same publication. The :class:`Boundary` ORM table
has no effective_from/to columns, so loading every row would
forever-stack expired bindings on top of currently-active ones --
producing per-ZIP city/county "ghost" overlaps that double-count
local rate. The fix: filter rows by current effectivity at parse
time. This file pins down the regression that surfaced as
TN ZIP 37027 (Brentwood) returning 14.75% combined: the SST file
historically bound 37027 to Nashville (city 52006) and Brentwood
(city 54780) plus the now-active Davidson County row, and all
three were being loaded into the boundary table.
"""

from __future__ import annotations

import datetime as dt
from pathlib import Path

import pytest

from opensalestax.data.sst_parser import BOUNDARY_COLUMNS
from opensalestax.states._sst_base import SstStateModule, _record_active_on


def _make_record(
    eff_from: dt.date | None = None,
    eff_to: dt.date | None = None,
):
    """Build a tiny duck-typed object with the two attributes the helper reads."""

    class _R:
        pass

    r = _R()
    r.effective_from = eff_from
    r.effective_to = eff_to
    return r


def test_record_active_on_open_ended_passes_today() -> None:
    """Open-ended (effective_to=None) rows are always active when in_force."""
    r = _make_record(eff_from=dt.date(2020, 1, 1), eff_to=None)
    assert _record_active_on(r, dt.date(2026, 5, 4)) is True


def test_record_active_on_drops_expired() -> None:
    """A row that ended before ``as_of`` is filtered out."""
    r = _make_record(eff_from=dt.date(2024, 1, 1), eff_to=dt.date(2024, 3, 31))
    assert _record_active_on(r, dt.date(2026, 5, 4)) is False


def test_record_active_on_drops_future() -> None:
    """A row whose ``effective_from`` is after ``as_of`` is filtered out."""
    r = _make_record(eff_from=dt.date(2099, 1, 1), eff_to=None)
    assert _record_active_on(r, dt.date(2026, 5, 4)) is False


def test_record_active_on_keeps_today_boundary() -> None:
    """Rows whose window includes ``as_of`` exactly at either edge are active."""
    edge_low = _make_record(
        eff_from=dt.date(2026, 5, 4), eff_to=dt.date(2026, 12, 31)
    )
    edge_high = _make_record(
        eff_from=dt.date(2025, 1, 1), eff_to=dt.date(2026, 5, 4)
    )
    assert _record_active_on(edge_low, dt.date(2026, 5, 4)) is True
    assert _record_active_on(edge_high, dt.date(2026, 5, 4)) is True


def test_record_active_on_missing_effective_dates_treated_as_active() -> None:
    """Defensive: a record missing both date fields stays in the stream."""
    r = _make_record(eff_from=None, eff_to=None)
    assert _record_active_on(r, dt.date(2026, 5, 4)) is True


# ---------------------------------------------------------------------------
# End-to-end boundary parsing -- the regression test for the TN multi-city bug
# ---------------------------------------------------------------------------
def _row(
    record_type: str,
    eff_from: str,
    eff_to: str,
    zip5: str,
    *,
    county_fips: str = "",
    city_code: str = "",
) -> str:
    """Build a single SST boundary CSV row of the right column count.

    Matches the layout consumed by
    :func:`opensalestax.data.sst_parser.parse_boundary_csv` (89
    columns; cols 18-20 ZIP range, col23 state FIPS, col25 county
    FIPS, col26 city code).
    """
    cols = [""] * BOUNDARY_COLUMNS
    cols[0] = record_type
    cols[1] = eff_from
    cols[2] = eff_to
    cols[17] = zip5
    cols[19] = zip5
    cols[22] = "47"  # TN state FIPS
    cols[24] = county_fips
    cols[25] = city_code
    return ",".join(cols)


class _FakeTnModule(SstStateModule):
    """Minimal SstStateModule subclass for parser-level testing.

    Pinning :attr:`boundaries_as_of` to a known date keeps the test
    deterministic even as real-world clocks and quarterly files
    move. Disables the cross-border ZCTA filter by registering 47
    as the state FIPS so all 37xxx ZIPs map to TN.
    """

    state_abbrev = "TN"
    state_name = "Tennessee"
    state_fips = "47"
    sst_member = True
    has_sales_tax = True
    boundaries_as_of = dt.date(2026, 5, 4)


def test_parse_boundaries_drops_expired_type_z_city_overlap(tmp_path: Path) -> None:
    """The TN 37027 Brentwood-Nashville-Davidson regression scenario.

    Before the fix: the SST file binds 37027 to Nashville (52006,
    expired Q3 2025) AND Brentwood (54780, expired Q1 2024) AND
    Davidson County (037, currently effective). The loader would
    insert all three; downstream rate-lookup would sum
    state + Davidson + Nashville + Brentwood = 14.75% instead of
    the correct state + Davidson = 9.25% (or, if the data were
    pristine and Brentwood's Williamson County binding were the
    only one published, 9.75%).

    After the fix: only the currently-effective Davidson row
    survives the parser, so a fresh DB load no longer carries
    the expired city bindings.
    """
    csv_path = tmp_path / "TNB2026Q2FEB23.csv"
    csv_path.write_text(
        "\n".join(
            [
                # Expired Brentwood city binding (Q1 2024)
                _row("Z", "20240101", "20240331", "37027", city_code="54780"),
                # Expired Nashville (Metro) city binding (Q3 2025)
                _row("Z", "20250701", "20250930", "37027", city_code="52006"),
                # Currently active Davidson County binding (Q4 2025+)
                _row("Z", "20251001", "29991231", "37027", county_fips="037"),
            ]
        )
        + "\n"
    )

    module = _FakeTnModule()
    rows = list(module.parse_boundaries(csv_path, "TN-SST-2026Q2FEB23"))

    # State always emitted alongside any active binding row.
    state_rows = [r for r in rows if r.authority_type == "state"]
    county_rows = [r for r in rows if r.authority_type == "county"]
    city_rows = [r for r in rows if r.authority_type == "city"]

    # The two expired city bindings must be filtered out entirely.
    assert city_rows == [], (
        f"Expected zero city bindings (Brentwood + Nashville rows are expired); "
        f"got {[(r.authority_name, r.zip5) for r in city_rows]!r}"
    )
    # Davidson County survives.
    assert len(county_rows) == 1
    assert county_rows[0].authority_name == "Davidson County"
    assert county_rows[0].zip5 == "37027"
    # And state is yielded once for the surviving row.
    assert len(state_rows) >= 1
    assert all(r.authority_name == "Tennessee" for r in state_rows)


def test_parse_boundaries_drops_future_record(tmp_path: Path) -> None:
    """Future-dated rows (effective_from > as_of) are also filtered out.

    Pinned ``boundaries_as_of`` to 2026-05-04; a record beginning
    2030-01-01 must not be loaded into the live boundary set.
    """
    csv_path = tmp_path / "TNB2030Q1JAN1.csv"
    csv_path.write_text(
        "\n".join(
            [
                _row("Z", "20300101", "29991231", "37027", county_fips="037"),
            ]
        )
        + "\n"
    )

    module = _FakeTnModule()
    rows = list(module.parse_boundaries(csv_path, "TN-SST-2030Q1JAN1"))
    assert rows == []


def test_parse_boundaries_keeps_open_ended_active_rows(tmp_path: Path) -> None:
    """Currently effective rows (open-ended or in-window) make it through."""
    csv_path = tmp_path / "TNB2026Q2FEB23.csv"
    csv_path.write_text(
        "\n".join(
            [
                _row(
                    "Z",
                    "20260101",
                    "29991231",
                    "37067",
                    county_fips="187",
                ),  # Williamson; open-ended
                _row(
                    "Z",
                    "20250101",
                    "20271231",
                    "37027",
                    county_fips="037",
                ),  # Davidson; in-window
            ]
        )
        + "\n"
    )

    module = _FakeTnModule()
    rows = list(module.parse_boundaries(csv_path, "TN-SST-2026Q2FEB23"))
    counties = sorted(r.authority_name for r in rows if r.authority_type == "county")
    assert counties == ["Davidson County", "Williamson County"]


def test_boundaries_as_of_override_lets_tests_pin_a_snapshot(tmp_path: Path) -> None:
    """Subclasses / tests override ``boundaries_as_of`` for historical snapshots.

    Setting ``boundaries_as_of`` to 2024-02-15 should make the
    expired Brentwood (Q1 2024) row VISIBLE while still excluding
    the Davidson County row that didn't begin until 2025-10-01.
    """
    csv_path = tmp_path / "TNB-historic.csv"
    csv_path.write_text(
        "\n".join(
            [
                _row("Z", "20240101", "20240331", "37027", city_code="54780"),
                _row("Z", "20251001", "29991231", "37027", county_fips="037"),
            ]
        )
        + "\n"
    )

    class _HistoricalModule(_FakeTnModule):
        boundaries_as_of = dt.date(2024, 2, 15)

    rows = list(_HistoricalModule().parse_boundaries(csv_path, "TN-SST-historic"))
    types = sorted((r.authority_type, r.authority_name) for r in rows)
    # Brentwood city visible; Davidson County not yet effective.
    assert ("city", "TN-city-54780") in types
    assert not any(t == ("county", "Davidson County") for t in types)


# ---------------------------------------------------------------------------
# Tennessee module wiring — make sure the real module inherits the filter
# ---------------------------------------------------------------------------
def test_tennessee_module_inherits_boundaries_as_of_default() -> None:
    """The real TN module should leave ``boundaries_as_of`` as None
    (i.e., use today) so the production loader filters by the
    current quarter without manual configuration.
    """
    from opensalestax.states.tennessee import TENNESSEE

    assert TENNESSEE.boundaries_as_of is None


@pytest.mark.parametrize("zip5", ["37027", "37067"])
def test_tn_brentwood_franklin_drop_all_type_z_cities(tmp_path: Path, zip5: str) -> None:
    """End-to-end regression: 37027 Brentwood and 37067 Franklin scenarios.

    The production prod-DB query at the time of the fix showed:

    - 37027 had 2 type-z city bindings (Nashville + Brentwood) +
      Williamson County's missing type-z + a (wrong) Davidson
      County type-z left over from older quarterlies.
    - 37067 had 3 type-z city bindings + Williamson County.

    With the parser filter applied to a TN file containing the
    same expired rows, no city authorities should reach the
    BoundaryRow stream for either ZIP.
    """
    # Compose a tiny synthetic SST file with a representative spread
    # of expired city rows alongside one currently active county row.
    rows: list[str] = []
    rows.append(_row("Z", "20210401", "20211231", zip5, city_code="54780"))
    rows.append(_row("Z", "20240101", "20240331", zip5, city_code="52006"))
    rows.append(_row("Z", "20240701", "20240930", zip5, city_code="27740"))
    # Currently active county-only binding -- 37027 -> Davidson;
    # 37067 -> Williamson. (Both intentionally use 037 to keep the
    # assertion uniform; the test cares only that no CITY rows leak.)
    rows.append(_row("Z", "20260101", "29991231", zip5, county_fips="037"))

    csv_path = tmp_path / f"TNB-regression-{zip5}.csv"
    csv_path.write_text("\n".join(rows) + "\n")

    module = _FakeTnModule()
    parsed = list(module.parse_boundaries(csv_path, "TN-SST-regression"))
    cities = [r for r in parsed if r.authority_type == "city"]
    assert cities == [], (
        f"ZIP {zip5}: expected no city bindings after expired-row filter; "
        f"got {[(r.authority_name, r.zip4_low, r.zip4_high) for r in cities]!r}"
    )
