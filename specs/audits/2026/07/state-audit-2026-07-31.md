# Daily state sales tax audit — 2026-07-31 (buffer-day catch-up: AK, AL, AR, AZ, CA, CO, ND, NE, NH, NJ)

## TL;DR
- Day 31 is a **buffer/catch-up day** (the rotation table only runs days
  1–26), so this run audited the **10 jurisdictions with no audit record
  at all**. The `specs/audits/` history begins 2026-06-21; these ten
  (rotation days 1, 2, 3, 15, 16) had never been covered.
- **4 jurisdictions have confirmed rate drift on the live engine
  (AR, AZ, ND, NE); 6 are clean (AK, AL, CA, CO, NH, NJ).**
- **9 individual jurisdiction rates are wrong right now**, all with a
  2026-07-01 effective date:
  - **AR — 6 jurisdictions** (Van Buren, El Dorado, Chester, Perry,
    Cross County, Jackson County). Two of them (Cross, Jackson) mean the
    engine **over-collects**; the other four under-collect.
  - **AZ — 1** (Town of Florence, 2.00% → 3.50%, −1.50pp).
  - **ND — 1** (City of Scranton, 1.00% → 2.00%, −1.00pp).
  - **NE — 1** (City of Edgar, 1.00% → 1.50%, −0.50pp).
- **Root cause for AR/ND/NE is a single thing: prod is still on the
  2026 Q2 SST files and Q3 has been published for all three.** No code
  is wrong — the data is a quarter stale. Per audit policy the SST files
  are chipped for Eric, not auto-pulled.
- **AZ is not an SST state** — its drift needs an AZ DOR rate-table
  reload (`TPT_RATETABLE_07012026.pdf`), chipped separately.
- **No code or test-pin changes were made** — every finding is a
  data-refresh action, and hand-editing rates would paper over the stale
  loader input rather than fix it.
- Also found: **four future-dated changes** already published (AZ
  Huachuca City 8/1, AZ Kingman 9/1, AZ Tusayan + San Tan Valley 10/1,
  ND Minot/Kindred/Walhalla 10/1) — recorded here so a later audit
  doesn't rediscover them cold.

## Coverage gap this run closed

| Rotation day | Pair | Previously audited? |
|---:|---|---|
| 1 | AK, AL | never |
| 2 | AR, AZ | never |
| 3 | CA, CO | never |
| 15 | ND, NE | never |
| 16 | NH, NJ | never |

July's rotation also skipped days 21 (RI, SC), 23 (TX, UT), 24 (VA, VT)
and 25 (WA, WI), but those four pairs were covered by the 2026-06-21 and
2026-06-29 runs, so they are inside the "at least monthly" requirement
and were deprioritized behind the never-audited ten.

---

## AR (Arkansas) — SST member — ⚠️ DRIFT (6 jurisdictions)

- Source: **Arkansas DFA Q3 2026 city/county rate table**
  (`cityCountyTaxTable_Jul_Sep_2026.pdf`, downloaded and parsed directly),
  cross-checked against the DFA "Local Sales & Use Tax Rate Changes" page.
- Last loaded on prod: `ARR2026Q2MAR02.csv` / `ARB2026Q2MAR02.zip`
- Latest available from SST: **`ARR2026Q3JUN02.csv` /
  `ARB2026Q3JUN02.zip`** — one quarter newer.
- Drift summary: **6 jurisdictions wrong**, all effective 2026-07-01 and
  all explained by the stale Q2 file. Four under-collect, two
  over-collect.
- Recommended action: **REFRESH NEEDED** — load AR Q3 SST files on prod
  (chipped). No code change.
- Details (live engine `GET /v1/rates`, probed 2026-07-31):

  | Jurisdiction (probe ZIP) | Expected (DFA Q3) | Actual (engine) | Delta |
  |---|---|---|---|
  | Van Buren city (72956)   | 2.500% city → **10.250%** combined | 1.500% city → 9.250% | **−1.000** |
  | El Dorado city (71730)   | 1.750% city → **10.250%** combined | 1.250% city → 9.750% | **−0.500** |
  | Chester city (72934)     | 1.000% city (newly enacted) → **8.750%** | 0.000% city → 7.750% | **−1.000** |
  | Perry city (72125)       | 1.000% city (newly enacted) → **10.250%** | 0.000% city → 9.250% | **−1.000** |
  | Cross County (Wynne, 72396)   | 2.125% county → **9.625%** | 3.000% county → 10.500% | **+0.875** |
  | Jackson County (Newport, 72112) | 1.875% county → **9.875%** | 2.250% county → 10.250% | **+0.375** |

- The Cross/Jackson County rows are the higher-risk pair: a rate that is
  too **high** makes the engine over-collect, which is the failure mode a
  consumer notices as an actual overcharge rather than an underpayment.
- Verified-clean AR probes (no change, engine correct): Little Rock
  8.625%, Fort Smith 9.500%, Fayetteville 9.750%, Springdale 9.750%,
  Jonesboro 8.500%, Conway 9.125%, Hot Springs 9.500%, Rogers 9.500%.
- Also published but **not yet effective** (2026-10-01): Alpena
  2.250%, Hempstead County 2.750%, Logan County 1.500%, Stone County
  1.000%, plus annexation updates for Rogers, Bentonville, Pea Ridge,
  Avoca, Highfill, Conway, Salem, Sheridan, Manila, Maumelle,
  Pocahontas, Benton, Greenwood. The Q4 SST file will carry these.

## AZ (Arizona) — non-SST — ⚠️ DRIFT (1 jurisdiction)

- Source: **AZ DOR "Rate and Code Updates"** (Model City Tax Code) plus
  the **`TPT_RATETABLE_07012026.pdf`** rate tables (confirmed header:
  "Effective July 1, 2026").
- Last loaded on prod: AZ DOR CSV (per the AZ state module; not an SST
  quarterly file).
- Drift summary: **1 jurisdiction wrong.** Town of Florence raised every
  Privilege Tax classification including Retail Sales (business code 017)
  from 2.00% to 3.50% effective 2026-07-01 (ordinance 780-26).
- Recommended action: **REFRESH NEEDED** — reload the AZ DOR rate table
  from the 2026-07-01 edition (chipped). No code change.
- Details:

  | City (probe ZIP) | Expected (AZ DOR 7/1/26) | Actual (engine) | Delta |
  |---|---|---|---|
  | Florence (85132) | 3.500% city → **10.200%** combined | 2.000% city → 8.700% | **−1.500** |

- Verified-clean AZ probes: Phoenix 9.100%, Tucson 8.700%, Mesa 8.300%,
  Chandler 7.800%, Scottsdale 8.000%, Glendale 9.200%, Gilbert 8.300%,
  Tempe 8.100%, Flagstaff 9.386%. None of the nine largest cities
  changed in 2026.
- Two other 2026-07-01 AZ ordinances are **correctly not drift**:
  - **Oro Valley** — imposed a 2.50% *use* tax only; the retail rate is
    unchanged, and the engine's 8.600% combined is right.
  - **South Tucson** — dropped *food for home consumption* (code 062)
    from 1.5% to 0.0%. That is a reduced-rate category the engine does
    not model; the general retail rate is unchanged. Same shape as the
    open PR prepared-food follow-up.
  - Note also that probe ZIP 85713 resolves to Tucson (2.600%), not the
    separately-incorporated City of South Tucson — a ZIP-granularity
    limitation, not new drift.
- **Future-dated, already published** (do not "fix" early): Huachuca
  City 1.90% → 2.90% on 2026-08-01; Kingman 2.50% → 3.00% on 2026-09-01;
  Tusayan 2.00% → 4.00% and the new Town of San Tan Valley on 2026-10-01.

## ND (North Dakota) — SST member — ⚠️ DRIFT (1 jurisdiction)

- Source: **ND Office of State Tax Commissioner** "City and County Local
  Tax Rate Changes".
- Last loaded on prod: `NDR2026Q2FEB11.zip` / `NDB2026Q2FEB19.zip`
- Latest available from SST: **`NDR2026Q3MAY19.zip` /
  `NDB2026Q3MAY19.zip`** — one quarter newer.
- Drift summary: **1 jurisdiction wrong.** City of Scranton went from
  1% to 2% effective 2026-07-01 (the same ordinance also extended the
  tax to use tax).
- Recommended action: **REFRESH NEEDED** — load ND Q3 SST files on prod
  (chipped).
- Details:

  | City (probe ZIP) | Expected (ND OSTC) | Actual (engine) | Delta |
  |---|---|---|---|
  | Scranton (58653) | 2.000% city → **7.000%** combined | 1.000% city → 6.000% | **−1.000** |

- Verified-clean ND probes: Fargo 7.750%, Bismarck 8.000%, Grand Forks
  7.250%, Minot 7.500%, West Fargo 8.000%, Williston 8.000%, Jamestown
  7.500%, Grafton 8.750%, Park River 8.500%, Hillsboro 8.000%, LaMoure
  8.000%. The 2026-01-01 changes (Sherwood 2%, Surrey 3%, Walsh County
  1%) are already correctly loaded.
- **Not rate drift — an unmodeled feature:** the other two 2026-07-01 ND
  changes (Drayton, Oakes) are *maximum-tax / refund-cap* changes, not
  rate changes. ND lets cities cap the local tax per sale (e.g. Drayton's
  $50-per-sale cap); the engine returns a flat percentage and does not
  model per-sale caps at all. This is a pre-existing capability gap
  affecting many ND cities, not something the Q3 refresh fixes. Worth a
  decision record if ND accuracy matters for large-ticket sales.
- **Future-dated** (2026-10-01): Minot, Kindred, Walhalla.

## NE (Nebraska) — SST member — ⚠️ DRIFT (1 jurisdiction)

- Source: **Nebraska DOR** local sales and use tax rate change notices.
- Last loaded on prod: `NER2026Q2FEB25.zip` / `NEB2026Q2APR20.zip`
- Latest available from SST: **`NER2026Q3MAY26.zip` /
  `NEB2026Q3JUN08.zip`** — one quarter newer.
- Drift summary: **1 jurisdiction wrong.** City of Edgar raised its
  local rate from 1.0% to 1.5% effective 2026-07-01.
- Recommended action: **REFRESH NEEDED** — load NE Q3 SST files on prod
  (chipped).
- Details:

  | City (probe ZIP) | Expected (NE DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Edgar (68935) | 1.500% city → **7.000%** combined | 1.000% city → 6.500% | **−0.500** |

- Note: Edgar's authority is still an unlabelled placeholder in the
  engine (`NE-city-14450` rather than "Edgar"). Same friendly-name gap
  the WV/UT/WI name tables have been chipping away at; recorded, not
  fixed here.
- Verified-clean NE probes: Omaha 7.000%, Lincoln 7.250%, Bellevue
  7.000%, Grand Island 7.500%, Kearney 7.000%, Fremont 7.000%, Norfolk
  7.500%, Papillion 7.500%, Hastings 7.000%.
- Blaine County's 2% *lodging* rate terminated 2026-07-01 — lodging is
  outside the general sales-tax engine's scope, noted for completeness.

---

## AK (Alaska) — non-SST (no state tax) — ✅ clean

- Source: Alaska Remote Seller Sales Tax Commission (ARSSTC) member
  rate tables.
- Drift summary: **none.** Alaska has no state sales tax; the engine
  correctly returns 0.000% state plus borough/city components.
- The one 2026 ARSSTC change found (City of Nome, general retail 5% →
  6% effective 2026-01-01) is **already correctly loaded** — the engine
  returns 6.000% for 99762.
- Details:

  | City (ZIP) | Expected (ARSSTC) | Actual (engine) | Delta |
  |---|---|---|---|
  | Homer (99603)       | 7.850% | 7.850% | 0.000 |
  | Juneau (99801)      | 5.000% | 5.000% | 0.000 |
  | Ketchikan (99901)   | 8.000% | 8.000% | 0.000 |
  | Sitka (99835)       | 6.000% | 6.000% | 0.000 |
  | Wasilla (99654)     | 2.500% | 2.500% | 0.000 |
  | Kodiak (99615)      | 7.000% | 7.000% | 0.000 |
  | Seward (99664)      | 7.000% | 7.000% | 0.000 |
  | Bethel (99559)      | 6.000% | 6.000% | 0.000 |
  | Nome (99762)        | 6.000% | 6.000% | 0.000 |
  | Anchorage (99501)   | 0.000% | 0.000% | 0.000 |

- Anchorage correctly returns 0.000% — it levies no general sales tax.

## AL (Alabama) — non-SST — ✅ clean on covered cities (1 coverage gap)

- Source: ALDOR local rate listings; 2026 change notices.
- Drift summary: **no rate drift in the covered tier-1 cities.** All
  eight majors match their pinned ALDOR values.
- Details:

  | City (ZIP) | Expected (ALDOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Birmingham (35203) | 10.000% | 10.000% | 0.000 |
  | Montgomery (36104) | 10.000% | 10.000% | 0.000 |
  | Mobile (36602)     | 10.000% | 10.000% | 0.000 |
  | Huntsville (35801) |  9.000% |  9.000% | 0.000 |
  | Tuscaloosa (35401) | 10.000% | 10.000% | 0.000 |
  | Hoover (35226)     |  9.500% |  9.500% | 0.000 |
  | Auburn (36830)     |  9.000% |  9.000% | 0.000 |
  | Dothan (36303)     |  9.000% |  9.000% | 0.000 |
  | Mountain Brook (35213) | 10.000% (city 3%→4%, applied) | 10.000% | 0.000 |
  | Helena (35080)     | 10.000% | 10.000% | 0.000 |

- **Coverage gap (not drift):** Tuscumbia (35674) returns state 4% +
  Colbert County 1.5% = 5.500% with **no city component**, though
  Tuscumbia levies a city tax (recently raised to 4%). This is the
  documented Alabama home-rule limitation — the API already emits a
  `coverage_warning` saying city overlays are not modelled. Worth
  noting that the warning is now *pessimistic*: many AL cities
  (Birmingham, Mobile, Mountain Brook, Helena…) **are** modelled, so
  consumers can't tell which cities are covered. Recorded as a
  documentation-accuracy follow-up, not a rate fix.
- Alabama's 2% state grocery rate resumed 2026-07-01 (Act 2026-604
  suspended it through 6/30). Reduced-rate food handling is out of the
  general-rate engine's scope today — same category as the open PR
  prepared-food item.

## CA (California) — non-SST — ✅ clean

- Source: **CDTFA "California City and County Sales and Use Tax Rates"**,
  table header confirmed **"Effective July 1, 2026"**.
- Drift summary: **none.** All ten probed cities match CDTFA exactly.
  This is the strongest single result of the run given CA is the largest
  economy audited and its district taxes change most often.
- Details:

  | City (ZIP) | Expected (CDTFA 7/1/26) | Actual (engine) | Delta |
  |---|---|---|---|
  | Los Angeles (90001)   |  9.750% |  9.750% | 0.000 |
  | San Diego (92101)     |  7.750% |  7.750% | 0.000 |
  | San Jose (95110)      | 10.000% | 10.000% | 0.000 |
  | San Francisco (94102) |  8.625% |  8.625% | 0.000 |
  | Fresno (93701)        |  8.350% |  8.350% | 0.000 |
  | Sacramento (95814)    |  8.750% |  8.750% | 0.000 |
  | Long Beach (90802)    | 10.500% | 10.500% | 0.000 |
  | Oakland (94601)       | 10.750% | 10.750% | 0.000 |
  | Bakersfield (93301)   |  8.250% |  8.250% | 0.000 |
  | Anaheim (92801)       |  7.750% |  7.750% | 0.000 |
- Minor note: the engine's *decomposition* differs from the pinned test
  narrative for Los Angeles (engine reports county 2.500% + city 0.000%;
  the pin comment says county 2.250%). The combined rate is correct and
  matches CDTFA, so this is a labelling nuance in how LA County's
  district taxes are attributed, not an error. Not worth a change.

## CO (Colorado) — non-SST — ✅ clean (state-only by design)

- Source: Colorado DOR; project decision record
  `specs/decisions/04-colorado-home-rule.md`.
- Drift summary: **none.** The state rate is still **2.9%** for 2026 and
  the engine returns exactly that, with an explicit `coverage_warning`
  that ~70 home-rule cities self-administer and are not modelled.
- Details: Denver (80202), Colorado Springs (80903), Aurora (80010),
  Fort Collins (80521), Lakewood (80226) all return 2.900% — the
  intended, documented behaviour, not drift.
- 2026 administrative change worth knowing (no rate impact): HB 25B-1005
  ended the retailer's vendor-fee retention as of 2026-01-01. It affects
  remittance, not the rate this API returns.

## NH (New Hampshire) — non-SST — ✅ clean

- Source: NH Department of Revenue Administration.
- Drift summary: **none.** New Hampshire levies no general sales tax at
  any level; the engine returns 0.000% with no jurisdictions.
- Details: Concord (03301), Manchester (03101), Nashua (03060) all
  0.000%.
- NH's 8.5% Meals & Rentals tax is a separate excise on prepared food,
  lodging and vehicle rentals — deliberately outside a general sales-tax
  engine.

## NJ (New Jersey) — SST member — ✅ clean

- Source: NJ Division of Taxation.
- Last loaded on prod: `NJR2018Q1OCT16.zip` / `NJB2019Q2MAR27.csv`.
  These look alarmingly old but are **the newest files SST publishes for
  New Jersey** — confirmed against the SST rate and boundary directory
  listings today. NJ is not behind; its rate has not moved since 2018.
- Drift summary: **none.** Flat **6.625%** statewide, unchanged for 2026.
- Details: Newark (07102), Jersey City (07302), Paterson (07501),
  Trenton (08608), Camden (08102) all 6.625%.
- The Urban Enterprise Zone half-rate (3.3125%, 32 designated zones) is
  still deliberately deferred — a certified-retailer attribute the API
  has no input for. Unchanged for 2026.

---

## Cross-cutting observation: three states, one stale-quarter cause

AR, ND and NE all drifted for the same reason, and it is the same reason
WV, WY, SD and TN drifted in the 2026-07-22 and 2026-07-26 audits: **prod
is running the 2026 Q2 SST files while Q3 has been published.** Seven
states have now been individually chipped for a Q3 refresh across four
audits, and the chips have not been applied.

This is worth naming as a process finding rather than seven separate data
findings. A single "refresh all SST states to Q3" pass would clear the
whole backlog, and the per-state chips will keep re-opening every audit
cycle until it happens. The states with confirmed drift attributable to
the stale quarter are now AR (6 jurisdictions), ND (1), NE (1), plus the
coverage gaps flagged for WV.

## Actions taken

- **No code or test changes.** Every finding is a data-refresh action;
  hand-editing rate pins would mask the stale loader input rather than
  fix it, and would drift right back on the next load.
- **5 background-task chips opened:**
  1. Refresh AR SST quarterly Q2 → Q3 (`ARR2026Q3JUN02` /
     `ARB2026Q3JUN02`) — 6 wrong jurisdictions, 2 over-collecting.
  2. Refresh ND SST quarterly Q2 → Q3 (`NDR2026Q3MAY19` /
     `NDB2026Q3MAY19`) — Scranton.
  3. Refresh NE SST quarterly Q2 → Q3 (`NER2026Q3MAY26` /
     `NEB2026Q3JUN08`) — Edgar.
  4. Reload the AZ DOR rate table to the 2026-07-01 edition — Florence.
  5. Do a single fleet-wide Q3 SST refresh covering all seven
     chip-backlogged states at once (AR, ND, NE, SD, TN, WV, WY).
- `specs/handoff.md` open follow-ups updated.
- Report committed and pushed only after the mandatory quality-gate +
  SonarQube scan passed with zero new BLOCKER/CRITICAL, then CI watched
  to green.

## Suggested next buffer-day target

The remaining under-covered pairs are RI + SC (last audited 2026-06-21)
and TX + UT / VA + VT / WA + WI (last audited 2026-06-29). RI + SC is the
oldest and should be the next catch-up run if day 21 is missed again.
