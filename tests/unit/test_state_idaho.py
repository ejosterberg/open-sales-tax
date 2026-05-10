# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Idaho state module (Phase 6 Batch B, v0.7 -- tier-1 ratchet)."""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.idaho import IDAHO, Idaho
from opensalestax.states.protocol import StateModule


def test_idaho_metadata() -> None:
    assert IDAHO.state_abbrev == "ID"
    assert IDAHO.state_name == "Idaho"
    assert IDAHO.sst_member is False  # ID is NOT in SST
    assert IDAHO.has_sales_tax is True
    assert IDAHO.tier == 1
    assert IDAHO.self_seeded is True  # signals the loader to skip file lookup


def test_idaho_satisfies_protocol() -> None:
    assert isinstance(IDAHO, StateModule)
    assert isinstance(Idaho(), StateModule)


def test_idaho_is_registered() -> None:
    assert get_state_module("ID") is IDAHO


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in Chapter 36
        ("groceries", True),  # ID is one of the few states that fully taxes groceries
        ("prescription_drugs", False),  # Idaho Code section 63-3622N
        ("prepared_food", True),  # section 63-3612 / IDAPA 35.01.02.041
        ("digital_goods", True),  # section 63-3616(b) -- canned software + permanent-right media
        ("general", True),  # section 63-3619 / 63-3616
    ],
)
def test_idaho_taxability(category: str, expected_taxable: bool) -> None:
    rule = IDAHO.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_idaho_unknown_category_returns_none() -> None:
    assert IDAHO.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_idaho_parse_rates_yields_6_pct_state_plus_resort_cities() -> None:
    """Idaho's statewide rate is 6% effective 2006-10-01 (HB 82, 2006 1st Extra. Sess.).

    iter-75 added the 6 highest-population resort cities under
    Idaho Code section 50-1044 (Sun Valley / Ketchum / McCall /
    Stanley / Donnelly / Cascade), each at 3%.
    """
    from opensalestax.states.id_data import ID_RESORT_CITIES

    rows = list(IDAHO.parse_rates(None, "v0.7-statewide"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    assert len(state_rows) == 1
    state = state_rows[0]
    assert state.authority_name == "Idaho"
    assert state.rate_pct == Decimal("6.000")
    assert state.effective_from == dt.date(2006, 10, 1)
    assert state.effective_to is None
    assert state.parent_authority_name is None

    city_rows = [r for r in rows if r.authority_type == "city"]
    assert len(city_rows) == len(ID_RESORT_CITIES)
    for r in city_rows:
        assert r.parent_authority_name == "Idaho"
        assert r.rate_pct == Decimal("3.000")


def test_idaho_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(IDAHO.parse_rates(None, "test"))
    rows_with_path = list(IDAHO.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_idaho_parse_boundaries_emits_resort_city_pairs() -> None:
    """iter-75 added (state, city) BoundaryRows for ID resort-city ZIPs."""
    from opensalestax.states.id_data import ID_RESORT_CITIES

    rows = list(IDAHO.parse_boundaries(None, "v0.7-resort-cities"))
    # state + city per ZIP, so total = 2 * sum(zips)
    expected = sum(len(zips) for _, (_, zips) in ID_RESORT_CITIES.items()) * 2
    assert len(rows) == expected
    # Every resort-city ZIP appears exactly twice (state + city)
    for _city, (_, zips) in ID_RESORT_CITIES.items():
        for zip5 in zips:
            zip_rows = [r for r in rows if r.zip5 == zip5]
            types = {r.authority_type for r in zip_rows}
            assert types == {"state", "city"}, f"{zip5}: {types}"


def test_idaho_special_cases_empty() -> None:
    """Resort-city taxes and the digital-goods sub-split are documented but not yet
    exposed via SpecialCase (engine support pending).
    """
    cases = list(IDAHO.special_cases())
    assert cases == []


def test_idaho_holidays_for_all_years_returns_empty() -> None:
    """Regression test: Idaho has NO sales-tax holidays in any year.

    Confirmed against the Idaho State Tax Commission 2026-05-03. This
    test exists specifically to catch any future regression where a
    contributor accidentally adds a holiday window (e.g. by
    copy-pasting from a state that does have one).
    """
    for year in range(2024, 2031):
        holidays = list(IDAHO.holidays_for(year))
        assert holidays == [], f"Idaho should have no holidays in {year}"


def test_idaho_groceries_notes_cite_income_tax_credit_offset() -> None:
    """The grocery rule must explicitly note that Idaho taxes groceries fully
    and offsets via a separate income-tax credit (NOT a sales-tax reduction).
    Otherwise an integrator could be misled into thinking 'grocery credit'
    means the sales tax is reduced.
    """
    rule = IDAHO.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    notes_lower = (rule.notes or "").lower()
    assert "income-tax credit" in notes_lower or "income tax credit" in notes_lower
    assert "grocery credit" in notes_lower
    assert "6%" in notes_lower or "6.0" in notes_lower or "full" in notes_lower


def test_idaho_prescription_drugs_cite_63_3622n() -> None:
    """Prescription-drug exemption must cite the controlling statute."""
    rule = IDAHO.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert "63-3622N" in (rule.notes or "")


def test_idaho_digital_goods_notes_call_out_saas_exclusion() -> None:
    """Digital-goods rule encodes the dominant taxable case but must document
    the SaaS / remotely-accessed-software / subscription exclusion under
    Idaho Code section 63-3616(b).
    """
    rule = IDAHO.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "63-3616" in notes
    notes_lower = notes.lower()
    assert "saas" in notes_lower or "remotely accessed" in notes_lower
    assert "permanent right" in notes_lower
