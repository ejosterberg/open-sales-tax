# MO state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **MO is non-SST** -- self-seeded from MO DOR 2026 quarterly rate tables
  (dor.mo.gov/taxation/business/tax-types/sales-use/rate-tables/).
- **No live rate drift on probed tier-1 cities.** KCMO 64108 live 8.97500%
  (state 4.225 + Jackson 1.375 + KC 3.25 + Zoo 0.125), St. Louis 63103
  live 9.67900%, Sioux Falls (SD) 57104 cross-check 6.20000% -- all match
  pins. The MO DOR **october2026.pdf / october2026.xlsx** rate tables are
  published but came back binary via WebFetch in this run; cell-level diff
  deferred.
- All iter-170/171 KCMO Clay-side (64118/64119, 64156) + Platte-side
  (64153/64154) pins pass live.
- **Status: UNCHANGED** -- no new drift surfaced; Q4 full-table diff is
  the owed next step but not a blocker.

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| self-seeded | `MO-SELF-V0.56` (per handoff) | 2026-05-15 |
| zcta-census-2020 | `MO-ZCTA-2020` | 2026-05-11 |

(Prod `data_versions` for MO shows `MO-SST-V0.55.4` label but MO is NOT
SST -- the label is historical, the data loader uses MO DOR for rates.)

## MO DOR primary-source check (2026-11-01)

- `dor.mo.gov/taxation/business/tax-types/sales-use/rate-tables/2026/` --
  "10/2026 - 12/2026" PDF (`october2026.pdf`) and xlsx variant exist.
  Binary bodies returned by WebFetch, saved for offline parse.
- MO's quarterly schedule means a Q4 refresh will land city overlay
  changes effective 2026-10-01. **Not probed in this run; chipped.**

## Live probes

| City | ZIP | Expected (pin) | Actual | Delta |
|---|---|---|---|---|
| KCMO (Jackson) | 64108 | 8.975 | 8.975 | 0.00 |
| KCMO (Clay) | 64118 | 8.725 | (pin passes) | 0.00 |
| St. Louis | 63103 | 9.679 | 9.679 | 0.00 |
| Springfield | 65806 | 8.100 | (pin passes) | 0.00 |

## Open follow-ups

- Offline parse `october2026.xlsx`, diff vs. `mo_data.py` (15 seeded cities
  + 114 county portions). Any delta since v0.56 is a candidate chip.
- Cass + North Kansas City city overlays remain deferred per handoff.
- v0.30 long-tail county fills (Lebanon/Laclede, etc.) all pass live.
