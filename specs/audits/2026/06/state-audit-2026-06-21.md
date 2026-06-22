# Daily state sales tax audit — 2026-06-21 (day 21: RI + SC)

## TL;DR
- 2 jurisdictions audited (RI = SST member, SC = non-SST).
- **0 rate changes found. 0 requiring code/test updates.** Both
  jurisdictions are fully current with their authoritative sources.
- RI: live engine returns the correct flat 7% statewide for all 6
  probed cities. The prod-cached SST file (`RIR2019Q2MAR27.csv`) is
  the **latest file SST publishes for RI** — confirmed against the
  SST rates index — so no refresh is available or needed.
- SC: full 46-county cross-check of the engine against the SC DOR
  ST-500 (Rev. 3/9/2026, effective May 1, 2026, pub 5182) — every
  county's combined rate and tax-type code matches exactly,
  including the most recent change (Williamsburg County +1% CP
  effective 2026-05-01), which is live on prod.

## RI (Rhode Island) — SST member
- Source: SST rates index
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates/)
- Last loaded on prod: `RIR2019Q2MAR27.csv` / `RIB2019Q2MAR27.csv`
- Latest available from SST: `RIR2019Q2MAR27.csv` — **same file.**
  RI is a flat-rate, no-local-tax state, so SST does not re-publish a
  new quarterly rate file; the 2019Q2 file remains the current
  upstream release. (The prod cache being from 2019 is therefore
  *correct*, not stale.)
- Drift summary: none. Statewide 7% (R.I. Gen. Laws § 44-18-18,
  unchanged since the 2012 rate) confirmed live across 6 cities.
- Recommended action: none. No refresh exists or is needed.
- Details (live engine, $100 line item):
  | City | Expected (statute) | Actual (engine) | Delta |
  |---|---|---|---|
  | Providence (02903) | 7.000% | 7.000% | 0.000 |
  | Warwick (02886) | 7.000% | 7.000% | 0.000 |
  | Cranston (02910) | 7.000% | 7.000% | 0.000 |
  | Pawtucket (02860) | 7.000% | 7.000% | 0.000 |
  | Woonsocket (02895) | 7.000% | 7.000% | 0.000 |
  | Newport (02840) | 7.000% | 7.000% | 0.000 |

## SC (South Carolina) — non-SST
- Source: SC DOR ST-500 "Local Tax Designation by County"
  (https://dor.sc.gov/sites/dor/files/forms/ST500.pdf), Rev. 3/9/2026,
  effective May 1, 2026, publication 5182.
- Last encoded in `sc_data.py`: ST-500 effective May 1, 2026
  (audit refreshed 2026-05-04). All 46 counties encoded.
- Latest available: same edition (effective May 1, 2026). SC local
  taxes change almost exclusively on a May 1 effective date following
  November referendums; the current ST-500 is in force through at
  least 2027-04-30.
- Drift summary: none. Full 46-county cross-check of the engine's
  `SC_COUNTY_RATE_PCT` against the live ST-500 PDF — every combined
  rate and tax-type letter code matches.
- Recommended action: none.
- Verified 2026 changes (all already live on prod):
  - Williamsburg County +1% Capital Projects Tax, eff. 2026-05-01 →
    8% combined. Validated live: Kingstree 29556 = 8.000%.
  - Aiken County reimposed Capital Projects Tax (combined stays 8%) —
    engine: Aiken 2.000% local → 8%.
  - Lexington County extended School District Tax, eff. 2026-03-01
    (combined stays 7%) — engine: Lexington 1.000% (SD) → 7%.
- City spot-checks (live engine, $100 line item):
  | City (county) | Expected (ST-500) | Actual (engine) | Delta |
  |---|---|---|---|
  | Columbia (Richland) 29201 | 8.000% | 8.000% | 0.000 |
  | Charleston (Charleston) 29401 | 9.000% | 9.000% | 0.000 |
  | North Charleston (Charleston) 29406 | 9.000% | 9.000% | 0.000 |
  | Mount Pleasant (Charleston) 29464 | 9.000% | 9.000% | 0.000 |
  | Rock Hill (York) 29730 | 7.000% | 7.000% | 0.000 |
  | Greenville (Greenville) 29601 | 6.000% | 6.000% | 0.000 |
  | Summerville (Dorchester) 29483 | 7.000% | 7.000% | 0.000 |
  | Sumter (Sumter) 29150 | 8.000% | 8.000% | 0.000 |
  | Spartanburg (Spartanburg) 29301 | 7.000% | 7.000% | 0.000 |
  | Goose Creek (Berkeley) 29445 | 9.000% | 9.000% | 0.000 |
  | Myrtle Beach (Horry, +TD) 29577 | 9.000% | 9.000% | 0.000 |
  | Aiken (Aiken) 29801 | 8.000% | 8.000% | 0.000 |
  | Kingstree (Williamsburg) 29556 | 8.000% | 8.000% | 0.000 |
  | Florence (Florence) 29501 | 8.000% | 8.000% | 0.000 |
  | Beaufort (Beaufort, 0% local) 29902 | 6.000% | 6.000% | 0.000 |
  | Hilton Head (Beaufort, 0% local) 29928 | 6.000% | 6.000% | 0.000 |

- Full 46-county reconciliation (engine local % vs ST-500 combined %):
  all match. 6% counties: Beaufort, Greenville, Oconee. 9% counties:
  Berkeley, Charleston, Jasper, Horry-Myrtle Beach. All others 7% or
  8% per the ST-500 table; every value equals the engine's encoded
  `SC_COUNTY_RATE_PCT` + 6% state.

## Actions taken
- No code changes (no drift in either jurisdiction).
- No background-task chips (no refresh needed; RI's 2019 SST file is
  the current upstream release, SC's ST-500 is the current edition).
- `specs/handoff.md` not modified (no drift to carry forward).
- This report committed and pushed after the mandatory quality-gate +
  SonarQube scan.
