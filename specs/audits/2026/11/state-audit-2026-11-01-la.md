# Daily state sales tax audit — 2026-11-01 (full-sweep, LA)

Part of the multi-agent full-sweep audit run on 2026-11-01, South-Central region
(AR, LA, MS, OK, TX).

## TL;DR

- **LA fully clean at the headline level.** Louisiana statewide rate is
  **5.000%** per Act 11 of the 2024 3rd Extraordinary Session (eff
  2025-01-01, stepdown to 4.75% on 2030-01-01). Confirmed against LDR
  on 2026-11-01.
- **Parishes remain deferred.** Per decision 05 (SubJurisdiction
  Protocol), LA's 64-parish patchwork is not modeled in v0.59; the
  single `LA` pin `New Orleans (parish deferred)` 70112 → 5.000% is a
  state-only expectation, not a defect.
- Prod carries `LA-SST-V0.13`, fetched 2026-05-04. Louisiana is NOT an
  SST member; the "SST" source string here is the module's internal
  seed label, not an upstream file.

## Primary source

- `src/opensalestax/states/louisiana.py` docstring, which cites Act 11
  (2024 3rd ES, HB 10) and the statutory layers in La. R.S. 47:302,
  321, 321.1, 331, 332. No 2026 or 2027 statutory amendments known
  that would move the 5.000% headline.
- LDR has published no 2026 statewide rate change. The 2026 Second
  Amendment Weekend Sales Tax Holiday (Sept 4–6, 2026) is a temporary
  per-category exemption; not a rate change.

## Pins

- 1 `LA` pin: `New Orleans (parish deferred)` 70112 → 5.000%. Consistent
  with the module and intentionally state-only.

## Status

**UNCHANGED.** No fix needed. No reload owed.

## Follow-ups (not scope of this audit)

- Parish-level coverage remains the project's largest open feature-gap
  for LA. Louisiana's SubJurisdiction Protocol roadmap is tracked
  outside the daily audit cadence.
