# NE state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **NE is 2 quarters stale on prod** (`NER2026Q2FEB25` / `NEB2026Q2APR20`);
  latest upstream is **`NER2026Q4AUG21` / `NEB2026Q4OCT20`** (apply Q4,
  skip Q3).
- **1 live under-collection** confirmed by live probe:
  **Edgar 68935 (-0.50pp since 2026-07-01)**. Engine returns 6.500% vs
  expected 7.000%. Same chip as 2026-08-15 and 2026-07-31; still unapplied.
- No code fix is possible -- NE is SST. The fix is the `NER2026Q4AUG21`
  refresh.
- All 14 NE tier-1 city pins already match exact (Omaha, Lincoln,
  Bellevue, Grand Island, Kearney, etc.), per handoff audit 2026-08-15.
- **Status: REFRESH_PENDING** (chipped; no new code change).

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| sst | `NE-SST-2026Q2FEB25` | 2026-05-05 |
| zcta-census-2020 | `NE-ZCTA-2020` | 2026-05-11 |

## Upstream (SST Governing Board, 2026-11-01)

- Rate: `NER2026Q4AUG21.zip`
- Boundary: `NEB2026Q4OCT20.zip` (very recent boundary rebuild)

## Live probes (`/v1/calculate` bare-ZIP, $100)

| City | ZIP | Expected (NE DOR) | Actual | Delta |
|---|---|---|---|---|
| Edgar | 68935 | 7.000 | **6.500** | **-0.50** |

Expected comes from NE DOR *Local Sales and Use Tax Rates* eff
07-01-2026 (`Edgar 1.5% 7.0% (.07) 102-161 14450`). This chip has
been unaddressed since the 2026-08-15 audit.

## Confirmed-no-change (handoff & 2026-08-15 audit)

Per handoff: "NE has NO changes scheduled for the quarter beginning
2026-10-01, so after the Q3 refresh Nebraska is clean through year-end."
Primary-source re-check for 2026-Q4 attempted this run but revenue.nebraska.gov
returned 404 for the local-rate index page -- no evidence contradicting the
handoff claim surfaced.

## Changes committed

- Audit report only. The existing Edgar `DOR_GRID` pin at 7.000 and
  the `ne_names.py` entry for FIPS code 14450 are correct; no code
  change is needed. The pin fails under `-m liveapi` until prod
  loads NE Q4.

## Open follow-ups

- Load `NER2026Q4AUG21` + `NEB2026Q4OCT20` on prod -- resolves Edgar.
- Re-run the Q4 primary-source check for NE DOR tables once a stable
  URL is identified; the current revenue.nebraska.gov path is 404.
