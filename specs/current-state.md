# OpenSalesTax — Current State

**Last updated:** 2026-05-03
**Status:** **🎉 Phase 1 shipped as v0.1.0.** API live, 29 states
represented (7 tier 1 + 22 tier 2), 200 unit tests passing,
SonarQube clean (0/0/0/0, all-A ratings), CI green on PostgreSQL
and MariaDB. Live at
[github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax).

## Phase 1 deliverables

| # | Section | Status | Tests | Notes |
|---|---|---|---:|---|
| A | Scaffolding (Poetry, ruff, mypy, pre-commit, CI) | ✅ | n/a | DCO-enforced PR check; matrix CI on both engines |
| B | DB layer (settings, models, sessions, Alembic) | ✅ | 8 unit | First migration hand-written for portability |
| C | Core engine + state Protocol + no_tax module | ✅ | 44 unit + 5 integration | Decimal-only currency math, 4dp rounding |
| D | SST data ingestion (research + fetcher + parser) | ✅ | 19 unit | Real MN rate + boundary fixtures bundled |
| E | Minnesota module (tier 1) | ✅ | 15 unit | 6.875% state base, 6 taxability rules |
| F | Wisconsin module (tier 1) + dual-sentinel parser | ✅ | 13 unit | 5.0% state base, contrasting clothing-taxable rule |
| G | v1 API surface (4 endpoints) | ✅ | 12 integration | OpenAPI 3.x at /v1/openapi.json |
| G2 | 22 tier-2 SST states via SstStateModule base | ✅ | 26 unit | AR, GA, IA, IN, KS, KY, MI, NE, NV, NJ, NC, ND, OH, OK, RI, SD, TN, UT, VT, WA, WV, WY |
| H | Rate limiting + CLI + Docker + 5 docs files | ✅ | n/a | uvicorn factory mode; both DB profiles in compose |
| I | Acceptance walkthrough + v0.1.0 release | ✅ | n/a | See `phase-1-foundation/acceptance-walkthrough.md` |

## What v0.1.0 delivers

- **A working FastAPI service** with 4 endpoints, OpenAPI docs,
  per-IP rate limiting, dual-engine (PostgreSQL + MariaDB) support
- **29 US states represented** in code (5 no-tax + 2 tier-1 SST +
  22 tier-2 SST). All 52 jurisdictions enumerable via `/v1/states`.
- **Real SST data parsing** validated against MN + WI's actual
  upstream files (bundled as test fixtures for reproducibility)
- **200 passing unit tests + 17 integration tests** (CI matrix
  exercises both engines on every PR)
- **SonarQube clean:** 0 bugs, 0 vulnerabilities, 0 code smells,
  0 security hotspots, all-A ratings on 1822 LOC
- **Honest documentation:** README quickstart + 5 docs files;
  every defer is called out (no overpromising)

## Honest deferrals (v0.2 or later)

Per `phase-1-foundation/acceptance-walkthrough.md`:

- **`opensalestax data load` + `data activate` CLI** -- the
  fetcher works; the loader pipeline is v0.2's headline item
- **API-key auth mode** -- plumbed in settings, middleware comes in v0.2
- **First non-SST tier-1 state** (CA recommended) -- v0.2
- **Per-state address-fixture sweep** for the 22 tier-2 modules --
  v0.2 / per-state maintainer onboarding
- **Address-level boundary resolution via PostGIS** -- Phase 4
- **Sales-tax holidays + exemption certificates** -- Phase 5
- **Canadian sales tax** -- explicitly out of scope for v1; see
  `specs/research/canada-sources.md` for future-scope research

## Decisions locked

| # | Decision | Status |
|---|---|---|
| 01 | Language: Python 3.11+ + FastAPI | ✅ |
| 02 | License: Apache 2.0 + DCO + SPDX (no CLA, NOTICE stub) | ✅ |
| 03 | Database: dual MariaDB + PostgreSQL via SQLAlchemy 2.x | ✅ |
| -- | Patent posture: acknowledged in constitution §2 | ✅ |
| -- | Branding: GitHub repo `open-sales-tax`, package `opensalestax`, domains `opensalestax.org` + `.com` (Eric owns) | ✅ |
| -- | Phase 1 coverage tiers: tier 1/2/0 with MN+WI tier 1, 22 SST tier 2, no_tax tier 1 | ✅ |

## Reference artifacts

| Artifact | Status |
|---|---|
| `LICENSE` (Apache 2.0) | ✅ |
| `NOTICE` | ✅ |
| `CONTRIBUTING.md` (with DCO instructions) | ✅ |
| `MAINTAINERS.md` (Eric initial; per-state slots) | ✅ |
| `USERS.md` (deployer registry stub) | ✅ |
| `pyproject.toml` (Poetry; deps + ruff/pytest/mypy) | ✅ |
| `Dockerfile` + `docker-compose.yml` | ✅ |
| `.github/workflows/ci.yml` | ✅ |
| `sonar-project.properties` | ✅ |
| `README.md` (5-min quickstart + coverage table) | ✅ |
| `docs/quickstart.md` `docs/api.md` `docs/state-modules.md` `docs/data-refresh.md` `docs/disclaimer.md` | ✅ |
| `specs/decisions/01-language-framework.md` `02-license.md` `03-database.md` | ✅ |
| `specs/research/sovos-state-summary.md` `sst-file-format.md` `canada-sources.md` (+ original 3) | ✅ |

## Notes for next session

Phase 1 is shipped. Next session should open
`specs/phase-2-loader/spec.md` (or similar) and prioritize:

1. **Data-load CLI** (`opensalestax data load --state MN
   --version MN-SST-2026Q2FEB18`) that uses the existing fetcher
   + parsers + state modules and writes to the DB.
2. **Activate flag** for switching the live data version per
   state (so a tenant can pin to 2026Q2 even after 2026Q3 lands).
3. **API-key auth mode** + `api_keys` table + key-management CLI.
4. First non-SST tier-1 state (California is the highest-impact
   target).

See `phase-1-foundation/acceptance-walkthrough.md` "What v0.2
should ship next" for the full priority order.
