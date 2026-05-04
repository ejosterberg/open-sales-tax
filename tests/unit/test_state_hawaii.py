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


def test_hawaii_parse_rates_yields_4_0_pct() -> None:
    """Hawaii's statewide GET rate is 4.0% effective 1965-01-01 (Act 155, SLH 1965)."""
    rows = list(HAWAII.parse_rates(None, "v0.13-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Hawaii"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("4.000")
    assert row.effective_from == dt.date(1965, 1, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None  # state-level rate has no parent


def test_hawaii_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(HAWAII.parse_rates(None, "test"))
    rows_with_path = list(HAWAII.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_hawaii_parse_boundaries_returns_empty() -> None:
    """Hawaii's per-county surcharges (Honolulu/Kauai/Hawaii/Maui) are deferred
    from v1 -- no boundary rows are shipped until a per-county data path lands.
    """
    rows = list(HAWAII.parse_boundaries(None, "v0.13-statewide"))
    assert rows == []


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


def test_hawaii_module_docstring_documents_per_county_surcharge_deferral() -> None:
    """Regression test: the module docstring MUST document the four
    county surcharges (Honolulu / Kauai / Hawaii County / Maui) and
    their deferral. Otherwise a maintainer might silently encode one
    county without addressing the under-collection on the others.
    """
    import opensalestax.states.hawaii as hi_mod

    docstring = hi_mod.__doc__ or ""
    docstring_lower = docstring.lower()
    # All four counties must be enumerated.
    assert "honolulu" in docstring_lower
    assert "kauai" in docstring_lower
    assert "maui" in docstring_lower
    # 'Hawaii County' (the Big Island) must be called out distinctly
    # from the state itself.
    assert "hawaii county" in docstring_lower or "big island" in docstring_lower
    # Must cite HRS section 46-16.8 (the county surcharge authorizing
    # statute).
    assert "46-16.8" in docstring
    # Must call out the deferral.
    assert "defer" in docstring_lower


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


def test_hawaii_general_notes_call_out_get_model_and_county_undercollection() -> None:
    """The general rule must call out (a) the GET-vs-sales-tax legal
    distinction and (b) the per-county-surcharge under-collection.
    Both are load-bearing distinctions integrators rely on.
    """
    rule = HAWAII.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    notes_lower = notes.lower()
    # Must mention the GET-vs-sales-tax legal distinction.
    assert "get" in notes_lower or "general excise tax" in notes_lower
    assert "not" in notes_lower and "sales tax" in notes_lower
    # Must call out the per-county under-collection.
    assert "0.5" in notes or "4.5" in notes or "surcharge" in notes_lower
    assert "under-collect" in notes_lower or "undercollect" in notes_lower


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
