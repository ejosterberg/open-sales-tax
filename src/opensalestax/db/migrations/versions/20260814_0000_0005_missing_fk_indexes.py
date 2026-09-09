# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Add missing FK indexes on boundaries and rates

Three FK columns across two tables had no supporting B-tree index,
causing sequential scans in distinct hot paths:

``idx_boundaries_authority``  (boundaries.authority_id)
    Every ZIP5 lookup calls several coverage-counting queries of the
    form ``SELECT authority_id, COUNT(...) FROM boundaries WHERE
    authority_id IN (...) GROUP BY authority_id``.  These run without
    a zip5 filter so they cannot use the existing
    ``idx_boundaries_zip`` index.  Without this index every such query
    scans the full boundaries table (millions of rows across 24+ SST
    states).  Affected: ``_dedup_typez_fallback``,
    ``lookup_jurisdictions_by_zip5_loose``, and
    ``_dedup_single_local_districts`` in ``core/lookup.py``.

``idx_boundaries_data_version``  (boundaries.data_version_id)
    ``data load`` and ``data purge`` delete a ``DataVersion`` row and
    rely on the ON DELETE CASCADE to remove all child boundary rows.
    Without an index the CASCADE resolves by scanning the entire
    boundaries table once per deleted version — extremely slow for
    24-state loads.  Also speeds up the JOIN in
    ``_canonical_state_for_zip``.

``idx_rates_data_version``  (rates.data_version_id)
    The loader queries ``SELECT * FROM rates WHERE data_version_id = ?``
    before purging stale rates (``loader.py`` ~line 482).  The FK is
    ``ON DELETE SET NULL``, so deleting a DataVersion also triggers a
    scan of the rates table to null-out the column.  Without this index
    both operations perform full table scans on a table that can hold
    millions of rate rows.

Revision ID: 0005_missing_fk_indexes
Revises: 0004_taxability_thresholds
Create Date: 2026-08-14
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0005_missing_fk_indexes"
down_revision: str | Sequence[str] | None = "0004_taxability_thresholds"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_index("idx_boundaries_authority", "boundaries", ["authority_id"])
    op.create_index("idx_boundaries_data_version", "boundaries", ["data_version_id"])
    op.create_index("idx_rates_data_version", "rates", ["data_version_id"])


def downgrade() -> None:
    op.drop_index("idx_rates_data_version", table_name="rates")
    op.drop_index("idx_boundaries_data_version", table_name="boundaries")
    op.drop_index("idx_boundaries_authority", table_name="boundaries")
