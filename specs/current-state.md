# OpenSalesTax — Current State

**Last updated:** 2026-05-03
**Status:** Phase 1 Section A complete (scaffold landed). DB layer (Section B) is the next concrete work.

**2026-05-02 update:** Added `specs/research/sovos-state-summary.md`
+ `.tsv` — captured Sovos's state-by-state guide (50 states + DC) as
a cross-reference for nexus thresholds and base rates. Reference
only, not an ingestible data source per constitution §3.

**2026-05-02 second update:** Stack, license, and database
decisions all made. See `specs/decisions/`.

- **Language/framework:** ✅ Python 3.11+ + FastAPI (decision 01)
- **License:** ✅ Apache 2.0 (with DCO sign-off, SPDX headers,
  no CLA, NOTICE stub) (decision 02)
- **Patent posture:** ✅ acknowledged in constitution §2 with
  mitigation rules
- **Database:** ✅ dual MariaDB + PostgreSQL via SQLAlchemy 2.x +
  Alembic; PostGIS recommended for Phase 4+ (decision 03)

**2026-05-03 update:** Phase 1 re-scoped per Eric's "as many states
as we can from the start" priority. Tier 1 = MN, WI (full
taxability matrix). Tier 2 = the other 22 SST states (rate-only
via SST data, default taxability). No-tax states unchanged.
Section G2 added to `tasks.md` for the rapid SST rollout.

**2026-05-03 third update:** Branding settled. GitHub repo will be
**`ejosterberg/open-sales-tax`** (not `sales_tax_api_service`).
Domains **`opensalestax.org`** (intended for the OSS project site)
and **`opensalestax.com`** (reserved for the eventual hosted SaaS)
both registered by Eric. The Python package name stays
`opensalestax` (per PEP 8). Local clone path on Eric's machine
remains `sales_tax_api_service\` — the local directory doesn't
have to match the repo name and renaming would break in-flight
work.

**2026-05-03 second update:** Phase 1 Section A (scaffolding)
shipped. Repo now has:

- pyproject.toml (Poetry-managed); ruff/pytest/mypy/coverage
  configured
- src/opensalestax/ package skeleton with SPDX headers on every file
- LICENSE / NOTICE / CONTRIBUTING / MAINTAINERS / USERS
- .pre-commit-config.yaml (ruff + hygiene hooks)
- .github/workflows/ci.yml — lint + DCO check + test matrix
  across PostgreSQL and MariaDB
- tests/test_smoke.py — minimal import + version check
- .gitignore tightened (no longer blocks shipped CSV/ZIP fixtures)

Eric needs to install Python 3.11+ and Poetry locally before
`poetry install` can run; CI doesn't depend on that. Section B
(database layer) is the next concrete work.

## What exists

| Artifact | Status |
|---|---|
| Project README | ✅ |
| CLAUDE.md (per-session context) | ✅ |
| .gitignore | ✅ |
| `specs/constitution.md` | ✅ |
| `specs/current-state.md` (this file) | ✅ |
| `specs/handoff.md` | ✅ |
| `specs/research/data-sources.md` | ✅ |
| `specs/research/prior-art.md` | ✅ |
| `specs/research/state-coverage.md` | ✅ |
| `specs/phase-1-foundation/spec.md` | ✅ |
| `specs/decisions/01-language-framework.md` | ✅ Python 3.11+ + FastAPI |
| `specs/decisions/02-license.md` | ✅ Apache 2.0 + DCO + SPDX |
| `specs/decisions/03-database.md` | ✅ Dual MariaDB + PostgreSQL via SQLAlchemy 2.x |
| `LICENSE` (Apache 2.0 full text) | ✅ |
| `NOTICE` (stub) | ✅ |
| `CONTRIBUTING.md` (with DCO instructions) | ✅ |
| `MAINTAINERS.md` (Eric initial; tier 1/2 state slots) | ✅ |
| `USERS.md` (deployer registry stub) | ✅ |
| `pyproject.toml` (Poetry; deps + ruff/pytest/mypy config) | ✅ |
| `.python-version` (3.11) | ✅ |
| `.pre-commit-config.yaml` (ruff, hygiene hooks) | ✅ |
| `.github/workflows/ci.yml` (lint + DCO + dual-engine test matrix) | ✅ |
| `src/opensalestax/` package skeleton (10 modules, all SPDX-headered) | ✅ |
| `tests/test_smoke.py` (verifies imports + version) | ✅ |
| Git repo initialized | ✅ already initialized; commits accumulating |
| GitHub remote created | ❌ — pending Eric's per-deploy push approval |
| `poetry install` ever run | ❌ — pending Eric installing Python 3.11+ and Poetry locally |
| Database layer (Section B) | ❌ — next concrete work |

## What's been decided

- **Project name:** OpenSalesTax (working title; rename if needed before public launch)
- **Mission:** free, self-hostable, OSS sales tax calculation API
- **License:** ✅ Apache 2.0 (decision 02)
- **Contributor agreement:** ✅ DCO sign-off, no CLA (decision 02)
- **Per-file headers:** ✅ SPDX (`# SPDX-License-Identifier: Apache-2.0`)
- **Patent posture:** ✅ acknowledged + mitigation rules (constitution §2)
- **Language/framework:** ✅ Python 3.11+ + FastAPI (decision 01)
- **Distribution model:** primary self-hostable Docker; optional future SaaS
- **Core architecture:** per-state contributor modules with common interface
- **Data sources:** SST quarterly files + state DOR public data + TIGER/Line boundary data
- **Database (proposed, pending confirmation):** dual MariaDB + PostgreSQL via SQLAlchemy 2.x; PostGIS recommended for Phase 4+ address-level production deployments

## What's NOT decided (smaller items, can punt to implementation)

- **Initial state coverage** — phase-1-foundation/spec.md proposes 2 SST states (MN + WI as a pair: Eric's home + Wisconsin's contrasting clothing-tax rule). Could be expanded.
- **Geocoding strategy** — option A: rely on caller-supplied lat/lon; option B: bundle a geocoder (Nominatim/Pelias). Phase 1 should punt.
- **Auth model for the API** — option A: open / no auth (rate-limited only); option B: API keys. Phase 1 should ship both.
- **Hosted SaaS business model** — out of scope for v1; mentioned only.

## Phases (proposed)

| # | Phase | Status |
|---|---|---|
| 1 | Foundation: language scaffold + DB schema + 2 SST states + 4 API endpoints + Docker + CI | 📝 spec'd |
| 2 | All 24 SST states + admin / data-refresh CLI | ⏭️ planned |
| 3 | First non-SST state (CA — high impact, high difficulty) + state-maintainer onboarding docs | ⏭️ planned |
| 4 | Boundary-resolution improvements: address-level (PostGIS) + ZIP+4 fallback | ⏭️ planned |
| 5 | Taxability matrix v1 (item categories + state-specific rules) | ⏭️ planned |
| 6 | Performance + caching + horizontal scale | ⏭️ planned |
| 7 | Client SDKs: Python, JS/TS, PHP (for SC Books) | ⏭️ planned |
| 8 | Hosted SaaS layer (multi-tenant, billing, dashboards) — optional, post-OSS-launch | ⏭️ optional |

## Risk register

- **Upstream data format drift** — SST has been stable since 2005, but a format
  change would require all state modules to adapt. Mitigation: per-state
  parsers; format change in one doesn't break others.
- **Contributor recruitment** — the "per-state volunteer" model only works if
  volunteers actually sign up. Mitigation: ship 2-3 states ourselves to prove
  the model; recruit at OSS conferences + state CPA associations.
- **Scope creep into nexus determination** — strong temptation to answer "do I
  owe tax in this state?" alongside "what's the rate?" Resist; nexus is a
  separate project. Constitution §13 forbids.
- **Disclaimer adequacy** — IRS / state DORs could in theory complain about
  software giving "tax advice." Mitigation: clear disclaimers in every API
  response + docs; explicit "calculation only, not advice."

## Notes for next session

Section A (scaffolding) is done. Next concrete work is **Section B
(database layer)** per `specs/phase-1-foundation/tasks.md`:

1. Tasks 06–10: settings module, SQLAlchemy declarative models,
   async session factory, Alembic init + first migration,
   conftest.py with dual-engine fixture.
2. After Section B: Section C (core engine + state-module
   pattern + the no_tax module).
3. Then Section D (SST data ingestion) and E (Minnesota end-to-end).
4. **Pause before pushing to GitHub** — the remote needs Eric's
   per-deploy approval per handoff standing rules.

Eric needs to install Python 3.11+ and Poetry locally before
`poetry install` can run; the work in Section B can proceed
without it (Claude writes code; Eric runs `poetry install` when
ready). CI on GitHub doesn't need anything local.
