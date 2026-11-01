# AK state-tax audit — 2026-11-01 (full-sweep Pacific)

**Auditor:** region-agent (Pacific sweep)
**Branch:** `audit-sweep-pac-20261101`
**Status:** REFRESH_PENDING (prod reload backlog + 3 new ARSSTC monthly sheets since last confirmed)

## What was checked

- Prod `data_versions` for AK: `AK-SST-V0.54-ARSSTC` fetched **2026-05-10** (predates
  commit `e99237f` which fixed 7 ZIPs). Live engine still returns the pre-fix answers.
- ARSSTC source page https://arsstc.org/business-sellers/tax-rates/ — three new
  monthly rate sheets have published since the last confirmed 7-1-2026:
  - `ARRSTC-Sales-Tax-Rate-Sheet-with-Zip-Codes-8-1-2026.xlsx`
  - `ARRSTC-Sales-Tax-Rate-Sheet-with-Zip-Codes-9-1-2026.xlsx`
  - `ARRSTC-Sales-Tax-Rate-Sheet-with-Zip-Codes-10-1-2026.xlsx` **(current)**
- `src/opensalestax/states/ak_data.py` and `AK_BOROUGH_ZIPS` — no changes this run.
- 1 contradictory DOR_GRID pin remains (Kenai 99611) — **not touched** per the
  2026-09-28 finding (borough-suppressed-inside-city modeling question, decide
  rather than delete).

## Live defects still outstanding (no new fixes landed this run)

### 1. 7 ZIPs fixed in repo (commit `e99237f`) NEVER RELOADED on prod

| ZIP | Repo says | Prod returns | Delta |
|---|---:|---:|---:|
| 99928 Ward Cove | 2.5 | 5.5 | **over-collects 3.00pp** |
| 99903 | 8.0 | 0.0 | under-collects 8.00pp |
| 99918 | 8.0 | 0.0 | under-collects 8.00pp |
| 99950 | 8.0 | 0.0 | under-collects 8.00pp |
| 99824 Douglas | 5.0 | 0.0 | under-collects 5.00pp |
| 99836 | 6.0 | 0.0 | under-collects 6.00pp |
| 99850 | 4.5 | 0.0 | under-collects 4.50pp |

Fix is a plain `data load -s AK -v AK-SST-V0.54-ARSSTC` **after** redeploy
(reuse existing label; new label would double-stack per loader semantics).

### 2. 3 new ARSSTC monthly sheets to diff (8-1, 9-1, 10-1-2026)

The 7-1-2026 sheet produced the Phase 1 AK data; it was unchanged across
7-1, 8-1, and 9-1 per the 2026-10-01 audit note. The 10-1-2026 sheet is
new ground and has NOT been compared against `ak_data.py`. Watch the
`inoutcity` column `'I '` trailing-space trap. Chipped for a dedicated
10-1-2026 diff when the daily rotation next hits AK (day 1).

## Files touched

None. Audit report only.

## Live engine status

No code change this run. 7 live-wrong AK ZIPs remain pending prod reload.

## Commits

- `data(AK): full-sweep 2026-11-01 audit — refresh pending (prod reload + 10-1-2026 ARSSTC)`
