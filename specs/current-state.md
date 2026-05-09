# OpenSalesTax — Current State

**Last updated:** 2026-05-08
**Status:** **v0.54.5 shipped.** Three small UX/perf releases since
v0.54.3: rate-limit response headers (`X-RateLimit-Limit/Remaining/
Reset`) so clients can self-pace, CORS `expose_headers` so browser
JS can read them, NM live grid expanded 1 → 7 entries, and
`Cache-Control` on `/v1/states` (1h) + `/v1/rates` (5 min) so
Cloudflare can shoulder popular-ZIP traffic. Live grid 387/387
green.

**v0.54.3 (2026-05-08)** -- loader bulk-insert refactor unblocks
the previously OOM-prone UT (1.5M boundaries) and WA (1.2M boundaries)
reloads -- the natural reload path now scales for any state. Decision
10 retried in iter-61 with row-count loose fallback; still regressed
GA Roswell via a different path; reverted with deeper lessons.

**v0.54.2 (2026-05-08)** shipped per-real-IP rate limiting via
`CF-Connecting-IP` (closes the Cloudflare-edge-IP-rotation gap from
v0.54.1; opt-in via `OPENSALESTAX_TRUST_FORWARDED_FOR`); +20 high-
traffic friendly placenames across KS / UT / WA / AR (each verified
by ZIP probe + FIPS cross-check); SonarQube cleanup dropped open
code smells 308 → 28 by suppressing `python:S1192` on the data
files where repetition is the schema. Decision 10 (WY synthetic-+4)
was attempted + reverted; lessons recorded for the next try.

**v0.54.1 (2026-05-06)** wired `SlowAPIMiddleware` so the configured
per-IP rate limit actually enforces (it was inert in v0.54.0 and
earlier) and added a `SecurityHeadersMiddleware` that attaches HSTS
/ nosniff / X-Frame-Options DENY / Referrer-Policy / Permissions-
Policy to every response. First formal security audit at
`specs/security/audit-2026-05-04.md`; SonarQube re-scan came back A
across all four ratings with zero security findings.

SST loader + lookup engine matches every published DOR rate within
0.05% across **375 sampled city/ZIP+4 combos** on the live engine
-- coverage spans **every US jurisdiction (50 states + DC + PR)**
for the first time as of iter 57. The dedup logic stabilized
across six consecutive refinements (v0.43-v0.48): TN code-63
county-equivalent skip, cross-county IMPROVE Act dedup, strict-
lookup type-z fallback dedup, "most rows beats has-typez"
tiebreaker, lone-district county-overlay heuristic, and the 20-
row threshold to filter stray district bindings.

**Alaska is no longer a no-tax state.** v0.49 promoted AK from
``NoTaxState`` to a real state module via ARSSTC data; v0.50/v0.51
extended coverage to 42 verified municipalities; v0.52 added
borough-wide rates (Kenai Peninsula 3%, Ketchikan Gateway 2.5%)
for unincorporated ZIPs with the city-suppresses-borough rule.
Anchorage and Fairbanks correctly return 0% (in-state retail
unchanged); the long tail of small AK cities and seasonal rates
remain deferred.

VT Local Option Sales Tax (Burlington + ~17 other LOST
municipalities at 7%) now collected via SST 'A' (address-level)
record support added in v0.40. 1495 unit tests pass, mypy clean,
ruff clean, full live DOR grid green on every release.

The CO/LA-flagged `SubJurisdiction` Protocol extension is now
the gating dependency for proper home-rule / parish / municipal
modeling on AL (~700+ home-rule cities), CO, LA, plus per-county
surcharges on HI/NM, plus NJ UEZ / Salem County reduced rates.
Captured in `specs/decisions/04-colorado-home-rule.md` and
`specs/decisions/05-louisiana-parishes.md` for v1.0+ design.

Public live API: [api.opensalestax.org](https://api.opensalestax.org/v1/docs).
Source: [github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax).

## Live deployment

| Field | Value |
|---|---|
| **Hostname** | `opensalestax-01` (SSH alias on Eric's box) |
| **IP** | `10.32.161.126` (DHCP from LAN; private) |
| **Proxmox VMID** | 906 (on `pmvm1`) |
| **Specs** | 4 vCPU / 8 GB RAM / 80 GB disk, Debian 13 |
| **Provisioned** | 2026-05-03 |
| **Stack** | Docker Compose (`postgres` profile) — API + PostgreSQL 15 |
| **Public API** | [api.opensalestax.org](https://api.opensalestax.org/v1/docs) (Cloudflare-fronted) |
| **Demo site** | [demo.opensalestax.org](https://demo.opensalestax.org) |
| **Health check** | `curl https://api.opensalestax.org/v1/health` |
| **Loaded data** | All 52 jurisdictions; SST states refreshed periodically as new quarterly files become available |

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
| [v0.26.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.26.0) | 2026-05-04 | The big-three non-SST states (TX/NY/FL) shipped per-county + per-city coverage in one push via 3 parallel sub-agents. TX 49 cities + 7 transit districts. NY 30 cities including NYC consolidated (8.875%) + MCTD as separate authority. FL all 67 counties + 30 cities (FL has no city tax). DOR grid 153 → 201 ZIPs. |
| [v0.27.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.27.0) | 2026-05-04 | CA / IL / PA self-seeded loaders shipped. Phase 6 / Batch D. |
| [v0.28.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.28.0) | 2026-05-04 | Census ZCTA→county relationship file ingested as `zip_county.py` (33,791 ZIPs); CA loader emits per-ZIP+county boundaries via the new ZIP_COUNTY map. |
| [v0.29.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.29.0) | 2026-05-04 | Loader auto-purges all prior DataVersions for the same (state, source) — fixes prod accumulating stacked versions and over-collecting after multiple loads. |
| [v0.30.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.30.0) | 2026-05-04 | Decision 06: roadmap for additional tax types (admissions, entertainment, liquor, lodging, restaurant) deferred to post-v1. |
| [v0.31.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.31.0) | 2026-05-04 | MO/MS/SC/VA per-county/per-city expansion (4 parallel agents). |
| [v0.32.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.32.0) | 2026-05-04 | HI per-county GET surcharges (Honolulu / Hawaii / Kauai / Maui split). PR municipal SUT. |
| [v0.33.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.33.0) | 2026-05-04 | AL + NM loaders shipped (303/303 DOR pass). |
| [v0.34.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.34.0) | 2026-05-04 | NE Papillion 11% city-stacking bug fixed (`_pick_one_city_county_per_zip5` dedup picks one city/county per ZIP); AL long-tail counties filled (308/308). |
| [v0.35.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.35.0) | 2026-05-04 | KS Olathe 13.475% bug fixed by dropping type-4-only districts (CIDs) from zip5-only queries. |
| [v0.36.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.36.0) | 2026-05-04 | TN/WA city authorities already include county portion; drop county to avoid double-collection (Brentwood 12.5% → 10.25%). |
| [v0.37.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.37.0) | 2026-05-05 | CI fix (style-vs-lint), README refresh, 8 confidence badges, demo-site verification. |
| [v0.38.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.38.0) | 2026-05-05 | `/v1/rates` now uses loose lookup when no zip4 (matches `/v1/calculate`); CI no longer runs the live DOR grid (eliminates network-flakiness). Decision 07 documents WY multi-row county taxes. |
| [v0.39.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.39.0) | 2026-05-05 | WY's lone type-1 SST jurisdiction (FIPS Place 13150) renders as "Casper" instead of placeholder; decision 08 documents the VT 'A' (address-level) boundary record gap. |
| [v0.40.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.40.0) | 2026-05-05 | **VT Local Option Sales Tax now collected.** Burlington 05401 + ~17 other VT LOST municipalities go from state-only 6% to combined 7% via three SST parser fixes: 'A' record support, UTF-8 BOM stripping, blank-rate-column tolerance. |
| [v0.41.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.41.0) | 2026-05-05 | Loose-lookup dedup prefers curated friendly names over `XX-city-NNNNN` placeholders (fixes Burlington 05401 displaying "VT-city-66175"). |
| [v0.42.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.42.0) | 2026-05-05 | 10 new ZIP-probe-vetted Vermont placenames; fewer-total-ZIPs dedup tiebreaker fixes Winooski 05404 displaying "Colchester". 12/12 tested VT cities now display correct names. |
| [v0.43.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.43.0) | 2026-05-05 | TN code-63 county-equivalent overlays now skipped (Johnson City 12.0% → 9.75%); ~30 type-63 rows in the TN SST file encoded levies that are already collapsed into the city's combined local rate. |
| [v0.44.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.44.0) | 2026-05-05 | Cross-county IMPROVE Act dedup (Brentwood 11.75% → 10.25%) — TN ZIPs straddling counties no longer stack 4× IMPROVE Acts. |
| [v0.45.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.45.0) | 2026-05-05 | Strict-lookup type-z fallback dedup (Johnson City 37601-1234: 17.75% → 9.75%) — synthetic and real +4 addresses without precise SST coverage now match the loose lookup. Decision 09 resolved within iter. |
| [v0.46.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.46.0) | 2026-05-05 | "Most rows for THIS ZIP" beats "has-typez" tiebreaker (Roswell GA 30075: 6% → 7.0%); Papillion NE 68046 now displays "Papillion" instead of "La Vista". |
| [v0.47.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.47.0) | 2026-05-05 | Lone type-4-only district treated as county-wide overlay (Roswell GA: 7.0% → 7.75% with Fulton TSPLOST). |
| [v0.48.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.48.0) | 2026-05-05 | 20-row threshold filters stray district bindings (Suwanee GA 30024: 6.75% → 6.0%) — Fulton TSPLOST's 7 stray rows in this Gwinnett ZIP no longer apply. |
| [v0.49.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.49.0) | 2026-05-05 | **Alaska promoted from no-tax to a real state module** via the Alaska Remote Seller Sales Tax Commission (ARSSTC) data. 20 verified municipalities ship general-retail rates (Juneau 5%, Sitka 6%, Kodiak 7%, Wasilla 2.5%, Bethel 6%, etc.); pre-v0.49 every AK ZIP returned 0%. Anchorage and Fairbanks correctly return 0%; borough-stack rules and seasonal rates documented as deferred. |
| [v0.50.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.50.0) | 2026-05-05 | AK coverage extends from 20 → 32 cities (+12 ARSSTC entries: Adak 4%, Craig 7%, Dillingham 6%, Galena 3%, Houston 2%, Kake 5%, Nenana 4%, Old Harbor 3%, Ouzinkie 6%, Saint Paul 3.5%, Unalakleet 5%, Unalaska 3%). |
| [v0.51.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.51.0) | 2026-05-05 | AK coverage 32 → 42 cities (+10 more ARSSTC: Aleknagik, Aniak, Gustavus, Mountain Village, Quinhagak, Selawik, Seldovia, Tenakee Springs, Thorne Bay, Togiak). Spec docs refreshed. |
| [v0.52.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.52.0) | 2026-05-05 | AK borough-wide rates for unincorporated ZIPs (KPB 3%, KGB 2.5%) -- Anchor Point 99556, Sterling 99672, Ninilchik 99639, etc. now return their borough rate. Suppressed inside city limits per the existing v0.36 city-includes-county exclusivity. |
| [v0.53.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.53.0) | 2026-05-05 | Strict-lookup typez-fallback rewrite (REVERTED in v0.53.1 -- regressed OK Edmond 73034-1234 cross-county +4 lookups). |
| [v0.53.1](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.53.1) | 2026-05-05 | Revert v0.53 typez-fallback widening; restore v0.51 candidate-restricted dedup. Decision 10 documents the synthetic-+4 case (Casper WY 82601-0001 returns 5% instead of 6%) as deferred future work. |
| [v0.54.0](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.54.0) | 2026-05-05 | AK coverage 42 → 50 cities (+8 ARSSTC long-tail entries). |
| [v0.54.1](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.54.1) | 2026-05-06 | **Security fix.** `SlowAPIMiddleware` wired so per-IP rate limit actually enforces (it was inert pre-fix); `SecurityHeadersMiddleware` attaches HSTS / nosniff / X-Frame-Options DENY / Referrer-Policy / Permissions-Policy on every response. First formal security audit baseline at `specs/security/audit-2026-05-04.md`. |
| [v0.54.2](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.54.2) | 2026-05-08 | Per-real-IP rate limiting via `CF-Connecting-IP` (opt-in `OPENSALESTAX_TRUST_FORWARDED_FOR`); +20 friendly placenames (KS Manhattan; UT Logan/Murray/Orem/Park City/St. George; WA Kennewick/Kent/Lakewood/Oak Harbor/Spokane Valley/Wenatchee/Yakima; AR Conway/Hot Springs/N Little Rock/Lowell/Rogers/Sherwood/Springdale); SonarQube code smells 308 → 28; Decision 10 attempted + reverted. |
| [v0.54.3](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.54.3) | 2026-05-08 | **Loader OOM fix.** Boundary + rate loaders now bulk-insert via Core in 5K-row batches. UT (1.5M boundaries) + WA (1.2M boundaries) reloads no longer SIGKILL the prod container; the SQL-rename workaround for placename pushes is retired. Decision 10 retried with row-count loose fallback; still regressed via a different path; reverted with deeper lessons. |
| [v0.54.4](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.54.4) | 2026-05-08 | `X-RateLimit-Limit/Remaining/Reset` response headers via `Limiter(headers_enabled=True)`; CORS `expose_headers` for the rate-limit trio + `Retry-After` so browser fetch() callers can read them; NM live grid expanded 1 → 7 entries (Albuquerque/Santa Fe/Las Cruces/Rio Rancho/Farmington/Gallup/Espanola). |
| [v0.54.5](https://github.com/ejosterberg/open-sales-tax/releases/tag/v0.54.5) | 2026-05-08 | HTTP caching: `Cache-Control: public, max-age=3600` on `/v1/states`; `public, max-age=300` on `/v1/rates`. Cloudflare + browser caches dramatically cut origin load on popular ZIPs. POST `/v1/calculate` stays uncached. |

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
| 04 | Colorado home-rule cities deferred to SubJurisdiction Protocol | ⏭️ Open |
| 05 | Louisiana parishes deferred to SubJurisdiction Protocol | ⏭️ Open |
| 06 | Additional tax types (admissions/lodging/etc.) deferred to v0.30+ roadmap | ⏭️ Open |
| 07 | WY multi-row county taxes need empirical SST jurisdiction-code capture | ✅ Resolved (iter 43) -- rates verified correct against SalesTaxHandbook |
| 08 | VT 'A' (address-level) boundary record support | ✅ Resolved (v0.40) |
| 09 | Strict-lookup type-z fallback dedup | ✅ Resolved (v0.45) |
| 10 | Wide-range type-4 records suppress city authority on synthetic +4 | ⏭️ Open (real +4s + loose lookup unaffected) |
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
