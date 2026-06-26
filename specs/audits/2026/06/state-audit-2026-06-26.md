# Daily state sales tax audit — 2026-06-26 (day 26: WV + WY)

## TL;DR
- 2 jurisdictions audited (both SST member states).
- **0 rate changes found in either state's top cities — engine matches
  the authoritative sources exactly.** No code/test updates required.
- **BUT both states are running stale SST quarterly files on prod and
  need a REFRESH:**
  - WV is **two quarters behind** (prod = 2026 Q1; latest = **Q3**).
  - WY is **one quarter behind** (prod = 2026 Q2; latest = **Q3**).
- Two background-task chips opened for Eric to apply the Q3 refreshes
  (SST files are not auto-pulled per audit policy).
- WV note: several **new small municipalities** adopted the 1%
  municipal tax in 2026 (Bramwell, Glenville, Hinton, Marlinton,
  Pineville, Anmoore, Bath) plus rate increases (Richwood, Westover).
  These will only surface in the engine after the Q3 file is loaded —
  they're the concrete payoff of the WV refresh.

## WV (West Virginia) — SST member
- Source: SST Governing Board rate/boundary index
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates/ ,
  .../Boundary/); cross-checked against WV Tax Division "Municipalities
  Imposing Sales and Use Taxes"
  (https://tax.wv.gov/Documents/SUT/MunicipalitiesImposingSalesAndUseTaxes.pdf).
- Last loaded on prod: `WVR2026Q1AUG14.csv` / `WVB2026Q1SEP02.csv`
- Latest available from SST: **`WVR2026Q3FEB25.csv` /
  `WVB2026Q3APR29.csv`** — two quarters newer than prod.
- Drift summary: **none in the engine's top-5 cities** — all return the
  correct 6% state + 1% municipal = 7.000%. The stale file does NOT
  cause drift in existing cities (WV's 6% state rate is fixed and the
  major municipalities' 1% rates are unchanged); it causes *missing
  coverage* of municipalities that newly adopted the tax in 2026.
- Recommended action: **REFRESH NEEDED** — load WV Q3 SST files on
  prod (chipped for Eric). Picks up the new 2026 municipalities.
- Details (live engine, `/v1/rates`):
  | City | Expected (WV DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Charleston (25301) | 7.000% | 7.000% | 0.000 |
  | Huntington (25701) | 7.000% | 7.000% | 0.000 |
  | Morgantown (26505) | 7.000% | 7.000% | 0.000 |
  | Parkersburg (26101) | 7.000% | 7.000% | 0.000 |
  | Wheeling (26003) | 7.000% | 7.000% | 0.000 |
  | Beckley (25801) | 7.000% | 7.000% | 0.000 |
  | Clarksburg (26301) | 7.000% | 7.000% | 0.000 |
  | Martinsburg (25401) | 7.000% | 7.000% | 0.000 |
- New 2026 WV municipalities to verify after the Q3 refresh (state 6% +
  1% municipal = 7%): Bramwell (Mercer), Glenville (Gilmer), Hinton
  (Summers), Marlinton (Pocahontas), Pineville (Wyoming Co), Anmoore
  (Harrison), Bath/Berkeley Springs (Morgan). Plus rate increases:
  Richwood, Westover (both +1%). Source: WV Tax Division municipal
  list + usgeocoder 2026 WV change summary.

## WY (Wyoming) — SST member
- Source: SST Governing Board rate/boundary index; cross-checked
  against WY Excise Tax Division rate charts
  (https://excise-tax-div.wyo.gov/sales-use-tax-rate-charts) and
  SalesTaxHandbook 2026 WY county table.
- Last loaded on prod: `WYR2026Q2APR1.csv` / `WYB2026Q2FEB23.csv`
- Latest available from SST: **`WYR2026Q3JUN2.CSV` /
  `WYB2026Q3MAY18.CSV`** — one quarter newer than prod.
- Drift summary: **none.** All 7 probed county/city stacks match the
  authoritative WY chart. The WY Excise Division master chart's most
  recent edition is still "April 2026" (it updates only when rates
  change), indicating no county rate changes took effect for the
  major counties at the Q3 (July 1 2026) boundary — the Q3 SST file
  is a routine republication for these jurisdictions.
- Recommended action: **REFRESH NEEDED** — load WY Q3 SST files on
  prod (chipped for Eric) to stay current and catch any
  smaller-jurisdiction specific-purpose-tax sunsets/renewals the
  top-7 probe doesn't cover.
- Details (live engine, `/v1/rates`):
  | City (county) | Expected (WY DOR/handbook) | Actual (engine) | Delta |
  |---|---|---|---|
  | Cheyenne (Laramie) 82001 | 5.000% | 5.000% | 0.000 |
  | Casper (Natrona) 82601 | 6.000% | 6.000% | 0.000 |
  | Jackson (Teton) 83001 | 7.000% | 7.000% | 0.000 |
  | Sheridan (Sheridan) 82801 | 6.000% | 6.000% | 0.000 |
  | Gillette (Campbell) 82716 | 5.000% | 5.000% | 0.000 |
  | Laramie city (Albany) 82070 | 6.000% | 6.000% | 0.000 |
  | Rock Springs (Sweetwater) 82901 | 6.000% | 6.000% | 0.000 |
- Minor coverage note (not drift): Teton Village (83025) and Alta
  (83414) carry WY's highest combined rate (9%) via a resort-district
  overlay on top of Teton County's 3%. Jackson proper (83001) is
  correctly 7%. Whether the resort-district ZIPs resolve to 9% is a
  separate coverage question — logged here, not chipped, as it is a
  long-standing resort-overlay modeling item, not a Q3 rate change.

## Actions taken
- No code changes (no rate drift in either jurisdiction's covered
  cities).
- 2 background-task chips opened:
  1. Refresh WV SST quarterly Q1 → Q3 (`WVR2026Q3FEB25` /
     `WVB2026Q3APR29`).
  2. Refresh WY SST quarterly Q2 → Q3 (`WYR2026Q3JUN2` /
     `WYB2026Q3MAY18`).
- `specs/handoff.md` updated: added both Q3 refreshes to open
  follow-ups (drift-equivalent — stale upstream data).
- This report committed and pushed only after the mandatory
  quality-gate + SonarQube scan pass with zero new BLOCKER/CRITICAL.
