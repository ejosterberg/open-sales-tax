# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""API-key authentication helpers.

Two auth modes are supported (selected via
``OPENSALESTAX_AUTH_MODE``):

- **open** -- the default; no auth, IP-based rate limiting
- **api_key** -- ``X-API-Key`` header required on every protected
  request. Keys are stored as SHA-256 hashes; the plaintext key
  exists only at the moment it's minted (and printed to the
  operator).

Health endpoints stay unauthenticated regardless of mode so
monitoring tools always work.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import secrets
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from opensalestax.db.models import ApiKey
from opensalestax.db.session import get_session
from opensalestax.settings import get_settings

# How many characters of plaintext entropy to mint. 32 chars of
# urlsafe base64 = 192 bits of entropy. Comfortably collision-free.
_KEY_LENGTH_BYTES = 24

API_KEY_HEADER_NAME = "X-API-Key"


@dataclass(frozen=True, slots=True)
class MintedKey:
    """Returned to the operator when a new key is created.

    The ``plaintext`` field is the value the operator must save NOW
    -- it's never persisted server-side. The DB only stores the hash.
    """

    plaintext: str
    label: str
    db_id: int


def hash_key(plaintext: str) -> str:
    """Return the canonical SHA-256 hex digest used for the ``key_hash`` column."""
    return hashlib.sha256(plaintext.encode("utf-8")).hexdigest()


def mint_key() -> str:
    """Generate a fresh URL-safe API key string."""
    return secrets.token_urlsafe(_KEY_LENGTH_BYTES)


async def create_api_key(
    session: AsyncSession,
    label: str,
    *,
    rate_limit_per_minute: int | None = None,
    notes: str | None = None,
) -> MintedKey:
    """Mint and persist a new API key.

    Returns the plaintext for the operator to save; the database
    only ever sees the hash.
    """
    plaintext = mint_key()
    key_hash = hash_key(plaintext)
    row = ApiKey(
        key_hash=key_hash,
        label=label,
        rate_limit_per_minute=rate_limit_per_minute,
        notes=notes,
    )
    session.add(row)
    await session.commit()
    await session.refresh(row)
    return MintedKey(plaintext=plaintext, label=label, db_id=row.id)


async def revoke_api_key(session: AsyncSession, label: str) -> int:
    """Mark every active key with this label as revoked.

    Returns the number of keys revoked. Useful for "the laptop is
    lost" scenarios where you want to nuke all keys with a label.
    """
    # Load matching rows so we can both update and return an accurate
    # count without depending on Result.rowcount (whose typing is
    # uneven across SQLAlchemy async dialect adapters).
    rows = list(
        (
            await session.execute(
                select(ApiKey).where(ApiKey.label == label, ApiKey.revoked_at.is_(None))
            )
        )
        .scalars()
        .all()
    )
    if not rows:
        return 0

    now = dt.datetime.now(tz=dt.UTC)
    for row in rows:
        row.revoked_at = now
    await session.commit()
    return len(rows)


async def list_active_api_keys(session: AsyncSession) -> list[ApiKey]:
    """Return every non-revoked API key, ordered by id."""
    rows = (
        (
            await session.execute(
                select(ApiKey).where(ApiKey.revoked_at.is_(None)).order_by(ApiKey.id)
            )
        )
        .scalars()
        .all()
    )
    return list(rows)


_SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def authenticate(
    request: Request,
    session: _SessionDep,
) -> ApiKey | None:
    """FastAPI dependency that enforces auth based on the active mode.

    - In ``open`` mode: returns ``None`` (no key needed).
    - In ``api_key`` mode: requires an ``X-API-Key`` header that
      matches a non-revoked key. Returns the matched
      :class:`ApiKey` row, updating its ``last_used_at``.

    Raises :class:`HTTPException` 401 on missing or invalid keys
    when in ``api_key`` mode.
    """
    settings = get_settings()
    if settings.auth_mode == "open":
        return None

    header_value = request.headers.get(API_KEY_HEADER_NAME)
    if not header_value:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Missing {API_KEY_HEADER_NAME} header.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    key_hash = hash_key(header_value)
    row = (
        await session.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.revoked_at.is_(None))
        )
    ).scalar_one_or_none()

    if row is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or revoked API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Best-effort last_used_at update (don't fail the request if it can't write)
    try:
        await session.execute(
            update(ApiKey)
            .where(ApiKey.id == row.id)
            .values(last_used_at=dt.datetime.now(tz=dt.UTC))
        )
        await session.commit()
    except Exception:  # pragma: no cover -- defensive; write may race
        await session.rollback()

    return row
