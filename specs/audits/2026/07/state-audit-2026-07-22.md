# Daily state sales tax audit — 2026-07-22 (day 22: SD + TN)

## TL;DR
- **2 states audited** (SD, TN — both SST members). **0 rate changes found;
  0 requiring code/test updates.**
- **No real-world rate drift in either state.** Every tier-1 city probe returns
  the correct combined rate on the live engine, identical to the 2026-06-29
  buffer-day audit (23 days ago) — no movement.
- **One standing item persists (not new):** both prod SST *rate* files are
  badly stale (SD ~9 quarters, TN ~5 quarters behind) and boundary files are
  1 quarter behind. Latest available is still **Q3 2026** — no Q4 file posted
  yet (Q4 posts ~mid-September). The Q3 refresh was already chipped on
  2026-06-29 but has **not been applied to prod**. Re-chipped today (chips do
  not persist across app restarts, and it's been 23 days).
- **No commits with code/data changes** — the stale files still yield correct
  numbers because neither state's rates have moved, so this is a
  file-currency-hygiene item, not a correctness fix. SST files are never
  auto-pulled per audit policy — Eric reviews/applies the refresh.

## SD (South Dakota) — SST member
- Source: SST Governing Board rates index
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates/); cross-checked
  against SD DOR structure (state **4.2%** reduced rate + up to 2% municipal;
  no county general sales tax).
- Last loaded on prod: **`SDR2024Q1DEC12.zip`** (rate — 2024 Q1) /
  **`SDB2026Q2FEB23.zip`** (boundary — 2026 Q2)
- Latest available: **`SDR2026Q3JUN02.zip` / `SDB2026Q3JUN04.zip`** (unchanged
  since the 2026-06-29 audit; no Q4 posted)
- Drift summary: **none.** SD's 4.2% state rate is uniform statewide and
  unchanged (the 2023 reduction from 4.5%→4.2% runs through **2027-06-30**,
  then sunsets back to 4.5% unless extended — flag for a CY2027 audit).
  Municipal 2% unchanged. The old rate file still yields correct numbers.
- Recommended action: **REFRESH NEEDED** (rate file ~9 quarters stale;
  boundary 1 quarter behind). Re-chipped.
- Details (live engine, 2026-07-22):
  | City | Expected (SD DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Sioux Falls (57104) | 6.200% | 6.200% | 0.000 |
  | Rapid City (57701) | 6.200% | 6.200% | 0.000 |
  | Aberdeen (57401) | 6.200% | 6.200% | 0.000 |
  | Pierre (57501) | 6.200% | 6.200% | 0.000 |
  | Brookings (57006) | 6.200% | 6.200% | 0.000 |
  | Vermillion (57069) | 6.200% | 6.200% | 0.000 |
  | Yankton (57078) | 6.200% | 6.200% | 0.000 |
  | Watertown (57201) | 6.200% | 6.200% | 0.000 |

## TN (Tennessee) — SST member
- Source: SST Governing Board rates index; cross-checked against TN DOR Local
  Option Sales Tax structure (state **7%** + local option ≤2.75%) + IMPROVE Act
  transit (Nashville/Davidson 0.5%) + Memphis city 0.5%.
- Last loaded on prod: **`TNR2025Q1MAR07.csv`** (rate — 2025 Q1) /
  **`TNB2026Q2FEB23.zip`** (boundary — 2026 Q2)
- Latest available: **`TNR2026Q3JUN11.csv` / `TNB2026Q3MAY22.zip`** (unchanged
  since the 2026-06-29 audit; no Q4 posted)
- Drift summary: **none.** All probed cities match exactly, including the
  Nashville and Memphis overlays. No enacted July-1-2026 county local-option
  change (HB308 — authorizing a 3.75% jail-construction local option for
  certain counties — is only "as introduced," not law). The engine's 9.75% for
  Nashville/Memphis is correct per the cited model: Memphis = state 7% + Shelby
  2.25% + Memphis city 0.5%; Nashville = state 7% + Davidson 2.25% + IMPROVE
  Act 0.5% transit.
- Recommended action: **REFRESH NEEDED** (rate file ~5 quarters behind;
  boundary 1 quarter behind). Re-chipped.
- Details (live engine, 2026-07-22):
  | City | Expected (TN DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Nashville/Metro (37201) | 9.750% | 9.750% | 0.000 |
  | Memphis (38103) | 9.750% | 9.750% | 0.000 |
  | Knoxville (37902) | 9.250% | 9.250% | 0.000 |
  | Chattanooga (37402) | 9.250% | 9.250% | 0.000 |
  | Clarksville (37040) | 9.500% | 9.500% | 0.000 |
  | Murfreesboro (37130) | 9.750% | 9.750% | 0.000 |
  | Johnson City (37604) | 9.500% | 9.500% | 0.000 |
  | Cleveland (37311) | 9.750% | 9.750% | 0.000 |

---

## Actions taken
- **0 code/data commits** — no drift; both states' rates are unchanged, so the
  stale prod files still return correct numbers.
- **1 report file** (this file).
- **1 SST refresh chip** re-opened: refresh SD + TN to Q3 2026
  (`SDR2026Q3JUN02`/`SDB2026Q3JUN04`, `TNR2026Q3JUN11`/`TNB2026Q3MAY22`).
  Supersedes the 2026-06-29 consolidated chip (which also covered UT/VT/WA/WI —
  those are re-audited on their own rotation days 23–25).
- `specs/handoff.md` open-follow-ups updated to reflect the re-audit (SD/TN
  still clean; refresh still pending application).

## Latest-version reference (for the refresh chip)
| State | Prod rate | Prod boundary | Latest rate | Latest boundary |
|---|---|---|---|---|
| SD | SDR2024Q1DEC12 | SDB2026Q2FEB23 | **SDR2026Q3JUN02** | **SDB2026Q3JUN04** |
| TN | TNR2025Q1MAR07 | TNB2026Q2FEB23 | **TNR2026Q3JUN11** | **TNB2026Q3MAY22** |

## Flags for future audits
- **SD CY2027:** the 4.2% state rate sunsets back to **4.5%** on **2027-06-30**
  unless the legislature extends it. Re-verify SD in the July-2027 rotation
  (and watch the 2027 legislative session) — if it reverts, every SD combined
  rate rises 0.3% and the engine will need a data reload against the then-current
  SST file.
