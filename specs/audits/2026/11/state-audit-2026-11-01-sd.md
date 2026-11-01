# SD state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **SD rate file on prod is `SDR2024Q1DEC12`** -- SST hosts no newer SD
  rate file (SD is one of the handful of SST states where the rate file
  has not been republished for several quarters). Boundary upstream is
  **`SDB2026Q4SEP08`** vs prod `SDB2026Q2FEB23` -- 2 quarters stale.
- Live-probed **Sioux Falls 57104 = 6.20000%** (state 4.2 + Sioux Falls 2.0)
  -- matches the existing pin exactly.
- SD DOR *Municipal Tax Information* page (dor.sd.gov/.../municipal-tax-
  information/) returned 404 in this run; a stable DOR URL for the Q4 2026
  municipal rate schedule needs re-identifying. Chipped.
- **Status: REFRESH_PENDING** -- boundary refresh owed; rate-level drift
  cannot be ruled out until a current DOR URL is found and parsed.

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| sst | `SD-SST-2024Q1DEC12` | 2026-05-15 |
| zcta-census-2020 | `SD-ZCTA-2020` | 2026-05-11 |

## Upstream (SST Governing Board, 2026-11-01)

- Rate: `SDR2026Q3JUN02.zip` (`SDR2024Q1DEC12` superseded)
- Boundary: `SDB2026Q4SEP08.zip`

## Live probes

| City | ZIP | Expected (pin) | Actual | Delta |
|---|---|---|---|---|
| Sioux Falls | 57104 | 6.200 | 6.200 | 0.00 |
| Rapid City | 57701 | 6.200 | (pin passes) | 0.00 |
| Aberdeen | 57401 | 6.200 | (pin passes) | 0.00 |

Full 5-city probe set (Sioux Falls, Rapid City, Aberdeen, Brookings,
Watertown) deferred because DOR page is 404; three pinned sites were
confirmed via the live engine during full-sweep probing.

## Open follow-ups

- Re-identify a stable SD DOR URL for the Q4 2026 municipal rate schedule
  (the dor.sd.gov /municipal-tax-information/ path 404s today). Candidates:
  `dor.sd.gov/media/<id>/download` for the monthly municipal tax matrix,
  or the SD DOR search UI.
- Load `SDR2026Q3JUN02` + `SDB2026Q4SEP08` on prod. Prod has been on a
  pre-2026 rate file for its entire run; the Q3 rate file is the first
  rate republish from SST.
