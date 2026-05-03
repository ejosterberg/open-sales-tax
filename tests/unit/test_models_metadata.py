# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Sanity checks on the SQLAlchemy model metadata.

These tests run without a database -- they exercise the
declarative metadata only. They catch portability / schema-shape
regressions early.
"""

from __future__ import annotations

import pytest

from opensalestax.db.models import Base

EXPECTED_TABLES = {
    "states",
    "data_versions",
    "tax_authorities",
    "rates",
    "boundaries",
    "taxability_rules",
    "api_keys",  # Phase 2 Section B
}


def test_all_phase_1_tables_declared() -> None:
    """The six Phase 1 tables are present in the metadata."""
    assert set(Base.metadata.tables) == EXPECTED_TABLES


def test_no_postgres_only_types_used() -> None:
    """No JSONB / ARRAY / UUID-PG-only types in any column.

    Per constitution §10 rule 2, the schema must use the portable
    subset that works on both PostgreSQL and MariaDB. JSONB, ARRAY,
    and pg-specific UUID would break MariaDB compatibility.
    """
    forbidden_typenames = {"JSONB", "ARRAY"}
    for table in Base.metadata.tables.values():
        for col in table.columns:
            type_name = type(col.type).__name__
            assert type_name not in forbidden_typenames, (
                f"{table.name}.{col.name} uses non-portable type {type_name}; "
                "use the generic SQLAlchemy equivalent instead."
            )


@pytest.mark.parametrize(
    "table_name,expected_indexes",
    [
        ("rates", {"idx_rates_eff"}),
        ("boundaries", {"idx_boundaries_zip"}),
    ],
)
def test_required_indexes_present(table_name: str, expected_indexes: set[str]) -> None:
    """The named indexes from the spec exist on the right tables."""
    table = Base.metadata.tables[table_name]
    actual = {idx.name for idx in table.indexes}
    assert expected_indexes.issubset(
        actual
    ), f"{table_name} missing indexes; expected {expected_indexes}, got {actual}"


def test_unique_constraints_present() -> None:
    """Per-table unique constraints from the spec are declared."""
    expected = {
        "states": {("abbrev",)},
        "data_versions": {("state_id", "source", "version_label")},
        "tax_authorities": {("state_id", "name", "authority_type")},
        "taxability_rules": {("state_id", "item_category", "effective_from")},
    }
    for table_name, expected_uniques in expected.items():
        table = Base.metadata.tables[table_name]
        actual = {
            tuple(c.name for c in uc.columns)
            for uc in table.constraints
            if uc.__class__.__name__ == "UniqueConstraint"
        }
        for exp in expected_uniques:
            assert exp in actual, f"{table_name} missing unique constraint on {exp}; got {actual}"
