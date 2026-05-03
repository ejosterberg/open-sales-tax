# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Pure tests for the auth helper functions (no DB needed)."""

from __future__ import annotations

from opensalestax.auth import API_KEY_HEADER_NAME, hash_key, mint_key


def test_mint_key_is_url_safe_and_long_enough() -> None:
    """Minted keys are URL-safe ASCII at least 30 chars long."""
    key = mint_key()
    assert len(key) >= 30
    # urlsafe characters: A-Za-z0-9_- (no padding here)
    assert all(c.isalnum() or c in "_-" for c in key)


def test_mint_key_returns_distinct_values() -> None:
    """Two calls don't return the same key (vanishingly small collision chance)."""
    keys = {mint_key() for _ in range(100)}
    assert len(keys) == 100


def test_hash_key_is_deterministic() -> None:
    """Same plaintext always hashes to the same string."""
    plaintext = "abc123"
    assert hash_key(plaintext) == hash_key(plaintext)


def test_hash_key_returns_64_hex_chars() -> None:
    """SHA-256 hex digest is 64 chars."""
    h = hash_key("anything")
    assert len(h) == 64
    int(h, 16)  # should not raise -- valid hex


def test_hash_key_different_inputs_differ() -> None:
    assert hash_key("a") != hash_key("b")


def test_header_name_is_canonical() -> None:
    assert API_KEY_HEADER_NAME == "X-API-Key"
