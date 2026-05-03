# OpenSalesTax — Current State

**Last updated:** 2026-05-02
**Status:** Pre-development. Specs + research only. No code.

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
| Stack chosen (Python? Node? Go?) | ❌ pending Eric's call |
| License file (LICENSE) | ❌ Apache 2.0 recommended; pending owner sign-off |
| Git repo initialized | ❌ — left for the bootstrap session to do after Eric reviews |
| GitHub remote created | ❌ — left for the bootstrap session |
| Any code at all | ❌ |

## What's been decided

- **Project name:** OpenSalesTax (working title; rename if needed before public launch)
- **Mission:** free, self-hostable, OSS sales tax calculation API
- **License recommendation:** Apache 2.0 (pending Eric sign-off)
- **Distribution model:** primary self-hostable Docker; optional future SaaS
- **Core architecture:** per-state contributor modules with common interface
- **Data sources:** SST quarterly files + state DOR public data + TIGER/Line boundary data
- **Database:** PostgreSQL 15+ with PostGIS for geometry

## What's NOT decided (open for the bootstrap session)

- **Implementation language / framework** — Python+FastAPI recommended; Eric to confirm
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

- Eric will start a new Claude Code session in this directory to bootstrap.
- That session should: (1) propose the stack pick to Eric, (2) on approval,
  scaffold the chosen language, (3) initialize git + GitHub repo, (4) start
  Phase 1.
- The bootstrap session does NOT need to fetch SST data or implement any
  state module — Phase 1's `spec.md` is the right starting point.
