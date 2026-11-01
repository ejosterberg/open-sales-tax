# PR state-tax audit — 2026-11-01 (full-sweep Pacific)

**Auditor:** region-agent (Pacific sweep)
**Branch:** `audit-sweep-pac-20261101`
**Status:** UNCHANGED

## What was checked

- `src/opensalestax/states/puerto_rico.py` — PR IVU encoded as two RateRows
  (10.5% state per 13 L.P.R.A. § 32021 + 1.0% municipal per § 32024 = 11.5%
  combined). Rate structure unchanged since 2015-07-01.
- Prod `data_versions`: `PR-SST-V0.32-MUNICIPAL` fetched 2026-05-05 — the
  module is self-seeded (not actually SST, flagged as `self_seeded=True`),
  so the "SST" source label is a loader convention; nothing to refresh at
  the SST level.
- Departamento de Hacienda https://hacienda.pr.gov/ — no press release
  announcing a change to the 11.5% combined IVU, and no 2026 "Días sin IVU"
  (Days Without IVU) back-to-school holiday has been announced. The press
  room (`/sala-de-prensa-virtual/comunicados-de-prensa`) was unreachable
  this run (returned a "Página no encontrada" error page), so a late
  announcement cannot be ruled out.

## Findings

None. PR remains at the statutory 11.5% uniform rate across all 78
municipios. No 2026 "Días sin IVU" holiday to encode (the holiday is
enacted ad hoc each year — the no-holiday-yet regression test continues
to pin this through 2030).

## Files touched

None. Audit report only.

## Live engine status

Engine returns 11.500% for every PR ZIP, as intended.

## Follow-ups

- The B2B 4% Special IVU (§ 32022) remains out of scope for the v1 retail
  engine (unchanged from the module docstring). Not drift.
- If Hacienda publishes a "Días sin IVU" 2026 Carta Circular later in the
  year, update `holidays_for(year)` and relax the regression test for the
  announced year.

## Commits

- `data(PR): full-sweep 2026-11-01 audit — unchanged (11.5% IVU, no 2026 holiday announced)`
