# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Hawaii state module (Phase 6 Batch C -- non-SST tier-0 -> tier-1).

Hawaii is the GET-model state: HRS Chapter 237 imposes a General Excise
Tax on the seller's gross receipts rather than a transactional tax on
the buyer. For API purposes the module encodes the GET as if it were a
4.0% sales tax (per the per-state research brief). These tests pin the
GET-vs-sales-tax docstring distinction, the groceries-fully-taxed
peer-state difference, the no-holidays regression, and the per-county
surcharge documented-deferral.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.hawaii import HAWAII, Hawaii
from opensalestax.states.protocol import StateModule


def test_hawaii_metadata() -> None:
    assert HAWAII.state_abbrev == "HI"
    assert HAWAII.state_name == "Hawaii"
    assert HAWAII.sst_member is False  # HI is NOT in SST
    # API-shape: GET modeled as a sales tax (see module docstring rationale).
    assert HAWAII.has_sales_tax is True
    assert HAWAII.tier == 1
    assert HAWAII.self_seeded is True  # signals the loader to skip file lookup


def test_hawaii_satisfies_protocol() -> None:
    assert isinstance(HAWAII, StateModule)
    assert isinstance(Hawaii(), StateModule)


def test_hawaii_is_registered() -> None:
    assert get_state_module("HI") is HAWAII


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in HRS Chapter 237
        ("groceries", True),  # peer-state difference: HI fully taxes groceries
        ("prescription_drugs", False),  # HRS section 237-24.3(6)
        ("prepared_food", True),  # general 4.0% rate; no separate prepared-food rate
        ("digital_goods", True),  # TIR 2018-09 confirms software/SaaS/streaming all taxable
        ("general", True),  # HRS section 237-13(2)(A)
    ],
)
def test_hawaii_taxability(category: str, expected_taxable: bool) -> None:
    rule = HAWAII.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_hawaii_unknown_category_returns_none() -> None:
    assert HAWAII.taxability_for("shave-ice", dt.date(2026, 5, 3)) is None


def test_hawaii_parse_rates_yields_state_4_0_pct_and_per_county_surcharges() -> None:
    """Hawaii's statewide GET rate is 4.0% effective 1965-01-01 (Act 155, SLH
    1965), plus per-county surcharges under HRS section 46-16.8 shipped in v0.32.
    """
    rows = list(HAWAII.parse_rates(None, "v0.32-counties"))
    state_rows = [r for r in rows if r.authority_type == "state"]
    county_rows = [r for r in rows if r.authority_type == "county"]
    assert len(state_rows) == 1
    state = state_rows[0]
    assert state.authority_name == "Hawaii"
    assert state.rate_pct == Decimal("4.000")
    assert state.effective_from == dt.date(1965, 1, 1)
    assert state.effective_to is None
    assert state.parent_authority_name is None  # state-level rate has no parent
    # 5 HI counties: Hawaii / Honolulu / Kalawao / Kauai / Maui.
    county_by_name = {r.authority_name: r for r in county_rows}
    assert set(county_by_name) == {
        "Hawaii County",
        "Honolulu County",
        "Kalawao County",
        "Kauai County",
        "Maui County",
    }
    # Per-county surcharge rates (HI DOTAX county-surcharge schedule;
    # Maui corrected 0.000 -> 0.500 on 2026-07-06 daily audit).
    assert county_by_name["Honolulu County"].rate_pct == Decimal("0.500")
    assert county_by_name["Kauai County"].rate_pct == Decimal("0.500")
    assert county_by_name["Hawaii County"].rate_pct == Decimal("0.500")
    assert county_by_name["Maui County"].rate_pct == Decimal("0.500")
    assert county_by_name["Kalawao County"].rate_pct == Decimal("0.000")
    # Each county RateRow's parent must be the state.
    for c in county_rows:
        assert c.parent_authority_name == "Hawaii"
    # Per-county surcharge effective dates (HRS section 46-16.8).
    assert county_by_name["Honolulu County"].effective_from == dt.date(2007, 1, 1)
    assert county_by_name["Kauai County"].effective_from == dt.date(2019, 1, 1)
    assert county_by_name["Hawaii County"].effective_from == dt.date(2020, 1, 1)
    assert county_by_name["Maui County"].effective_from == dt.date(2024, 1, 1)


def test_hawaii_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same rows whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(HAWAII.parse_rates(None, "test"))
    rows_with_path = list(HAWAII.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_hawaii_parse_boundaries_emits_state_and_county_for_every_hi_zip() -> None:
    """v0.32: HI ZCTA-driven boundaries -- every HI ZIP gets state + county
    bindings so per-county surcharges resolve correctly. Spot-check the four
    inhabited counties via known centroid ZIPs.
    """
    rows = list(HAWAII.parse_boundaries(None, "v0.32-counties"))
    # Every emitted row must be tagged "Hawaii" (state) or one of the 5 county names.
    valid_authorities = {
        "Hawaii",
        "Hawaii County",
        "Honolulu County",
        "Kalawao County",
        "Kauai County",
        "Maui County",
    }
    for row in rows:
        assert row.authority_name in valid_authorities, row.authority_name
    # Spot-check: Honolulu 96813 -> state + Honolulu County.
    honolulu = [r for r in rows if r.zip5 == "96813"]
    names = sorted(r.authority_name for r in honolulu)
    assert names == ["Hawaii", "Honolulu County"]
    # Spot-check: Hilo 96720 -> state + Hawaii County (Big Island).
    hilo = [r for r in rows if r.zip5 == "96720"]
    names = sorted(r.authority_name for r in hilo)
    assert names == ["Hawaii", "Hawaii County"]
    # Spot-check: Lihue 96766 -> state + Kauai County.
    lihue = [r for r in rows if r.zip5 == "96766"]
    names = sorted(r.authority_name for r in lihue)
    assert names == ["Hawaii", "Kauai County"]
    # Spot-check: Kahului 96732 -> state + Maui County (0.5% surcharge since 2024-01-01).
    kahului = [r for r in rows if r.zip5 == "96732"]
    names = sorted(r.authority_name for r in kahului)
    assert names == ["Hawaii", "Maui County"]


def test_hawaii_combined_rate_oahu_arithmetic() -> None:
    """state 4.0% + Honolulu County 0.5% should sum to 4.5% on Oahu."""
    rows = list(HAWAII.parse_rates(None, "v0.32-counties"))
    state = next(r for r in rows if r.authority_type == "state")
    honolulu = next(r for r in rows if r.authority_name == "Honolulu County")
    combined = state.rate_pct + honolulu.rate_pct
    assert combined == Decimal("4.500")


def test_hawaii_combined_rate_maui_is_4_5() -> None:
    """Maui County's 0.5% GET surcharge has been in effect since
    2024-01-01 (County Ordinance 5511, signed 2023-07-19), so the
    combined GET on Maui is 4.5% (state 4.0% + county 0.5%). Verified
    against the HI DOTAX county-surcharge schedule on the 2026-07-06
    daily audit, which corrected an earlier revision that wrongly had
    Maui at 4.0% (state-only) and under-collected 0.5% from 2024-01-01.
    """
    rows = list(HAWAII.parse_rates(None, "v0.32-counties"))
    state = next(r for r in rows if r.authority_type == "state")
    maui = next(r for r in rows if r.authority_name == "Maui County")
    combined = state.rate_pct + maui.rate_pct
    assert combined == Decimal("4.500")


def test_hawaii_special_cases_empty() -> None:
    """The GET pass-through grossing-up rates (4.1666% on bare 4.0%; 4.7120%
    on 4.5% Oahu) are seller-pricing concerns documented in the module
    docstring, not engine SpecialCase entries.
    """
    cases = list(HAWAII.special_cases())
    assert cases == []


def test_hawaii_holidays_for_all_years_returns_empty() -> None:
    """Regression test: Hawaii has NO GET holidays in any year.

    Confirmed against the Hawaii Department of Taxation 2026-05-03.
    Bills proposing GET holidays have been introduced in past sessions
    but none have been enacted. This test exists specifically to catch
    any future regression where a contributor accidentally adds a
    holiday window (e.g. by copy-pasting from a state that does have
    one).
    """
    for year in range(2024, 2031):
        holidays = list(HAWAII.holidays_for(year))
        assert holidays == [], f"Hawaii should have no holidays in {year}"


def test_hawaii_module_docstring_documents_get_not_sales_tax() -> None:
    """Regression test: the module docstring MUST prominently document
    that Hawaii has a General Excise Tax (GET), NOT a sales tax. This
    is the single most important load-bearing distinction in the module
    and a future maintainer must not silently delete it.
    """
    import opensalestax.states.hawaii as hi_mod

    docstring = hi_mod.__doc__ or ""
    docstring_lower = docstring.lower()
    # Must use the exact phrase 'General Excise Tax' AND its acronym 'GET'.
    assert "general excise tax" in docstring_lower
    assert "GET" in docstring  # case-sensitive; the acronym must appear
    # Must explicitly disclaim that Hawaii is a sales-tax state.
    assert "does not have a sales tax" in docstring_lower or "not a sales tax" in docstring_lower
    # Must cite the controlling chapter.
    assert "Chapter 237" in docstring or "HRS Chapter 237" in docstring


def test_hawaii_module_docstring_documents_per_county_surcharge_data() -> None:
    """Regression test: the module docstring MUST document the four
    inhabited county surcharges (Honolulu / Kauai / Hawaii County /
    Maui), their per-county effective dates, and the controlling
    statute (HRS section 46-16.8). Otherwise a maintainer might
    silently change a rate without traceability to the source.
    """
    import opensalestax.states.hawaii as hi_mod

    docstring = hi_mod.__doc__ or ""
    docstring_lower = docstring.lower()
    # All four inhabited counties must be enumerated.
    assert "honolulu" in docstring_lower
    assert "kauai" in docstring_lower
    assert "maui" in docstring_lower
    # 'Hawaii County' (the Big Island) must be called out distinctly
    # from the state itself.
    assert "hawaii county" in docstring_lower or "big island" in docstring_lower
    # Must cite HRS section 46-16.8 (the county surcharge authorizing
    # statute).
    assert "46-16.8" in docstring
    # Must record that per-county data shipped (v0.32 promotion) so a
    # future maintainer doesn't reintroduce the deferral.
    assert "v0.32" in docstring or "shipped" in docstring_lower


def test_hawaii_groceries_notes_call_out_food_tax_credit_distinction() -> None:
    """The groceries rule must explicitly distinguish the income-tax
    food/excise credit (HRS section 235-55.85) from a GET-side
    exemption -- otherwise a reader could mistakenly assume Hawaii has
    a grocery exemption like most other states.
    """
    rule = HAWAII.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    notes_lower = notes.lower()
    # Must call out that groceries are taxable.
    assert "taxable" in notes_lower
    # Must cite the income-tax credit statute and clarify it's NOT a
    # GET-side exemption.
    assert "235-55.85" in notes
    assert "income-tax credit" in notes_lower or "income tax credit" in notes_lower


def test_hawaii_prescription_drugs_cite_section_237_24_3() -> None:
    """Prescription-drug exemption must cite the controlling statute."""
    rule = HAWAII.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    assert "237-24.3" in (rule.notes or "")


def test_hawaii_general_notes_call_out_get_model_and_county_surcharges() -> None:
    """The general rule must call out (a) the GET-vs-sales-tax legal
    distinction and (b) the per-county-surcharge structure (all four
    inhabited counties -- Honolulu / Kauai / Hawaii / Maui -- at 4.5%
    combined). Both are load-bearing distinctions integrators rely on.
    """
    rule = HAWAII.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    notes_lower = notes.lower()
    # Must mention the GET-vs-sales-tax legal distinction.
    assert "get" in notes_lower or "general excise tax" in notes_lower
    assert "not" in notes_lower and "sales tax" in notes_lower
    # Must call out the per-county surcharge structure and statute.
    assert "0.5" in notes or "4.5" in notes or "surcharge" in notes_lower
    assert "46-16.8" in notes


def test_hawaii_general_taxability_cites_section_237_13() -> None:
    """The general rule must cite HRS section 237-13(2)(A) (the general
    retail rate) so a future maintainer can verify the rate against
    the controlling statute.
    """
    rule = HAWAII.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert "237-13" in (rule.notes or "")


def test_hawaii_digital_goods_cite_tir_2018_09() -> None:
    """Digital-goods rule must cite Tax Information Release No. 2018-09
    (the Department of Taxation guidance confirming software/SaaS/
    streaming are all taxable under GET) so a future maintainer
    understands why HI does not need a sub-category split between
    permanent-right and subscription digital media.
    """
    rule = HAWAII.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "2018-09" in notes
    notes_lower = notes.lower()
    # Must clarify the unified base covers both downloads and SaaS.
    assert "saas" in notes_lower or "streaming" in notes_lower or "remotely" in notes_lower
