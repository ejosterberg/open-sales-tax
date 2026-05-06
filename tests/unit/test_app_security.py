# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""App-level security middleware: rate limiting + response headers.

These tests exist to lock the wiring in place. v0.54.x shipped a
broken rate limiter (slowapi was registered but ``SlowAPIMiddleware``
was never added to the app, so ``default_limits`` never enforced).
A regression that re-introduces that bug should fail
``test_rate_limit_fires_after_threshold`` immediately.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

import opensalestax.settings as settings_module
from opensalestax.app import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    """Build a fresh app with a deliberately low per-IP rate limit."""
    monkeypatch.setenv(
        "OPENSALESTAX_DATABASE_URL",
        "postgresql+asyncpg://u:p@localhost:5432/db",
    )
    monkeypatch.setenv("OPENSALESTAX_RATE_LIMIT_PER_MINUTE", "3")
    monkeypatch.setattr(settings_module, "_settings", None)
    app = create_app()
    with TestClient(app, follow_redirects=False) as c:
        yield c
    monkeypatch.setattr(settings_module, "_settings", None)


def test_response_carries_security_headers(client: TestClient) -> None:
    """Every response should carry the defense-in-depth headers."""
    response = client.get("/")
    assert response.status_code == 307
    headers = {k.lower(): v for k, v in response.headers.items()}
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "max-age=31536000" in headers["strict-transport-security"]
    assert "geolocation=()" in headers["permissions-policy"]


def test_rate_limit_fires_after_threshold(client: TestClient) -> None:
    """slowapi default_limits should return 429 once the per-IP cap is hit."""
    # The 3/minute limit means the first 3 succeed, the 4th must be denied.
    for _ in range(3):
        assert client.get("/").status_code == 307
    blocked = client.get("/")
    assert blocked.status_code == 429
    body = blocked.json()
    assert "Rate limit exceeded" in body["detail"]


def test_rate_limit_response_also_carries_security_headers(
    client: TestClient,
) -> None:
    """Defense-in-depth headers must apply to 429s, not just successful responses."""
    for _ in range(3):
        client.get("/")
    blocked = client.get("/")
    assert blocked.status_code == 429
    headers = {k.lower(): v for k, v in blocked.headers.items()}
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
