# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Eric Osterberg and OpenSalesTax contributors
"""Pydantic request and response models for the v1 API.

These doubles as the OpenAPI schema (FastAPI generates the spec
from these models) and as runtime validation. Per constitution
sec 5, the API is OpenAPI 3.x; the schema lives at
``/v1/openapi.json``.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------------------------------------------------------------------------
# /v1/health
# ---------------------------------------------------------------------------
class HealthResponse(BaseModel):
    """Liveness + readiness signal for the API."""

    status: Literal["ok", "degraded"]
    version: str = Field(description="OpenSalesTax package version")
    database_connected: bool = Field(
        description="True if the configured DATABASE_URL accepts connections."
    )


# ---------------------------------------------------------------------------
# /v1/states
# ---------------------------------------------------------------------------
class StateInfo(BaseModel):
    """One entry in the /v1/states coverage list."""

    abbrev: str = Field(min_length=2, max_length=2, description="USPS abbreviation")
    name: str
    has_sales_tax: bool
    sst_member: bool
    tier: Literal[0, 1, 2] = Field(
        description=(
            "0 = unsupported (no module loaded); "
            "1 = fully maintained (taxability matrix + tests); "
            "2 = rate-only via SST data with default taxability."
        )
    )
    notes: str = ""


class StatesResponse(BaseModel):
    """Top-level response for /v1/states."""

    states: list[StateInfo]
    total: int


# ---------------------------------------------------------------------------
# /v1/rates
# ---------------------------------------------------------------------------
class JurisdictionRate(BaseModel):
    """One jurisdiction's contribution to the rate stack."""

    name: str
    type: Literal["state", "county", "city", "district"]
    rate_pct: Decimal


class RatesResponse(BaseModel):
    """Top-level response for /v1/rates."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "input": {"zip5": "55401", "zip4": None},
                "jurisdictions": [
                    {"name": "Minnesota", "type": "state", "rate_pct": "6.875"},
                ],
                "combined_rate_pct": "6.875",
                "disclaimer": "Calculation only; not legal or tax advice. Verify against your state Department of Revenue before remitting.",
            }
        }
    )

    input: dict
    jurisdictions: list[JurisdictionRate]
    combined_rate_pct: Decimal
    disclaimer: str


# ---------------------------------------------------------------------------
# /v1/calculate
# ---------------------------------------------------------------------------
class AddressInput(BaseModel):
    """ZIP-based address for Phase 1 calculations."""

    zip5: str = Field(min_length=5, max_length=5, pattern=r"^\d{5}$")
    zip4: str | None = Field(default=None, min_length=4, max_length=4, pattern=r"^\d{4}$")


class LineItemRequest(BaseModel):
    """One taxable line in a calculate request."""

    amount: Decimal = Field(ge=0, description="Pre-tax amount, non-negative.")
    category: str = Field(default="general")

    @field_validator("amount")
    @classmethod
    def _quantize_amount(cls, v: Decimal) -> Decimal:
        # Coerce arbitrary-precision input to 4dp; matches the engine's TAX_QUANTUM
        return v


class CalculateRequest(BaseModel):
    """POST /v1/calculate request body."""

    address: AddressInput
    line_items: list[LineItemRequest] = Field(default_factory=list)


class CalculatedLineResponse(BaseModel):
    """One calculated line in the response."""

    amount: Decimal
    category: str
    tax: Decimal
    rate_pct: Decimal
    jurisdictions: list[JurisdictionRate] = Field(default_factory=list)
    note: str | None = None


class CalculateResponse(BaseModel):
    """POST /v1/calculate response body."""

    subtotal: Decimal
    tax_total: Decimal
    lines: list[CalculatedLineResponse]
    disclaimer: str
