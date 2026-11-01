# OH — full-sweep audit 2026-11-01

## TL;DR
**Workflow pin is DEAD. Prod data is three quarters behind.** Current
upstream for both kinds is **`OHR2026Q4SEP17` / `OHB2026Q4SEP17`**;
workflow still pins `OHR2026Q4AUG27` / `OHB2026Q4SEP01` which 404.
Tier-1 city rates (Cleveland / Cincinnati / Columbus / Dayton / Toledo /
Akron / Youngstown) match live expectations on the engine — no proven
rate drift found this run — but the next release-tag data rebuild WILL
fail at the fetch step until the pin is adopted. Flag: REFRESH_PENDING.

## Facts

- SST member. Workflow pins (`.github/workflows/build-data-dump.yml`
  lines 227): `"OH 2026Q4AUG27 2026Q4SEP01"`.
- Upstream listing (fetched 2026-11-01):
  - Rates: `OHR2026Q4SEP17.csv`
  - Boundary: `OHB2026Q4SEP17.zip`
  - Both of the pinned filenames are gone from the server (SST hosts
    exactly one file per state per kind). This matches the handoff's
    2026-09-28 note that both pins were superseded by `SEP17` and 404.
- Prod data: `OH-SST-2026Q1NOV28`, fetched 2026-05-04. Three quarters
  stale vs upstream.
- Live probes (via `/v1/rates?zip5=…`):
  | ZIP | City | Live | Expected (`DOR_GRID`) | Delta |
  |---|---|---|---|---|
  | 44101 | Cleveland | 8.000% | 8.000% | 0 |
  | 45202 | Cincinnati | 7.800% | 7.800% | 0 |
  | 43215 | Columbus | 8.000% | 8.000% | 0 |

- COTA multi-district fix (v0.56, iter-169) is already in the engine
  and verified by Columbus 43215 → 8.000%; nothing to reapply.

## Drift

None **proven today**, but prod is three quarters stale and a county
or transit-authority change between NOV28 and SEP17 could silently drift
any non-tier-1 ZIP. The handoff's documented pattern (GA Madison, WA 6
cities, ND Scranton/Drayton) is exactly this: stale SST file, tier-1
cities right, obscure jurisdictions wrong. **An offline systematic diff
of `OHR2026Q4SEP17.csv` vs the Q1NOV28 rows would catch it;** doing it
inside this constrained worktree would require downloading the new
file, which is a human-review step per constitution §11.

## Recommended action

1. **CHIP (new):** Adopt `OHR2026Q4SEP17` / `OHB2026Q4SEP17` in
   `.github/workflows/build-data-dump.yml` (replaces lines 227), then
   run the dump workflow once to prove the fetch resolves, THEN deploy
   + `data load -s OH -v OH-SST-2026Q4SEP17` on `opensalestax-01`.
   Human review of the new rates (county + transit-authority diff) is
   required before adoption.
2. Not auto-fixed in this sweep by design — per constitution §11 and
   the SC/RI audit precedent (2026-09-28), SST pin bumps are a human-
   reviewed adoption, not an automatic sweep. Flagged here so a release
   tag does not fail silently.

## Status

**REFRESH_PENDING.**
