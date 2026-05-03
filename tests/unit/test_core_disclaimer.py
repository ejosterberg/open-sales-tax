# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the core disclaimer module."""

from __future__ import annotations

from opensalestax.core.disclaimer import DISCLAIMER, disclaimer


def test_disclaimer_function_returns_constant() -> None:
    assert disclaimer() == DISCLAIMER


def test_disclaimer_is_constitutional() -> None:
    """Constitution §13: every calc response must disclaim non-advice."""
    text = disclaimer().lower()
    # Must clearly state this isn't advice
    assert "not legal" in text
    assert "tax advice" in text
    # Must clearly state this is calculation only
    assert "calculation" in text


def test_disclaimer_is_non_empty_string() -> None:
    assert isinstance(DISCLAIMER, str)
    assert DISCLAIMER.strip()
