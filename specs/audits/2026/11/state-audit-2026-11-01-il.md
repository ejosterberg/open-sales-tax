# IL — full-sweep audit 2026-11-01

## TL;DR
No new drift. Sangamon/Franklin county fix (commit `6e870e2`) is still
in-repo-but-not-deployed; Springfield 62701 continues to under-collect
0.50pp on the live engine until prod is redeployed.

## Facts

- Non-SST — IL rate data lives in `src/opensalestax/states/il_data.py`
  (self-seeded from IDOR `ordmache-current.txt`).
- Prod `data_versions` row: `IL-SST-V0.31-STATEWIDE`, fetched 2026-05-04.
  No reload required (IL is engine-data; `data load` creates the SST
  stub only). Fix lands on an API-only redeploy.
- Latest IDOR Informational Bulletin for a general sales-tax rate
  change: **FY 2026-26-A** (eff 2026-07-01). No new sales-tax rate-
  change bulletin posted for 2026-10-01 or 2027-01-01 as of today
  (verified by fetching the IDOR bulletins index: FY 2027-02 is
  municipal auto-renting, FY 2027-03 is telecom, FY 2027-04 is hemp —
  none change the general sales-tax rate).
- Repo state: `IL_COUNTY_RATE_PCT` has Sangamon 1.500 (+0.5pp vs prod)
  and Franklin 1.000 (-1.0pp vs prod), both commented with FY 2026-26-A
  as the source. Correct.
- Live probe: Springfield 62701 returns **9.500%**; the repo pin asserts
  **10.000%** (fails under `-m liveapi` by design until reload).

## Drift table

| City | ZIP | Live engine | Repo expected | Delta | Reason |
|---|---|---|---|---|---|
| Springfield | 62701 | 9.500% | 10.000% | −0.5pp | Sangamon +0.5 (FY 2026-26-A), not deployed |

## Recommended action

- No code change in this sweep.
- Carry the existing deploy chip ("Deploy IL Sangamon/Franklin county
  fix to prod (redeploy api)") forward unchanged.

## Status

**UNCHANGED (deploy chip still pending from 2026-07-08).**
