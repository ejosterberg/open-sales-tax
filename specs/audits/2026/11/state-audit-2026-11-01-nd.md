# ND state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **ND is 2 quarters stale on prod** (`NDR2026Q2FEB11` / `NDB2026Q2FEB19`); latest
  upstream is **`NDR2026Q4AUG14` / `NDB2026Q4AUG14`** (2026-Q3 skipped, apply Q4).
- **3 live under-collections** confirmed by live probe (`api.opensalestax.org`):
  Scranton 58653 (-1.00pp), Drayton 58225 (-2.00pp), **Minot 58701 (-0.50pp since
  2026-10-01, 31 days)**.
- No code fix is possible -- ND is SST. The fix is the `data load -s ND
  -v ND-SST-2026Q2FEB11` (or new label) refresh of the Q4 file.
- Minot pin bumped `7.500 -> 8.000` with Q4 attribution.
- **Status: REFRESH_PENDING** (chipped; data refresh owed).

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| sst | `ND-SST-2026Q2FEB11` | 2026-05-15 |
| zcta-census-2020 | `ND-ZCTA-2020` | 2026-05-11 |

## Upstream (SST Governing Board, 2026-11-01)

- Rate: `NDR2026Q4AUG14.zip`
- Boundary: `NDB2026Q4AUG14.zip`

## Live probes (`/v1/calculate` bare-ZIP, $100)

| City | ZIP | Expected (ND notice) | Actual | Delta | Effective |
|---|---|---|---|---|---|
| Fargo | 58102 | 7.750 | (passes) | 0.00 | -- |
| Minot | 58701 | **8.000** | **7.500** | **-0.50** | **2026-10-01** |
| Scranton | 58653 | 7.000 | 6.000 | -1.00 | 2026-07-01 |
| Drayton | 58225 | 8.500 | 6.500 | -2.00 | 2026-07-01 |

Sources: ND Office of State Tax Commissioner permit-holder notices
(Minot 0.5% increase ordinance; Scranton new 2% sales/use/gross-receipts;
Drayton cumulative 1% + 0.5% + 2% = 3.5% total local).

## Changes committed

1. `tests/integration/test_sst_dor_validation.py` -- Minot pin
   `7.500 -> 8.000`, comment updated with Q4 effective-date attribution.
   Fails under `-m liveapi` until the Q4 refresh loads on prod.
2. No module changes required (ND rates come wholly from the SST file).

## Open follow-ups

- Load `NDR2026Q4AUG14` + `NDB2026Q4AUG14` on prod -- resolves all three
  under-collections at once.
- Fargo (Resolution 1756025) and Ellendale (Article 5.0309) boundary
  changes effective 2026-10-01 ride in on the Q4 boundary file.
- Deferred: ND local tax maximum/refund-cap caps (Kindred, Walhalla 2026-10-01
  cap removals) remain a documented engine gap, not drift.
