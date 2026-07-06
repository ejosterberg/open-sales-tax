# Daily state sales tax audit — 2026-07-06 (day 6: GA + HI)

## TL;DR
- 2 jurisdictions audited. **1 real rate correction found and fixed**
  (HI Maui County 0.5% GET surcharge, under-collected since 2024-01-01),
  requiring code + test updates. **1 SST currency refresh flagged**
  (GA Q2 2026 → Q3 2026 rate file), chipped for Eric's review.
- No engine-vs-pin drift in either state; all top cities matched the
  live engine exactly. The GA finding is a stale-cache currency item;
  the HI finding is a genuine authoritative-rate correction.

## GA (Georgia — SST member)
- **Source:** SST Governing Board rate/boundary file index
  (streamlinedsalestax.org rate-and-boundary-file-updates) + GA DOR
  sales-tax-rate charts.
- **Last loaded on prod:** rate `GAR2026Q2FEB19.csv`, boundary
  `GAB2026Q2FEB16.zip` (Q2 2026).
- **Latest available:** rate **`GAR2026Q3JUN05`** (Q3 2026, posted
  2026-06-08); boundary current (SST GA boundary last posted Q4 2025 /
  prod's Q2 2026 boundary is at least as current).
- **Drift summary:** No real-world rate drift. All 10 GA tier-1 cities
  match the live engine, which matches GA DOR published combined rates.
- **Recommended action:** REFRESH NEEDED — chip the GA Q3 2026 rate-file
  refresh for Eric's review (don't auto-pull SST files). Routine
  currency; no known rate change embedded, but Q3 may carry new/updated
  local jurisdictions that only surface after the load.
- **Details (live engine vs. GA DOR):**

  | City | ZIP+4 | Expected (DOR) | Engine | Delta |
  |------|-------|---------------:|-------:|------:|
  | Atlanta | 30303-1015 | 8.900 | 8.900 | 0 |
  | Savannah | 31401-0001 | 7.000 | 7.000 | 0 |
  | Macon | 31201-0001 | 8.000 | 8.000 | 0 |
  | Athens | 30601-0001 | 8.000 | 8.000 | 0 |
  | Albany | 31701-0001 | 8.000 | 8.000 | 0 |
  | Marietta | 30060-0001 | 6.000 | 6.000 | 0 |
  | Columbus | 31901-0001 | 9.000 | 9.000 | 0 |
  | Roswell | 30075-0001 | 7.750 | 7.750 | 0 |
  | Suwanee | 30024-0001 | 6.000 | 6.000 | 0 |
  | Alpharetta | 30022-1234 | 7.750 | 7.750 | 0 |

## HI (Hawaii — non-SST, hardcoded GET module)
- **Source:** Hawaii DOTAX county-surcharge schedule
  (https://tax.hawaii.gov/geninfo/countysurcharge/) + Maui County
  Council public notice (Ordinance 5511).
- **Last loaded on prod:** self-seeded from `hi_data.py` (no SST file).
- **Latest available:** N/A (module-encoded). Authoritative source
  says Maui County surcharge = 0.5%, effective 2024-01-01 → 2030-12-31.
- **Drift summary:** **Real under-collection.** The engine returned
  **4.000%** for Maui County (96732 Kahului); the correct combined rate
  is **4.500%** (state 4.0% + Maui County 0.5% surcharge, in effect
  since 2024-01-01). `hi_data.py` wrongly recorded Maui at 0.000% with a
  "not enacted" comment. Under-collection has been live since 2024-01-01.
- **Recommended action:** FIXED in repo — Maui 0.000→0.500%, effective
  2024-01-01; all HI docstrings/notes, the coverage warning, and the
  Kahului live pin updated. **Prod HI reload chipped** (live engine
  still returns 4.0% until redeploy). Full write-up:
  `specs/findings/hi-maui-county-surcharge-2026-07.md`.
- **Details (live engine vs. HI DOTAX):**

  | County / City | ZIP+4 | Expected (DOTAX) | Engine (pre-fix) | Delta |
  |---------------|-------|-----------------:|-----------------:|------:|
  | Honolulu (Oahu) 96813 | 0001 | 4.500 | 4.500 | 0 |
  | Hilo (Hawaii Co) 96720 | 0001 | 4.500 | 4.500 | 0 |
  | Lihue (Kauai) 96766 | 0001 | 4.500 | 4.500 | 0 |
  | **Kahului (Maui) 96732** | 0001 | **4.500** | **4.000** | **+0.500 under** |
  | Pearl City (Oahu) 96782 | 0001 | 4.500 | 4.500 | 0 |
  | Kailua-Kona (Hawaii Co) 96740 | 0001 | 4.500 | 4.500 | 0 |

## Actions taken
1. **HI Maui fix (committed):** `hi_data.py` Maui 0.000→0.500% eff
   2024-01-01; `hawaii.py` docstring/notes; removed HI from
   `coverage.py` warning set (gap now closed); cleaned stale "HI Maui
   dispute" references in API schemas/handlers; updated
   `test_state_hawaii.py`, `test_core_coverage.py`, and the Kahului
   `test_sst_dor_validation.py` pin. Findings doc added.
2. **HI prod reload (chipped):** live engine returns old 4.0% for Maui
   until redeploy + `data load -s HI`.
3. **GA Q3 2026 SST refresh (chipped):** currency refresh Q2→Q3, no
   real-world drift.

## Notes for future audits
- **GA CY2026 stable:** GA combined rates for the top-10 cities are
  steady vs. Q2; the Q3 file is a currency bump, not a rate change.
- **HI now fully modeled:** all four inhabited counties at 4.5%
  combined; HI removed from the coverage-warning set. If a future HI
  county surcharge lapses (all current ones sunset 2030-12-31), revisit.
