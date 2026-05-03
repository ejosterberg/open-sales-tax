# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Async SQLAlchemy engine and session factory.

Per constitution §10 rule 4, engine selection happens here and
NOWHERE ELSE. Application code reads ``settings.database_dsn`` and
gets back a session; whether the underlying engine is PostgreSQL
or MariaDB is invisible.
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from opensalestax.settings import Settings, get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine(settings: Settings | None = None) -> AsyncEngine:
    """Return the process-singleton AsyncEngine.

    The first call constructs the engine from the active Settings;
    subsequent calls return the same instance. Tests can reset by
    calling :func:`reset_engine` between scenarios.
    """
    global _engine, _sessionmaker
    if _engine is None:
        s = settings or get_settings()
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
