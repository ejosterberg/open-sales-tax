# KS state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **KS is 2 quarters stale on prod** (`KSR2026Q2FEB18` / `KSB2026Q2FEB18`);
  latest upstream is **`KSR2026Q4AUG19` / `KSB2026Q4AUG19`**.
- **KS DOR published both Q3 and Q4 rate-change bulletins** (edu960726.xlsx,
  edu961026.xlsx on ksrevenue.gov/salesratechanges.html) plus Publication 1700
  revisions for 07/2026 and 10/2026. Contents couldn't be parsed in this run
  (binary xlsx bodies via WebFetch) -- flagged for primary-source parse before
  bumping any pins.
- Live-probed **Topeka 66603 = 9.35000%** (state 6.5 + Shawnee 1.35 + Topeka
  1.5) -- matches the existing pin exactly.
- **Status: REFRESH_PENDING** -- data refresh owed; no code fix identified
  from the sources successfully read.

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| sst | `KS-SST-2026Q2FEB18` | 2026-05-15 |
| zcta-census-2020 | `KS-ZCTA-2020` | 2026-05-11 |

## Upstream (SST Governing Board, 2026-11-01)

- Rate: `KSR2026Q4AUG19.zip`
- Boundary: `KSB2026Q4AUG19.zip`

## KS DOR change bulletins (dates from index page, 2026-11-01)

- `pdf/edu960726.xlsx` -- Effective July 1, 2026, Sales Tax Rate Updates Only
- `pdf/edu961026.xlsx` -- Effective October 1, 2026, Sales Tax Rate Updates Only
- `pdf/pub17000726.xlsx`, `pdf/pub17001026.xlsx` -- Publication 1700 all-rates
  workbooks for 07/2026 and 10/2026

The xlsx bodies could not be parsed via WebFetch (binary stream returned).
Follow-up: run `openpyxl`/`pandas` on the saved copies to extract rate-change
rows, then diff vs. the engine. Chipped.

## Live probes

| City | ZIP | Expected (existing pin) | Actual | Delta |
|---|---|---|---|---|
| Topeka | 66603 | 9.35 (state 6.5 + Shawnee 1.35 + Topeka 1.5) | 9.35 | 0.00 |

## Open follow-ups

- Parse `edu961026.xlsx` offline, diff against engine. Any cities not matched
  in `KS_CITIES` are a candidate chip.
- Load `KSR2026Q4AUG19` + `KSB2026Q4AUG19` on prod. KS is SST -- all rates
  flow through the SST file, so refresh resolves any drift mechanically
  for in-file jurisdictions.
