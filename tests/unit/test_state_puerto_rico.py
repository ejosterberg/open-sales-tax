# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Puerto Rico jurisdiction module (Phase 8 -- US territory tier-0 -> tier-1).

PR is a US territory (commonwealth), not a US state. Its IVU
(Impuesto sobre Ventas y Uso) is administered by the Departamento
de Hacienda de Puerto Rico under the Codigo de Rentas Internas
(13 L.P.R.A. sections 32001 et seq.). The module encodes the
combined 11.5% rate (10.5% state + 1.0% municipal) as a single
territory-level RateRow per the encoding decision documented in
the module's docstring.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.protocol import StateModule
from opensalestax.states.puerto_rico import PUERTO_RICO, PuertoRico


def test_puerto_rico_metadata() -> None:
    assert PUERTO_RICO.state_abbrev == "PR"
    assert PUERTO_RICO.state_name == "Puerto Rico"
    assert PUERTO_RICO.sst_member is False  # PR is a US territory; not eligible for SST
    assert PUERTO_RICO.has_sales_tax is True  # IVU is structurally a sales tax
    assert PUERTO_RICO.tier == 1
    assert PUERTO_RICO.self_seeded is True  # signals the loader to skip file lookup


def test_puerto_rico_satisfies_protocol() -> None:
    assert isinstance(PUERTO_RICO, StateModule)
    assert isinstance(PuertoRico(), StateModule)


def test_puerto_rico_is_registered() -> None:
    assert get_state_module("PR") is PUERTO_RICO


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption in Codigo de Rentas Internas
        ("groceries", False),  # exempt per 13 L.P.R.A. section 32023
        ("prescription_drugs", False),  # exempt per 13 L.P.R.A. section 32023
        ("prepared_food", True),  # excluded from grocery exemption; section 32020
        ("digital_goods", True),  # 13 L.P.R.A. sections 32011, 32020
        ("general", True),  # general imposition under 13 L.P.R.A. section 32020
    ],
)
def test_puerto_rico_taxability(category: str, expected_taxable: bool) -> None:
    rule = PUERTO_RICO.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes  # statutory citation must be present


def test_puerto_rico_unknown_category_returns_none() -> None:
    assert PUERTO_RICO.taxability_for("piragua-cart", dt.date(2026, 5, 3)) is None


def test_puerto_rico_parse_rates_yields_combined_11_5_pct() -> None:
    """PR's combined IVU rate is 11.5% (10.5% state + 1.0% municipal),
    encoded as a single territory-level row per the module's encoding
    decision. Effective from 2015-07-01 (Act No. 72 of 2015).
    """
    rows = list(PUERTO_RICO.parse_rates(None, "v0.13-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Puerto Rico"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("11.500")
    assert row.effective_from == dt.date(2015, 7, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None  # territory-level rate has no parent


def test_puerto_rico_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    from pathlib import Path

    rows_with_none = list(PUERTO_RICO.parse_rates(None, "test"))
    rows_with_path = list(PUERTO_RICO.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_puerto_rico_parse_boundaries_returns_empty() -> None:
    """PR's IVU is statutorily uniform across all 78 municipalities --
    no per-municipality variation, so no sub-state boundaries to ship.
    """
    rows = list(PUERTO_RICO.parse_boundaries(None, "v0.13-statewide"))
    assert rows == []


def test_puerto_rico_special_cases_empty() -> None:
    """The 4% Special IVU on B2B services (13 L.P.R.A. section 32022)
    is documented but not yet exposed via SpecialCase (engine support
    pending B2B-service-tax sub-base).
    """
    cases = list(PUERTO_RICO.special_cases())
    assert cases == []


def test_puerto_rico_holidays_for_all_years_returns_empty() -> None:
    """Regression test: PR's "Dias sin IVU" holiday is enacted ad hoc
    each year; as of this module's ship date (2026-05-03) the
    Departamento de Hacienda had NOT yet announced 2026 dates or
    scope. holidays_for(year) returns an empty iterator for every
    year until an official announcement is encoded.

    This regression test exists specifically to catch any future
    contributor who adds holiday data without consulting Hacienda's
    official Carta Circular for that year. When 2026 (or 2027, etc.)
    is officially announced, the test must be relaxed for the
    affected year and a HolidayWindow added with the announced data.
    """
    for year in range(2024, 2031):
        holidays = list(PUERTO_RICO.holidays_for(year))
        assert holidays == [], f"PR should have no encoded holidays in {year}"


def test_puerto_rico_module_docstring_documents_territorial_status() -> None:
    """Regression test: the module docstring MUST prominently document
    that PR is a US territory (not a US state) and that its tax
    authority is the Departamento de Hacienda. This is load-bearing
    context that distinguishes PR from the 50 state modules in the
    catalog and prevents future contributors from accidentally
    treating PR as if it were SST-eligible or under federal/state
    DOR oversight.
    """
    from opensalestax.states import puerto_rico as pr_module

    doc = (pr_module.__doc__ or "").lower()
    assert "us territory" in doc or "u.s. territory" in doc
    assert "departamento de hacienda" in doc
    # Must explicitly state that PR is not in SST -- accept either
    # plain prose ("not an sst member") or markdown-emphasis prose
    # ("not** an sst member") since the docstring uses Markdown for
    # emphasis on the load-bearing negation.
    assert "sst member" in doc
    assert "not an sst member" in doc or "not** an sst member" in doc


def test_puerto_rico_module_docstring_documents_combined_rate_rationale() -> None:
    """Regression test: the module docstring MUST document the
    encoding decision to emit a SINGLE combined 11.5% rate rather
    than splitting into 10.5% state + 1.0% municipal rows. Future
    maintainers (or auditors) need to find this rationale without
    re-deriving it; the docstring is the canonical home for the
    decision.
    """
    from opensalestax.states import puerto_rico as pr_module

    doc = pr_module.__doc__ or ""
    # Both statutory components must be cited in the rate-structure
    # discussion.
    assert "10.5%" in doc
    assert "1.0%" in doc
    assert "11.5%" in doc
    # The encoding-decision rationale must explicitly appear.
    doc_lower = doc.lower()
    assert "encoding decision" in doc_lower
    # Both controlling statutes must be cited.
    assert "32021" in doc  # state portion
    assert "32024" in doc  # municipal portion


def test_puerto_rico_groceries_notes_cite_section_32023_and_call_out_prepared_food() -> None:
    """Regression test: the grocery-exemption notes MUST cite the
    controlling statute (13 L.P.R.A. section 32023) and MUST call
    out that prepared food, restaurant meals, candy, and dietary
    supplements remain taxable. A reader should not assume ALL food
    is exempt -- the exemption is narrow (unprepared food only).
    """
    rule = PUERTO_RICO.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "32023" in notes
    notes_lower = notes.lower()
    # Must call out the major exclusions a layperson might miss.
    assert "prepared food" in notes_lower
    assert "candy" in notes_lower
    assert "act no. 72" in notes_lower or "2015" in notes_lower


def test_puerto_rico_general_notes_cite_both_statutory_components() -> None:
    """Regression test: the 'general' rule's notes must cite BOTH the
    state-portion statute (section 32021) and the municipal-portion
    statute (section 32024) so the 11.5% combined rate's legal
    components are traceable directly from the rule that the engine
    applies to general taxable items.
    """
    rule = PUERTO_RICO.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "32021" in notes
    assert "32024" in notes
    assert "11.5%" in notes
    # Territorial status must also be reiterated in the engine-
    # consulted rule (not only in the docstring).
    notes_lower = notes.lower()
    assert "territory" in notes_lower or "commonwealth" in notes_lower


def test_puerto_rico_prescription_drugs_call_out_otc_distinction() -> None:
    """Regression test: the prescription-drug-exemption notes MUST
    call out that OVER-THE-COUNTER (OTC) medications are NOT covered
    by the exemption -- otherwise an integrator could miscategorize
    OTC pain relievers, vitamins, etc. as exempt and under-collect.
    """
    rule = PUERTO_RICO.taxability_for("prescription_drugs", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "32023" in notes
    notes_lower = notes.lower()
    assert "over-the-counter" in notes_lower or "otc" in notes_lower


def test_puerto_rico_digital_goods_notes_call_out_b2b_special_ivu() -> None:
    """Regression test: the digital-goods notes must point an
    integrator toward the SEPARATE 4% Special IVU on B2B services
    (13 L.P.R.A. section 32022) for B2B service transactions, so
    that a B2B SaaS seller does not silently apply the 11.5% retail
    rate to a transaction that should fall under the narrower 4%
    rate (or vice versa).
    """
    rule = PUERTO_RICO.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    notes = rule.notes or ""
    assert "32022" in notes
    notes_lower = notes.lower()
    assert "4%" in notes
    assert "b2b" in notes_lower or "business-to-business" in notes_lower
