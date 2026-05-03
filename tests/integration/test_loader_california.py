# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Integration test for loading California (the self-seeded path).

Verifies the loader's ``self_seeded`` branch: no upstream file
needed, parse_rates yields a single statewide row, the API can
then return CA's 7.25% rate without any prior `data fetch`.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from opensalestax.app import create_app
from opensalestax.data.loader import load_state_data
from opensalestax.db.models import Boundary, DataVersion, Rate, State, TaxAuthority
from opensalestax.db.session import get_session


@pytest_asyncio.fixture
async def client(db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    app = create_app()
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


@pytest.mark.asyncio
async def test_load_california_without_a_file(async_session: AsyncSession) -> None:
    """California loads without `data fetch` -- self_seeded skips the file lookup."""
    summary = await load_state_data(
        async_session,
        state_abbrev="CA",
        version_label="v0.2-statewide",
        cache_dir=None,  # no cache; self_seeded ignores it
    )

    assert summary.state_abbrev == "CA"
    assert summary.rates_loaded == 1
    assert summary.boundaries_loaded == 0  # no boundaries in v0.2

    ca = (await async_session.execute(select(State).where(State.abbrev == "CA"))).scalar_one()
    assert ca.has_sales_tax is True
    assert ca.sst_member is False

    state_auth = (
        await async_session.execute(
            select(TaxAuthority).where(
                TaxAuthority.state_id == ca.id,
                TaxAuthority.authority_type == "state",
            )
        )
    ).scalar_one()
    state_rate = (
        (await async_session.execute(select(Rate).where(Rate.authority_id == state_auth.id)))
        .scalars()
        .first()
    )
    assert state_rate is not None
    assert state_rate.rate_pct == Decimal("7.250")

    # No boundaries shipped for CA in v0.2
    boundaries = (await async_session.execute(select(Boundary))).scalars().all()
    assert list(boundaries) == []


@pytest.mark.asyncio
async def test_load_california_creates_data_version(async_session: AsyncSession) -> None:
    """Even self-seeded loads create a DataVersion row for traceability."""
    await load_state_data(
        async_session,
        state_abbrev="CA",
        version_label="v0.2-statewide",
        cache_dir=None,
    )
    versions = (await async_session.execute(select(DataVersion))).scalars().all()
    labels = {v.version_label for v in versions}
    assert "CA-SST-V0.2-STATEWIDE" in labels  # _full_label normalizer


@pytest.mark.asyncio
async def test_california_idempotent_load(async_session: AsyncSession) -> None:
    """Running load CA twice doesn't accumulate duplicate rates."""
    await load_state_data(async_session, "CA", "v0.2-statewide")
    await load_state_data(async_session, "CA", "v0.2-statewide")

    rates = (await async_session.execute(select(Rate))).scalars().all()
    assert len(list(rates)) == 1  # not 2 -- idempotent
