# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""initial schema -- 6 tables for Phase 1

Schema tracks specs/phase-1-foundation/spec.md section 2.

Portability: every type used here works on PostgreSQL 15+ and
MariaDB 11+. SERIAL/AUTO_INCREMENT is selected automatically by
SQLAlchemy's Integer(autoincrement=True). JSON maps to JSONB on
PG and JSON on MariaDB. CURRENT_TIMESTAMP works on both.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-05-03

"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial_schema"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # ---- states -----------------------------------------------------------
    op.create_table(
        "states",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("abbrev", sa.String(length=2), nullable=False),
        sa.Column("name", sa.String(length=60), nullable=False),
        sa.Column("sst_member", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sst_joined", sa.Date(), nullable=True),
        sa.Column("has_sales_tax", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("abbrev"),
    )

    # ---- data_versions ----------------------------------------------------
    op.create_table(
        "data_versions",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=40), nullable=False),
        sa.Column("version_label", sa.String(length=60), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.current_timestamp(),
        ),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_id", "source", "version_label", name="uq_data_versions_label"),
    )

    # ---- tax_authorities --------------------------------------------------
    op.create_table(
        "tax_authorities",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("authority_type", sa.String(length=20), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["tax_authorities.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("state_id", "name", "authority_type", name="uq_authority_identity"),
    )

    # ---- rates ------------------------------------------------------------
    op.create_table(
        "rates",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("authority_id", sa.Integer(), nullable=False),
        sa.Column("rate_pct", sa.Numeric(precision=8, scale=5), nullable=False),
        sa.Column("effective_from", sa.Date(), nullable=False),
        sa.Column("effective_to", sa.Date(), nullable=True),
        # Generic JSON: JSONB on PG, JSON on MariaDB. NULL = applies to all categories.
        sa.Column("applies_to_categories", sa.JSON(), nullable=True),
        sa.Column("data_version_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["authority_id"], ["tax_authorities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["data_version_id"], ["data_versions.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_rates_eff",
        "rates",
        ["authority_id", "effective_from", "effective_to"],
    )

    # ---- boundaries -------------------------------------------------------
    op.create_table(
        "boundaries",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("authority_id", sa.Integer(), nullable=False),
        sa.Column("zip5", sa.String(length=5), nullable=False),
        sa.Column("zip4_low", sa.String(length=4), nullable=True),
        sa.Column("zip4_high", sa.String(length=4), nullable=True),
        sa.Column("address_pattern", sa.String(length=255), nullable=True),
        sa.Column("data_version_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["authority_id"], ["tax_authorities.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["data_version_id"], ["data_versions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_boundaries_zip",
        "boundaries",
        ["zip5", "zip4_low", "zip4_high"],
    )

    # ---- taxability_rules -------------------------------------------------
    op.create_table(
        "taxability_rules",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("item_category", sa.String(length=60), nullable=False),
        sa.Column("is_taxable", sa.Boolean(), nullable=False),
        sa.Column("rate_modifier", sa.Numeric(precision=8, scale=5), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "effective_from",
            sa.Date(),
            nullable=False,
            server_default=sa.text("'1900-01-01'"),
        ),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "state_id", "item_category", "effective_from", name="uq_taxability_effective"
        ),
    )


def downgrade() -> None:
    # Drop in reverse dependency order.
    op.drop_table("taxability_rules")
    op.drop_index("idx_boundaries_zip", table_name="boundaries")
    op.drop_table("boundaries")
    op.drop_index("idx_rates_eff", table_name="rates")
    op.drop_table("rates")
    op.drop_table("tax_authorities")
    op.drop_table("data_versions")
    op.drop_table("states")
