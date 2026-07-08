# Daily state sales tax audit — 2026-07-08 (day 8: IL + IN)

## TL;DR
- 2 jurisdictions audited (Illinois — non-SST; Indiana — SST member).
- **1 real rate change found requiring code + test updates: Sangamon
  County, IL added a +0.50% public-safety tax effective 2026-07-01
  (IDOR FY 2026-26-A), raising Springfield from 9.50% → 10.00%.**
  Also caught the same bulletin's Franklin County, IL −1.00%
  (2.00% → 1.00%). Both fixed in-repo (engine data, not a
  boundary/SST refresh). **Prod redeploy pending** (chipped) — the
  live engine still returns the old rates until then.
- Indiana: clean. Flat 7% statewide, no local option taxes; all 3
  tier-1 cities match. SST files on prod are ancient
  (`INR2008Q4MAY7` / `INB2005Q1JAN6`) but functionally correct
  because IN has had zero rate/jurisdiction change since April 2008.
  Refresh chipped for file-currency hygiene only (no drift).

## IL (Illinois — non-SST)
- Source (authoritative, primary): IDOR Informational Bulletin
  **FY 2026-26-A**, "Sales Tax Rate Change Summary, Effective
  July 1, 2026" (reissued 2026-05-20). Retrieved 2026-07-08 from
  https://tax.illinois.gov/content/dam/soi/en/web/tax/research/publications/bulletins/documents/2026/fy-2026-26.pdf
  Also reviewed: FY 2026-10-A (Jan 1, 2026 changes — already captured
  in the 2026-05-04 module build; no missed drift).
- Last loaded on prod: `il_data.py` module data verified 2026-05-04
  against IDOR ordmache (2026-01-01) + Avalara; IL DataVersion
  `IL-SST-V0.31-STATEWIDE` (2026-05-04) + ZCTA `IL-ZCTA-2020`.
- Latest available: county rates changed 2026-07-01 (this bulletin).
- Drift summary: **Sangamon County local portion 1.00% → 1.50%**
  (added 0.50% County Public Safety Tax) — the engine under-collected
  Springfield and all Sangamon County ZIPs by 0.50% as of 2026-07-01
  (7 days before this audit). Separately, **Franklin County 2.00% →
  1.00%** (−1.00% County Public Safety) — over-collect for Franklin
  County ZIPs (no seeded tier-1 city; applied via ZCTA fallback).
- Recommended action: **DONE in-repo** — bumped both county rates in
  `il_data.py`, updated the Springfield unit-test pin (9.500 →
  10.000) and the live-API integration grid pin. Deploy to prod
  (engine-only; no SST/boundary reload needed) — **chipped**.

### Tier-1 city cross-check vs. live engine (api.opensalestax.org)
All 11 probed with a single $100 general line. "Expected" = current
IDOR rate after the July 1, 2026 changes.

| City | ZIP | Expected (IDOR) | Engine (live) | Delta | Note |
|------|-----|-----------------|---------------|-------|------|
| Chicago | 60601 | 10.250 | 10.250 | 0 | not in July change list |
| Joliet | 60432 | 8.750 | 8.750 | 0 | not in July change list |
| Elgin | 60120 | 8.500 | 8.500 | 0 | not in July change list |
| Champaign | 61820 | 9.000 | 9.000 | 0 | not in July change list |
| Cicero | 60804 | 10.750 | 10.750 | 0 | not in July change list |
| Evanston | 60201 | 10.250 | 10.250 | 0 | not in July change list |
| Aurora | 60505 | 8.250 | 8.250 | 0 | not in July change list |
| Naperville | 60540 | 7.750 | 7.750 | 0 | not in July change list |
| **Springfield** | 62701 | **10.000** | 9.500 | **+0.500** | **Sangamon Co +0.5% public-safety eff 2026-07-01 — FIXED in repo, prod pending** |
| Rockford | 61101 | 8.750 | 8.750 | 0 | Winnebago unchanged |
| Peoria | 61602 | 9.000 | 9.000 | 0 | citywide unchanged; July change is the Glen Hollow *Business District* only (sub-ZIP, intentionally not modeled) |

**All ~30 changed municipalities in FY 2026-26-A were cross-checked
against the engine's `IL_CITIES` seed — none are seeded**, so no
municipal (home-rule / non-home-rule) rate fixes were required. The
only engine-relevant changes were the two County Public Safety
adjustments (Sangamon, Franklin). Metro-East Mass Transit District
(MED) changes for Edwardsville/Troy are district-level and not
seeded. The Peoria Glen Hollow Business District (+1.00% → 10.00%)
is a sub-ZIP overlay outside v1 scope.

## IN (Indiana — SST member)
- Source: SST Governing Board state-tax-files index
  (https://www.streamlinedsalestax.org/state-tax-files) + Indiana DOR.
  Indiana levies a **flat 7% statewide** sales tax with **no county
  or municipal local option sales tax** (rate set April 1, 2008; no
  change since).
- Last loaded on prod: rate file `INR2008Q4MAY7.csv`, boundary
  `INB2005Q1JAN6.csv`; DataVersion `IN-SST-2008Q4MAY7` (2026-05-04) +
  ZCTA `IN-ZCTA-2020`.
- Latest available: SST continues to publish quarterly IN files, but
  the encoded rate is unchanged (7% flat, no locals). The prod cache
  is old on the *filename* but not on the *content*.
- Drift summary: **none.** All 3 tier-1 cities return exactly 7.000%.
- Recommended action: no correctness change. Chipped a low-priority
  SST file-currency refresh (hygiene only — zero rate impact).

### Tier-1 city cross-check vs. live engine
| City | ZIP | Expected (IN DOR) | Engine (live) | Delta |
|------|-----|-------------------|---------------|-------|
| Indianapolis | 46204 | 7.000 | 7.000 | 0 |
| Fort Wayne | 46802 | 7.000 | 7.000 | 0 |
| Evansville | 47708 | 7.000 | 7.000 | 0 |

## Actions taken this run
1. **Commit (engine data + tests):** `il_data.py` Sangamon County
   1.000→1.500 and Franklin County 2.000→1.000; Springfield unit +
   integration pins 9.500→10.000. IDOR FY 2026-26-A cited inline.
2. **Chip:** "Deploy IL Sangamon/Franklin county fix to prod
   (redeploy api)" — engine-only, no data reload.
3. **Chip:** "Refresh IN SST quarterly to current (file-currency
   hygiene; no rate drift)" — low priority.

## Verification notes
- Live engine request schema: `POST /v1/calculate` with
  `{"address":{"zip5":"…"}, "line_items":[{"amount":"100.00",
  "category":"general"}]}`. Effective rate read from
  `tax_total / subtotal` (and confirmed against each jurisdiction's
  `rate_pct` breakdown in the response `lines[].jurisdictions`).
- The Springfield integration-grid pin is `@pytest.mark.liveapi`, so
  it fails against the live engine until prod is redeployed. CI runs
  `-m "not liveapi"`, so the push stays green; the local unit test
  (module data) passes immediately with the corrected 10.000.
