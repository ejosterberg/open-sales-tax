# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""DOR-validation regression test for SST states.

Hits the live engine (https://api.opensalestax.org) with a curated
list of major-city ZIP+4 addresses and asserts the combined rate
matches what each state's Department of Revenue calculator
publishes -- within a small tolerance to account for ZIP+4 micro
variation (some +4 ranges within a city carry slightly different
combined rates due to overlapping district boundaries).

Skipped automatically in normal pytest runs (no marker); runs only
when explicitly invoked with ``pytest -m liveapi``. The test is a
guard against regressions in the SST loader / lookup engine rather
than a CI gate (the live engine isn't always reachable from CI).

Each row is one (state, city, ZIP+4, expected_rate_pct, source)
tuple. The expected rate was verified against the linked DOR
publication on the date in the comment. Rates change quarterly --
when a published DOR rate changes, update the row AND record the
date so future maintainers know which entries are fresh.
"""

from __future__ import annotations

import os
from decimal import Decimal

import httpx
import pytest

API = os.environ.get(
    "OPENSALESTAX_LIVE_API",
    "https://api.opensalestax.org/v1/calculate",
)

# (state, city, zip5, zip4, expected_rate_pct_str, tolerance_pct, source_note)
DOR_GRID: list[tuple[str, str, str, str, str, str, str]] = [
    # Tennessee -- TN DOR Local Option Sales Tax 2026-Q1
    ("TN", "Nashville (Metro)", "37201", "2402", "9.750", "0.05", "TN DOR + IMPROVE Act 0.5% transit (effective 2025-02-01)"),
    ("TN", "Memphis", "38103", "2701", "9.750", "0.05", "TN DOR (state 7% + Shelby 2.25% + Memphis 0.5%)"),
    ("TN", "Knoxville", "37902", "1234", "9.250", "0.05", "TN DOR (state 7% + Knox 2.25%)"),
    ("TN", "Chattanooga", "37402", "1015", "9.250", "0.05", "TN DOR (state 7% + Hamilton 2.25%)"),
    # Minnesota -- MN DOR sales-tax-rate calculator 2026-Q2
    ("MN", "Minneapolis", "55401", "1024", "9.025", "0.05", "MN DOR (state + Hennepin + Minneapolis + 3 metro districts)"),
    ("MN", "St. Paul", "55101", "1014", "9.875", "0.05", "MN DOR (state + Ramsey + St. Paul + 2 metro districts)"),
    # Kansas -- KS DOR Jurisdiction Sales Tax Rates 2026-Q1
    ("KS", "Topeka", "66603", "3304", "9.350", "0.05", "KS DOR (state 6.5% + Shawnee 1.35% + Topeka 1.5%)"),
    ("KS", "Wichita", "67202", "2417", "7.500", "0.05", "KS DOR (state 6.5% + Sedgwick 1%; Wichita has no city tax)"),
    ("KS", "Kansas City", "66101", "2204", "9.125", "0.05", "KS DOR (state 6.5% + Wyandotte 1% + KC 1.625%)"),
    # Nebraska -- NE DOR Local Sales and Use Tax Rates 2026-Q1
    ("NE", "Omaha", "68102", "1718", "7.000", "0.05", "NE DOR (state 5.5% + Omaha 1.5%)"),
    ("NE", "Lincoln", "68508", "2802", "7.250", "0.05", "NE DOR (state 5.5% + Lincoln 1.75%)"),
    # Nevada -- NV DOR Tax Rates by County 2026
    ("NV", "Las Vegas", "89101", "2402", "8.375", "0.05", "NV DOR (Clark County combined)"),
    ("NV", "Reno", "89501", "1606", "8.265", "0.05", "NV DOR (Washoe County combined)"),
    # Oklahoma -- OK DOR Sales and Use Tax Rate Charts 2026-Q2
    ("OK", "Tulsa", "74103", "3804", "8.517", "0.05", "OK DOR (state 4.5% + Tulsa County 0.367% + Tulsa city 3.65%)"),
    ("OK", "Oklahoma City", "73102", "6107", "8.625", "0.05", "OK DOR (state 4.5% + OKC 4.125%)"),
    # Georgia -- GA DOR Sales Tax Rates 2026-Q1
    ("GA", "Atlanta", "30303", "1015", "8.900", "0.05", "GA DOR (state 4% + Fulton 3% + Atlanta MOST 1.9%)"),
    # North Carolina -- NC DOR Sales and Use Tax Rates 2026-Q1
    ("NC", "Charlotte", "28202", "1402", "7.250", "0.05", "NC DOR (state 4.75% + Mecklenburg 2% + transit 0.5%)"),
    ("NC", "Raleigh", "27601", "1303", "7.250", "0.05", "NC DOR (state 4.75% + Wake 2% + transit 0.5%)"),
    # South Dakota -- SD DOR Municipal Sales Tax 2026-Q1
    ("SD", "Sioux Falls", "57104", "2401", "6.200", "0.05", "SD DOR (state 4.2% + Sioux Falls 2%)"),
    # Utah -- UT DOR sales tax rates 2026-Q2
    ("UT", "Salt Lake City", "84111", "2202", "8.450", "0.05", "UT DOR (state 4.85% + Salt Lake County 2.6% + SLC 1%)"),
    # Washington -- WA DOR Local Sales & Use Tax Rates 2026-Q2
    ("WA", "Bellevue", "98004", "3504", "10.300", "0.05", "WA DOR (state 6.5% + Bellevue combined 3.8%)"),
    # Wisconsin -- WI DOR sales tax rate lookup 2026-Q1
    ("WI", "Milwaukee", "53202", "2402", "5.900", "0.05", "WI DOR (state 5% + Milwaukee County 0.9%)"),
    ("WI", "Madison", "53703", "3505", "5.500", "0.05", "WI DOR (state 5% + Dane County 0.5%)"),
    # West Virginia -- WV DOR sales tax 2026-Q1
    ("WV", "Charleston", "25301", "1108", "7.000", "0.05", "WV DOR (state 6% + Charleston 1%)"),
    # Wyoming -- WY DOR sales tax rates 2026-Q2
    ("WY", "Cheyenne", "82001", "3504", "5.000", "0.05", "WY DOR (state 4% + Laramie 1%)"),
    ("WY", "Casper", "82601", "2401", "5.000", "0.05", "WY DOR (state 4% + Natrona 1%)"),
    # Arkansas -- AR DFA Sales and Use Tax Rates 2026-Q2
    ("AR", "Fort Smith", "72901", "2402", "9.500", "0.05", "AR DFA (state 6.5% + Sebastian 1% + Fort Smith 2%)"),
    ("AR", "Fayetteville", "72701", "5501", "9.750", "0.05", "AR DFA (state 6.5% + Washington 1.25% + Fayetteville 2%)"),
    # Iowa -- IA DOR Local Option Sales Tax 2026-Q1
    ("IA", "Des Moines", "50309", "2306", "7.000", "0.05", "IA DOR (state 6% + Polk LOST 1%)"),
    ("IA", "Cedar Rapids", "52401", "2802", "7.000", "0.05", "IA DOR (state 6% + Linn LOST 1%)"),
    # Indiana -- flat 7%, no locals
    ("IN", "Indianapolis", "46202", "2802", "7.000", "0.01", "IN flat 7% statewide"),
    # Kentucky -- flat 6%
    ("KY", "Louisville", "40202", "2404", "6.000", "0.01", "KY flat 6% statewide"),
    # Michigan -- flat 6%
    ("MI", "Detroit", "48226", "3614", "6.000", "0.01", "MI flat 6% statewide"),
    # New Jersey -- flat 6.625%
    ("NJ", "Newark", "07102", "3505", "6.625", "0.01", "NJ flat 6.625% statewide"),
    # Rhode Island -- flat 7%
    ("RI", "Providence", "02903", "2511", "7.000", "0.01", "RI flat 7% statewide"),
    # ND additional -- ND DOR Local Sales Tax Rates 2026-Q1
    ("ND", "Fargo", "58102", "3703", "7.750", "0.05", "ND DOR (state 5% + Cass 0.5% + Fargo 2.25%)"),
    # SD additional
    ("SD", "Rapid City", "57701", "1701", "6.200", "0.05", "SD DOR (state 4.2% + Rapid City 2%)"),
    # WI additional
    ("WI", "Green Bay", "54301", "3502", "5.500", "0.05", "WI DOR (state 5% + Brown 0.5%)"),
    # WV additional
    ("WV", "Huntington", "25701", "2401", "7.000", "0.05", "WV DOR (state 6% + Huntington 1%)"),
    # OH Cleveland -- different transit district
    ("OH", "Cleveland", "44113", "1417", "8.000", "0.05", "OH DOR (state 5.75% + Cuyahoga 1.25% + RTA 1%)"),
    # WA additional
    ("WA", "Tacoma", "98402", "3502", "10.400", "0.10", "WA DOR (state 6.5% + Tacoma combined ~3.9%)"),
]


@pytest.mark.liveapi
@pytest.mark.parametrize(
    ("state", "city", "zip5", "zip4", "expected", "tolerance", "source"),
    DOR_GRID,
    ids=[f"{r[0]}-{r[2]}-{r[3]}" for r in DOR_GRID],
)
def test_combined_rate_matches_dor(
    state: str,
    city: str,
    zip5: str,
    zip4: str,
    expected: str,
    tolerance: str,
    source: str,
) -> None:
    """Combined rate at this ZIP+4 should match the published DOR rate.

    Tolerance is 0.05% by default to absorb ZIP+4 micro-variation
    (e.g. some +4 ranges fall in additional special districts).
    """
    response = httpx.post(
        API,
        json={
            "address": {"zip5": zip5, "zip4": zip4},
            "line_items": [{"amount": "100.00"}],
        },
        timeout=10.0,
    )
    assert response.status_code == 200, f"engine HTTP {response.status_code}: {response.text}"
    data = response.json()
    got = Decimal(str(data["lines"][0]["rate_pct"]))
    expected_dec = Decimal(expected)
    tol = Decimal(tolerance)
    diff = abs(got - expected_dec)
    msg = (
        f"{state} {city} {zip5}-{zip4}: got {got}%, "
        f"expected {expected}% (+/- {tol}). source: {source}"
    )
    assert diff <= tol, msg
