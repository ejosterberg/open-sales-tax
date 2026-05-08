# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Runtime settings loaded from environment variables.

12-factor configuration: every knob is an env var prefixed with
``OPENSALESTAX_``. Constitution §10 mandates that engine selection
happens via ``DATABASE_URL`` only -- no application code branches
on dialect.
"""

from __future__ import annotations

from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the OpenSalesTax API.

    All values come from environment variables with the
    ``OPENSALESTAX_`` prefix. Replace ``<USER>`` and ``<PASSWORD>``
    placeholders with your real credentials when setting the env
    var; never commit real credentials to source control::

        OPENSALESTAX_DATABASE_URL=postgresql+asyncpg://<USER>:<PASSWORD>@localhost:5432/opensalestax
        OPENSALESTAX_AUTH_MODE=open
        OPENSALESTAX_RATE_LIMIT_PER_MINUTE=60
    """

    model_config = SettingsConfigDict(
        env_prefix="OPENSALESTAX_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ----- Database -----------------------------------------------------
    database_url: SecretStr = Field(
        ...,
        description=(
            "SQLAlchemy async DSN with placeholder credentials. "
            "PostgreSQL example: "
            "postgresql+asyncpg://<USER>:<PASSWORD>@<HOST>:5432/<DBNAME>. "
            "MariaDB example: "
            "mysql+asyncmy://<USER>:<PASSWORD>@<HOST>:3306/<DBNAME>."
        ),
    )
    database_echo: bool = Field(
        default=False,
        description="If true, SQLAlchemy logs every SQL statement (noisy; dev only).",
    )

    # ----- API ----------------------------------------------------------
    auth_mode: Literal["open", "api_key"] = Field(
        default="open",
        description=(
            "Authentication mode. 'open' means no auth with IP-based "
            "rate limiting; 'api_key' requires an X-API-Key header."
        ),
    )
    rate_limit_per_minute: int = Field(
        default=60,
        ge=1,
        description="Per-IP (or per-API-key) requests per minute.",
    )
    trust_forwarded_for: bool = Field(
        default=False,
        description=(
            "If true, the rate-limit key_func reads the real client IP "
            "from the CF-Connecting-IP header (or first hop of "
            "X-Forwarded-For), rather than request.client.host. Only "
            "enable when the API sits behind a trusted proxy (Cloudflare, "
            "an internal LB) that always sets these headers -- otherwise "
            "any caller can spoof their IP and bypass rate limiting. "
            "Off by default; opensalestax.org's Cloudflare-fronted prod "
            "sets this true."
        ),
    )

    # ----- CORS ---------------------------------------------------------
    cors_allowed_origins: str = Field(
        default="*",
        description=(
            "Comma-separated list of allowed CORS origins for browser "
            "callers. Default '*' permits any origin -- appropriate for "
            "the demo / public engine instances. Tighten to e.g. "
            "'https://opensalestax.org,https://app.example.com' on "
            "private deployments."
        ),
    )

    # ----- Logging / ops -----------------------------------------------
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
        description="Root logger level.",
    )

    # ----- Convenience --------------------------------------------------
    @property
    def database_dsn(self) -> str:
        """Return the database DSN as a plain string (for SQLAlchemy)."""
        return self.database_url.get_secret_value()

    @property
    def database_dialect(self) -> str:
        """Return the dialect name extracted from the DSN scheme.

        Used ONLY for logging / diagnostics. Application code MUST NOT
        branch on this value -- portability is enforced at the SQLAlchemy
        and Alembic layer (constitution §10 rule 1).
        """
        scheme = self.database_dsn.split(":", 1)[0]
        return scheme.split("+", 1)[0]


_settings: Settings | None = None


def get_settings() -> Settings:
    """Return a process-singleton Settings instance.

    Cached after first call. Tests can override by clearing the cache:
    ``opensalestax.settings._settings = None``.
    """
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
