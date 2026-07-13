# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Async SQLAlchemy engine and session factory.

Per constitution §10 rule 4, engine selection happens here and
NOWHERE ELSE. Application code reads ``settings.database_dsn`` and
gets back a session; whether the underlying engine is PostgreSQL
or MariaDB is invisible.
"""

from __future__ import annotations

import importlib.util
from collections.abc import AsyncIterator
from urllib.parse import urlsplit

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from opensalestax.settings import Settings, get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None

# Async DB drivers that ship as OPTIONAL Poetry extras rather than being
# installed by default: driver-module -> extra name. Used only to turn
# SQLAlchemy's late, cryptic "No module named X" into an upfront, actionable
# "install this extra" message. This is a preflight availability check, NOT
# dialect branching -- the engine is still built generically by SQLAlchemy,
# so constitution §10 rule 4 (engine selection lives here and only here) holds.
_OPTIONAL_DRIVERS: dict[str, str] = {
    "asyncmy": "mariadb",
}


def _require_dsn_driver(dsn: str) -> None:
    """Fail fast if the DSN names an optional driver that isn't installed.

    Example: a ``mysql+asyncmy://`` DSN on a default (PostgreSQL) install
    raises with ``pip install "opensalestax[mariadb]"`` instead of a bare
    ``ModuleNotFoundError`` surfacing deep inside SQLAlchemy on first connect.
    """
    scheme = urlsplit(dsn).scheme
    driver = scheme.split("+", 1)[1] if "+" in scheme else ""
    extra = _OPTIONAL_DRIVERS.get(driver)
    if extra is not None and importlib.util.find_spec(driver) is None:
        raise RuntimeError(
            f"The database DSN uses the optional '{driver}' driver, which is "
            f"not installed. Install the extra:  "
            f'pip install "opensalestax[{extra}]"  '
            f"(or, for a source checkout, `poetry install --extras {extra}`)."
        )


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return the process-singleton AsyncEngine.

    The first call constructs the engine from the active Settings;
    subsequent calls return the same instance. Tests can reset by
    calling :func:`reset_engine` between scenarios.
    """
    global _engine, _sessionmaker
    if _engine is None:
        s = settings or get_settings()
        _require_dsn_driver(s.database_dsn)
        _engine = create_async_engine(
            s.database_dsn,
            echo=s.database_echo,
            future=True,
            pool_pre_ping=True,
        )
        _sessionmaker = async_sessionmaker(
            _engine,
            expire_on_commit=False,
            class_=AsyncSession,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    """Return the process-singleton sessionmaker bound to the engine."""
    if _sessionmaker is None:
        get_engine()  # initializes both engine and sessionmaker
    assert _sessionmaker is not None
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency: yield an AsyncSession, close on request exit.

    Usage::

        from fastapi import Depends
        from opensalestax.db.session import get_session

        @router.get("/things")
        async def list_things(session: AsyncSession = Depends(get_session)):
            ...
    """
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        yield session


async def reset_engine() -> None:
    """Dispose the engine and clear the singleton state.

    Used by tests that need a clean slate between fixtures, or by
    long-running services that need to roll the connection pool.
    """
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
