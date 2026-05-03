# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the Settings module."""

from __future__ import annotations

import opensalestax.settings as settings_module
from opensalestax.settings import Settings


def test_settings_loads_from_env(monkeypatch) -> None:
    """Settings reads OPENSALESTAX_*-prefixed env vars."""
    monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    monkeypatch.setenv("OPENSALESTAX_AUTH_MODE", "api_key")
    monkeypatch.setenv("OPENSALESTAX_RATE_LIMIT_PER_MINUTE", "120")

    s = Settings()  # type: ignore[call-arg]
    assert s.database_dsn == "postgresql+asyncpg://u:p@localhost:5432/db"
    assert s.auth_mode == "api_key"
    assert s.rate_limit_per_minute == 120


def test_database_dialect_extracts_scheme(monkeypatch) -> None:
    """database_dialect returns 'postgresql' or 'mysql' from the DSN."""
    monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "postgresql+asyncpg://u:p@h:5432/db")
    assert Settings().database_dialect == "postgresql"  # type: ignore[call-arg]

    monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "mysql+asyncmy://u:p@h:3306/db")
    assert Settings().database_dialect == "mysql"  # type: ignore[call-arg]


def test_get_settings_caches(monkeypatch) -> None:
    """get_settings returns the same instance on repeated calls."""
    monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "postgresql+asyncpg://u:p@localhost:5432/db")
    settings_module._settings = None  # reset singleton
    a = settings_module.get_settings()
    b = settings_module.get_settings()
    assert a is b
