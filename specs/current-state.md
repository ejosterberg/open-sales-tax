# OpenSalesTax — Current State

**Last updated:** 2026-05-02
**Status:** Pre-development. Specs + research only. No code.

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
  mitigation rules (no reverse-engineering of commercial APIs;
  no naming features after commercial products; vet contributions
  from current/former commercial-vendor employees)
- **Database:** ✅ dual MariaDB + PostgreSQL via SQLAlchemy 2.x +
  Alembic; PostGIS recommended for Phase 4+ address-level
  production deployments (decision 03). Constitution §10 and
  Phase 1 spec schema updated for portability.

Bootstrap is now unblocked. Next session writes Phase 1 plan +
tasks, then scaffolds.

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
| License file (LICENSE) | ❌ — bootstrap session creates after DB decision |
| NOTICE file | ❌ — bootstrap session creates as empty stub |
| CONTRIBUTING.md (with DCO instructions) | ❌ — bootstrap session creates |
| MAINTAINERS.md | ❌ — bootstrap session creates with Eric as initial |
| DCO CI check | ❌ — bootstrap session adds GitHub Actions workflow |
| Git repo initialized | ❌ — bootstrap session does after DB decision |
| GitHub remote created | ❌ — bootstrap session does after DB decision |
| Any code at all | ❌ |

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

All three foundational decisions are settled (decisions 01–03).
Bootstrap is unblocked. The next session should:

1. Read `specs/phase-1-foundation/plan.md` and `tasks.md` (drafted
   2026-05-02 alongside the decisions).
2. Execute the scaffolding tasks: Poetry + ruff + pytest +
   pre-commit, LICENSE / NOTICE / CONTRIBUTING / MAINTAINERS,
   DCO CI check, dual-engine docker-compose.
3. Pause for Eric before pushing to GitHub (the remote needs
   his per-deploy approval per handoff standing rules).
4. Begin Phase 1 implementation per the task list.

The bootstrap session does NOT need to fetch SST data or
implement any state module on day one — scaffolding + initial
schema is the right starting point.
