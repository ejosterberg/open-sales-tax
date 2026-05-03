# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""SQLAlchemy 2.x declarative models.

Schema mirrors specs/phase-1-foundation/spec.md section 2.

**Portability constraint** (constitution §10 rule 2): only types
that work identically on PostgreSQL and MariaDB are used here.

- ``Integer`` with ``autoincrement=True`` -- emits ``SERIAL`` on
  PostgreSQL and ``AUTO_INCREMENT`` on MariaDB.
- ``JSON`` (the generic SQLAlchemy type) -- maps to ``JSONB`` on
  PostgreSQL and ``JSON`` on MariaDB. Application code must use
  generic JSON path operators, never PostgreSQL-only ``->``/``->>``.
- ``DateTime(timezone=True)`` for timestamps.
- ``Numeric(8, 5)`` for tax rates -- precise to 0.001%.
- ``Text`` for free-form notes.

If you need a PostgreSQL-only feature later, it must live inside an
Alembic migration with a dialect conditional, never in this file.
See specs/decisions/03-database.md.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# ---------------------------------------------------------------------------
# Schema-level constants -- defined once, referenced from FK targets and
# relationship cascades. Keeps duplicate-literal lint rules (S1192) quiet
# and makes refactors trivial if a column ever moves.
# ---------------------------------------------------------------------------
_FK_STATES_ID = "states.id"
_FK_TAX_AUTHORITIES_ID = "tax_authorities.id"
_FK_DATA_VERSIONS_ID = "data_versions.id"
_CASCADE_ALL_DELETE_ORPHAN = "all, delete-orphan"


class Base(DeclarativeBase):
    """Declarative base for all OpenSalesTax models."""


# --------------------------------------------------------------------------
# states -- the 50 + DC + PR jurisdictions
# --------------------------------------------------------------------------
class State(Base):
    __tablename__ = "states"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    abbrev: Mapped[str] = mapped_column(String(2), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    sst_member: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    sst_joined: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    has_sales_tax: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # relationships
    data_versions: Mapped[list[DataVersion]] = relationship(
        back_populates="state", cascade=_CASCADE_ALL_DELETE_ORPHAN
    )
    tax_authorities: Mapped[list[TaxAuthority]] = relationship(
        back_populates="state", cascade=_CASCADE_ALL_DELETE_ORPHAN
    )
    taxability_rules: Mapped[list[TaxabilityRule]] = relationship(
        back_populates="state", cascade=_CASCADE_ALL_DELETE_ORPHAN
    )

    def __repr__(self) -> str:
        return f"<State {self.abbrev}>"


# --------------------------------------------------------------------------
# data_versions -- per-state, per-source data drops (e.g. MN-SST-2026Q2APR15)
# Declared before rates / boundaries because both reference it.
# --------------------------------------------------------------------------
class DataVersion(Base):
    __tablename__ = "data_versions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_FK_STATES_ID, ondelete="CASCADE"), nullable=False
    )
    source: Mapped[str] = mapped_column(String(40), nullable=False)
    version_label: Mapped[str] = mapped_column(String(60), nullable=False)
    fetched_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    state: Mapped[State] = relationship(back_populates="data_versions")
    rates: Mapped[list[Rate]] = relationship(back_populates="data_version")
    boundaries: Mapped[list[Boundary]] = relationship(back_populates="data_version")

    __table_args__ = (
        UniqueConstraint("state_id", "source", "version_label", name="uq_data_versions_label"),
    )

    def __repr__(self) -> str:
        return f"<DataVersion {self.version_label}>"


# --------------------------------------------------------------------------
# tax_authorities -- state DOR, county, city, special district
# --------------------------------------------------------------------------
class TaxAuthority(Base):
    __tablename__ = "tax_authorities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_FK_STATES_ID, ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    authority_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # 'state', 'county', 'city', 'district'
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(_FK_TAX_AUTHORITIES_ID, ondelete="SET NULL"), nullable=True
    )

    state: Mapped[State] = relationship(back_populates="tax_authorities")
    parent: Mapped[TaxAuthority | None] = relationship(
        remote_side="TaxAuthority.id", back_populates="children"
    )
    children: Mapped[list[TaxAuthority]] = relationship(
        back_populates="parent", cascade=_CASCADE_ALL_DELETE_ORPHAN
    )
    rates: Mapped[list[Rate]] = relationship(
        back_populates="authority", cascade=_CASCADE_ALL_DELETE_ORPHAN
    )
    boundaries: Mapped[list[Boundary]] = relationship(
        back_populates="authority", cascade=_CASCADE_ALL_DELETE_ORPHAN
    )

    __table_args__ = (
        UniqueConstraint("state_id", "name", "authority_type", name="uq_authority_identity"),
    )

    def __repr__(self) -> str:
        return f"<TaxAuthority {self.name} ({self.authority_type})>"


# --------------------------------------------------------------------------
# rates -- effective-dated rate per authority
# --------------------------------------------------------------------------
class Rate(Base):
    __tablename__ = "rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    authority_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_FK_TAX_AUTHORITIES_ID, ondelete="CASCADE"), nullable=False
    )
    rate_pct: Mapped[Decimal] = mapped_column(Numeric(8, 5), nullable=False)
    effective_from: Mapped[dt.date] = mapped_column(Date, nullable=False)
    effective_to: Mapped[dt.date | None] = mapped_column(Date, nullable=True)
    # Generic JSON: maps to JSONB on PG, JSON on MariaDB. NULL = applies to all categories.
    applies_to_categories: Mapped[Any | None] = mapped_column(JSON, nullable=True)
    data_version_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey(_FK_DATA_VERSIONS_ID, ondelete="SET NULL"), nullable=True
    )

    authority: Mapped[TaxAuthority] = relationship(back_populates="rates")
    data_version: Mapped[DataVersion | None] = relationship(back_populates="rates")

    __table_args__ = (Index("idx_rates_eff", "authority_id", "effective_from", "effective_to"),)

    def __repr__(self) -> str:
        return f"<Rate {self.rate_pct}% authority={self.authority_id}>"


# --------------------------------------------------------------------------
# boundaries -- which authorities apply to which addresses
# Phase 1: ZIP+4 ranges. Phase 4 will add geometry columns (PostGIS / R-tree).
# --------------------------------------------------------------------------
class Boundary(Base):
    __tablename__ = "boundaries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    authority_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_FK_TAX_AUTHORITIES_ID, ondelete="CASCADE"), nullable=False
    )
    zip5: Mapped[str] = mapped_column(String(5), nullable=False)
    zip4_low: Mapped[str | None] = mapped_column(String(4), nullable=True)
    zip4_high: Mapped[str | None] = mapped_column(String(4), nullable=True)
    address_pattern: Mapped[str | None] = mapped_column(String(255), nullable=True)
    data_version_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_FK_DATA_VERSIONS_ID, ondelete="CASCADE"), nullable=False
    )

    authority: Mapped[TaxAuthority] = relationship(back_populates="boundaries")
    data_version: Mapped[DataVersion] = relationship(back_populates="boundaries")

    __table_args__ = (Index("idx_boundaries_zip", "zip5", "zip4_low", "zip4_high"),)

    def __repr__(self) -> str:
        return f"<Boundary zip={self.zip5}-{self.zip4_low or '????'} authority={self.authority_id}>"


# --------------------------------------------------------------------------
# taxability_rules -- per-state per-category taxability matrix
# --------------------------------------------------------------------------
class TaxabilityRule(Base):
    __tablename__ = "taxability_rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_id: Mapped[int] = mapped_column(
        Integer, ForeignKey(_FK_STATES_ID, ondelete="CASCADE"), nullable=False
    )
    item_category: Mapped[str] = mapped_column(String(60), nullable=False)
    is_taxable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    rate_modifier: Mapped[Decimal | None] = mapped_column(Numeric(8, 5), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    effective_from: Mapped[dt.date] = mapped_column(
        Date, nullable=False, default=dt.date(1900, 1, 1)
    )
    effective_to: Mapped[dt.date | None] = mapped_column(Date, nullable=True)

    state: Mapped[State] = relationship(back_populates="taxability_rules")

    __table_args__ = (
        UniqueConstraint(
            "state_id", "item_category", "effective_from", name="uq_taxability_effective"
        ),
    )

    def __repr__(self) -> str:
        return f"<TaxabilityRule state={self.state_id} {self.item_category}={self.is_taxable}>"


# --------------------------------------------------------------------------
# api_keys -- per-key auth + per-key rate limit (Phase 2 Section B)
# --------------------------------------------------------------------------
class ApiKey(Base):
    """An API key issued by an operator.

    The plaintext key is **never stored**. Clients send the
    plaintext key in the ``X-API-Key`` header; the server hashes
    the incoming value (sha256) and compares against ``key_hash``.

    The ``label`` field is a human-readable identifier ("eric's
    laptop", "scbooks-prod") so an operator can revoke a specific
    key by name without remembering the hash.
    """

    __tablename__ = "api_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key_hash: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    """SHA-256 hex digest of the plaintext key. 64 hex chars."""

    label: Mapped[str] = mapped_column(String(120), nullable=False)
    """Human-readable identifier; not unique (multiple keys can share a label)."""

    rate_limit_per_minute: Mapped[int | None] = mapped_column(Integer, nullable=True)
    """Override the default rate limit for this key. NULL = use server default."""

    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.current_timestamp(),
    )
    revoked_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    """When the key was revoked. NULL = active."""

    last_used_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    """Updated on every successful auth. Useful for spotting unused keys."""

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    @property
    def is_active(self) -> bool:
        """True if the key has not been revoked."""
        return self.revoked_at is None

    def __repr__(self) -> str:
        return f"<ApiKey {self.label!r} id={self.id} active={self.is_active}>"


__all__ = [
    "ApiKey",
    "Base",
    "Boundary",
    "DataVersion",
    "Rate",
    "State",
    "TaxAuthority",
    "TaxabilityRule",
]
