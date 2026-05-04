# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Per-item price thresholds on taxability_rules (v0.13)

Adds two nullable columns to ``taxability_rules`` so per-state
modules can encode threshold-based clothing exemptions
(NY <$110 fully exempt, MA first $175 exempt, RI first $250
exempt) without per-state engine branches.

Both columns are nullable; existing rows continue to mean
"no threshold." Portable across PostgreSQL and MariaDB.

Revision ID: 0004_taxability_thresholds
Revises: 0003_holiday_periods
Create Date: 2026-05-03
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0004_taxability_thresholds"
down_revision: str | Sequence[str] | None = "0003_holiday_periods"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "taxability_rules",
        sa.Column("taxable_threshold_amount", sa.Numeric(precision=12, scale=2), nullable=True),
    )
    op.add_column(
        "taxability_rules",
        sa.Column("threshold_semantic", sa.String(length=20), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("taxability_rules", "threshold_semantic")
    op.drop_column("taxability_rules", "taxable_threshold_amount")
