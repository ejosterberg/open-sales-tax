# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Integration tests for API-key auth.

Verifies both modes:
- ``open`` (default) -- no auth required
- ``api_key`` -- X-API-Key header required, valid key needed
"""

from __future__ import annotations

from collections.abc import AsyncIterator

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

import opensalestax.settings as settings_module
from opensalestax.app import create_app
from opensalestax.auth import (
    create_api_key,
    list_active_api_keys,
    revoke_api_key,
)
from opensalestax.db.session import get_session


@pytest_asyncio.fixture
async def api_key_client(db_engine: AsyncEngine, monkeypatch) -> AsyncIterator[AsyncClient]:
    """An AsyncClient configured for api_key auth mode."""
    monkeypatch.setenv("OPENSALESTAX_AUTH_MODE", "api_key")
    monkeypatch.setenv(
        "OPENSALESTAX_DATABASE_URL",
        str(db_engine.url).replace("***", "opensalestax"),
    )
    settings_module._settings = None  # reset cache
    app = create_app()

    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    settings_module._settings = None  # restore


@pytest_asyncio.fixture
async def open_mode_client(db_engine: AsyncEngine, monkeypatch) -> AsyncIterator[AsyncClient]:
    """An AsyncClient with auth mode forced to open (the default)."""
    monkeypatch.setenv("OPENSALESTAX_AUTH_MODE", "open")
    monkeypatch.setenv(
        "OPENSALESTAX_DATABASE_URL",
        str(db_engine.url).replace("***", "opensalestax"),
    )
    settings_module._settings = None
    app = create_app()
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)

    async def _override_session() -> AsyncIterator[AsyncSession]:
        async with sessionmaker() as session:
            yield session

    app.dependency_overrides[get_session] = _override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    settings_module._settings = None


# ---------------------------------------------------------------------------
# Helper CRUD tests against a real DB
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_create_api_key_persists_hash_not_plaintext(
    async_session: AsyncSession,
) -> None:
    """The DB row stores the hash; the plaintext is only returned to the caller."""
    minted = await create_api_key(async_session, label="test-key")
    assert minted.plaintext  # caller gets the plaintext
    assert minted.label == "test-key"
    assert minted.db_id > 0

    rows = await list_active_api_keys(async_session)
    assert len(rows) == 1
    row = rows[0]
    assert row.label == "test-key"
    # The DB row's key_hash should be a SHA-256 hex (64 chars), not the plaintext
    assert len(row.key_hash) == 64
    assert row.key_hash != minted.plaintext


@pytest.mark.asyncio
async def test_revoke_api_key_marks_as_revoked(async_session: AsyncSession) -> None:
    """revoke_api_key sets revoked_at and removes from active list."""
    await create_api_key(async_session, label="revoke-me")
    await create_api_key(async_session, label="revoke-me")  # two with same label
    n = await revoke_api_key(async_session, "revoke-me")
    assert n == 2
    assert await list_active_api_keys(async_session) == []


@pytest.mark.asyncio
async def test_revoke_unknown_label_returns_zero(async_session: AsyncSession) -> None:
    """Revoking a label with no matching keys is a no-op."""
    n = await revoke_api_key(async_session, "never-existed")
    assert n == 0


# ---------------------------------------------------------------------------
# HTTP behavior under each auth mode
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_open_mode_allows_requests_without_key(
    open_mode_client: AsyncClient,
) -> None:
    """In open mode, /v1/rates works without an X-API-Key header."""
    response = await open_mode_client.get("/v1/rates", params={"zip5": "55401"})
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_key_mode_rejects_missing_header(
    api_key_client: AsyncClient,
) -> None:
    """No header -> 401."""
    response = await api_key_client.get("/v1/rates", params={"zip5": "55401"})
    assert response.status_code == 401
    assert "X-API-Key" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_key_mode_rejects_unknown_key(
    api_key_client: AsyncClient,
) -> None:
    """An X-API-Key value with no matching DB row -> 401."""
    response = await api_key_client.get(
        "/v1/rates",
        params={"zip5": "55401"},
        headers={"X-API-Key": "definitely-not-a-real-key"},
    )
    assert response.status_code == 401
    assert "Invalid" in response.json()["detail"]


@pytest.mark.asyncio
async def test_api_key_mode_accepts_valid_key(
    api_key_client: AsyncClient, db_engine: AsyncEngine
) -> None:
    """A request with a valid X-API-Key passes through to the endpoint."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        minted = await create_api_key(session, label="integration-test")

    response = await api_key_client.get(
        "/v1/rates",
        params={"zip5": "55401"},
        headers={"X-API-Key": minted.plaintext},
    )
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_api_key_mode_rejects_revoked_key(
    api_key_client: AsyncClient, db_engine: AsyncEngine
) -> None:
    """A previously-valid key that's been revoked -> 401."""
    sessionmaker = async_sessionmaker(db_engine, expire_on_commit=False)
    async with sessionmaker() as session:
        minted = await create_api_key(session, label="will-be-revoked")
        await revoke_api_key(session, "will-be-revoked")

    response = await api_key_client.get(
        "/v1/rates",
        params={"zip5": "55401"},
        headers={"X-API-Key": minted.plaintext},
    )
    assert response.status_code == 401
