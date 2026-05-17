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
# /v1/capabilities -- static manifest
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_capabilities_returns_version_and_endpoints(client: AsyncClient) -> None:
    """The capabilities endpoint reports the engine's version + endpoint paths."""
    response = await client.get("/v1/capabilities")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == __version__
    # Must include every known endpoint slug.
    assert set(body["endpoints"].keys()) >= {
        "health",
        "states",
        "rates",
        "calculate",
        "capabilities",
    }
    for slug, desc in body["endpoints"].items():
        assert desc["path"].startswith("/v1/"), f"{slug} path missing /v1 prefix"
        assert desc["version"] >= 1


@pytest.mark.asyncio
async def test_capabilities_features_includes_known_keys(client: AsyncClient) -> None:
    """The features dict must include the known stable feature keys.

    These keys form the connector-facing contract; adding new ones is
    non-breaking, removing or flipping them is breaking. This test guards
    against accidental removal.
    """
    response = await client.get("/v1/capabilities")
    body = response.json()
    features = body["features"]
    for key in (
        "coverage_warning",
        "shipping_first_class",
        "vendor_allocation",
        "transaction_record_back",
    ):
        assert key in features, f"feature {key!r} missing from capabilities"
        assert isinstance(features[key], bool)


@pytest.mark.asyncio
async def test_capabilities_coverage_warning_is_true_post_iter_189(
    client: AsyncClient,
) -> None:
    """coverage_warning feature flipped True when iter-189 shipped."""
    response = await client.get("/v1/capabilities")
    assert response.json()["features"]["coverage_warning"] is True


@pytest.mark.asyncio
async def test_capabilities_shipping_first_class_is_true_post_v059(
    client: AsyncClient,
) -> None:
    """shipping_first_class flipped True when v0.59.0 shipped."""
    response = await client.get("/v1/capabilities")
    assert response.json()["features"]["shipping_first_class"] is True


# ---------------------------------------------------------------------------
# /v1/calculate shipping -- v0.59.0
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_calculate_without_shipping_omits_shipping_block(
    client: AsyncClient,
) -> None:
    """Requests that don't include `shipping` get no shipping block back.

    Preserves pre-v0.59.0 behavior; existing consumers see no change.
    """
    response = await client.post(
        "/v1/calculate",
        json={
            "address": {"zip5": "55401"},
            "line_items": [{"amount": "100.00", "category": "general"}],
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body.get("shipping") is None


# Per-rule shipping behavior is exercised against the live engine via
# tests/integration/test_sst_dor_validation.py (which has loaded data);
# the no-DB CI run validates only the request/response shape via
# test_calculate_without_shipping_omits_shipping_block above. Per-state
# rule selection is unit-tested in tests/unit/test_core_shipping.py.


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

    Phase 7 complete in v0.11.0: every SST member is now tier-1.
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in (
        # Phase 1 SST tier-1
        "MN",
        "WI",
        # v0.8 promotions
        "AR",
        "GA",
        "IA",
        "IN",
        # v0.9 promotions
        "KS",
        "KY",
        "MI",
        "NE",
        "NV",
        # v0.10 promotions
        "NC",
        "ND",
        "NJ",
        "OH",
        "OK",
        # v0.11 promotions (final batch)
        "RI",
        "SD",
        "TN",
        "UT",
        "VT",
        "WA",
        "WV",
        "WY",
        # No-tax states
        "AK",
        "DE",
        "MT",
        "NH",
        "OR",
    ):
        assert states_by_abbrev[abbrev]["tier"] == 1, f"{abbrev} should be tier 1"


@pytest.mark.asyncio
async def test_phase_7_sst_promotions_are_tier_1_sst(client: AsyncClient) -> None:
    """Phase 7 complete: every SST member is tier-1.

    AR, GA, IA, IN promoted in v0.8; KS, KY, MI, NE, NV in v0.9;
    NC, ND, NJ, OH, OK in v0.10; RI, SD, TN, UT, VT, WA, WV, WY
    in v0.11.
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in (
        "AR",
        "GA",
        "IA",
        "IN",
        "KS",
        "KY",
        "MI",
        "NC",
        "ND",
        "NE",
        "NJ",
        "NV",
        "OH",
        "OK",
        "RI",
        "SD",
        "TN",
        "UT",
        "VT",
        "WA",
        "WV",
        "WY",
    ):
        s = states_by_abbrev[abbrev]
        assert s["tier"] == 1
        assert s["has_sales_tax"] is True
        assert s["sst_member"] is True


@pytest.mark.asyncio
async def test_no_jurisdictions_remain_tier_0(client: AsyncClient) -> None:
    """v0.13 ships AL/HI/NM/PR (Phase 6 Batch C) -- all 52
    jurisdictions are now tier-1 maintained. (HI/NM are encoded as
    sales taxes for API purposes; legally HI is a General Excise
    Tax and NM is a Gross Receipts Tax.)
    """
    response = await client.get("/v1/states")
    tier_0 = [s["abbrev"] for s in response.json()["states"] if s["tier"] == 0]
    assert tier_0 == [], f"Expected zero tier-0 jurisdictions; found {tier_0}."


@pytest.mark.asyncio
async def test_alabama_is_tier_1_non_sst(client: AsyncClient) -> None:
    """AL was promoted from tier 0 to tier 1 in v0.13 (Phase 6 Batch C).

    Alabama is a non-SST state with the most fragmented local
    sales-tax landscape in the country (~700+ self-administering
    home-rule cities). v1 ships the state-portion-only 4.0% rate
    per Ala. Code section 40-23-2(1) plus the two annual sales-tax
    holidays; county and municipal rates are deferred to the
    SubJurisdiction Protocol abstraction. See
    ``specs/decisions/04-colorado-home-rule.md`` and
    ``specs/decisions/05-louisiana-parishes.md`` for the deferral
    rationale.
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    s = states_by_abbrev["AL"]
    assert s["tier"] == 1
    assert s["has_sales_tax"] is True
    assert s["sst_member"] is False


@pytest.mark.asyncio
async def test_phase_3_non_sst_states_are_tier_1(client: AsyncClient) -> None:
    """CA (v0.2), TX/NY/FL (v0.3), CT/DC/SC (v0.6), CO/ID/LA/MO/MS (v0.7),
    ME (v0.12, non-SST, no local tax), AL (v0.13, non-SST,
    home-rule-deferred), HI (v0.13, non-SST, GET model encoded as
    sales tax with per-county surcharges deferred), NM (v0.13,
    non-SST, GRT modeled as sales tax with per-county surcharges
    deferred), PR (v0.13, US territory, IVU 11.5% combined): all
    tier 1 non-SST.
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    for abbrev in (
        "AL",
        "CA",
        "TX",
        "NY",
        "FL",
        "CT",
        "DC",
        "SC",
        "CO",
        "HI",
        "ID",
        "LA",
        "ME",
        "MO",
        "MS",
        "NM",
        "PR",
    ):
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


@pytest.mark.asyncio
async def test_puerto_rico_is_tier_1_us_territory(client: AsyncClient) -> None:
    """PR was promoted from tier 0 to tier 1 in Phase 8.

    Puerto Rico is a US TERRITORY (commonwealth), not a US state. Its
    IVU (Impuesto sobre Ventas y Uso) is administered by the
    Departamento de Hacienda de Puerto Rico under the Codigo de
    Rentas Internas (13 L.P.R.A. sections 32001 et seq.). The
    combined IVU rate is 11.5% (10.5% state per 13 L.P.R.A. section
    32021 + 1.0% municipal per 13 L.P.R.A. section 32024) and is
    uniform across all 78 PR municipalities. PR is NOT an SST member
    (SST membership is limited to US states).
    """
    response = await client.get("/v1/states")
    states_by_abbrev = {s["abbrev"]: s for s in response.json()["states"]}
    s = states_by_abbrev["PR"]
    assert s["tier"] == 1
    assert s["has_sales_tax"] is True
    assert s["sst_member"] is False


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


@pytest.mark.asyncio
async def test_rates_zip5_only_finds_type4_only_city(
    client: AsyncClient, db_engine: AsyncEngine
) -> None:
    """``/v1/rates`` (no zip4) must agree with ``/v1/calculate`` on city authorities.

    Regression for the SLC 84101 inconsistency: a city authority bound
    only via type-4 (per-+4) boundary records must surface in the
    zip5-only ``/rates`` response, not just ``/calculate``. Otherwise the
    two endpoints disagree on the combined rate, which is confusing.
    """
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        await _seed_state_with_type4_only_city(session)

    rates_resp = await client.get("/v1/rates", params={"zip5": "84101"})
    calc_resp = await client.post(
        "/v1/calculate",
        json={
            "address": {"zip5": "84101"},
            "line_items": [{"amount": "100.00", "category": "general"}],
        },
    )
    assert rates_resp.status_code == 200
    assert calc_resp.status_code == 200

    rates_combined = Decimal(rates_resp.json()["combined_rate_pct"])
    calc_combined = Decimal(calc_resp.json()["lines"][0]["rate_pct"])
    assert (
        rates_combined == calc_combined
    ), f"/rates ({rates_combined}) and /calculate ({calc_combined}) disagree"

    # And the city itself must appear in /rates.
    rates_names = {j["name"] for j in rates_resp.json()["jurisdictions"]}
    assert "Test City" in rates_names


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


async def _seed_state_with_type4_only_city(session: AsyncSession) -> None:
    """Seed a state where the city authority is bound only via type-4 records.

    Mirrors the SLC 84101 shape: state and county have zip-wide (type-z)
    boundaries; the city authority is reachable only when iterating
    type-4 (per-+4) records. The strict ``lookup_jurisdictions_by_zip``
    skips it without a +4; the loose lookup picks it up.
    """
    ut = State(abbrev="ZZ", name="Test-State", has_sales_tax=True, sst_member=False)
    session.add(ut)
    await session.flush()

    version = DataVersion(state_id=ut.id, source="test", version_label="ZZ-type4-test")
    session.add(version)
    await session.flush()

    state_auth = TaxAuthority(state_id=ut.id, name="Test-State", authority_type="state")
    county_auth = TaxAuthority(state_id=ut.id, name="Test County", authority_type="county")
    city_auth = TaxAuthority(state_id=ut.id, name="Test City", authority_type="city")
    session.add_all([state_auth, county_auth, city_auth])
    await session.flush()

    session.add_all(
        [
            Rate(
                authority_id=state_auth.id,
                rate_pct=Decimal("4.850"),
                effective_from=dt.date(2009, 1, 1),
                data_version_id=version.id,
            ),
            Rate(
                authority_id=county_auth.id,
                rate_pct=Decimal("2.600"),
                effective_from=dt.date(2009, 1, 1),
                data_version_id=version.id,
            ),
            Rate(
                authority_id=city_auth.id,
                rate_pct=Decimal("1.000"),
                effective_from=dt.date(2009, 1, 1),
                data_version_id=version.id,
            ),
            # State + county have type-z (zip-wide) bindings.
            Boundary(authority_id=state_auth.id, zip5="84101", data_version_id=version.id),
            Boundary(authority_id=county_auth.id, zip5="84101", data_version_id=version.id),
            # City has ONLY type-4 (per-+4) bindings -- no zip-wide row.
            # The strict lookup misses this without a +4 query parameter;
            # the loose lookup finds it.
            Boundary(
                authority_id=city_auth.id,
                zip5="84101",
                zip4_low="0000",
                zip4_high="9999",
                data_version_id=version.id,
            ),
        ]
    )
    await session.commit()
