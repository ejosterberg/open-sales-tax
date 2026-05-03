# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""holiday_periods table for sales-tax holidays (v0.5)

Adds one new table; portable across PostgreSQL and MariaDB.

Revision ID: 0003_holiday_periods
Revises: 0002_api_keys
Create Date: 2026-05-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_holiday_periods"
down_revision: str | Sequence[str] | None = "0002_api_keys"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "holiday_periods",
        sa.Column("id", sa.Integer(), nullable=False, autoincrement=True),
        sa.Column("state_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("starts_on", sa.Date(), nullable=False),
        sa.Column("ends_on", sa.Date(), nullable=False),
        sa.Column("applicable_categories", sa.JSON(), nullable=True),
        sa.Column("max_amount_per_item", sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["state_id"], ["states.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "idx_holidays_state_dates",
        "holiday_periods",
        ["state_id", "starts_on", "ends_on"],
    )


def downgrade() -> None:
    op.drop_index("idx_holidays_state_dates", table_name="holiday_periods")
    op.drop_table("holiday_periods")
