# OpenSalesTax — Current State

**Last updated:** 2026-05-04
**Status:** **v0.25.0 shipped.** SST loader + lookup engine now
matches every Tier-1 SST state's published DOR rate within 0.05%
across **153 sampled city/ZIP+4 combos** on the live engine.
Coverage explosion this iter: 5 newly-seeded non-SST states
(CT/MO/MS/SC/VA) move from state-only to per-county + per-city,
Arizona widens 20→48 cities, GA gets district friendly names
(Fulton TSPLOST, DeKalb MARTA), OK gets Newcastle, plus 14 DOR
regression rows for cities that became correct after v0.24's
expired-record filter (TN Brentwood/Franklin, GA Alpharetta,
MN suburbs, AZ secondary cities). Pre-built data dumps now ship
with every release via the CI workflow at
`.github/workflows/build-data-dump.yml` — new users go from
`pip install` to working in <2 min via `opensalestax data restore`.
1317 unit tests, mypy clean, ruff clean.

The CO/LA-flagged `SubJurisdiction` Protocol extension is now
the gating dependency for proper home-rule / parish / municipal
modeling on AL (~700+ home-rule cities), CO, LA, plus per-county
surcharges on HI/NM. Captured in
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
| [v0.11.1](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.11.1) | 2026-05-03 | Engine wires `rate_modifier` through; reduced grocery rates now applied correctly across IL/MO/MS/AR/KS/OK/TN/UT/VA/NC |
| [v0.12.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.12.0) | 2026-05-03 | Maine tier-1 (5.5% + no-local + no-holidays) — 48 of 52 jurisdictions now tier-1 |
| [v0.13.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.13.0) | 2026-05-03 | Phase 6 Batch C complete — AL, HI, NM, PR tier-1 (4 parallel agents). **All 52 jurisdictions are now tier-1 maintained.** Plus per-item taxable thresholds in the engine — NY $110 / MA $175 / RI $250 clothing exemptions now enforced. |
| [v0.14.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.14.0) | 2026-05-03 | Boundary data initiative — 41,702 ZIP→authority boundaries across all 52 jurisdictions. SST refresh + new Census ZCTA loader (`data load-zcta`). Engine answers real US ZIPs at major cities for the first time. Multiple loader-robustness fixes (mixed-case SST record types, 90-column rows, csv↔zip fallback, idempotent boundary delete). |
| [v0.15.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.15.0) | 2026-05-03 | SST loader: county-name lookup, NV single-digit jurisdiction-type fix, MN/Mpls under-collection fixed, multi-triplet district parsing |
| [v0.16.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.16.0) | 2026-05-03 | Cross-border ZIP filter (Census ZIP→state); per-state jurisdiction_types merged with defaults rather than replaced |
| [v0.17.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.17.0) | 2026-05-03 | Four SST correctness fixes: TN double-counting, WA L-code triplet over-collection, OK 98XXX composite filter, NC + VT + SD touch-ups |
| [v0.18.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.18.0) | 2026-05-03 | GA Atlanta + OK OKC fixed; engine loose-fallback when ZIP+4 has no type-4 coverage; per-state validation tightened |
| [v0.19.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.19.0) | 2026-05-03 | Friendly receipt authority names for TN, OH, GA, KS, NE |
| [v0.20.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.20.0) | 2026-05-03 | Friendly names for WA / OK / NC + WI county; introduced live DOR-validation grid (25/25 pass) |
| [v0.21.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.21.0) | 2026-05-03 | Friendly names for AR / IA / ND / SD / UT / WV; DOR validation grid expanded to 41 ZIPs, all pass |
| [v0.22.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.22.0) | 2026-05-04 | OK Norman 12.625% double-counting fixed (loose-fallback picks closest +4); SST parser zero-pads +4 ranges; 8 new friendly names (KS Olathe, TN Clarksville/Murfreesboro, OK Moore/Lawton/Ardmore/Bethany/Broken Arrow/Ponca City, SD Aberdeen); DOR grid 41 → 49 ZIPs |
| [v0.23.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.23.0) | 2026-05-04 | Arizona TPT loader: per-county + top-20-city seeded from AZ DOR May 2026 CSV. Phoenix 5.6% → 9.10% combined. Loader fix: `_maybe_load_boundaries` now invokes `parse_boundaries(None, ...)` for self_seeded states. DOR grid 49 → 60 ZIPs. |
| [v0.24.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.24.0) | 2026-05-04 | TN Brentwood 14.75% → 9.75% (parser now filters expired boundary records via `_record_active_on`); backported to MN/WI/GA. New `opensalestax data restore` CLI + CI workflow that pre-builds a Postgres pg_dump per release tag — new-user install goes from 50 min to <2 min. 30 new friendly names (NE x11, OH x3 transit, WA x6, OK x10). 3 parallel sub-agents in worktrees shipped 1900+ lines. DOR grid 60 → 89 ZIPs. |
| [v0.25.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.25.0) | 2026-05-04 | 5 newly-seeded non-SST states (CT/MO/MS/SC/VA) move from state-only to per-county + per-city. Arizona widens 20 → 48 cities (4 new counties online: Cochise/Santa Cruz/Gila/Navajo). GA district friendly names (Fulton TSPLOST, DeKalb MARTA, Fayette District). OK Newcastle (city 51150). 2 parallel sub-agents in worktrees shipped ~600 lines of state data. DOR grid 89 → 153 ZIPs. |

## Coverage (after v0.5)

| Tier | Count | States |
|---|---:|---|
| **Tier 1** -- fully maintained | **52** | Every US state, plus DC and Puerto Rico |
| **Tier 2** -- rate-only via SST data | **0** | (Phase 7 complete — every SST member promoted to tier-1) |
| Unsupported | **0** | (Phase 6 Batch C complete — AL/HI/NM/PR all tier-1 in v0.13.0) |

**All 52 jurisdictions are fully tier-1 maintained.** Phase 7 closed in v0.11.0; ME added in v0.12.0; AL/HI/NM/PR added in v0.13.0. HI's General Excise Tax and NM's Gross Receipts Tax are encoded as sales taxes for API compatibility. Per-county/parish/home-rule local rates remain deferred behind the planned `SubJurisdiction` Protocol abstraction (decision docs 04 + 05).

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
| Threshold rules (NY $110 below_exempt, MA $175 / RI $250 above_excess) | v0.13 | ✅ |
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
