# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for opensalestax.core.coverage."""

from __future__ import annotations

from opensalestax.core.coverage import (
    STATE_COVERAGE_WARNINGS,
    coverage_warning_for_states,
)


def test_known_gap_states_have_warnings() -> None:
    """The states with documented coverage gaps each have a warning.

    HI was removed on 2026-07-06: the last open HI item (the Maui
    County 0.5% GET surcharge) was confirmed in effect since
    2024-01-01 and encoded, so all four inhabited counties are now
    correctly modeled and HI no longer understates the rate.
    """
    assert "CO" in STATE_COVERAGE_WARNINGS
    assert "LA" in STATE_COVERAGE_WARNINGS
    assert "AL" in STATE_COVERAGE_WARNINGS
    assert "HI" not in STATE_COVERAGE_WARNINGS  # resolved 2026-07-06


def test_warning_for_states_returns_none_for_clean_state() -> None:
    """States with full coverage return None."""
    assert coverage_warning_for_states(["MN"]) is None
    assert coverage_warning_for_states(["TX", "CA"]) is None
    assert coverage_warning_for_states([]) is None


def test_warning_for_states_returns_message_for_co() -> None:
    """A CO-only query returns the CO warning."""
    msg = coverage_warning_for_states(["CO"])
    assert msg is not None
    assert "Colorado" in msg
    assert "home-rule" in msg


def test_warning_for_states_returns_message_for_co_mixed() -> None:
    """A query that returns multiple states picks up CO's warning when CO is one."""
    msg = coverage_warning_for_states(["CA", "CO"])
    assert msg is not None
    assert "Colorado" in msg


def test_warning_for_states_joins_multiple_warnings() -> None:
    """Multiple warning states get joined with separator."""
    msg = coverage_warning_for_states(["CO", "LA"])
    assert msg is not None
    assert "Colorado" in msg
    assert "Louisiana" in msg
    assert " | " in msg


def test_warning_messages_are_under_280_chars() -> None:
    """Warning messages should fit in a UI banner without truncation.

    Soft cap at 600 chars (banner-friendly across a typical viewport).
    """
    for abbrev, msg in STATE_COVERAGE_WARNINGS.items():
        assert len(msg) < 600, f"{abbrev} warning is {len(msg)} chars (too long for banner)"
