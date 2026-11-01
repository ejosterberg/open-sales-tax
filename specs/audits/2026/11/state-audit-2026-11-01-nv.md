# Daily state sales tax audit — 2026-11-01 (full-sweep: NV)

## TL;DR

- **NV is SST but Nevada has not been republished by SST since
  2025-11-05** — the one file upstream remains `NVR2025Q4NOV05` /
  `NVB2025Q4NOV05`, and prod carries that exact label (`NV-SST-2025Q4NOV05`,
  fetched 2026-05-04). This is the "SST never republished" case the
  `check_sst_pins.py` module describes — pin matches the only file
  upstream, so it is current, not stale.
- **Live probes:** Las Vegas 89101 → 8.375% (Clark County LVCT) ✓;
  Carson City 89701 → 7.60% ✓. Both match NV DOR's published rate
  table (`https://tax.nv.gov/sales-use-tax/`), effective 2026-04-01.
- **No code or data change this run.**
- **Status:** UNCHANGED.

## Source

- SST Governing Board rate/boundary index — single file per state.
- NV Department of Taxation, Sales/Use Tax Rate Chart (effective
  2026-04-01). Clark County combined 8.375%, Washoe 8.265%, Carson
  City 7.60%, Churchill 7.60%, Douglas 7.10%, Elko 7.10%, Esmeralda
  6.85%, Eureka 6.85%, Humboldt 6.85%, Lander 7.10%, Lincoln 7.10%,
  Lyon 7.10%, Mineral 6.85%, Nye 7.60%, Pershing 7.10%, Storey 7.60%,
  White Pine 7.725%.
- `src/opensalestax/data/sst_index.py` documents the "never-republished"
  states (IN 2008, KY 2012, MI 2023, NJ 2018, **NV 2025**, RI 2019).

## Procedure

- `check_sst_pins.py` logic: compare pinned filename to the single file
  upstream. For NV, pin and upstream both resolve to `2025Q4NOV05`, so
  the pin is current.
- Live probes against `api.opensalestax.org`:
  - `89101` Las Vegas → 8.375% ✓
  - `89701` Carson City → 7.60% ✓
- Spot check NV DOR Tax Notice archive
  (`https://tax.nv.gov/division/tax-publications/`) for any 2026-Q4
  local change: none announced; the quarterly table in use is still
  the 2026-04-01 edition. Nevada's county option taxes are
  statutorily capped and changes require legislative action.
- DOR_GRID pins for NV (lines 195–196): Las Vegas 8.375 ✓,
  Reno 8.265 ✓. Both match.

## Known gaps

None material. NV has no sub-county (city) sales tax.

## Actions taken

None. Audit report only.
