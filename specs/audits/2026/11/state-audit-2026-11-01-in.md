# IN — full-sweep audit 2026-11-01

## TL;DR
Clean. SST pin `INR2008Q4MAY7` / `INB2005Q1JAN6` still matches the only
file upstream (SST has never republished Indiana since 2008). Live
engine returns flat 7.000% for Indianapolis 46202. No action.

## Facts

- SST member. Workflow pins: `INR2008Q4MAY7` / `INB2005Q1JAN6`.
- Upstream listing (fetched 2026-11-01): `INR2008Q4MAY7.csv` /
  `INB2005Q1JAN6.csv` — **pin equals upstream**.
- Prod data: `IN-SST-2008Q4MAY7`, fetched 2026-05-04. Current.
- Indiana levies **7.0% flat statewide** (Ind. Code 6-2.5-2) with no
  local option — no county, no city, no special district can impose a
  general sales tax. The 2008 file is correct because the rate has not
  moved in 17 years.
- Live probe: Indianapolis 46202 → **7.000%** ✓.

## Drift

None.

## Recommended action

None. The `INR2008Q4` / `INB2005Q1` filenames are
*not* stale — they are the current publication. Do not re-investigate
until SST publishes a new IN file (which will only happen if Indiana
raises the state rate).

## Status

**UNCHANGED.**
