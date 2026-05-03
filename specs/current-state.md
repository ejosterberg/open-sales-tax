# OpenSalesTax — Current State

**Last updated:** 2026-05-03
**Status:** **v0.7.0 shipped.** Phase 6 Batch B — 5 new tier-1
states added in parallel by 5 sub-agents (CO, ID, LA, MO, MS).
508 unit tests + 38 integration tests, CI matrix green on
PostgreSQL + MariaDB, ruff + mypy clean.

**v0.6 / Phase 6 buildout in progress, started 2026-05-03;
Batches A + B shipped same day.** Two agents (CO, LA) flagged
that proper home-rule / parish modeling needs a
`SubJurisdiction` Protocol extension — captured in
`specs/decisions/04-colorado-home-rule.md` and
`specs/decisions/05-louisiana-parishes.md` for v1.0+ design.

Live at [github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax).

## Live deployment

| Field | Value |
|---|---|
| **Hostname** | `opensalestax-01` (SSH alias on Eric's box) |
| **IP** | `10.32.161.126` (DHCP from LAN) |
| **Proxmox VMID** | 906 (on `pmvm1`) |
| **Specs** | 4 vCPU / 8 GB RAM / 80 GB disk, Debian 13 |
| **Provisioned** | 2026-05-03 |
| **Stack** | Docker Compose (`postgres` profile) — API + PostgreSQL 15 |
| **API base URL** | `http://10.32.161.126:8080` |
| **Health check** | `curl http://10.32.161.126:8080/v1/health` |
| **Loaded data** | 11 of 16 tier-1 states (9 self-seeded at v0.6 + MN/WI at SST 2026Q2FEB18); 5 no-tax states (AK/DE/MT/NH/OR) registered without DataVersion rows |

Dockerfile patched in commit `a8712c7` to fix `PYTHONPATH` so alembic + the CLI find the `opensalestax` package without a wheel install. Use `python -m opensalestax ...` rather than the bare `opensalestax` script (entry-point not installed in the runtime image).

## Release ladder

| Tag | Date | Headline |
|---|---|---|
| [v0.1.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.1.0) | 2026-05-03 | Foundation: 4 endpoints, 29 states (7 tier-1 + 22 tier-2), dual DB, SST data parsing |
| [v0.2.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.2.0) | 2026-05-03 | Data-load CLI, API-key auth, California |
| [v0.3.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.3.0) | 2026-05-03 | TX, NY, FL tier-1 |
| [v0.4.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.4.0) | 2026-05-03 | PA, IL, MD, MA, AZ tier-1 |
| [v0.5.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.5.0) | 2026-05-03 | Sales-tax holidays support |
| [v0.6.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.6.0) | 2026-05-03 | CT, DC, SC, VA tier-1 (Batch A — 4 parallel agents) |
| [v0.7.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.7.0) | 2026-05-03 | CO, ID, LA, MO, MS tier-1 (Batch B — 5 parallel agents) |
| [v0.7.1](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.7.1) | 2026-05-03 | Per-jurisdiction tax dollar amount + OpenAPI examples + README "try it" recipes |
| [v0.8.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.8.0) | 2026-05-03 | AR, GA, IA, IN tier-1 (Phase 7 Batch P1 — 4 SST tier-2→tier-1 promotions) |
| [v0.9.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.9.0) | 2026-05-03 | KS, KY, MI, NE, NV tier-1 (Phase 7 Batch P2 — 5 more SST promotions) |
| [v0.10.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.10.0) | 2026-05-03 | NJ, NC, ND, OH, OK tier-1 (Phase 7 Batch P3 — 5 more SST promotions) |
| [v0.11.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.11.0) | 2026-05-03 | RI, SD, TN, UT, VT, WA, WV, WY tier-1 (Phase 7 Batch P4 — **final SST batch; all 22 SST members now tier-1**) |

## Coverage (after v0.5)

| Tier | Count | States |
|---|---:|---|
| **Tier 1** -- fully maintained | **47** | All 50 states except AL, HI, NM (and DC; PR remains tier-0 territorial regime) |
| **Tier 2** -- rate-only via SST data | **0** | (Phase 7 complete — every SST member promoted to tier-1) |
| Unsupported | **5** | AL, HI, NM, PR, + 1 |

**47 of 52 jurisdictions are fully tier-1 maintained.** Phase 7 closed v0.11.0 — every SST member is now tier-1.

## Feature ladder

| Feature | Phase | Status |
|---|---|---|
| Per-state contributor Protocol + registry | Phase 1 | ✅ |
| ZIP+4 jurisdiction lookup | Phase 1 | ✅ |
| Multi-jurisdiction rate stack | Phase 1 | ✅ |
| Effective-dated rates with active-row resolution | Phase 1 | ✅ |
| Per-state taxability matrix | Phase 1 | ✅ |
| 4-endpoint v1 API (health, states, rates, calculate) | Phase 1 | ✅ |
| OpenAPI 3.x auto-gen + Swagger UI | Phase 1 | ✅ |
| Per-IP rate limiting | Phase 1 | ✅ |
| Dual MariaDB + PostgreSQL via SQLAlchemy | Phase 1 | ✅ |
| SST file fetcher + parser | Phase 1 | ✅ |
| `data load` CLI (idempotent end-to-end pipeline) | Phase 2 | ✅ |
| `data status` / `data purge` / `data fetch --state/--version` | Phase 2 | ✅ |
| API-key auth mode + key-management CLI | Phase 2 | ✅ |
| `self_seeded` non-SST loader path (CA pattern) | Phase 2 | ✅ |
| Sales-tax holidays (per-state windows + engine integration) | v0.5 | ✅ |
| Threshold rules (NY $110, MA $175 clothing) | v0.6+ | ⏭️ |
| `rate_modifier` engine wiring (IL reduced grocery rate) | v0.6+ | ⏭️ |
| Address-level resolution via PostGIS | Phase 4 | ⏭️ |
| Exemption certificates | Phase 5 | ⏭️ |
| Returns filing | -- | Out of scope (constitution §13) |
| Hosted SaaS layer | -- | Optional, post-v1 |

## Decisions locked

| # | Decision | Status |
|---|---|---|
| 01 | Language: Python 3.11+ + FastAPI | ✅ |
| 02 | License: Apache 2.0 + DCO + SPDX (no CLA) | ✅ |
| 03 | Database: dual MariaDB + PostgreSQL via SQLAlchemy 2.x | ✅ |
| -- | Patent posture: acknowledged in constitution §2 | ✅ |
| -- | Branding: `opensalestax.org` + `.com` registered; repo `open-sales-tax` | ✅ |
| -- | Phase 1 coverage tiers: tier 1/2/0 | ✅ |
| -- | `self_seeded` Protocol attribute for non-SST states | ✅ (v0.2) |
| -- | Sales-tax holidays as a first-class engine feature | ✅ (v0.5) |

## Quality bar maintained across every release

- 0 bugs / 0 vulnerabilities / 0 code smells / 0 security hotspots in SonarQube
- All-A ratings (reliability, security, maintainability)
- Every commit signed off via DCO; CI enforces
- Every test passes against PostgreSQL AND MariaDB in CI
- Ruff lint + format clean; mypy clean

## Next-session priorities (v0.6 candidates)

In rough order of value-per-effort:

1. **Threshold rules** for NY's <$110 and MA's <$175 clothing
   exemptions. Same shape as holidays but year-round; reuses the
   `max_amount_per_item` pattern + adds per-item amount comparison
   to the engine.
2. **`rate_modifier` engine wiring** so IL's 1% reduced grocery
   rate produces correct tax amounts (currently the modifier is
   stored but ignored).
3. **More tier-1 states**: CT (statewide 6.35%), DC (6%),
   MO (4.225%), MS (7%), SC (6%), VA (4.3%) -- mostly mechanical
   following the CA pattern.
4. **2027 holiday data** for the 4 holiday states (TX, FL, MA, MD)
   -- proactive update once legislatures publish 2027 dates.
5. **CDTFA loader** for California's ~1,700 district rates -- the
   first significant non-SST data ingestion.
6. **PostGIS address-level resolution** -- v1.0 territory; needs
   real boundary data from US Census TIGER/Line shapefiles.
7. **Client SDKs** (Python, JS/TS, PHP for SC Books integration).

## Notes for next session

Read `specs/handoff.md` for the next-step guidance and standing
rules. The spec-kit playbook continues to apply: every meaningful
feature gets its own `specs/phase-N-<name>/` directory if it's
non-trivial.

The autonomous build session that produced v0.2 → v0.5 ran on
2026-05-03; Eric's "as far as possible" mandate was honored
through 5 releases. Eric will direct whether to continue
autonomously or pause for review.
