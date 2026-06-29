# Daily state sales tax audit — 2026-06-29 (buffer-day catch-up: SD, TN, TX, UT, VA, VT, WA, WI)

## TL;DR
- **8 jurisdictions audited** — a buffer-day catch-up, not the normal
  2/day pair. The daily rotation started 2026-06-20 (iter-233) but the
  Claude Code app was not open on days 22–25, so the day-22 (SD, TN),
  day-23 (TX, UT), day-24 (VA, VT) and day-25 (WA, WI) pairs were never
  run. Days 27–31 are reserved for exactly this catch-up; today (day 29)
  closes the gap.
- **No real-world rate drift found in any of the 8 states.** Every
  top-city probe returns the correct combined rate for the normal
  call shapes (bare ZIP5 and real ZIP+4).
- **2 issues surfaced:**
  1. **WI Milwaukee stale test pin** (engine correct, pin wrong) —
     fixed in this commit (5.900 → 7.900, WI Act 12 city tax).
  2. **UT `-0001` placeholder county-drop** — a per-ZIP data-resolution
     edge case affecting only the synthetic `-0001` ZIP+4. Low
     real-world impact; written up as a finding and chipped.
- **All 6 SST-member states in this batch are 1+ quarters behind on
  prod and need a Q3 2026 SST refresh** (SD and TN are *much* further
  behind on their rate files). One consolidated refresh chip opened.
- TX and VA (non-SST) are fully current; no action.

## Rotation gap context

| Day | Date | Pair | Ran? |
|----:|------|------|------|
| 21 | 06-21 | RI, SC | ✅ |
| 22 | 06-22 | SD, TN | ❌ → caught up here |
| 23 | 06-23 | TX, UT | ❌ → caught up here |
| 24 | 06-24 | VA, VT | ❌ → caught up here |
| 25 | 06-25 | WA, WI | ❌ → caught up here |
| 26 | 06-26 | WV, WY | ✅ |
| 27–29 | 06-27..29 | buffer | catch-up (this run) |

---

## SD (South Dakota) — SST member
- Source: SST Governing Board rate/boundary index
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates/ ,
  .../Boundary/); cross-checked against SD DOR (state 4.2% reduced
  rate, in effect since 2023-07-01).
- Last loaded on prod: **`SDR2024Q1DEC12.zip`** (rate — 2024 Q1!) /
  `SDB2026Q2FEB23.zip` (boundary — 2026 Q2)
- Latest available: **`SDR2026Q3JUN02.zip` / `SDB2026Q3JUN04.zip`**
- Drift summary: **none.** SD's 4.2% state rate + 2% municipal is
  unchanged, so the very old rate file still yields correct numbers.
- Recommended action: **REFRESH NEEDED** (rate file ~9 quarters stale;
  boundary 1 quarter behind). Chipped.
- Details (live engine):
  | City | Expected (SD DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Sioux Falls (57104) | 6.200% | 6.200% | 0.000 |
  | Rapid City (57701) | 6.200% | 6.200% | 0.000 |
  | Aberdeen (57401) | 6.200% | 6.200% | 0.000 |
  | Pierre (57501) | 6.200% | 6.200% | 0.000 |

## TN (Tennessee) — SST member
- Source: SST Governing Board index; cross-checked against TN DOR Local
  Option Sales Tax + IMPROVE Act transit (Nashville 0.5%).
- Last loaded on prod: **`TNR2025Q1MAR07.csv`** (rate — 2025 Q1) /
  `TNB2026Q2FEB23.zip` (boundary — 2026 Q2)
- Latest available: **`TNR2026Q3JUN11.csv` / `TNB2026Q3MAY22.zip`**
- Drift summary: **none.** All probed cities match exactly, including
  the Nashville and Brentwood IMPROVE Act transit overlays.
- Recommended action: **REFRESH NEEDED** (rate file ~5 quarters behind;
  boundary 1 quarter behind). Chipped.
- Details (live engine):
  | City | Expected (TN DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Nashville/Metro (37201) | 9.750% | 9.750% | 0.000 |
  | Memphis (38103) | 9.750% | 9.750% | 0.000 |
  | Knoxville (37902) | 9.250% | 9.250% | 0.000 |
  | Chattanooga (37402) | 9.250% | 9.250% | 0.000 |
  | Clarksville (37040) | 9.500% | 9.500% | 0.000 |
  | Murfreesboro (37130) | 9.750% | 9.750% | 0.000 |

## TX (Texas) — non-SST
- Source: TX Comptroller (https://comptroller.texas.gov/taxes/sales/).
  Structure: state 6.25% + up to 2.0% local = **8.25% statewide cap**.
- Drift summary: **none.** All 6 probed metros sit at the 8.25% cap.
- Recommended action: none — current.
- Details (live engine):
  | City | Expected (TX Comptroller) | Actual (engine) | Delta |
  |---|---|---|---|
  | Houston (77002) | 8.250% | 8.250% | 0.000 |
  | Dallas (75201) | 8.250% | 8.250% | 0.000 |
  | Austin (78701) | 8.250% | 8.250% | 0.000 |
  | San Antonio (78205) | 8.250% | 8.250% | 0.000 |
  | Fort Worth (76102) | 8.250% | 8.250% | 0.000 |
  | El Paso (79901) | 8.250% | 8.250% | 0.000 |

## UT (Utah) — SST member
- Source: SST Governing Board index; cross-checked against UT State Tax
  Commission combined rates (state 4.85% + county local + city option).
- Last loaded on prod: `UTR2026Q2MAR20.zip` / `UTB2026Q2MAR20.zip`
- Latest available: **`UTR2026Q3MAY11.zip` / `UTB2026Q3MAY11.zip`**
- Drift summary: **no real-world rate drift** — bare-ZIP5 and real-+4
  lookups all return the correct combined rate. **One data-resolution
  edge case:** the synthetic `-0001` ZIP+4 drops the county binding for
  some ZIPs (Provo, St George, Clearfield), under-collecting by the
  county rate. Normal callers (no +4, or any real +4) are unaffected.
- Recommended action: (a) **REFRESH NEEDED** to Q3 (chipped, with the
  SST batch); (b) **investigate the `-0001` county-drop** — written up
  in `specs/findings/ut-zip4-0001-county-drop-2026-06.md` and chipped.
  Do NOT auto-fix the affected DOR_GRID pins by swapping their ZIP+4.
- Details (live engine):
  | City | Expected (UT TC) | Actual (engine, no +4) | `-0001` quirk |
  |---|---|---|---|
  | Salt Lake City (84111) | 8.450% | 8.450% | ok (8.450) |
  | Ogden (84401) | 7.250% | 7.250% | ok (7.250) |
  | Provo (84601) | 7.450% | 7.450% | **4.950 ✗ county dropped** |
  | Orem (84057) | 7.450% | 7.450% | ok (7.450) |
  | St George (84770) | 6.750% | 6.750% | **5.150 ✗ county dropped** |
  | Clearfield (84015) | 7.250% | 7.250% | **4.950 ✗ county dropped** |

## VA (Virginia) — non-SST
- Source: VA Tax (https://www.tax.virginia.gov/retail-sales-and-use-tax).
  Structure: state 4.3% + state-mandated local 1.0% = 5.3% base;
  regional add-ons of 0.7% (Hampton Roads, Northern VA, Central VA)
  and the Historic Triangle 1.0% (Williamsburg/James City/York).
- Drift summary: **none.** Regional structure intact across all tiers.
- Recommended action: none — current.
- Details (live engine):
  | City | Expected (VA Tax) | Actual (engine) | Delta |
  |---|---|---|---|
  | Virginia Beach (23451) | 6.000% | 6.000% | 0.000 |
  | Norfolk (23510) | 6.000% | 6.000% | 0.000 |
  | Chesapeake (23320) | 6.000% | 6.000% | 0.000 |
  | Alexandria (22301) | 6.000% | 6.000% | 0.000 |
  | Newport News (23601) | 6.000% | 6.000% | 0.000 |
  | Hampton (23666) | 6.000% | 6.000% | 0.000 |

## VT (Vermont) — SST member
- Source: SST Governing Board index; cross-checked against VT DOR
  (state 6% + 1% Local Option Sales Tax in adopting municipalities).
- Last loaded on prod: `VTR2026Q2FEB20.zip` / `VTB2026Q2FEB20.zip`
- Latest available: **`VTR2026Q3MAY20.zip` / `VTB2026Q3MAY20.zip`**
- Drift summary: **none.** LOST municipalities at 7%, non-LOST
  (Bennington) at 6%.
- Recommended action: **REFRESH NEEDED** to Q3 (chipped with the batch).
- Details (live engine):
  | City | Expected (VT DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Burlington (05401) | 7.000% | 7.000% | 0.000 |
  | Montpelier (05602) | 7.000% | 7.000% | 0.000 |
  | Essex Junction (05452) | 7.000% | 7.000% | 0.000 |
  | Middlebury (05753) | 7.000% | 7.000% | 0.000 |
  | Barre City (05641) | 7.000% | 7.000% | 0.000 |
  | St. Albans City (05478) | 7.000% | 7.000% | 0.000 |

## WA (Washington) — SST member
- Source: SST Governing Board index; cross-checked against WA DOR
  (state 6.5% + local combined, varies by location code).
- Last loaded on prod: `WAR2026Q2FEB26.zip` / `WAB2026Q2FEB26.zip`
- Latest available: **`WAR2026Q3MAY27.zip` / `WAB2026Q3MAY27.zip`**
- Drift summary: **none** in the probed cities.
- Recommended action: **REFRESH NEEDED** to Q3 (chipped with the batch).
  WA changes local rates frequently; the Q3 load is worth applying to
  catch smaller-jurisdiction movements the top-cities probe doesn't see.
- Details (live engine):
  | City | Expected (WA DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Bellevue (98004) | 10.300% | 10.300% | 0.000 |
  | Tacoma (98402) | 10.400% | 10.400% | 0.000 |
  | Vancouver (98660) | 8.900% | 8.900% | 0.000 |
  | Bellingham (98225) | 9.100% | 9.100% | 0.000 |
  | Federal Way (98003) | 10.300% | 10.300% | 0.000 |
  | Renton (98055) | 10.500% | 10.500% | 0.000 |

## WI (Wisconsin) — SST member
- Source: SST Governing Board index; cross-checked against WI DOR
  (state 5% + county 0.5%/0.9% + Milwaukee city 2% per Act 12).
- Last loaded on prod: `WIR2026Q2FEB18.csv` / `WIB2026Q2FEB18.zip`
- Latest available: **`WIR2026Q3MAY22.csv` / `WIB2026Q3MAY22.zip`**
- Drift summary: **no engine drift.** Milwaukee correctly returns
  7.900% (Act 12 city tax). A **stale DOR_GRID pin** (`53202-2402`
  expected 5.900%, predating Act 12) was the only mismatch — fixed in
  this commit. The parallel `53202-0001` pin already expected 7.900%.
- Recommended action: (a) **REFRESH NEEDED** to Q3 (chipped with the
  batch); (b) test-pin fix committed.
- Details (live engine):
  | City | Expected (WI DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Milwaukee (53202) | 7.900% | 7.900% | 0.000 |
  | Madison (53703) | 5.500% | 5.500% | 0.000 |
  | Green Bay (54301) | 5.500% | 5.500% | 0.000 |
  | Janesville (53545) | 5.500% | 5.500% | 0.000 |
  | Eau Claire (54701) | 5.500% | 5.500% | 0.000 |

---

## Actions taken
- **1 commit (this report + test fix):**
  - Fixed stale WI Milwaukee `53202-2402` DOR_GRID pin (5.900 → 7.900,
    WI Act 12 city tax) in
    `tests/integration/test_sst_dor_validation.py`.
- **1 finding written + chipped:**
  - `specs/findings/ut-zip4-0001-county-drop-2026-06.md` (UT `-0001`
    placeholder drops county for some ZIPs).
- **1 consolidated SST refresh chip** for the 6 SST states in this
  batch needing Q3 2026 (SD, TN, UT, VT, WA, WI). SST files are not
  auto-pulled per audit policy.
- `specs/handoff.md` updated: added the 6 Q3 refreshes and the UT
  `-0001` finding to open follow-ups.
- Report committed/pushed only after the mandatory quality-gate +
  SonarQube scan passed with zero new BLOCKER/CRITICAL.

## Latest-version reference (for the refresh chip)
| State | Prod rate | Prod boundary | Latest rate | Latest boundary |
|---|---|---|---|---|
| SD | SDR2024Q1DEC12 | SDB2026Q2FEB23 | **SDR2026Q3JUN02** | **SDB2026Q3JUN04** |
| TN | TNR2025Q1MAR07 | TNB2026Q2FEB23 | **TNR2026Q3JUN11** | **TNB2026Q3MAY22** |
| UT | UTR2026Q2MAR20 | UTB2026Q2MAR20 | **UTR2026Q3MAY11** | **UTB2026Q3MAY11** |
| VT | VTR2026Q2FEB20 | VTB2026Q2FEB20 | **VTR2026Q3MAY20** | **VTB2026Q3MAY20** |
| WA | WAR2026Q2FEB26 | WAB2026Q2FEB26 | **WAR2026Q3MAY27** | **WAB2026Q3MAY27** |
| WI | WIR2026Q2FEB18 | WIB2026Q2FEB18 | **WIR2026Q3MAY22** | **WIB2026Q3MAY22** |
