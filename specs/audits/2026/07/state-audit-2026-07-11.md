# Daily state sales tax audit — 2026-07-11 (day 11: MD + ME)

## TL;DR
- 2 states audited (Maryland, Maine — both non-SST, both flat statewide
  with **no local sales tax**). **0 rate changes found; 0 requiring
  code/test updates.** Both live-engine rates match their DOR
  authoritative rates exactly.
- One **documentation-only** improvement applied: added the Maryland
  **3% data/IT-services tax** (effective 2025-07-01, HB 352) to the
  `maryland.py` module docstring as an unmodeled category-specific
  rate — mirroring how `maine.py` already documents its 8%/9%/10%/14%
  category rates. No behavior/data/test change; general MD rate stays
  6%.

## MD (Maryland)
- Source: Maryland Comptroller (marylandtaxes.gov / marylandcomptroller.gov);
  Md. Code Ann., Tax-General. Cross-checked vs MD Comptroller 2025
  legislative-session tax alert + Technical Bulletin No. 56.
- Model type: **self-seeded, non-SST, flat statewide 6% with no local
  sales tax** (`src/opensalestax/states/maryland.py`). No SST quarterly
  file — nothing to refresh for currency.
- Last loaded on prod: engine-derived (self-seeded); no upstream file
  version applies.
- Latest available: general rate **6.000%**, unchanged since 2008-01-03.
- Drift summary: **None.** Live engine returns 6.000% for every MD ZIP
  probed (8/8).
- Recommended action: none for rates. Docstring note added for the new
  3% data/IT-services category rate (out of v1 scope).
- Details (live engine at api.opensalestax.org/v1/calculate, $100 line):

  | City | ZIP | Expected (DOR) | Actual (engine) | Delta |
  |---|---|---|---|---|
  | Baltimore | 21201 | 6.000 | 6.00000 | 0.000 |
  | Annapolis | 21401 | 6.000 | 6.00000 | 0.000 |
  | Rockville | 20850 | 6.000 | 6.00000 | 0.000 |
  | Frederick | 21701 | 6.000 | 6.00000 | 0.000 |
  | Gaithersburg | 20877 | 6.000 | 6.00000 | 0.000 |
  | Bethesda | 20814 | 6.000 | 6.00000 | 0.000 |
  | Columbia | 21044 | 6.000 | 6.00000 | 0.000 |
  | Salisbury | 21801 | 6.000 | 6.00000 | 0.000 |

- **2025/2026 legislative note (informational, out of v1 scope):** Maryland
  enacted a **3% sales-and-use-tax rate on data / information technology
  services and system/application software publishing services** (NAICS
  518, 519, 5132, 5415) effective **2025-07-01** via HB 352 (Budget
  Reconciliation and Financing Act of 2025, Gov. Moore signed 2025-05-20;
  MD Comptroller Technical Bulletin No. 56). This is a **new
  category-specific rate that does NOT change the 6% general rate** on
  tangible personal property. Because OpenSalesTax v1 does not yet model
  per-category rates (the same limitation that leaves Maine's 8%/9%/10%
  rates unmodeled), the engine correctly continues to apply 6% to general
  TPP. Captured in the `maryland.py` docstring this run as a follow-up for
  the category-aware-rate engine extension.

## ME (Maine)
- Source: Maine Revenue Services
  (maine.gov/revenue/taxes/sales-use-service-provider-tax/rates-due-dates);
  Me. Rev. Stat. tit. 36 §1811(1). Fetched + confirmed live this run.
- Model type: **self-seeded, non-SST, flat statewide 5.5% with no local
  sales tax** (`src/opensalestax/states/maine.py`; in the no-local-tax
  club with IN/KY/MI/RI). No SST quarterly file — nothing to refresh.
- Last loaded on prod: engine-derived (self-seeded); no upstream file
  version applies.
- Latest available: general rate **5.500%**, in effect since 2013-10-01.
- Drift summary: **None.** Live engine returns 5.500% for every ME ZIP
  probed (8/8). Module docstring's category-rate documentation (8%
  prepared food, 9% lodging, 10% short-term auto rental, 14% adult-use
  cannabis) still matches Maine Revenue Services guidance.
- Recommended action: none. Fully current.
- Details (live engine, $100 line):

  | City | ZIP | Expected (DOR) | Actual (engine) | Delta |
  |---|---|---|---|---|
  | Portland | 04101 | 5.500 | 5.50000 | 0.000 |
  | Lewiston | 04240 | 5.500 | 5.50000 | 0.000 |
  | Bangor | 04401 | 5.500 | 5.50000 | 0.000 |
  | Augusta | 04330 | 5.500 | 5.50000 | 0.000 |
  | South Portland | 04106 | 5.500 | 5.50000 | 0.000 |
  | Biddeford | 04005 | 5.500 | 5.50000 | 0.000 |
  | Auburn | 04210 | 5.500 | 5.50000 | 0.000 |
  | Presque Isle | 04769 | 5.500 | 5.50000 | 0.000 |

- **Note (informational):** The MRS rates page (table header dated
  10/1/2019) still lists adult-use marijuana at 10%; the `maine.py`
  docstring reflects the **14%** adult-use-cannabis rate effective
  **2026-01-01** (PL 2025 c. 87 §7; PL 2025 c. 388 Pt. F). Cannabis is
  outside the v1 taxability matrix and not emitted by the engine, so
  there is no engine drift either way — documentation-only, no action.

## Actions taken this run
1. **Docstring note (committed):** added the MD 3% data/IT-services
   category-rate note to `src/opensalestax/states/maryland.py`.
   Documentation-only — no data, behavior, or test change. General MD
   rate remains 6.000% (still pinned by `test_phase_4_states.py`).
2. This audit report file.

No rate-fix commits, no boundary-refresh chips, no findings-file
investigations — both states are flat, current, and matching the live
engine.
