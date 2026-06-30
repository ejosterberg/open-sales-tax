# Daily state sales tax audit — 2026-06-30 (buffer-day catch-up: PA + PR)

## TL;DR
- **2 jurisdictions audited** (PA + PR) — a buffer-day catch-up, not a
  scheduled pair. Day-of-month 30 has no rotation assignment (days
  27–31 are buffer/catch-up).
- **PA + PR are the day-20 pair**, which was *never run* this cycle: the
  daily rotation was set up on 2026-06-20 (iter-233) but no day-20
  (PA, PR) audit was produced, and the next scheduled turn isn't until
  2026-07-20. Auditing them today gives both jurisdictions their June
  review before the month rolls over.
- **0 rate changes found. 0 requiring code/test updates.** Both
  jurisdictions are fully current with their authoritative sources and
  the live engine matches every pinned value exactly.
- No SST refresh applies — both are self-seeded non-SST jurisdictions
  with no upstream quarterly file (rates are statutory, encoded
  in-module).

## Coverage context (why PA + PR today)
The day-keyed rotation began 2026-06-20. Coverage so far this cycle:
- Day 21 (RI, SC) ✓ — `state-audit-2026-06-21.md`
- Days 22–25 (SD/TN/TX/UT/VA/VT/WA/WI) ✓ — caught up `state-audit-2026-06-29.md`
- Day 26 (WV, WY) ✓ — `state-audit-2026-06-26.md`
- **Day 20 (PA, PR) — gap.** Setup day; pair never run. Closed here.

Days 1–19 jurisdictions (AK…OR) have not had a turn this cycle but are
scheduled 2026-07-01..07-19, so they remain within the "at least
monthly" window going forward. PA + PR were the only pair at risk of
crossing the June boundary un-reviewed.

## PA (Pennsylvania) — non-SST
- Source: PA Dept. of Revenue (revenue.pa.gov, now pa.gov/en/agencies/revenue);
  cross-checked Avalara + SalesTaxHandbook 2026 rate tables.
- Last loaded on prod: self-seeded — statutory rates in
  `src/opensalestax/states/pennsylvania.py` + `pa_data.py`
  (pins verified 2026-05-04). No upstream file to refresh.
- Latest available: 6.0% statewide; Allegheny Co +1.0% (Pittsburgh) →
  7.0%; Philadelphia City/County +2.0% → 8.0%; all other 65 counties
  6.0%. **No 2026 change** — PA's two local sales taxes (Allegheny
  RAD 1%, Philadelphia 2%) are the only locals statutorily permitted,
  unchanged since 2009.
- Drift summary: **none** — every probed city matches the engine and
  the published DOR/aggregator rates.
- Recommended action: none. Routine confirmation.
- Details (live `GET /v1/rates`, 2026-06-30):

  | City | ZIP | Expected (DOR) | Engine | Delta |
  |------|-----|---------------:|-------:|------:|
  | Philadelphia | 19102 | 8.000% | 8.00000% | 0 |
  | Pittsburgh | 15222 | 7.000% | 7.00000% | 0 |
  | Allentown | 18101 | 6.000% | 6.00000% | 0 |
  | Erie | 16501 | 6.000% | 6.00000% | 0 |
  | Reading | 19601 | 6.000% | 6.00000% | 0 |
  | Scranton | 18503 | 6.000% | 6.00000% | 0 |
  | Bethel Park (Allegheny) | 15102 | 7.000% | 7.00000% | 0 |

## PR (Puerto Rico) — non-SST, US territory
- Source: Departamento de Hacienda de Puerto Rico (hacienda.pr.gov);
  cross-checked Avalara + SalesTaxHandbook 2026.
- Last loaded on prod: self-seeded — statutory IVU rate in
  `src/opensalestax/states/puerto_rico.py` (10.5% state + 1.0%
  municipal, split into two RateRows per v0.32). No upstream file.
- Latest available: **11.5% combined** at every PR address (10.5% per
  13 L.P.R.A. §32021 + 1.0% municipal per §32024, uniform across all
  78 municipios). **No 2026 change** — structure stable since
  2015-07-01 (Act No. 72 of 2015). No "Días sin IVU" 2026 holiday has
  been confirmed via Hacienda announcement (module still returns no
  holiday window for 2026; no action needed).
- Drift summary: **none** — uniform 11.5% confirmed across 7 municipios.
- Recommended action: none. Routine confirmation.
- Details (live `GET /v1/rates`, 2026-06-30):

  | Municipio | ZIP | Expected (Hacienda) | Engine | Delta |
  |-----------|-----|--------------------:|-------:|------:|
  | San Juan | 00901 | 11.500% | 11.50000% | 0 |
  | Bayamón | 00956 | 11.500% | 11.50000% | 0 |
  | Carolina | 00979 | 11.500% | 11.50000% | 0 |
  | Ponce | 00731 | 11.500% | 11.50000% | 0 |
  | Caguas | 00725 | 11.500% | 11.50000% | 0 |
  | Arecibo | 00612 | 11.500% | 11.50000% | 0 |
  | Mayagüez | 00680 | 11.500% | 11.50000% | 0 |

## Actions taken
- None beyond this report. No code/test changes, no commits to state
  modules, no background-task chips: zero drift, both jurisdictions
  current, and neither has an SST quarterly file that could be stale.
- `specs/handoff.md` not updated (per task rule: update only when drift
  is found).
