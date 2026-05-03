# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Integration tests for the v1 API endpoints.

Exercises the full FastAPI app via httpx AsyncClient. DB-backed
endpoints (everything except the static /v1/states list) require
``OPENSALESTAX_DATABASE_URL`` -- skipped automatically when unset.
"""

from __future__ import annotations

import datetime as dt
from collections.abc import AsyncIterator
from decimal import Decimal

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from opensalestax import __version__
from opensalestax.app import create_app
from opensalestax.db.models import Boundary, DataVersion, Rate, State, TaxAuthority
from opensalestax.db.session import get_session


@pytest_asyncio.fixture
async def client(db_engine: AsyncEngine) -> AsyncIterator[AsyncClient]:
    """An httpx AsyncClient pointed at the FastAPI app in-process."""
    app = create_app()

    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


# ---------------------------------------------------------------------------
# /v1/health -- requires DB
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_health_returns_ok_with_version(client: AsyncClient) -> None:
    response = await client.get("/v1/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == __version__
    assert body["database_connected"] is True


# ---------------------------------------------------------------------------
# /v1/states -- pure-Python list, no DB needed but tested with DB present
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_states_lists_all_52(client: AsyncClient) -> None:
    response = await client.get("/v1/states")
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 52
    assert len(body["states"]) == 52


@pytest.mark.asyncio
async def test_states_marks_tier_1_states_correctly(client: AsyncClient) -> None:
    """All SST tier-1 + no-tax tier-1 states show tier=1.

    AR, GA, IA, IN promoted in v0.8; KS, KY, MI, NE, NV in v0.9 --
    all part of the Phase 7 SST ratchet.
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in (
        "MN",
        "WI",
        "AR",
        "GA",
        "IA",
        "IN",
        "KS",
        "KY",
        "MI",
        "NE",
        "NV",
        "AK",
        "DE",
        "MT",
        "NH",
        "OR",
    ):
        assert states_by_abbrev[abbrev]["tier"] == 1, f"{abbrev} should be tier 1"


@pytest.mark.asyncio
async def test_phase_7_sst_promotions_are_tier_1_sst(client: AsyncClient) -> None:
    """AR, GA, IA, IN promoted in v0.8; KS, KY, MI, NE, NV in v0.9. All SST tier-1."""
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in ("AR", "GA", "IA", "IN", "KS", "KY", "MI", "NE", "NV"):
        s = states_by_abbrev[abbrev]
        assert s["tier"] == 1
        assert s["has_sales_tax"] is True
        assert s["sst_member"] is True


@pytest.mark.asyncio
async def test_states_marks_unsupported_states_tier_0(client: AsyncClient) -> None:
    """States without a loaded module show tier 0.

    CA was promoted in v0.2; TX/NY/FL in v0.3; PA/IL/MD/MA/AZ in v0.4;
    CT/DC/SC/VA in v0.6; CO/ID/LA/MO/MS in v0.7. AL, NM, HI, etc.
    remain tier 0 until their state modules ship. (NM uses the
    Gross Receipts Tax model and waits on a separate non-sales-tax
    abstraction.)
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in ("AL", "HI", "NM"):
        assert states_by_abbrev[abbrev]["tier"] == 0


@pytest.mark.asyncio
async def test_phase_3_non_sst_states_are_tier_1(client: AsyncClient) -> None:
    """CA (v0.2), TX/NY/FL (v0.3), CT/DC/SC (v0.6), CO/ID/LA/MO/MS (v0.7): all tier 1 non-SST."""
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in ("CA", "TX", "NY", "FL", "CT", "DC", "SC", "CO", "ID", "LA", "MO", "MS"):
        s = states_by_abbrev[abbrev]
        assert s["tier"] == 1
        assert s["has_sales_tax"] is True
        assert s["sst_member"] is False


@pytest.mark.asyncio
async def test_virginia_is_tier_1_non_sst(client: AsyncClient) -> None:
    """VA was promoted from tier 0 to tier 1 in Phase 6 Batch B."""
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    s = states_by_abbrev["VA"]
    assert s["tier"] == 1
    assert s["has_sales_tax"] is True
    assert s["sst_member"] is False


@pytest.mark.asyncio
async def test_indiana_is_tier_1_sst(client: AsyncClient) -> None:
    """IN was promoted from tier 2 to tier 1 in Phase 7.

    Indiana is an SST member (unlike VA / SC / MS / etc.) and has the
    highest single-state sales tax rate in the country (7.0%) with
    NO local sales tax -- the combined rate at every IN address is
    exactly 7%.
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    s = states_by_abbrev["IN"]
    assert s["tier"] == 1
    assert s["has_sales_tax"] is True
    assert s["sst_member"] is True


@pytest.mark.asyncio
async def test_no_local_sales_tax_states_are_tier_1_sst(client: AsyncClient) -> None:
    """KY and MI joined IN as tier-1 SST states with NO local sales tax.

    Kentucky (KRS 139.200, 6.0%) and Michigan (MCL 205.52, 6.0%)
    both have NO local sales tax — the combined rate at every KY
    or MI address equals the state rate exactly. Indiana
    (Ind. Code 6-2.5-2-2, 7.0%) has the same property.
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in ("KY", "MI"):
        s = states_by_abbrev[abbrev]
        assert s["tier"] == 1
        assert s["has_sales_tax"] is True
        assert s["sst_member"] is True


@pytest.mark.asyncio
async def test_states_includes_dc_and_pr(client: AsyncClient) -> None:
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    assert "DC" in states_by_abbrev
    assert "PR" in states_by_abbrev


# ---------------------------------------------------------------------------
# /v1/rates -- requires seeded DB data
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_rates_returns_jurisdictions_for_seeded_zip(
    client: AsyncClient, db_engine: AsyncEngine
) -> None:
    """A seeded state-county-city stack returns three jurisdictions."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await _seed_minnesota_minneapolis(session)

    response = await client.get("/v1/rates", params={"zip5": "55401"})
    assert response.status_code == 200
    body = response.json()
    assert body["input"]["zip5"] == "55401"
    assert len(body["jurisdictions"]) >= 1
    # Combined rate should include MN's 6.875% state base + locals
    assert Decimal(body["combined_rate_pct"]) >= Decimal("6.875")
    assert "Calculation only" in body["disclaimer"]


@pytest.mark.asyncio
async def test_rates_rejects_bad_zip(client: AsyncClient) -> None:
    """ZIP5 must be exactly 5 digits."""
    response = await client.get("/v1/rates", params={"zip5": "abc"})
    assert response.status_code == 422  # FastAPI input validation


@pytest.mark.asyncio
async def test_rates_unknown_zip_returns_zero_combined(client: AsyncClient) -> None:
    """An unseeded ZIP returns no jurisdictions and combined_rate_pct=0."""
    response = await client.get("/v1/rates", params={"zip5": "00000"})
    assert response.status_code == 200
    body = response.json()
    assert body["jurisdictions"] == []
    assert Decimal(body["combined_rate_pct"]) == Decimal("0")


# ---------------------------------------------------------------------------
# POST /v1/calculate
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_calculate_minnesota_clothing_is_zero(
    client: AsyncClient, db_engine: AsyncEngine
) -> None:
    """A clothing line item in MN returns 0 tax (clothing is non-taxable)."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await _seed_minnesota_minneapolis(session)
        # Add MN's clothing-non-taxable rule
        from sqlalchemy import select

        from opensalestax.db.models import TaxabilityRule

        state_row = (await session.execute(select(State).where(State.abbrev == "MN"))).scalar_one()
        session.add(
            TaxabilityRule(
                state_id=state_row.id,
                item_category="clothing",
                is_taxable=False,
                effective_from=dt.date(1900, 1, 1),
                notes="Clothing is non-taxable in MN.",
            )
        )
        await session.commit()

    response = await client.post(
        "/v1/calculate",
        json={
            "address": {"zip5": "55401"},
            "line_items": [
                {"amount": "100.00", "category": "general"},
                {"amount": "50.00", "category": "clothing"},
            ],
        },
    )
    assert response.status_code == 200
    body = response.json()

    by_category = {line["category"]: line for line in body["lines"]}
    assert Decimal(by_category["clothing"]["tax"]) == Decimal("0")
    assert by_category["clothing"]["note"] is not None
    assert Decimal(by_category["general"]["tax"]) > Decimal("0")
    assert "Calculation only" in body["disclaimer"]


@pytest.mark.asyncio
async def test_calculate_rejects_negative_amount(client: AsyncClient) -> None:
    """Pydantic input validation blocks negative amounts."""
    response = await client.post(
        "/v1/calculate",
        json={
            "address": {"zip5": "55401"},
            "line_items": [{"amount": "-1.00", "category": "general"}],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_calculate_unknown_zip_returns_zero(client: AsyncClient) -> None:
    """Unknown ZIP -> 0 tax with explanatory note, not a failure."""
    response = await client.post(
        "/v1/calculate",
        json={
            "address": {"zip5": "00000"},
            "line_items": [{"amount": "100.00", "category": "general"}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert Decimal(body["tax_total"]) == Decimal("0")
    assert body["lines"][0]["note"]


@pytest.mark.asyncio
async def test_openapi_spec_is_published(client: AsyncClient) -> None:
    """OpenAPI 3.x spec must be reachable per constitution sec 5."""
    response = await client.get("/v1/openapi.json")
    assert response.status_code == 200
    spec = response.json()
    assert spec["info"]["title"] == "OpenSalesTax"
    paths = spec["paths"]
    assert "/v1/health" in paths
    assert "/v1/states" in paths
    assert "/v1/rates" in paths
    assert "/v1/calculate" in paths


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
async def _seed_minnesota_minneapolis(session: AsyncSession) -> None:
    """Seed the minimum data needed for Minneapolis (ZIP 55401) calculations."""
    mn = State(abbrev="MN", name="Minnesota", has_sales_tax=True, sst_member=True)
    session.add(mn)
    await session.flush()

    version = DataVersion(state_id=mn.id, source="test", version_label="MN-test-2026Q2")
    session.add(version)
    await session.flush()

    state_auth = TaxAuthority(state_id=mn.id, name="Minnesota", authority_type="state")
    county_auth = TaxAuthority(state_id=mn.id, name="Hennepin County", authority_type="county")
    session.add_all([state_auth, county_auth])
    await session.flush()

    today = dt.date.today()
    session.add_all(
        [
            Rate(
                authority_id=state_auth.id,
                rate_pct=Decimal("6.875"),
                effective_from=dt.date(2009, 7, 1),
                data_version_id=version.id,
            ),
            Rate(
                authority_id=county_auth.id,
                rate_pct=Decimal("0.150"),
                effective_from=dt.date(2017, 10, 1),
                data_version_id=version.id,
            ),
            Boundary(
                authority_id=state_auth.id,
                zip5="55401",
                data_version_id=version.id,
            ),
            Boundary(
                authority_id=county_auth.id,
                zip5="55401",
                data_version_id=version.id,
            ),
        ]
    )
    await session.commit()
    # Avoid lint about unused 'today' (kept for documentation)
    del today
