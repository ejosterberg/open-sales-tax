# Daily state sales tax audit — 2026-11-01 (full-sweep: NM)

## TL;DR

- **NM live engine returns rates matching the v0.57 ratchet** at the key
  tier-1 pins: Santa Fe 87501 → 8.1875%, Albuquerque 87102 → 7.625%.
  Both match the NM Taxation & Revenue Department's current GRT schedule
  (eff 2026-07-01) exactly.
- Prod `data_versions`: `NM-SST-V0.55.4` fetched 2026-05-15, `NM-ZCTA-2020`.
  NM is a self-seeded module (not a quarterly SST rate-file consumer),
  so there is no SST filename pin to bump.
- **Open items unchanged from prior audits** — one contradictory
  DOR_GRID pin (recorded in `specs/findings/dor-grid-contradictory-
  duplicate-pins-2026-09.md`) still awaits a primary-source call;
  not fixed in this sweep per briefing's "primary sources only" rule.
- **No code or data change this run.**
- **Status:** UNCHANGED.

## Source

- NM Taxation & Revenue Department, "Gross Receipts Tax Rate Schedule"
  (`https://www.tax.newmexico.gov/businesses/gross-receipts-overview/`).
  Schedule updated semi-annually (01-01 and 07-01).
- The GRT state portion is 4.875% (reduced from 5.0% on 2023-07-01;
  further reductions deferred by SB 2026).

## Procedure

- Live probes (`POST /v1/calculate`, bare ZIP5, $100):
  - `87102` Albuquerque → 7.625% (state 4.875 + ABQ city 2.75) ✓
    matches TRD schedule.
  - `87501` Santa Fe → 8.1875% (state 4.875 + Santa Fe city 3.3125) ✓.
- DOR_GRID pins for NM (lines 6961+): ABQ 7.625, Santa Fe 8.1875, Las
  Cruces 8.390, Rio Rancho 7.875, Farmington 8.1875, Gallup 8.5625,
  Espanola 8.875 — all match current TRD schedule.
- No new NM TRD rate publication noted since v0.57 ratchet (2026-07-01).
  Next scheduled TRD update is 2027-01-01.
- Open DOR_GRID contradictory-pin item (1 NM row) referenced in
  `specs/findings/dor-grid-contradictory-duplicate-pins-2026-09.md` —
  left untouched here because resolving it requires a TRD primary-source
  pull, which belongs with a dedicated finding update, not a drive-by
  edit.

## Known gaps / open items

- 1 contradictory DOR_GRID pin remains (per findings doc).
- NM has ~50 counties/municipalities with distinct GRT rates — the
  v0.57 ratchet covered the top-17 by population. Additional coverage
  is a ratchet candidate, not drift.

## Actions taken

None. Audit report only.
