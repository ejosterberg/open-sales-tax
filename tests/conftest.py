# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Pytest fixtures for OpenSalesTax tests.

Tests run against the database engine selected by
``OPENSALESTAX_DATABASE_URL`` -- normally PostgreSQL or MariaDB.
CI exercises both via a matrix so that a test passing on only one
engine is caught.

Tests that don't need a database (pure unit tests, smoke tests)
do not import these fixtures and run regardless of DB availability.

Tests that need a database use the ``async_session`` fixture; if
``OPENSALESTAX_DATABASE_URL`` is unset, those tests are skipped
with a clear message rather than failing.

Fixture scoping note: every fixture here is **function-scoped** to
avoid the event-loop crossing problems that pytest-asyncio's
session-scoped async fixtures still have. Schema create/drop per
test costs ~100ms and is well worth the reliability.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from opensalestax.db.models import Base


def _has_database_url() -> bool:
    return bool(os.environ.get("OPENSALESTAX_DATABASE_URL"))


def _database_url() -> str:
    url = os.environ.get("OPENSALESTAX_DATABASE_URL")
    if not url:
        pytest.skip(
            "OPENSALESTAX_DATABASE_URL is not set; database-backed test skipped. "
            "Run `docker compose --profile postgres up` (or --profile mariadb) "
            "and export the URL to enable these tests.",
            allow_module_level=False,
        )
    return url


@pytest_asyncio.fixture
async def db_engine() -> AsyncIterator[AsyncEngine]:
    """Function-scoped AsyncEngine pointed at OPENSALESTAX_DATABASE_URL.

    Schema is created at fixture entry and dropped at teardown.
    Per decision 03 / constitution §10, this works against both
    PostgreSQL and MariaDB unchanged.

    Function scope sidesteps the event-loop scoping issues that
    pytest-asyncio session-scoped async fixtures still have.
    """
    url = _database_url()
    engine = create_async_engine(url, echo=False, future=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    try:
        yield engine
    finally:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        await engine.dispose()


@pytest_asyncio.fixture
async def async_session(db_engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    """Function-scoped AsyncSession that rolls back on exit."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        try:
            yield session
        finally:
            await session.rollback()


@pytest.fixture
def database_available() -> bool:
    """Return True if a database URL is configured."""
    return _has_database_url()
