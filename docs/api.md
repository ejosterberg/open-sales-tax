# API Reference

Live OpenAPI 3.x spec at **`/v1/openapi.json`**. Interactive docs
at **`/v1/docs`** (Swagger UI) and **`/v1/redoc`** (ReDoc).

This document covers the four Phase 1 endpoints with concrete
examples. The OpenAPI spec is the contract; this page is the
narrative.

⚠️ **Calculation only. Not legal or tax advice.** Every response
includes a ``disclaimer`` field reiterating this.

## Versioning

Per [constitution §5](../specs/constitution.md), the API uses a
URI prefix (`/v1/`). Backward-compatible changes (adding fields,
adding endpoints) keep the v1 prefix. Breaking changes require
`/v2/`. Deprecations get 12 months' notice via response headers.

## Authentication

Two modes, switched via env var (`OPENSALESTAX_AUTH_MODE`):

- **`open` (default):** no auth required; per-IP rate limiting
  (default 60 req/min, configurable via
  `OPENSALESTAX_RATE_LIMIT_PER_MINUTE`).
- **`api_key`:** `X-API-Key` header required on every request.
  Per-key rate limits + usage tracking. Wired up in v0.2.

## Errors

| HTTP | Meaning |
|---:|---|
| 200 | OK |
| 400 | Engine-level validation error (e.g. bad ZIP format from underlying lookup). Body: `{"detail": "..."}`. |
| 422 | Pydantic input validation error (e.g. missing required field). Body: standard FastAPI validation-error structure. |
| 429 | Rate limit exceeded. Body: `{"detail": "Rate limit exceeded..."}`. |
| 500 | Internal error. Should not happen in normal use; please open an issue with the request that triggered it. |

## Endpoints

### `GET /v1/health`

Liveness + readiness signal. No auth or rate limiting (monitors
should be able to poll).

**Response 200:**
```json
{
  "status": "ok",
  "version": "0.1.0a2",
  "database_connected": true
}
```

`status` is `"degraded"` if the database ping fails.

### `GET /v1/states`

Coverage list for all 52 US tax jurisdictions (50 states + DC + PR).

**Response 200:**
```json
{
  "states": [
    {
      "abbrev": "MN",
      "name": "Minnesota",
      "has_sales_tax": true,
      "sst_member": true,
      "tier": 1,
      "notes": ""
    },
    {
      "abbrev": "AK",
      "name": "Alaska",
      "has_sales_tax": false,
      "sst_member": false,
      "tier": 1,
      "notes": "Some boroughs/cities collect local tax via ARSSTC."
    },
    ...
  ],
  "total": 52
}
```

**Tier semantics:**
- `0` -- unsupported (no module loaded; calculations return 0)
- `1` -- fully maintained (taxability matrix + tests)
- `2` -- rate-only via SST data with default taxability matrix

### `GET /v1/rates`

Active jurisdictional rate stack for an address.

**Query parameters:**
- `zip5` (required): 5-digit ZIP code
- `zip4` (optional): 4-digit ZIP+4 suffix

**Response 200:**
```json
{
  "input": {"zip5": "55401", "zip4": null},
  "jurisdictions": [
    {"name": "Minnesota", "type": "state", "rate_pct": "6.875"},
    {"name": "Hennepin County", "type": "county", "rate_pct": "0.150"}
  ],
  "combined_rate_pct": "7.025",
  "disclaimer": "Calculation only; not legal or tax advice. Verify against your state Department of Revenue before remitting."
}
```

If no jurisdictions are loaded for the ZIP, `jurisdictions` is
empty and `combined_rate_pct` is `0`.

### `POST /v1/calculate`

Tax calculation for one or more line items at an address.

**Request body:**
```json
{
  "address": {"zip5": "55401", "zip4": "1042"},
  "line_items": [
    {"amount": "100.00", "category": "general"},
    {"amount": "50.00", "category": "clothing"}
  ]
}
```

**Response 200:**
```json
{
  "subtotal": "150.00",
  "tax_total": "7.0250",
  "lines": [
    {
      "amount": "100.00",
      "category": "general",
      "tax": "7.0250",
      "rate_pct": "7.025",
      "jurisdictions": [
        {"name": "Minnesota", "type": "state", "rate_pct": "6.875"},
        {"name": "Hennepin County", "type": "county", "rate_pct": "0.150"}
      ],
      "note": null
    },
    {
      "amount": "50.00",
      "category": "clothing",
      "tax": "0",
      "rate_pct": "0",
      "jurisdictions": [],
      "note": "Clothing is non-taxable in Minnesota (Minn. Stat. 297A.67 subd 8)."
    }
  ],
  "disclaimer": "Calculation only; not legal or tax advice. Verify against your state Department of Revenue before remitting."
}
```

**Item categories** (Phase 1):

| Category | MN | WI | Default (tier 2) |
|---|---|---|---|
| `general` | taxable | taxable | taxable |
| `clothing` | NON-taxable | TAXABLE | taxable |
| `groceries` | NON-taxable | NON-taxable | NON-taxable |
| `prescription_drugs` | NON-taxable | NON-taxable | taxable* |
| `prepared_food` | taxable | taxable | taxable |
| `digital_goods` | taxable | taxable | taxable |

`*` Tier-2 modules apply default taxability; categories not
explicitly listed in the matrix are treated as taxable. State
maintainers should override to match their actual statutes.

**Currency math:** all amounts are `Decimal` (no floats). Tax
amounts round to 4 decimal places (HALF_UP). Display rounding is
the caller's job.

## Versioning future

| Version | Status |
|---|---|
| v0.1 (alpha) | API contract stable; data-loading manual |
| v0.2 | data-load CLI + API-key auth + first non-SST state (CA) |
| v0.3+ | per-state taxability matrices for tier-2 states; sales-tax holidays; exemption certificates |
| v1.0 | address-level resolution (PostGIS); production-ready for the long tail of states |
