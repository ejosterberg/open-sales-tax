# KY — full-sweep audit 2026-11-01

## TL;DR
Clean. SST pin `KYR2012Q4Aug13` / `KYB2013Q2MAR13` still matches the
only file upstream (SST has never republished Kentucky since 2012/2013).
Live engine returns flat 6.000% for Louisville 40202. No action.

## Facts

- SST member. Workflow pins: `KYR2012Q4Aug13` / `KYB2013Q2MAR13`.
- Upstream listing (fetched 2026-11-01): `KYR2012Q4Aug13.csv` /
  `KYB2013Q2MAR13.csv` — **pin equals upstream**.
- Prod data: `KY-SST-2012Q4AUG13`, fetched 2026-05-04. Current.
- Kentucky levies **6.0% flat statewide** (KRS 139) with no general
  local sales tax. Transient-room / restaurant / excise taxes exist at
  the municipal level but are out of OpenSalesTax v1 scope.
- Live probe: Louisville 40202 → **6.000%** ✓.

## Drift

None.

## Recommended action

None. The `KYR2012Q4` / `KYB2013Q2` filenames are *not* stale.

## Status

**UNCHANGED.**
