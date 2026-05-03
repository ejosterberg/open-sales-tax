# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Louisiana state module (Phase 6 Batch B / v0.7).

Louisiana is a non-SST state with a uniquely fragmented local
sales-tax landscape: each of 64 parishes independently administers
its own local sales/use tax. v0.7 ships the **state portion only**
(5% per Act 11 of 2024 3rd Extraordinary Session) and **does not
model parish, municipal, or special-district rates**. That deferral
is documented in:

- The module docstring (verified by an explicit test below)
- ``specs/decisions/05-louisiana-parishes.md``
- ``specs/research/references.md`` (LA section)

The currently-active LA holiday is the Annual Louisiana Second
Amendment Weekend Holiday (R.S. 47:305.62); two other historical
holidays (back-to-school under R.S. 47:305.54, hurricane prep under
R.S. 47:305.58) have been suspended since 2018 and were NOT
reauthorized in the 2025 Regular Session.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from pathlib import Path

import pytest

from opensalestax.states import get_state_module
from opensalestax.states.louisiana import LOUISIANA, Louisiana
from opensalestax.states.protocol import HolidayWindow, StateModule


def test_louisiana_metadata() -> None:
    assert LOUISIANA.state_abbrev == "LA"
    assert LOUISIANA.state_name == "Louisiana"
    assert LOUISIANA.sst_member is False  # LA is NOT in SST
    assert LOUISIANA.has_sales_tax is True
    assert LOUISIANA.tier == 1
    assert LOUISIANA.self_seeded is True  # signals loader to skip file lookup


def test_louisiana_satisfies_protocol() -> None:
    assert isinstance(LOUISIANA, StateModule)
    assert isinstance(Louisiana(), StateModule)


def test_louisiana_is_registered() -> None:
    assert get_state_module("LA") is LOUISIANA


@pytest.mark.parametrize(
    "category,expected_taxable",
    [
        ("clothing", True),  # no clothing exemption; back-to-school holiday suspended
        ("groceries", False),  # state-level exempt per R.S. 47:305(D); parishes vary
        ("prescription_drugs", False),  # exempt per R.S. 47:305(D) and 47:305.10
        ("prepared_food", True),  # food-at-home exemption excludes prepared food
        ("digital_goods", True),  # taxable since 2025-01-01 per Act 10 (HB 8)
        ("general", True),  # baseline tangible personal property at 5%
    ],
)
def test_louisiana_taxability(category: str, expected_taxable: bool) -> None:
    rule = LOUISIANA.taxability_for(category, dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is expected_taxable
    assert rule.notes
    # Statutory citation must appear in every rule's notes (constitution +
    # brief). Accept any of the LA citations that show up across categories.
    notes_lower = rule.notes.lower()
    assert any(
        token in notes_lower
        for token in (
            "47:301",
            "47:305",
            "47:305.10",
            "47:337",
            "act 10",
            "act 11",
            "art. vii",
        )
    )


def test_louisiana_unknown_category_returns_none() -> None:
    assert LOUISIANA.taxability_for("alpaca-fur", dt.date(2026, 5, 3)) is None


def test_louisiana_parse_rates_yields_5pct() -> None:
    """Louisiana's statewide rate is 5% effective 2025-01-01 through 2029-12-31."""
    rows = list(LOUISIANA.parse_rates(None, "v0.7-statewide"))
    assert len(rows) == 1
    row = rows[0]
    assert row.authority_name == "Louisiana"
    assert row.authority_type == "state"
    assert row.rate_pct == Decimal("5.000")
    assert row.effective_from == dt.date(2025, 1, 1)
    # The 5% rate is TEMPORARY -- Act 11 of 2024 3rd Extraordinary
    # Session sunsets it 2029-12-31; on 2030-01-01 the rate is
    # scheduled to step down to 4.75% absent further legislation.
    assert row.effective_to == dt.date(2029, 12, 31)
    assert row.parent_authority_name is None


def test_louisiana_parse_rates_ignores_source_file() -> None:
    """parse_rates returns the same row whether given a path or None."""
    rows_with_none = list(LOUISIANA.parse_rates(None, "test"))
    rows_with_path = list(LOUISIANA.parse_rates(Path("/dev/null"), "test"))
    assert rows_with_none == rows_with_path


def test_louisiana_parse_boundaries_returns_empty() -> None:
    """v0.7 doesn't ship LA boundaries; per-parish load deferred to v1.0+."""
    rows = list(LOUISIANA.parse_boundaries(None, "v0.7-statewide"))
    assert rows == []


def test_louisiana_special_cases_empty() -> None:
    cases = list(LOUISIANA.special_cases())
    assert cases == []


# ---------------------------------------------------------------------------
# Parish-deferral documentation tests -- specifically requested by the
# orchestrator brief: the parish limitation MUST be prominently documented.
# ---------------------------------------------------------------------------
def test_louisiana_module_docstring_documents_parish_deferral() -> None:
    """The module docstring must prominently document the parish-tax limitation.

    Required by the orchestrator brief. A future maintainer (or
    downstream caller reading the source) MUST be able to see the
    deferral without hunting for it.
    """
    docstring = Louisiana.__module__
    # Pull the actual docstring from the module object.
    import opensalestax.states.louisiana as la_module

    module_doc = la_module.__doc__
    assert module_doc is not None
    doc_lower = module_doc.lower()
    # Must mention parishes and that they are not modeled.
    assert "parish" in doc_lower
    # Must reference the decision document or otherwise call out v0.7 deferral.
    assert (
        "decisions/05-louisiana-parishes.md" in doc_lower
        or "not modeled" in doc_lower
        or "deferred" in doc_lower
    )
    # Must reference the count (64 parishes) so readers grasp the scale.
    assert "64" in module_doc
    # Sanity: the docstring must not be tiny (parish discussion is
    # substantial enough that a short docstring would mean we lost it).
    assert len(module_doc) > 1500
    # Avoid an unused-import lint failure on opensalestax.states.louisiana.
    del docstring, la_module


def test_louisiana_class_docstring_documents_parish_deferral() -> None:
    """The Louisiana class docstring also calls out the deferral.

    Many tooling surfaces (e.g., FastAPI auto-doc, IDE hover) show
    the class docstring rather than the module docstring; the
    parish-deferral note has to be visible there too.
    """
    assert Louisiana.__doc__ is not None
    class_doc_lower = Louisiana.__doc__.lower()
    assert "parish" in class_doc_lower
    assert "not modeled" in class_doc_lower or "v0.7" in class_doc_lower


def test_louisiana_groceries_notes_parish_caveat() -> None:
    """The grocery rule must call out that parishes generally still tax groceries."""
    rule = LOUISIANA.taxability_for("groceries", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "parish" in notes_lower
    assert "47:305" in rule.notes


def test_louisiana_general_notes_temporary_rate_caveat() -> None:
    """The general rule must explain that the 5% rate is TEMPORARY (Act 11 sunset)."""
    rule = LOUISIANA.taxability_for("general", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "temporary" in notes_lower or "2029" in rule.notes or "2030" in rule.notes
    assert "act 11" in notes_lower or "hb 10" in notes_lower


def test_louisiana_digital_goods_notes_post_2025_change() -> None:
    """The digital-goods rule must reference the 2025-01-01 Act 10 change.

    Pre-2025 LA generally did not tax digital products; the rule has
    to remind a maintainer that this is a recent change tied to a
    specific Act, not a long-standing position.
    """
    rule = LOUISIANA.taxability_for("digital_goods", dt.date(2026, 5, 3))
    assert rule is not None
    assert rule.is_taxable is True
    assert rule.notes is not None
    notes_lower = rule.notes.lower()
    assert "2025" in rule.notes
    assert "act 10" in notes_lower or "hb 8" in notes_lower


# ---------------------------------------------------------------------------
# Holiday tests (Second Amendment Weekend) -- mirrors test_state_south_carolina
# shape; LA has only one currently-active annual holiday.
# ---------------------------------------------------------------------------
def test_louisiana_holiday_count_2026() -> None:
    """LA has exactly one active annual holiday in 2026 (Second Amendment Weekend).

    The back-to-school (R.S. 47:305.54) and hurricane prep (R.S.
    47:305.58) holidays are suspended; HB 551 (2025) failed to
    reauthorize. Only the Second Amendment Weekend (R.S. 47:305.62)
    is active.
    """
    holidays = list(LOUISIANA.holidays_for(2026))
    assert len(holidays) == 1
    assert all(isinstance(h, HolidayWindow) for h in holidays)


def test_louisiana_holiday_dates_2026() -> None:
    """2026 Second Amendment Weekend: Friday Sept 4 through Sunday Sept 6.

    R.S. 47:305.62 specifies "the first consecutive Friday through
    Sunday of September" each year. September 1, 2026 is a Tuesday,
    so the first Friday is September 4.
    """
    (holiday,) = list(LOUISIANA.holidays_for(2026))
    assert holiday.starts_on == dt.date(2026, 9, 4)
    assert holiday.ends_on == dt.date(2026, 9, 6)
    # Sanity: starts on a Friday, ends on a Sunday (statutory pattern).
    assert holiday.starts_on.weekday() == 4  # Friday
    assert holiday.ends_on.weekday() == 6  # Sunday


def test_louisiana_holiday_has_no_per_item_cap() -> None:
    """R.S. 47:305.62 does not impose a per-item dollar threshold."""
    (holiday,) = list(LOUISIANA.holidays_for(2026))
    assert holiday.max_amount_per_item is None


def test_louisiana_holiday_categories_cover_firearms_and_hunting() -> None:
    """R.S. 47:305.62 covers firearms, ammunition, and hunting supplies."""
    (holiday,) = list(LOUISIANA.holidays_for(2026))
    assert holiday.applicable_categories is not None
    cats = set(holiday.applicable_categories)
    assert "firearms" in cats
    assert "ammunition" in cats
    assert "hunting_supplies" in cats


def test_louisiana_holiday_notes_cite_statute_and_local_scope() -> None:
    """The holiday window's notes must cite R.S. 47:305.62 AND note local applicability."""
    (holiday,) = list(LOUISIANA.holidays_for(2026))
    assert holiday.notes is not None
    assert "47:305.62" in holiday.notes
    notes_lower = holiday.notes.lower()
    # The statute extends to "the state of Louisiana and its political
    # subdivisions" -- the notes must surface that the holiday is one of
    # the few LA exemptions that DOES bind parishes.
    assert "parish" in notes_lower or "local" in notes_lower
    # Excluded items must be mentioned (animal feed / ATVs / business use)
    # so a downstream implementer knows the scope is narrower than "any
    # firearm-shaped item bought during the window".
    assert "atv" in notes_lower or "animal feed" in notes_lower or "business" in notes_lower


def test_louisiana_holiday_unknown_year_returns_empty() -> None:
    """Future / past years return empty (no extrapolation by design).

    The legislature has documented history of suspending and amending
    these holidays; later years require explicit data updates.
    """
    assert list(LOUISIANA.holidays_for(2024)) == []
    assert list(LOUISIANA.holidays_for(2025)) == []
    assert list(LOUISIANA.holidays_for(2027)) == []
    assert list(LOUISIANA.holidays_for(2099)) == []
