# Daily state sales tax audit — 2026-07-13 (day 13: MO + MS)

## TL;DR
- 2 states audited (both non-SST). **0 rate changes affecting covered
  jurisdictions; 0 requiring code/test updates.**
- Live engine matches every tier-1 pin exactly (0.00 drift across 15
  probes: 8 MO cities + 7 MS cities).
- MO **does** have Q3 2026 (effective 2026-07-01) DOR rate changes, but
  none touch our tier-1 cities — they hit small towns (Mountain Grove,
  Unity Village) and CID/TDD special districts the engine intentionally
  does not model. Noted, no action.
- MS is a flat-7% state with only Jackson (+1%) and Tupelo (+0.25%) local
  taxes; no 2026 changes.

## MO — Missouri
- Source: MO DOR 2026 Statewide Sales/Use Tax Rate Tables
  (https://dor.mo.gov/taxation/business/tax-types/sales-use/rate-tables/2026/);
  Q3 2026 change list cross-checked via MO DOR news release + usgeocoder
  2026 change tracker.
- Last verified: 2026-05-04 (pin comment in
  `tests/integration/test_sst_dor_validation.py`).
- Latest available: Q3 2026 tables, effective **2026-07-01**.
- Drift summary: **None for covered cities.** All 8 tier-1 MO pins match
  the live engine to the cent.
- Recommended action: None. Q3 changes are out-of-scope jurisdictions.
- Q3 2026 changes (effective 2026-07-01), for the record — none in our
  tier-1 set:
  - Cities: Mountain Grove, Unity Village
  - Special districts (engine does NOT model these by design — see the
    0.10 tolerance note in the MO test block): Stone County / Cole Camp /
    Owensville Area Ambulance Districts (rate changes); Hillcrest, Maple
    Park, Phoenix Center II, Branson Mills, Pleasant Hill Marketplace,
    North Glenstone CIDs (new); Tremont Square, Merchants Laclede,
    Truman Boulevard TDDs (repealed).
- Details (state 4.225% + county + city; engine = live api.opensalestax.org):

  | City | Expected (DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Kansas City (64108) | 8.975 | 8.97500 | 0.000 |
  | St. Louis (63103) | 9.679 | 9.67900 | 0.000 |
  | Springfield (65806) | 8.100 | 8.10000 | 0.000 |
  | Independence (64055) | 8.600 | 8.60000 | 0.000 |
  | Columbia (65201) | 7.975 | 7.97500 | 0.000 |
  | Lee's Summit (64063) | 8.475 | 8.47500 | 0.000 |
  | St. Joseph (64501) | 9.700 | 9.70000 | 0.000 |
  | O'Fallon (63366) | 7.950 | 7.95000 | 0.000 |

## MS — Mississippi
- Source: MS DOR sales tax (https://www.dor.ms.gov/sales-use) — the DOR
  TLS cert failed validation at audit time (intermediate-cert chain
  issue), so rates cross-checked via independent 2026 trackers
  (salestaxhandbook, taxcloud, Avalara city pages).
- Last verified: 2026-05-04 (pin comment in the MS test block).
- Latest available: 2026 rates — flat 7% state; Jackson +1% (Miss. Code
  Ann. §27-65-241), Tupelo +0.25% (H.B. 1685, Laws 2008).
- Drift summary: **None.** All 7 MS probes match to the cent.
- Recommended action: None. No 2026 local-rate changes; MS's structure
  is stable (only Jackson and Tupelo carry a general-retail local tax;
  Hattiesburg/Gulfport/Biloxi tourism taxes apply to hotels + prepared
  food only, not general retail — engine correctly returns 7%).
- Details (state 7% + local; engine = live api.opensalestax.org):

  | City | Expected (DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Jackson (39201) | 8.000 | 8.00000 | 0.000 |
  | Tupelo (38801) | 7.250 | 7.25000 | 0.000 |
  | Hattiesburg (39401) | 7.000 | 7.00000 | 0.000 |
  | Gulfport (39501) | 7.000 | 7.00000 | 0.000 |
  | Biloxi (39530) | 7.000 | 7.00000 | 0.000 |
  | Meridian (39301) | 7.000 | 7.00000 | 0.000 |
  | Greenville (38701) | 7.000 | 7.00000 | 0.000 |

## Notes for the next auditor
- MO DOR publishes quarterly; next window to check is Q4 2026 (effective
  2026-10-01) — no Q4 changes were posted as of this audit.
- If MO tier-1 coverage is ever expanded to include CID/TDD-heavy ZIPs,
  revisit the 0.10 tolerance and the "no special-district overlay"
  simplification in the MO test block.
- MS DOR site (dor.ms.gov) served an incomplete TLS chain on 2026-07-13;
  if it persists, a future audit should pin the DOR PDF URL instead of
  the HTML landing page.
