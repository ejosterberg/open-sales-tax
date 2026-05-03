# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Alembic environment for OpenSalesTax.

Async-friendly: uses SQLAlchemy 2.x AsyncEngine. Reads the database
URL from ``OPENSALESTAX_DATABASE_URL`` env var (via Settings), which
means the same migrations apply to either PostgreSQL or MariaDB
depending on which DSN you point at.
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from opensalestax.db.models import Base
from opensalestax.settings import get_settings

# ---------------------------------------------------------------------------
# Boilerplate Alembic config wiring
# ---------------------------------------------------------------------------
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolved_url() -> str:
    """Resolve the database URL from settings at migration time."""
    return get_settings().database_dsn


# ---------------------------------------------------------------------------
# Offline mode -- emit SQL without a live DB connection.
# Used for `alembic upgrade --sql` to generate migration scripts for review.
# ---------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = _resolved_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        render_as_batch=False,  # only enable for SQLite; we don't support SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online mode -- async engine; the production path.
# ---------------------------------------------------------------------------
def do_run_migrations(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online_async() -> None:
    configuration = config.get_section(config.config_ini_section) or {}
    configuration["sqlalchemy.url"] = _resolved_url()

    connectable = async_engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=None,
        future=True,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    asyncio.run(run_migrations_online_async())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
