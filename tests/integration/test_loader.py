# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Integration tests for the data loader.

Exercises the full load pipeline against the bundled MN + WI
fixtures: parse SST CSV -> normalize via state module -> insert
into a real DB. Skipped when ``OPENSALESTAX_DATABASE_URL`` is
unset.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.data.fixtures import state_fixture_dir
from opensalestax.data.loader import (
    LoaderError,
    list_loaded_versions,
    load_state_data,
    purge_data_version,
)
from opensalestax.db.models import (
    Boundary,
    DataVersion,
    Rate,
    State,
    TaxabilityRule,
    TaxAuthority,
)


@pytest.mark.asyncio
async def test_load_minnesota_end_to_end(async_session: AsyncSession) -> None:
    """Loading MN's bundled fixture inserts state, authorities, rates, taxability."""
    summary = await load_state_data(
        async_session,
        state_abbrev="MN",
        version_label="2026Q2FEB18",
        cache_dir=state_fixture_dir("MN"),
    )

    assert summary.state_abbrev == "MN"
    assert summary.version_label == "MN-SST-2026Q2FEB18"
    assert summary.rates_loaded > 0
    # MN file has 148 rate rows; we map 4 type codes to authority types.
    # Every row gets a Rate, so loaded count should be the parsed total.
    assert summary.rates_loaded == 148

    # State row exists with the expected metadata
    mn = (await async_session.execute(select(State).where(State.abbrev == "MN"))).scalar_one()
    assert mn.name == "Minnesota"
    assert mn.sst_member is True

    # The state-level authority has a 6.875% rate
    state_auth = (
        await async_session.execute(
            select(TaxAuthority).where(
                TaxAuthority.state_id == mn.id,
                TaxAuthority.authority_type == "state",
            )
        )
    ).scalar_one()
    assert state_auth.name == "Minnesota"

    state_rate = (
        (await async_session.execute(select(Rate).where(Rate.authority_id == state_auth.id)))
        .scalars()
        .first()
    )
    assert state_rate is not None
    assert state_rate.rate_pct == Decimal("6.87500")

    # Taxability matrix for clothing was loaded as non-taxable
    clothing_rule = (
        await async_session.execute(
            select(TaxabilityRule).where(
                TaxabilityRule.state_id == mn.id,
                TaxabilityRule.item_category == "clothing",
            )
        )
    ).scalar_one()
    assert clothing_rule.is_taxable is False
    assert "297A.67" in (clothing_rule.notes or "")


@pytest.mark.asyncio
async def test_load_is_idempotent(async_session: AsyncSession) -> None:
    """Re-running load drops the prior data version + reloads."""
    first = await load_state_data(
        async_session,
        state_abbrev="MN",
        version_label="2026Q2FEB18",
        cache_dir=state_fixture_dir("MN"),
    )

    second = await load_state_data(
        async_session,
        state_abbrev="MN",
        version_label="2026Q2FEB18",
        cache_dir=state_fixture_dir("MN"),
    )

    # Different DataVersion id (the old one was dropped + cascaded)
    assert second.data_version_id != first.data_version_id
    assert second.rates_loaded == first.rates_loaded

    # And there's exactly one DataVersion row for this label
    versions = (
        (
            await async_session.execute(
                select(DataVersion).where(DataVersion.version_label == "MN-SST-2026Q2FEB18")
            )
        )
        .scalars()
        .all()
    )
    assert len(versions) == 1


@pytest.mark.asyncio
async def test_load_wisconsin_state_base_is_5pct(async_session: AsyncSession) -> None:
    """WI's loader run produces a 5.0% state authority rate."""
    summary = await load_state_data(
        async_session,
        state_abbrev="WI",
        version_label="2026Q2FEB18",
        cache_dir=state_fixture_dir("WI"),
        load_boundaries=False,  # WI fixture has no boundary file
    )

    assert summary.state_abbrev == "WI"
    assert summary.rates_loaded > 100  # WI has 1941 rate rows

    wi = (await async_session.execute(select(State).where(State.abbrev == "WI"))).scalar_one()
    state_auth = (
        await async_session.execute(
            select(TaxAuthority).where(
                TaxAuthority.state_id == wi.id,
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
    assert state_rate.rate_pct == Decimal("5.000")

    # WI's clothing rule should be TAXABLE (the contrast with MN)
    clothing_rule = (
        await async_session.execute(
            select(TaxabilityRule).where(
                TaxabilityRule.state_id == wi.id,
                TaxabilityRule.item_category == "clothing",
            )
        )
    ).scalar_one()
    assert clothing_rule.is_taxable is True


@pytest.mark.asyncio
async def test_load_unknown_state_raises(async_session: AsyncSession) -> None:
    """Loading a state without a registered module fails clearly."""
    with pytest.raises(LoaderError, match="No state module"):
        await load_state_data(
            async_session,
            state_abbrev="ZZ",
            version_label="2026Q2FEB18",
            cache_dir=state_fixture_dir("MN"),
        )


@pytest.mark.asyncio
async def test_load_missing_file_raises(async_session: AsyncSession, tmp_path) -> None:
    """Loading from an empty cache fails with a helpful message."""
    with pytest.raises(LoaderError, match="No cached rates file"):
        await load_state_data(
            async_session,
            state_abbrev="MN",
            version_label="9999Q4DEC31",
            cache_dir=tmp_path,
        )


@pytest.mark.asyncio
async def test_purge_removes_data_version(async_session: AsyncSession) -> None:
    """purge_data_version deletes the version + cascades dependent rows."""
    await load_state_data(
        async_session,
        state_abbrev="MN",
        version_label="2026Q2FEB18",
        cache_dir=state_fixture_dir("MN"),
    )

    deleted = await purge_data_version(async_session, "MN", "2026Q2FEB18")
    assert deleted is True

    # No more rates / boundaries for this MN version
    versions = (
        (
            await async_session.execute(
                select(DataVersion).where(DataVersion.version_label == "MN-SST-2026Q2FEB18")
            )
        )
        .scalars()
        .all()
    )
    assert versions == []
    # The cascading delete also removed the rates
    rate_count = len((await async_session.execute(select(Rate))).scalars().all())
    assert rate_count == 0
    # ... and the boundaries
    boundary_count = len((await async_session.execute(select(Boundary))).scalars().all())
    assert boundary_count == 0


@pytest.mark.asyncio
async def test_purge_missing_version_returns_false(
    async_session: AsyncSession,
) -> None:
    """Purging a version that doesn't exist returns False, not an error."""
    deleted = await purge_data_version(async_session, "MN", "9999Q4DEC31")
    assert deleted is False


@pytest.mark.asyncio
async def test_list_loaded_versions(async_session: AsyncSession) -> None:
    """list_loaded_versions returns the loaded labels."""
    # Empty DB
    assert await list_loaded_versions(async_session) == []

    await load_state_data(
        async_session,
        state_abbrev="MN",
        version_label="2026Q2FEB18",
        cache_dir=state_fixture_dir("MN"),
    )

    rows = await list_loaded_versions(async_session)
    assert len(rows) == 1
    state_abbrev, label, fetched_at = rows[0]
    assert state_abbrev == "MN"
    assert label == "MN-SST-2026Q2FEB18"
    assert fetched_at is not None
