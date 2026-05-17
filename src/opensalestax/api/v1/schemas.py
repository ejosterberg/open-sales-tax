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
# /v1/capabilities
# ---------------------------------------------------------------------------
class EndpointDescriptor(BaseModel):
    """Path + spec-version of one engine endpoint."""

    path: str = Field(examples=["/v1/calculate"])
    version: int = Field(
        ge=1,
        description=(
            "Per-endpoint spec version. Bumped when the request/response "
            "shape changes incompatibly. Independent from package version."
        ),
        examples=[1],
    )


class CapabilitiesResponse(BaseModel):
    """Manifest of what this engine instance supports.

    Driver: connector-tier captain's cross-cutting note in
    ``engine-team-requests.md`` (2026-05-16). Connectors call this
    once on Test Connection / first calc and cache the result, so
    they can do version-aware feature detection without parsing
    semver strings out of ``/v1/health``.

    The ``features`` dict is the discoverable-feature contract:
    booleans connector code can branch on. Adding a new key
    that's ``true`` is non-breaking; flipping an existing ``true``
    to ``false`` is breaking and requires a major version bump.
    """

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "version": "0.59.0",
                "endpoints": {
                    "health": {"path": "/v1/health", "version": 1},
                    "states": {"path": "/v1/states", "version": 1},
                    "rates": {"path": "/v1/rates", "version": 1},
                    "calculate": {"path": "/v1/calculate", "version": 1},
                    "capabilities": {"path": "/v1/capabilities", "version": 1},
                },
                "features": {
                    "coverage_warning": True,
                    "shipping_first_class": False,
                    "vendor_allocation": False,
                    "transaction_record_back": False,
                },
            }
        }
    )

    version: str = Field(
        description="OpenSalesTax package version this engine is running.",
        examples=["0.59.0"],
    )
    endpoints: dict[str, EndpointDescriptor] = Field(
        description="Map of endpoint slug -> {path, version}.",
    )
    features: dict[str, bool] = Field(
        description=(
            "Discoverable-feature toggles. Connectors should branch on these "
            "rather than parsing the engine version string. Keys are stable: "
            "additions are non-breaking; removals or true->false flips require "
            "a major version bump."
        ),
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
    """One jurisdiction's contribution to the rate stack.

    ``tax`` is populated only when this object appears inside a
    ``/v1/calculate`` response (where a line amount exists). The
    sum of per-jurisdiction ``tax`` values equals the line's
    ``tax`` exactly -- the engine quantizes per-jurisdiction first,
    then sums.
    """

    name: str = Field(examples=["Minnesota", "MN-county-053", "City of Minneapolis"])
    type: Literal["state", "county", "city", "district"] = Field(examples=["state", "county"])
    rate_pct: Decimal = Field(examples=["6.875", "0.15", "0.5"])
    tax: Decimal | None = Field(
        default=None,
        description=(
            "Dollar amount this authority contributes to the line's tax. "
            "Present only in /v1/calculate responses; omitted in /v1/rates."
        ),
        examples=["6.8750", "0.1500"],
    )


class RatesResponse(BaseModel):
    """Top-level response for /v1/rates."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "input": {"zip5": "55401", "zip4": None},
                "jurisdictions": [
                    {"name": "Minnesota", "type": "state", "rate_pct": "6.875"},
                    {"name": "Hennepin County", "type": "county", "rate_pct": "0.15"},
                    {"name": "City of Minneapolis", "type": "city", "rate_pct": "0.5"},
                ],
                "combined_rate_pct": "7.525",
                "disclaimer": "Calculation only; not legal or tax advice. Verify against your state Department of Revenue before remitting.",
            }
        }
    )

    input: dict
    jurisdictions: list[JurisdictionRate]
    combined_rate_pct: Decimal
    disclaimer: str
    coverage_warning: str | None = Field(
        default=None,
        description=(
            "Populated only when the requested address falls in a state with "
            "known coverage gaps (CO home-rule, LA parishes, AL home-rule, "
            "HI Maui dispute). The returned combined_rate_pct may underreport "
            "the true rate in that case. Tracked per state in "
            "opensalestax.core.coverage."
        ),
        examples=[None, "Colorado: ~70 home-rule cities self-administer..."],
    )


# ---------------------------------------------------------------------------
# /v1/calculate
# ---------------------------------------------------------------------------
class AddressInput(BaseModel):
    """ZIP-based address for Phase 1 calculations."""

    zip5: str = Field(
        min_length=5,
        max_length=5,
        pattern=r"^\d{5}$",
        examples=["55401", "75201", "94102", "10001"],
    )
    zip4: str | None = Field(
        default=None,
        min_length=4,
        max_length=4,
        pattern=r"^\d{4}$",
        examples=["1234", None],
    )


class LineItemRequest(BaseModel):
    """One taxable line in a calculate request."""

    amount: Decimal = Field(
        ge=0,
        description="Pre-tax amount, non-negative.",
        examples=["100.00", "49.99", "1500.00"],
    )
    category: str = Field(
        default="general",
        description=(
            "Tax category. Standard categories: general, clothing, "
            "groceries, prescription_drugs, prepared_food, digital_goods. "
            "Per-state taxability rules apply."
        ),
        examples=["general", "clothing", "groceries", "digital_goods"],
    )

    @field_validator("amount")
    @classmethod
    def _quantize_amount(cls, v: Decimal) -> Decimal:
        # Coerce arbitrary-precision input to 4dp; matches the engine's TAX_QUANTUM
        return v


class ShippingInput(BaseModel):
    """Shipping/delivery component of a /v1/calculate request.

    First-class shipping handling shipped in v0.59.0 per connector-
    tier captain Ask 3. The engine applies the destination state's
    shipping taxability rule (CONDITIONAL / EXEMPT_IF_SEPARATELY_
    STATED / ALWAYS / MIXED / NONE) and returns the calculated
    shipping tax in a parallel ``ShippingOutput`` block on the
    response.

    Backward-compatible: callers that continue to send shipping as
    a ``LineItemRequest`` with ``category="shipping"`` are still
    accepted; the engine applies the state-specific rule either
    way. The first-class field is preferred for new integrations
    and is required for states that distinguish handling from
    shipping (Maryland).
    """

    amount: Decimal = Field(
        ge=0,
        description="Pre-tax shipping amount, non-negative.",
        examples=["12.50", "9.99"],
    )
    separately_stated: bool = Field(
        default=True,
        description=(
            "True if the shipping charge is displayed as a separate "
            "line on the invoice (default for e-commerce). Relevant "
            "in EXEMPT_IF_SEPARATELY_STATED states (CA, FL, IL, MA, "
            "MI, MO, NV, VA, etc.) where bundled shipping IS taxable."
        ),
    )
    is_handling_charge: bool = Field(
        default=False,
        description=(
            "True if this charge is a handling fee rather than pure "
            "shipping. Honored only in Maryland (where the state "
            "distinguishes shipping from handling); ignored in all "
            "other states."
        ),
    )
    method: str | None = Field(
        default=None,
        description="Carrier / shipping method label. Analytics only; ignored by the tax calculation.",
        examples=["ups_ground", "usps_priority", "fedex_2day", None],
    )


class ShippingOutput(BaseModel):
    """Shipping component of a /v1/calculate response."""

    amount: Decimal = Field(description="The pre-tax shipping amount the request submitted.")
    tax_amount: Decimal = Field(
        description="Tax owed on the shipping charge. Zero when the destination state's rule exempts.",
    )
    rate_pct: Decimal = Field(
        description="Effective shipping tax rate (combined state + county + city + district), or 0 if exempt.",
    )
    taxable_reason: str | None = Field(
        default=None,
        description=(
            "Human-readable debug aid explaining why shipping was/wasn't taxed (e.g. 'MN taxes shipping "
            "when items are taxable'). Useful for connector logs and merchant support; not a stable "
            "user-facing string."
        ),
        examples=[
            None,
            "MN taxes shipping when at least one item is taxable",
            "OR has no state sales tax",
        ],
    )


class CalculateRequest(BaseModel):
    """POST /v1/calculate request body."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "summary": "Single $100 general line, Minneapolis MN",
                    "value": {
                        "address": {"zip5": "55401"},
                        "line_items": [{"amount": "100.00", "category": "general"}],
                    },
                },
                {
                    "summary": "Mixed cart with non-taxable clothing (MN)",
                    "value": {
                        "address": {"zip5": "55401"},
                        "line_items": [
                            {"amount": "100.00", "category": "general"},
                            {"amount": "50.00", "category": "clothing"},
                        ],
                    },
                },
                {
                    "summary": "Cart with first-class shipping (v0.59.0+)",
                    "value": {
                        "address": {"zip5": "55401"},
                        "line_items": [{"amount": "100.00", "category": "general"}],
                        "shipping": {"amount": "12.50", "separately_stated": True},
                    },
                },
                {
                    "summary": "Texas back-to-school holiday (Aug 8)",
                    "value": {
                        "address": {"zip5": "75201"},
                        "line_items": [
                            {"amount": "75.00", "category": "clothing"},
                        ],
                    },
                },
            ]
        }
    )

    address: AddressInput
    line_items: list[LineItemRequest] = Field(default_factory=list)
    shipping: ShippingInput | None = Field(
        default=None,
        description=(
            "Optional shipping/delivery component. When omitted, the engine doesn't "
            "compute shipping tax (preserves pre-v0.59.0 behavior). When provided, "
            "engine returns a parallel ``shipping`` block on the response."
        ),
    )


class CalculatedLineResponse(BaseModel):
    """One calculated line in the response.

    Invariant: ``tax == sum(j.tax for j in jurisdictions)`` -- the
    per-jurisdiction breakdown reconciles exactly with the line
    total. Use the breakdown for accounting (state/county/city
    splits); use ``tax`` for the customer-facing total.
    """

    amount: Decimal
    category: str
    tax: Decimal
    rate_pct: Decimal
    jurisdictions: list[JurisdictionRate] = Field(default_factory=list)
    note: str | None = None


class CalculateResponse(BaseModel):
    """POST /v1/calculate response body."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "subtotal": "150.00",
                "tax_total": "0.1500",
                "lines": [
                    {
                        "amount": "100.00",
                        "category": "general",
                        "tax": "0.1500",
                        "rate_pct": "0.15",
                        "jurisdictions": [
                            {
                                "name": "MN-county-053",
                                "type": "county",
                                "rate_pct": "0.15",
                                "tax": "0.1500",
                            }
                        ],
                        "note": None,
                    },
                    {
                        "amount": "50.00",
                        "category": "clothing",
                        "tax": "0",
                        "rate_pct": "0",
                        "jurisdictions": [],
                        "note": "Clothing is non-taxable in Minnesota (Minn. Stat. 297A.67 subd 8).",
                    },
                ],
                "disclaimer": "Calculation only; not legal or tax advice. Verify against your state Department of Revenue before remitting.",
            }
        }
    )

    subtotal: Decimal
    tax_total: Decimal
    lines: list[CalculatedLineResponse]
    disclaimer: str
    coverage_warning: str | None = Field(
        default=None,
        description=(
            "Populated only when the requested address falls in a state with "
            "known coverage gaps (CO home-rule, LA parishes, AL home-rule, "
            "HI Maui dispute). The returned tax_total may underreport the "
            "true tax owed in that case. Tracked per state in "
            "opensalestax.core.coverage."
        ),
        examples=[None, "Colorado: ~70 home-rule cities self-administer..."],
    )
    shipping: ShippingOutput | None = Field(
        default=None,
        description=(
            "Shipping tax block when the request included a top-level ``shipping`` "
            "field. Omitted when the request didn't include shipping (preserves "
            "pre-v0.59.0 behavior)."
        ),
    )
