# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Integration test for loading California (the self-seeded path).

Verifies the loader's ``self_seeded`` branch: no upstream file
needed, parse_rates yields the state + per-county + per-city stack,
and parse_boundaries yields the ZIP bindings the engine needs to
return the correct combined rate at top-50 city ZIPs.
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
from opensalestax.states.ca_data import CA_CITIES, CA_COUNTY_RATE_PCT


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
    """California loads without `data fetch` -- self_seeded skips the file lookup.

    Post-v0.27 the loader yields:
    - 1 state row (California, 7.250%)
    - one county row per distinct county touched by a covered city
    - one city row per CA_CITIES entry
    """
    summary = await load_state_data(
        async_session,
        state_abbrev="CA",
        version_label="v0.27-top-50",
        cache_dir=None,  # no cache; self_seeded ignores it
    )

    assert summary.state_abbrev == "CA"
    expected_counties = {county for county, _, _ in CA_CITIES.values()}
    expected_rates = 1 + len(expected_counties) + len(CA_CITIES)
    assert summary.rates_loaded == expected_rates

    # v0.28+ pattern: parse_boundaries iterates ZIP_COUNTY for every CA
    # ZIP (state + county per ZIP) plus emits city BoundaryRows for the
    # CA_CITIES set on top. Count is no longer just 3*N for cities;
    # delegate to the module's actual output rather than hardcoding.
    from opensalestax.states.california import California

    expected_boundaries = sum(1 for _ in California().parse_boundaries(None, "v0.27-top-50"))
    assert summary.boundaries_loaded == expected_boundaries

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

    # Boundaries shipped for the top-50 cities.
    boundaries = (await async_session.execute(select(Boundary))).scalars().all()
    assert len(list(boundaries)) == expected_boundaries

    # County authorities must exist for every county referenced by a covered city.
    county_auths = (
        (
            await async_session.execute(
                select(TaxAuthority).where(
                    TaxAuthority.state_id == ca.id,
                    TaxAuthority.authority_type == "county",
                )
            )
        )
        .scalars()
        .all()
    )
    assert {a.name for a in county_auths} == expected_counties
    # Spot-check the two largest county district overlays.
    by_name = {a.name: a for a in county_auths}
    la_rate = (
        (
            await async_session.execute(
                select(Rate).where(Rate.authority_id == by_name["Los Angeles County"].id)
            )
        )
        .scalars()
        .first()
    )
    assert la_rate is not None
    assert la_rate.rate_pct == CA_COUNTY_RATE_PCT["Los Angeles County"]
    alameda_rate = (
        (
            await async_session.execute(
                select(Rate).where(Rate.authority_id == by_name["Alameda County"].id)
            )
        )
        .scalars()
        .first()
    )
    assert alameda_rate is not None
    assert alameda_rate.rate_pct == CA_COUNTY_RATE_PCT["Alameda County"]


@pytest.mark.asyncio
async def test_load_california_creates_data_version(async_session: AsyncSession) -> None:
    """Even self-seeded loads create a DataVersion row for traceability."""
    await load_state_data(
        async_session,
        state_abbrev="CA",
        version_label="v0.27-top-50",
        cache_dir=None,
    )
    versions = (await async_session.execute(select(DataVersion))).scalars().all()
    labels = {v.version_label for v in versions}
    assert "CA-SST-V0.27-TOP-50" in labels  # _full_label normalizer


@pytest.mark.asyncio
async def test_california_idempotent_load(async_session: AsyncSession) -> None:
    """Running load CA twice doesn't accumulate duplicate rates."""
    await load_state_data(async_session, "CA", "v0.27-top-50")
    await load_state_data(async_session, "CA", "v0.27-top-50")

    rates = (await async_session.execute(select(Rate))).scalars().all()
    expected_counties = {county for county, _, _ in CA_CITIES.values()}
    expected_rates = 1 + len(expected_counties) + len(CA_CITIES)
    # Idempotent: not 2x the count.
    assert len(list(rates)) == expected_rates
