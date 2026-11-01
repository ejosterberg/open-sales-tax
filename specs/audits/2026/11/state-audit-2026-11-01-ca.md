# CA state-tax audit — 2026-11-01 (full-sweep Pacific)

**Auditor:** region-agent (Pacific sweep)
**Branch:** `audit-sweep-pac-20261101`
**Status:** FIXED (test-pin cleanup); refresh-pending open for aggregator sweep

## What was checked

- `src/opensalestax/states/ca_data.py` (55 counties, 217 cities)
- `tests/integration/test_sst_dor_validation.py` CA DOR_GRID block
- Prod `data_versions` for CA: `CA-SST-V0.55.4` fetched 2026-05-15

## Findings

### 1. 7 contradictory DOR_GRID pins — FIXED THIS RUN

The 2026-09-28 sweep identified 7 CA ZIP+4s each carrying two contradictory
DOR_GRID rows. CDTFA 2026-07-01 rate schedule independently confirms the
engine (and the higher pin) in every case; the lower pins were stale
county-only leftovers from pre-city-coverage (iter-62 ZCTA expansion and
post-zip_county landings) that `-m liveapi` kept hidden from CI.

Removed the 7 stale lower pins:

| ZIP | City | Removed (stale) | Kept (CDTFA-verified) |
|---|---|---:|---:|
| 91501 | Burbank | 9.500 | 10.500 |
| 92590 | Temecula | 7.750 | 8.750 |
| 93401 | San Luis Obispo | 8.250 | 8.750 |
| 94010 | Burlingame | 9.375 | 9.625 |
| 94559 | Napa | 7.750 | 8.750 |
| 94965 | Sausalito | 8.250 | 9.250 |
| 95501 | Eureka | 9.500 | 10.250 |

Also re-cited the 5 surviving pins that previously cited **SalesTaxHandbook**
to **CDTFA 2026-07-01 schedule** (constitution §2 — primary sources only).
The 2 Burbank pins already cited CDTFA directly.

### 2. CDTFA Q4 2026 rate schedule — PUBLISHED, prod stale

**CDTFA has published "Tax Rates Effective October 1, 2026"** at
https://www.cdtfa.ca.gov/taxes-and-fees/sales-use-tax-rates.htm
(download: `SalesTaxRates10-1-26.xlsx`). Prod CA is still on
`CA-SST-V0.55.4` fetched 2026-05-15 (Q2 2026). Latest SST file (if
published) also unknown this run — SST state-tax-files index returned
404 to the audit fetch. **Refresh almost certainly needed.** The next
rotation day (2026-11-03, day 3) should diff the Oct-1 schedule against
`ca_data.py` and the kept DOR_GRID pins (which currently cite the
Q3 effective 2026-07-01 schedule).

### 3. 159 aggregator-cited pins still outstanding

Of the 790 DOR_GRID rows, 159 CA pins cite SalesTaxHandbook/Avalara. The 5
touched here were re-cited; **154 remain**. This is the same unsafe
population that produced the AZ September over-collections. Chipped for a
dedicated re-citation sweep.

## Files touched

- `tests/integration/test_sst_dor_validation.py` (CA DOR_GRID block only)

## Live engine status

No change to the live engine. This commit only cleans up a test-integrity
defect that would silently mask real rate drift (the Sahuarita AZ precedent).

## Commits

- `data(CA): full-sweep 2026-11-01 remove 7 contradictory DOR_GRID pins; re-cite 5 to CDTFA`
