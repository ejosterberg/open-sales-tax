# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Colorado state module (v0.7 tier-1 ratchet, state-portion only).

The home-rule limitation (CO has ~70 home-rule self-collecting cities
that are NOT modeled in v0.7) is enforced here by tests that assert
the warning text is present in both the module docstring and the
``general``/``groceries`` taxability notes. If a future maintainer
removes the warning without adding actual home-rule support, these
tests fail loudly. See ``specs/decisions/04-colorado-home-rule.md``.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import colorado as colorado_module
from opensalestax.states import get_state_module
from opensalestax.states.colorado import COLORADO, Colorado
from opensalestax.states.protocol import StateModule


def test_colorado_metadata() -> None:
    assert COLORADO.state_abbrev == "CO"
    assert COLORADO.state_name == "Colorado"
    assert COLORADO.sst_member is False  # CO is NOT in SST
    assert COLORADO.has_sales_tax is True
    assert COLORADO.tier == 1
    assert COLORADO.self_seeded is True  # signals loader to skip file lookup


def test_colorado_satisfies_protocol() -> None:
    assert isinstance(COLORADO, StateModule)
    assert isinstance(Colorado(), StateModule)


def test_colorado_is_registered() -> None:
    assert get_state_module("CO") is COLORADO


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # CO has no clothing exemption
        ("groceries", False),  # state-level exempt per 39-26-707(1)(e)
        ("prescription_drugs", False),  # exempt per 39-26-717
        ("prepared_food", True),  # state exemption is for home-consumption food only
        ("digital_goods", True),  # taxable per HB21-1312, effective 2021-07-01
        ("general", True),  # baseline tangible personal property
    ],
)
def test_colorado_taxability(category: str, expected_taxable: bool) -> None:
    rule = COLORADO.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution + brief).
    notes_lower = rule.notes.lower()
    assert "39-26" in notes_lower or "hb 21-1312" in notes_lower


def test_colorado_unknown_category_returns_none() -> None:
    assert COLORADO.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_colorado_parse_rates_yields_29_pct() -> None:
    """Colorado's statewide rate is 2.9% effective 2001-01-01."""
    rows = list(COLORADO.parse_rates(None, "v0.7-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Colorado"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("2.900")
    assert row.effective_from == dt.date(2001, 1, 1)
    assert row.effective_to is None
    assert row.parent_authority_name is None


def test_colorado_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(COLORADO.parse_rates(None, "test"))
    rows_with_path = list(COLORADO.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_colorado_parse_boundaries_returns_empty() -> None:
    """v0.7 doesn't ship CO boundaries; per-county / per-city loads deferred."""
    rows = list(COLORADO.parse_boundaries(None, "v0.7-statewide"))
    assert rows == []


def test_colorado_special_cases_empty() -> None:
    cases = list(COLORADO.special_cases())
    assert cases == []


def test_colorado_no_state_level_holidays() -> None:
    """Colorado has NO state-level sales-tax holidays for any year."""
    for year in (2024, 2025, 2026, 2027, 2099):
        assert list(COLORADO.holidays_for(year)) == []


# ---------------------------------------------------------------------------
# Home-rule limitation enforcement
# ---------------------------------------------------------------------------
# These tests are the load-bearing safety net for the "honest deferral"
# decision (specs/decisions/04-colorado-home-rule.md). If the warning
# text disappears without actual home-rule support landing, these tests
# fail and the PR is blocked.
def test_colorado_module_docstring_warns_about_home_rule() -> None:
    """The module docstring must prominently warn about the home-rule limitation."""
    docstring = colorado_module.__doc__ or ""
    docstring_lower = docstring.lower()
    # The word "home-rule" (with the hyphen) MUST appear -- it's the term
    # of art for the limitation.
    assert "home-rule" in docstring_lower
    # The docstring must say cities self-administer (or self-collect) so
    # readers understand WHY the state module can't model them.
    assert "self-administer" in docstring_lower or "self-collect" in docstring_lower
    # The warning must appear early -- not buried at the bottom. Check
    # that it shows up in the first 1500 characters of the docstring.
    assert "home-rule" in docstring[:1500].lower()


def test_colorado_general_rule_warns_about_home_rule_in_notes() -> None:
    """The ``general`` taxability rule must call out home-rule cities."""
    rule = COLORADO.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "home-rule" in notes_lower
    # Mention at least one of the largest home-rule cities by name so
    # the warning is concrete, not abstract.
    assert any(city in notes_lower for city in ("denver", "boulder", "colorado springs"))


def test_colorado_groceries_warns_about_local_taxes() -> None:
    """Groceries are state-exempt but most home-rule cities tax them locally."""
    rule = COLORADO.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    # The rule must explicitly warn that home-rule cities tax groceries
    # locally even though the state exempts them -- a critical gotcha.
    assert "home-rule" in notes_lower
    assert "local" in notes_lower
    # Must cite the underlying state-exemption statute.
    assert "39-26-707" in rule.notes


def test_colorado_digital_goods_cites_hb21_1312() -> None:
    """Digital goods rule must cite HB21-1312, the bill that made them taxable."""
    rule = COLORADO.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    assert "21-1312" in rule.notes  # tolerates "HB 21-1312" or "HB21-1312"
