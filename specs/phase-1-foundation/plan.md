# Phase 1 — Implementation Plan

> The HOW for Phase 1. Reads alongside `spec.md` (the WHAT) and
> `tasks.md` (the EXECUTION ORDER).

**Status:** drafted 2026-05-02 alongside decisions 01–03.
Not yet implemented.

## Architecture overview

```
┌──────────────────────────────────────────────────────────┐
│  Client (curl, SC Books, future SDK)                     │
└──────────────────────────┬───────────────────────────────┘
                           │  HTTPS / JSON
                           ▼
┌──────────────────────────────────────────────────────────┐
│  FastAPI app  (uvicorn worker, async)                    │
│  ┌────────────────────────────────────────────────────┐  │
│  │  api/v1/  — versioned route handlers               │  │
│  │    health.py  states.py  rates.py  calculate.py    │  │
│  └────────────┬───────────────────────────────────────┘  │
│               │ Pydantic request/response models          │
│  ┌────────────▼───────────────────────────────────────┐  │
│  │  core/  — engine: lookup → resolve → tax           │  │
│  │    lookup.py    (zip → jurisdictions)              │  │
│  │    resolve.py   (jurisdictions → applicable rates) │  │
│  │    calculate.py (rates × line items → tax)         │  │
│  └────────────┬───────────────────────────────────────┘  │
│               │                                           │
│  ┌────────────▼───────────────────────────────────────┐  │
│  │  states/  — per-state modules implementing         │  │
│  │            StateModule protocol                    │  │
│  │    minnesota.py   wisconsin.py   no_tax.py         │  │
│  └────────────┬───────────────────────────────────────┘  │
│               │                                           │
│  ┌────────────▼───────────────────────────────────────┐  │
│  │  db/  — SQLAlchemy 2.x async ORM + Alembic        │  │
│  │    models.py  session.py  migrations/              │  │
│  └────────────┬───────────────────────────────────────┘  │
└───────────────┼──────────────────────────────────────────┘
                │
        ┌───────┴────────┐
        ▼                ▼
   ┌────────┐      ┌─────────┐
   │ Postgres│      │ MariaDB │   ← either, via DATABASE_URL
   │ 15+    │      │ 11+     │
   └────────┘      └─────────┘
```

## File / module layout (`src` layout)

```
sales_tax_api_service/
├── pyproject.toml                  Poetry, ruff, pytest config
├── poetry.lock
├── .python-version                 3.11
├── .pre-commit-config.yaml
├── .gitignore                      (already exists)
├── LICENSE                         Apache 2.0
├── NOTICE                          stub
├── README.md                       (exists; quickstart updated post-scaffold)
├── CONTRIBUTING.md                 incl. DCO instructions
├── MAINTAINERS.md                  Eric initial
├── USERS.md                        stub for deployer registry
├── CLAUDE.md                       (exists)
├── docker-compose.yml              two profiles: postgres, mariadb
├── Dockerfile                      multi-stage Python 3.11 slim
│
├── .github/
│   └── workflows/
│       ├── ci.yml                  lint + DCO + test matrix
│       └── docker.yml              build + publish to GHCR
│
├── src/
│   └── opensalestax/
│       ├── __init__.py             version constant
│       ├── __main__.py             allows `python -m opensalestax`
│       ├── settings.py             pydantic-settings; DATABASE_URL etc.
│       ├── app.py                  FastAPI factory
│       │
│       ├── api/
│       │   ├── __init__.py
│       │   └── v1/
│       │       ├── __init__.py     v1 router
│       │       ├── health.py
│       │       ├── states.py
│       │       ├── rates.py
│       │       └── calculate.py
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── lookup.py           zip → jurisdictions
│       │   ├── resolve.py          jurisdictions → applicable rates
│       │   ├── calculate.py        rates × line items → tax
│       │   └── disclaimer.py       constitution §13 boilerplate
│       │
│       ├── states/
│       │   ├── __init__.py         registry of available state modules
│       │   ├── protocol.py         StateModule Protocol definition
│       │   ├── minnesota.py
│       │   ├── wisconsin.py
│       │   └── no_tax.py           shared by AK, DE, MT, NH, OR
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── models.py           SQLAlchemy declarative
│       │   ├── session.py          async engine + sessionmaker factory
│       │   └── migrations/         Alembic env
│       │       ├── env.py
│       │       ├── script.py.mako
│       │       └── versions/
│       │           └── 0001_initial.py
│       │
│       ├── data/
│       │   ├── __init__.py
│       │   ├── sst.py              SST file fetcher + parser shell
│       │   └── fixtures/           known-good test data per state
│       │       ├── mn/
│       │       └── wi/
│       │
│       └── cli/
│           ├── __init__.py
│           └── main.py             `opensalestax` entry point (Typer)
│
└── tests/
    ├── conftest.py                 async session, both-engines fixture
    ├── unit/
    │   ├── test_lookup.py
    │   ├── test_calculate.py
    │   └── test_state_minnesota.py
    │       test_state_wisconsin.py
    │       test_state_no_tax.py
    └── integration/
        ├── test_api_health.py
        ├── test_api_states.py
        ├── test_api_rates.py
        └── test_api_calculate.py
```

## Tooling choices

| Concern | Choice | Why |
|---|---|---|
| Dependency mgmt | **Poetry** | Mature, lockfile, virtualenv mgmt; specified in decision 01 |
| Lint + format | **ruff** | Single tool, fast, replaces flake8+isort+black; widely adopted |
| Type checking | **mypy** (basic mode) | Pydantic models do most of the heavy lifting; mypy as belt + suspenders |
| Tests | **pytest** + `pytest-asyncio` + `pytest-postgresql` + `pytest-mysql` | Standard; per-engine fixtures via container or service |
| HTTP client (tests) | **httpx** AsyncClient | First-party FastAPI test pattern |
| Pre-commit | **pre-commit** | Standard; ruff + DCO local check |
| Async runtime | **uvicorn** with `--workers` for prod | Default FastAPI choice; battle-tested |
| Settings | **pydantic-settings** | First-party Pydantic; env-var driven (12-factor) |
| CLI | **Typer** | Same Pydantic ecosystem; auto-generates help |

## Dual-engine plumbing

The architectural keystone from decision 03: **dialect difference
lives in SQLAlchemy + Alembic, never in business logic.**

Concretely:

- `db/session.py` reads `OPENSALESTAX_DATABASE_URL` and creates the
  appropriate `AsyncEngine`. No engine-aware code beyond this point.
- `db/models.py` uses portable types only:
  - `sqlalchemy.types.JSON` (maps to JSONB on PG, JSON on MariaDB)
  - `sqlalchemy.types.Numeric` for rate percentages
  - `sqlalchemy.Integer` with `autoincrement=True` (dialect-correct
    behavior is automatic)
  - `sqlalchemy.types.DateTime(timezone=True)` for timestamps
- Alembic migrations use `op.execute()` only when SQLAlchemy core
  can't express the change portably; document any such case.
- `tests/conftest.py` parameterizes session-scoped engine fixtures
  so each test runs against both engines unless explicitly marked
  otherwise.
- CI matrix in `.github/workflows/ci.yml`:
  ```yaml
  strategy:
    matrix:
      db: [postgres, mariadb]
  services:
    postgres: image: postgres:15
    mariadb:  image: mariadb:11
  ```

## State module pattern (the architectural keystone)

Every state is a Python module that conforms to a Protocol. The
core engine never knows or cares about specific states.

```python
# src/opensalestax/states/protocol.py
from typing import Protocol, Iterable, Optional
from datetime import date
from pathlib import Path

class StateModule(Protocol):
    state_abbrev: str          # 'MN'
    state_name: str            # 'Minnesota'
    sst_member: bool
    has_sales_tax: bool

    def parse_rates(self, source_file: Path, version_label: str) -> Iterable["RateRow"]:
        """Read upstream rate file, yield normalized rate rows."""

    def parse_boundaries(self, source_file: Path, version_label: str) -> Iterable["BoundaryRow"]:
        """Read upstream boundary file, yield normalized boundary rows."""

    def taxability_for(self, item_category: str, effective_date: date) -> Optional["TaxabilityRule"]:
        """Return per-category rule, or None if unknown."""

    def special_cases(self) -> Iterable["SpecialCase"]:
        """State-specific rules the engine consults during calculation."""
```

Phase 1 ships three concrete implementations:
- `minnesota.py` — full SST parser; clothing non-taxable
- `wisconsin.py` — full SST parser; clothing taxable
- `no_tax.py` — generic zero-rate; reused by AK, DE, MT, NH, OR

State modules **do not** import from `core/` or `api/` — the
dependency arrow points only one way: api → core → states → db.

## API surface (Phase 1)

Per `spec.md` §5:

- `GET /v1/health` — version + DB connectivity
- `GET /v1/states` — coverage list (52 entries)
- `GET /v1/rates?zip=...&zip4=...` — jurisdiction rates for an address
- `POST /v1/calculate` — full tax calc on line items

OpenAPI spec auto-generated by FastAPI at `/v1/openapi.json` and
interactive docs at `/v1/docs` (Swagger UI) and `/v1/redoc`.

Every response includes:
- `data_version` (e.g., `"MN-SST-2026Q2APR15"`) for reproducibility
- `disclaimer` field for non-health/non-states endpoints
  (constitution §13)

## Auth + rate limiting

Phase 1 ships both modes from day one (per spec §6):
- `OPENSALESTAX_AUTH_MODE=open` (default) — IP-based rate limit
  (60 req/min per IP via `slowapi` or similar)
- `OPENSALESTAX_AUTH_MODE=api_key` — `X-API-Key` header required;
  per-key rate limits

Storage for API keys: same DB; `api_keys` table added in a later
migration if api_key mode is enabled.

## Disclaimers (constitution §13)

Every API response that returns a tax calculation includes:
```json
{
  "disclaimer": "Calculation only; not legal or tax advice."
}
```

Plus a section in API docs and the README, per spec §9.

## Out of scope for Phase 1 (deferred)

- Address-level GIS resolution (Phase 4)
- Bundled geocoder (caller supplies lat/lon if needed)
- Returns filing
- Exemption-cert validation
- Sales-tax holidays
- Use-tax calc
- Item-category taxonomy beyond 6–7 basic categories
- Hosted SaaS layer
- Client SDKs in other languages (Phase 7)

## Risks specific to Phase 1

1. **SST file format unknowns** — addressed by Task 5 below
   (download a sample and document before writing parsers).
2. **Boundary resolution accuracy** — ZIP-only Phase 1; documented
   caveat in API docs.
3. **SST conformance test fixtures** — find them; if not found,
   spot-check against MN DOR + WI DOR official lookup tools.
4. **Dual-engine schema gotchas** — addressed by running every
   migration on both engines locally before commit, plus CI matrix.

## Definition of done for Phase 1

All acceptance criteria in `spec.md` pass. Specifically:
- `docker compose --profile postgres up` AND `--profile mariadb up`
  both bring online a working API in <60 seconds
- All four endpoints return correct data for MN + WI + the 5 no-tax
  states
- DCO check green on all merged commits
- README quickstart works on a fresh machine
- Tagged `v0.1.0` release on GitHub
