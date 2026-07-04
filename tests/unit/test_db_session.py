# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Tests for the optional-driver preflight guard in db.session.

MariaDB support ships as an optional extra (`opensalestax[mariadb]`), so a
default PostgreSQL install does not carry the asyncmy driver. `get_engine`
must fail fast with an actionable install hint when a `mysql+asyncmy://` DSN
is used without the extra -- rather than surfacing SQLAlchemy's bare
`ModuleNotFoundError` deep inside the first connection attempt.
"""

from __future__ import annotations

import pytest

from opensalestax.db import session as db_session


def test_require_dsn_driver_passes_for_postgres() -> None:
    """PostgreSQL DSNs name no optional driver, so the guard is a no-op."""
    db_session._require_dsn_driver("postgresql+asyncpg://u:p@h:5432/db")


def test_require_dsn_driver_passes_when_optional_driver_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mysql DSN is fine when the asyncmy driver is importable."""
    monkeypatch.setattr(db_session.importlib.util, "find_spec", lambda name: object())
    db_session._require_dsn_driver("mysql+asyncmy://u:p@h:3306/db")


def test_require_dsn_driver_raises_actionable_error_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A mysql DSN without the extra raises with the install command."""
    monkeypatch.setattr(db_session.importlib.util, "find_spec", lambda name: None)
    with pytest.raises(RuntimeError) as excinfo:
        db_session._require_dsn_driver("mysql+asyncmy://u:p@h:3306/db")
    msg = str(excinfo.value)
    assert "opensalestax[mariadb]" in msg
    assert "asyncmy" in msg


def test_get_engine_fails_fast_on_missing_mariadb_driver(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """get_engine surfaces the friendly error before building the engine."""
    monkeypatch.setattr(db_session.importlib.util, "find_spec", lambda name: None)
    monkeypatch.setenv("OPENSALESTAX_DATABASE_URL", "mysql+asyncmy://u:p@h:3306/db")

    from opensalestax import settings as settings_mod

    settings_mod._settings = None
    db_session._engine = None
    db_session._sessionmaker = None
    try:
        with pytest.raises(RuntimeError, match=r"opensalestax\[mariadb\]"):
            db_session.get_engine()
        # Guard must raise BEFORE the singleton is assigned.
        assert db_session._engine is None
    finally:
        settings_mod._settings = None
        db_session._engine = None
        db_session._sessionmaker = None
