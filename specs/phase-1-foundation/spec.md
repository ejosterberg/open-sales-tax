# Phase 1 — Foundation

> First shippable slice. Brings the architecture, two state modules,
> the API surface, and the deployment story online.
>
> **Status:** specced 2026-05-02. Not started.
> **Estimated scope:** 4-6 sessions if Python + FastAPI; 5-7 if Node + TS;
> 6-8 if Go.

## Goal

Ship a working OpenSalesTax v0.1 that an external user could `docker run`
and immediately get a correct sales-tax calculation for any US address
in **Minnesota** or **Wisconsin** (the two pilot states), plus zero-rate
responses for the 5 no-sales-tax states (AK, DE, MT, NH, OR).

Success looks like: a developer reads the README, runs one Docker
command, hits `POST /v1/calculate` with `{address: "...", amount: ...}`
for an MN address, and gets back the correct rate decomposition (state
+ county + city + special) matching what the MN DOR would say.

## In scope

### 1. Language scaffold + project structure

Whichever language Eric picks (Python+FastAPI recommended), set up:
- Standard project structure for that ecosystem
- Linter + formatter + test runner
- pyproject.toml / package.json / go.mod with pinned dependencies
- pre-commit hooks (or equivalent)
- Apache 2.0 LICENSE file at repo root
- CONTRIBUTING.md skeleton
- MAINTAINERS.md skeleton

### 2. Database

- **Dual-engine support:** PostgreSQL 15+ AND MariaDB 11+ as
  first-class citizens via SQLAlchemy 2.x + Alembic. See
  `specs/decisions/03-database.md` for the full rationale and
  rules.
- **Portable schema only.** All Phase 1 migrations must apply
  cleanly on both engines without dialect-specific branches.
  Allowed types: INTEGER, VARCHAR, TEXT, BOOLEAN, NUMERIC, DATE,
  TIMESTAMP, generic JSON, B-tree + UNIQUE indexes.
- **No PostGIS in Phase 1.** Address-level GIS is Phase 4.
- Schema below is shown in vendor-neutral SQL for reference;
  actual implementation uses SQLAlchemy declarative models with
  Alembic auto-generation.

```sql
-- States
CREATE TABLE states (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,  -- SERIAL on Postgres
    abbrev          VARCHAR(2) NOT NULL UNIQUE,
    name            VARCHAR(60) NOT NULL,
    sst_member      BOOLEAN NOT NULL DEFAULT FALSE,
    sst_joined      DATE NULL,
    has_sales_tax   BOOLEAN NOT NULL DEFAULT TRUE,
    notes           TEXT
);

-- Data versions for reproducibility (declared before rates because rates references it)
CREATE TABLE data_versions (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    state_id        INTEGER NOT NULL REFERENCES states(id),
    source          VARCHAR(40) NOT NULL,         -- 'sst', 'state_dor', 'manual'
    version_label   VARCHAR(60) NOT NULL,         -- 'MN-SST-2026Q2APR15'
    fetched_at      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    notes           TEXT
);

-- Tax authorities (state DOR, county, city, special district)
CREATE TABLE tax_authorities (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    state_id        INTEGER NOT NULL REFERENCES states(id),
    name            VARCHAR(120) NOT NULL,
    authority_type  VARCHAR(20) NOT NULL,        -- 'state', 'county', 'city', 'district'
    parent_id       INTEGER NULL REFERENCES tax_authorities(id),
    UNIQUE (state_id, name, authority_type)
);

-- Rates (effective-dated)
CREATE TABLE rates (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    authority_id    INTEGER NOT NULL REFERENCES tax_authorities(id),
    rate_pct        NUMERIC(8,5) NOT NULL,        -- 6.87500
    effective_from  DATE NOT NULL,
    effective_to    DATE NULL,                    -- NULL = current
    applies_to_categories JSON NULL,              -- portable JSON, not JSONB; NULL = applies to all
    data_version_id INTEGER NULL REFERENCES data_versions(id)
    -- index defined separately for portability
);
CREATE INDEX idx_rates_eff ON rates (authority_id, effective_from, effective_to);

-- Boundaries (ZIP+4 based for Phase 1; PostGIS / R-tree spatial later in Phase 4)
CREATE TABLE boundaries (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    authority_id    INTEGER NOT NULL REFERENCES tax_authorities(id),
    zip5            VARCHAR(5) NOT NULL,
    zip4_low        VARCHAR(4) NULL,
    zip4_high       VARCHAR(4) NULL,
    address_pattern VARCHAR(255) NULL,             -- optional regex for street-level (rare)
    data_version_id INTEGER NOT NULL REFERENCES data_versions(id)
);
CREATE INDEX idx_boundaries_zip ON boundaries (zip5, zip4_low, zip4_high);

-- Taxability matrix (per-state per-category)
CREATE TABLE taxability_rules (
    id              INTEGER PRIMARY KEY AUTO_INCREMENT,
    state_id        INTEGER NOT NULL REFERENCES states(id),
    item_category   VARCHAR(60) NOT NULL,         -- 'clothing', 'groceries', 'prepared_food', 'digital_goods'
    is_taxable      BOOLEAN NOT NULL,
    rate_modifier   NUMERIC(8,5) NULL,            -- e.g., reduced rate for groceries
    notes           TEXT,
    effective_from  DATE NOT NULL DEFAULT '1900-01-01',
    effective_to    DATE NULL,
    UNIQUE (state_id, item_category, effective_from)
);
```

**Notes on engine portability:**
- `AUTO_INCREMENT` shown for clarity; SQLAlchemy emits the right
  dialect-specific syntax (`SERIAL` on Postgres, `AUTO_INCREMENT`
  on MariaDB).
- `JSON` (not `JSONB`) — SQLAlchemy's generic type maps to JSONB
  on Postgres and JSON on MariaDB; query syntax stays portable.
- Indexes declared as separate `CREATE INDEX` statements; Alembic
  generates them either way.
- `CURRENT_TIMESTAMP` is the portable default (Postgres + MariaDB
  both support it; `NOW()` is Postgres-specific in some contexts).

### 3. Per-state module pattern

Define the interface every state module implements. Sketch (Python
syntax for illustration):

```python
class StateModule(Protocol):
    state_abbrev: str
    state_name: str
    sst_member: bool

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable[RateRow]:
        """Read upstream rate file, yield normalized rate rows."""

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable[BoundaryRow]:
        """Read upstream boundary file, yield normalized boundary rows."""

    def taxability_for(self, item_category: str, effective_date: date) -> Optional[TaxabilityRule]:
        """Return the per-category rule for this state, or None if unknown."""

    def special_cases(self) -> Iterable[SpecialCase]:
        """Optional state-specific rules the engine consults during calculation."""
```

Phase 1 ships:
- `states/minnesota.py` (or .ts / .go) — parses MN SST data
- `states/wisconsin.py` — parses WI SST data
- `states/no_tax.py` — generic zero-rate module used by AK, DE, MT, NH, OR

### 4. Data-loading CLI

```
opensalestax data fetch --state MN --version 2026Q2APR15
opensalestax data fetch --state WI --version 2026Q2APR15
opensalestax data list-versions
opensalestax data activate --state MN --version 2026Q2APR15
```

- Downloads the upstream file from SST.
- Parses via the state module.
- Inserts into rates + boundaries + taxability_rules tables.
- Tags with the data_version row.
- `activate` switches the "current" pointer for that state.

Reproducibility per constitution §6: a build pinned to a specific
data version yields the same calculations forever.

### 5. API endpoints (v1, four to start)

```
GET  /v1/health
     → 200 OK with version + DB connectivity status

GET  /v1/states
     → list of all 52 (50 + DC + PR) with coverage status:
       { abbrev, name, has_sales_tax, sst_member, supported,
         active_version }

GET  /v1/rates?address=...&zip=...&zip4=...
     → returns the applicable rates for an address (any combo of
       address / zip / zip4 supported; zip5+zip4 most precise in
       Phase 1):
       {
         "input": { "zip5": "55401", "zip4": "1402" },
         "jurisdictions": [
           { "name": "Minnesota", "type": "state", "rate_pct": 6.875 },
           { "name": "Hennepin County", "type": "county", "rate_pct": 0.150 },
           { "name": "Minneapolis", "type": "city", "rate_pct": 0.500 }
         ],
         "combined_rate_pct": 7.525,
         "data_version": "MN-SST-2026Q2APR15",
         "calculated_at": "2026-05-02T18:32:11Z"
       }

POST /v1/calculate
     body: {
       "address": { "zip5": "55401", "zip4": "1402" },
       "line_items": [
         { "amount": 100.00, "category": "general" },
         { "amount": 50.00,  "category": "clothing" }
       ]
     }
     → {
       "subtotal": 150.00,
       "tax_total": 7.5275,
       "lines": [
         {
           "amount": 100.00, "category": "general",
           "tax": 7.525, "rate_pct": 7.525,
           "jurisdictions": [...]
         },
         {
           "amount": 50.00, "category": "clothing",
           "tax": 0.00,    "rate_pct": 0.00,
           "note": "Clothing is non-taxable in Minnesota"
         }
       ],
       "data_version": "MN-SST-2026Q2APR15",
       "disclaimer": "Calculation only; not legal or tax advice."
     }
```

OpenAPI 3.x schema auto-generated by the framework (FastAPI does
this for free; Hono + zod-to-openapi for Node; swaggo for Go).

### 6. Auth — both modes from day one

- **Open mode** (default): no auth, IP-based rate limiting (default
  60 req/min per IP). Suitable for self-hosters' internal use.
- **API-key mode** (optional flag): `X-API-Key` header required;
  per-key rate limits + usage tracking. Suitable for shared
  deployments.

Toggle via env var `OPENSALESTAX_AUTH_MODE=open|api_key`.

### 7. Docker + Compose

- `Dockerfile` for the API server
- `docker-compose.yml` for local dev shipping **two database
  profiles** so contributors can run against either engine:
  - `docker compose --profile postgres up` → API + PostgreSQL 15
  - `docker compose --profile mariadb up` → API + MariaDB 11
  - Default profile (no flag) brings up PostgreSQL since it's the
    most common Python web stack
- No PostGIS in Phase 1; ZIP-based lookup is sufficient
- Image published to GitHub Container Registry
- Env-var-driven configuration (12-factor):
  `OPENSALESTAX_DATABASE_URL=postgresql+asyncpg://...` or
  `mysql+asyncmy://...`

### 8. CI on GitHub Actions

- Run linter + formatter check on every PR (ruff)
- **DCO sign-off check on every commit in every PR** (per
  constitution §14)
- Run tests on every PR — **matrix across both PostgreSQL and
  MariaDB** (per decision 03)
- Build Docker image on every PR; publish on push to main
- Conformance tests against SST gold-standard fixtures (when found)

### 9. Documentation

- `README.md` — install + run instructions
- `docs/quickstart.md` — 5-minute getting started
- `docs/api.md` — full API reference (auto-generated from OpenAPI)
- `docs/state-modules.md` — how to write a new state module (the
  community-contributor entry point)
- `docs/data-refresh.md` — how to update SST data quarterly
- `docs/disclaimer.md` — legal / tax-advice disclaimer (constitution §13)

## Out of scope (defer to later phases)

- **Address-level boundary resolution via PostGIS** — Phase 4
- **Geocoding** (address → lat/lon) — caller's responsibility for
  Phase 1; Phase 4 if we add bundled Nominatim
- **Returns filing** — out of scope entirely (TaxCloud's space)
- **Exemption-certificate validation** — Phase 5
- **Sales tax holidays** — Phase 5
- **Use tax calculation** — Phase 5
- **Item-category taxonomy** beyond a basic 6-7 categories — Phase 5
- **Hosted SaaS layer** — out of scope for OSS launch
- **Client SDKs** in other languages — Phase 7

## Acceptance criteria

- [ ] Repo public on GitHub under Apache 2.0
- [ ] LICENSE, NOTICE, CONTRIBUTING.md, MAINTAINERS.md present
      at repo root
- [ ] All Python source files carry SPDX header
      (`# SPDX-License-Identifier: Apache-2.0`)
- [ ] DCO sign-off check enforced in CI; passing on all PRs
- [ ] `docker compose --profile postgres up` brings the API
      online in <60 seconds
- [ ] `docker compose --profile mariadb up` brings the API online
      in <60 seconds (acceptance includes BOTH engines working)
- [ ] `curl localhost:8080/v1/health` returns 200 with version
- [ ] `curl localhost:8080/v1/states` lists 52 states with MN, WI,
      AK, DE, MT, NH, OR marked `supported: true`
- [ ] `curl localhost:8080/v1/rates?zip=55401` returns Minnesota
      jurisdictions with correct rate
- [ ] `curl localhost:8080/v1/rates?zip=53202` returns Wisconsin
      (Milwaukee) jurisdictions with correct rate
- [ ] `POST /v1/calculate` with a clothing line item in MN returns
      0% tax on that line; same in WI returns the WI rate
- [ ] CLI: `opensalestax data fetch --state MN --version <current>`
      successfully downloads + parses + inserts MN's current SST data
- [ ] All tests pass against PostgreSQL AND MariaDB
- [ ] CI green on every PR (lint + DCO + tests against both engines)
- [ ] OpenAPI spec accessible at `/v1/openapi.json`
- [ ] README's quickstart works on a fresh machine

## Key risks for Phase 1

1. **SST file format unknowns** — we don't have the full schema yet.
   Risk: parser harder than expected. Mitigation: download a sample
   and document the format as the very first task.
2. **Boundary resolution accuracy** — ZIP-only is a known
   approximation. Risk: some calls return wrong jurisdiction at ZIP
   boundaries. Mitigation: ship Phase 1 with explicit "ZIP-level
   precision" caveat in API docs; PostGIS / address-level is Phase 4.
3. **SST conformance test fixtures** — we believe these exist but
   haven't located them. Risk: no gold-standard validation. Mitigation:
   spot-check against MN DOR and WI DOR official lookup tools manually.
4. **Stack-pick deferred** — until Eric picks, we can't write code.
   Mitigation: ask early in the bootstrap session.

## Suggested task ordering (for tasks.md)

When the bootstrap session writes the tasks.md, suggested order:

1. Stack pick + scaffold (1 session)
2. Database schema + migrations (1 session)
3. SST file format documentation (download samples, document) (0.5 session)
4. MN state module + basic data load (1 session)
5. WI state module (faster — pattern established) (0.5 session)
6. No-tax state module (trivial) (0.25 session)
7. API endpoints (4) + OpenAPI auto-gen (1 session)
8. Auth modes + rate limiting (0.5 session)
9. Docker + docker-compose (0.5 session)
10. CI (GitHub Actions) (0.5 session)
11. Documentation pass (1 session)
12. Acceptance-criteria walkthrough (0.25 session)

Total: ~7 sessions for Python+FastAPI. Could compress to 4-5 if any
single session is allowed to be long.

## When Phase 1 is done

1. Tag `v0.1.0` release.
2. Write blog post / Show-HN post / send to relevant tax-tech communities.
3. Move to Phase 2: bring the remaining 22 SST states online using the
   MN/WI parser pattern.
4. Update `current-state.md` to reflect Phase 1 ship.
5. Open `phase-2-sst-rollout/spec.md`.
