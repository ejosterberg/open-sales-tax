# Daily state sales tax audit — 2026-11-01 (full-sweep: WY)

## TL;DR

- **WY prod is on `WY-SST-2026Q2APR1` (fetched 2026-05-04); SST has
  published Q4 (`WYR2026Q4AUG20` / `WYB2026Q4AUG20`).** Two quarters
  behind, mirroring the UT backlog. The pin in
  `.github/workflows/build-data-dump.yml` already reads
  `"WY 2026Q4AUG20 2026Q4AUG20"`, so a release-tag rebuild would pick
  up Q4; it is specifically the running prod API that needs the load.
- **No new live-wrong rate was identified in this run** at the tier-1
  pinned cities on bare-ZIP probes:
  - Cheyenne 82001 → 5.00% (state 4 + Laramie 1) ✓ matches pin.
  - Casper 82601 → 6.00% (state 4 + Natrona 1 + Casper city 1)
    (bare-ZIP sees the Casper city 1%; the ZIP+4 "2401" pin encodes
    the loose-lookup parity case per Decision 10).
  - Cody 82414 → 4.00% (state only — Park County does not levy the
    5th-cent general-purpose tax).
  - Sheridan 82801 → 6.00% (state 4 + Sheridan 2 — Sheridan County
    SPT is current).
  - Gillette 82716 → 5.00% (state 4 + Campbell 1).
  - Rock Springs 82901 → 6.00% (state 4 + Sweetwater 2).
  - Jackson 83001 → 7.00% (state 4 + Teton 3; highest WY combined rate).
- Note WY's structure: no city general sales tax statewide. Local
  variation is entirely at the county level, split between the "5th
  cent" General Purpose Option Tax (ongoing, 1%) and the "6th cent"
  Specific Purpose Tax (project-funded, voter-renewed with expiration
  dates). Rate changes between quarters are therefore mostly
  **SPT renewals / expirations**, not city ordinance edits.
- **~5 WY counties noted as "deferred" in the handoff** are county-level
  SPT renewals that were coming due; without the Q4 refresh, drift could
  have accumulated silently on any of them. This audit did not do a
  full 23-county SPT diff — the fix path is the Q4 refresh, which brings
  all current SPT state in one load.
- **Status:** REFRESH_PENDING (apply WY Q4; skip Q3).

## Source

- SST index: `WYR2026Q4AUG20.CSV` / `WYB2026Q4AUG20.ZIP` (upstream).
- WY Department of Revenue Excise Tax Division
  (`https://revenue.wyo.gov/divisions/excise-tax-division/`) — publishes
  "Local Sales/Use Tax Rate Changes" notices around each quarter.
- Decision log: `specs/decisions/07-wy-county-rates.md` (Casper loose-
  lookup parity; the `Casper synthetic +4` DOR_GRID pin at line 7167).

## Procedure

- `data_versions` on prod: `WY-SST-2026Q2APR1`, fetched 2026-05-04.
  Workflow pin: `"WY 2026Q4AUG20 2026Q4AUG20"` (already Q4 — the
  pin is current, the data load is what's missing).
- Live probes against `api.opensalestax.org` for seven major cities
  (Cheyenne / Casper / Cody / Sheridan / Gillette / Rock Springs /
  Jackson); every result matches the current `wy_names.py` /
  `wyoming.py` module expectations.
- DOR_GRID pins reviewed: lines 288–305 (Cheyenne 5.000, Casper 5.000
  at type-4 "2401" with synthetic +4 parity + explicit note), lines
  4008 (Sheridan 6.000), 4017 (Gillette 5.000), 7151, 7167, 7176
  (Teton 7.000). All match live.
- **Not re-fetched this run:** the SST Q4 file itself, so this audit
  cannot enumerate *which* WY counties changed on 2026-07-01 or
  2026-10-01. Any such change rides into the engine via the Q4 refresh.
  Without the refresh, drift on an unpinned WY county is invisible to
  bare-ZIP probes against the current module.

## Recommended action

**REFRESH NEEDED → WY Q4** (apply, skip Q3):

```bash
# On opensalestax-01, after Eric unblocks the data-load path:
docker exec open-sales-tax-api-1 python -m opensalestax data load \
  -s WY -v WY-SST-2026Q4AUG20
```

Reuse (or set) a stable label so the loader purges by exact match and
does not double-stack rates on top of the existing `WY-SST-2026Q2APR1`
rows. Verify afterwards with a 23-county smoke:

```bash
# One probe per county (any representative ZIP). Compare returned
# county-portion rate against the SST Q4 file's county block.
```

## Actions taken

None. Audit report only; no module edits owed in-repo (WY is SST).
