# Full-sweep state audit — GA — 2026-11-01

## TL;DR

- **GA is SST**. Prod is still on `GAR2026Q2FEB19` / `GAB2026Q2FEB16`
  (fetched 2026-05-04). Latest SST publishes **`GAR2026Q4OCT01.csv` /
  `GAB2026Q4AUG20.zip`** — one quarter beyond Q3 2026, two beyond prod.
- **Q4 moves 10 counties** effective **2026-10-01**, plus the known
  Madison 4% → 3% from 2026-07-01. **Two of the 10 Q4 moves hit tier-1
  cities**:
  - **Richmond (Augusta) 4.5% → 5.0%** — Augusta `30901` under-collects
    0.5pp (engine 8.500 vs GA DOR 9.000). Pinned this run.
  - **Dougherty (Albany) 4.0% → 5.0%** — Albany `31701` under-collects
    1.0pp (engine 8.000 vs GA DOR 9.000). Existing pin bumped
    8.000 → 9.000.
- **Madison County 4% → 3% (eff 2026-07-01)**: still over-collects
  1.0pp since 2026-07-01. Pin `30633 → 7.000` continues to fail under
  `-m liveapi` by design. 123 days unapplied.
- **GA is SST; there is no code fix.** The fix is one `data load -s GA`
  against `GAR2026Q4OCT01.csv` (reusing the existing label).
- **GA Q4 fixture deliberately NOT swapped in repo.**
  `fixtures/ga/GAR2026Q2FEB19.csv` is referenced by filename in
  `tests/unit/test_state_georgia.py` and in `georgia.py` docstrings;
  swapping belongs with the reviewed SST refresh, not this audit.
- **Commit** adds 1 new DOR_GRID pin (Augusta 30901 → 9.000) and bumps
  1 (Albany 31701 → 9.000); both fail under `-m liveapi` until prod
  loads GA Q4.

## Prod data version

```
GA | sst              | GA-SST-2026Q2FEB19 | 2026-05-04
GA | zcta-census-2020 | GA-ZCTA-2020       | 2026-05-11
```

## SST file index (2026-11-01)

```
GAR2026Q4OCT01.csv   (latest rate)
GAB2026Q4AUG20.zip   (latest boundary)
```

## Q2 → Q4 county-rate diff (every row that changed)

Diffed `fixtures/ga/GAR2026Q2FEB19.csv` against downloaded
`GAR2026Q4OCT01.csv`:

| County (FIPS) | Q2 (prod) | Q4 | Effective | GA DOR Q4 chart |
|---|---|---|---|---|
| **049 Charlton** | 3.0 | **4.0** | 2026-10-01 | "024 Charlton 8" ✓ |
| **095 Dougherty (Albany)** | 4.0 | **5.0** | 2026-10-01 | "047 Dougherty 9" ✓ |
| **149 Marion** | 3.0 | **4.0** | 2026-10-01 | "096 Marion 8" ✓ |
| **153 Monroe** | 3.0 | **4.0** | 2026-10-01 | "102 Monroe 9" (with 63-row stack) ✓ |
| **165 Peach** | 4.0 | **5.0** | 2026-10-01 | "111 Peach 9" ✓ |
| **195 Madison** | 4.0 | **3.0** | 2026-07-01 | "095 Madison 7" ✓ (known, 123 days unapplied) |
| **207 Rockdale** | 4.0 | **5.0** | 2026-10-01 | "122 Rockdale 7 E H S" (homestead stack) |
| **245 Richmond (Augusta)** | 4.5 | **5.0** | 2026-10-01 | "121 Richmond 9" ✓ |
| **267 Tattnall** | 4.0 | **5.0** | 2026-10-01 | "132 Tattnall 9" ✓ |
| **281 Towns** | 4.0 | **3.0** | 2026-10-01 | "139 Towns 7" ✓ (decrease) |
| **315 Warren** | 4.0 | **5.0** | 2026-10-01 | "149 Warren 9" ✓ |

Rockdale (207) GA DOR chart shows combined 7 with EHS letters =
Educational/Homestead/SPLOST stack; the 5% in the SST file is the
county overlay; the engine would then compound these via the type-63
MARTA / HOST entries so the final combined may differ from a naive
state+county sum. This audit does not re-derive the Rockdale stack —
calling it out as a check for the post-Q4-reload probe.

## Live engine probes (bare ZIP, `/v1/rates`)

| ZIP | City (county) | Engine | GA DOR Q4 expected | Delta |
|---|---|---|---|---|
| 30303 | Atlanta (Fulton + MOST) | 8.900 | 8.900 | 0.00 ✓ |
| 30901 | **Augusta (Richmond)** | **8.500** | **9.000** | **−0.500** (Q4) |
| 31701 | **Albany (Dougherty)** | **8.000** | **9.000** | **−1.000** (Q4) |
| 30633 | Danielsville (Madison) | **8.000** | **7.000** | **+1.000** (over, Q3) |

Albany and Augusta are the only two tier-1 cities impacted by the Q4
file. Madison continues to over-collect (123 days).

## Changes made this audit

### `tests/integration/test_sst_dor_validation.py`

1. **Albany `31701` pin bumped 8.000 → 9.000** (Dougherty +1.0pp eff
   2026-10-01); source note cites GAR2026Q4OCT01.csv county 095 and GA
   DOR Q4 2026 rate chart. Fails under `-m liveapi` until prod loads
   GA Q4.
2. **New pin: Augusta `30901` → 9.000** (Richmond 4.5 → 5.0, eff
   2026-10-01); appended to the daily-audit pin block near line 6820,
   adjacent to the existing Madison `30633 → 7.000` pin. Fails under
   `-m liveapi` until prod loads GA Q4.

## Status

- **REFRESH / RELOAD PENDING** — one `data load -s GA` resolves 11
  stale county rates (10 Q4 + 1 Q3) and both tier-1 pins.
- **No code change** — GA SST state.

## Reload command (for Eric when deploy unblocks)

```bash
ssh opensalestax-01 'cd /home/ejosterberg/open-sales-tax && \
  git pull --ff-only origin main && \
  docker compose build api && \
  docker compose up -d --force-recreate api && \
  docker exec open-sales-tax-api-1 python -m opensalestax data load \
    -s GA -v GA-SST-2026Q2FEB19'
```

Reuse the existing label (loader purges by exact label match). After
reload, the Augusta and Albany pins should xpass; Madison 30633 should
too. The GA Q2 fixture file can stay in repo until the reviewed Q4
fixture swap is cut.
