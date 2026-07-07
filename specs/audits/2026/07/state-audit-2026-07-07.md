# Daily state sales tax audit — 2026-07-07 (day 7: IA + ID)

## TL;DR
- 2 states audited (IA = SST member, ID = non-SST).
- **0 currency refreshes needed**, **0 real-world rate drift in tier-1 cities**.
- **1 confirmed engine over-collect surfaced** (Iowa — West Des Moines
  50265/50266 LOST dedup bug, pre-existing since iter-128, never written up
  as a finding or chipped). Needs code (engine dedup), not a data refresh —
  finding written + chipped this run.
- No auto-committed data fixes (nothing was a trivial one-line/pin change).

---

## IA (Iowa) — SST full member (joined 2005-10-01)

- **Source:** SST Governing Board rate/boundary file index
  (`streamlinedsalestax.org/Shared-Pages/rate-and-boundary-files/rate-and-boundary-file-updates`
  + `/state-details/iowa`); IA DOR LOST guidance (`tax.iowa.gov`).
- **Last loaded on prod:** rate `IAR2025Q3MAY30.zip`, boundary
  `IAB2026Q1DEC09.zip`.
- **Latest available:** rate **`IAR2025Q3MAY30`** (posted 2025-06-02) —
  this is the newest rate file SST lists for Iowa; the updates log shows
  **no 2026 Iowa rate file** (Iowa's LOST structure has been stable, so no
  new posting). Boundary on prod (`IAB2026Q1DEC09`, Q1 2026) is newer than
  the updates-log entry.
- **Drift summary:** Prod rate file **matches the latest SST-published rate
  file** — Iowa is current, no refresh needed. All 8 sampled tier-1 cities
  return the correct **7.000%** (state 6% + 1% county LOST). One real
  over-collect on the West Des Moines cross-county ZIPs (below).
- **Recommended action:** No data refresh. **Chip the West Des Moines LOST
  dedup over-collect** for engine work (see finding file).
- **Details:**

  | City | ZIP | Expected (IA DOR) | Actual (engine) | Delta |
  |------|-----|-------------------|-----------------|-------|
  | Des Moines | 50309 | 7.000% | 7.000% | ✓ |
  | Cedar Rapids | 52401 | 7.000% | 7.000% | ✓ |
  | Davenport | 52801 | 7.000% | 7.000% | ✓ |
  | Sioux City | 51101 | 7.000% | 7.000% | ✓ |
  | Iowa City | 52240 | 7.000% | 7.000% | ✓ |
  | Waterloo | 50701 | 7.000% | 7.000% | ✓ |
  | Council Bluffs | 51501 | 7.000% | 7.000% | ✓ |
  | Ames | 50010 | 7.000% | 7.000% | ✓ |
  | **West Des Moines** | **50265** | **7.000%** | **9.000%** | **+2.00% over** |
  | **West Des Moines** | **50266** | **7.000%** | **10.000%** | **+3.00% over** |

  **West Des Moines over-collect (confirmed live 2026-07-07):** the engine
  stacks multiple 1% LOST districts on the West Des Moines cross-county ZIPs:
  - `50265` → Iowa 6% + *Polk County LOST 1%* + *Union County LOST 1%* +
    *IA-district-98199 1%* = **9.0%**
  - `50266` → Iowa 6% + *IA-district-98049 1%* + *Polk County LOST 1%* +
    *Union County LOST 1%* + *IA-district-98199 1%* = **10.0%**

  West Des Moines' correct combined rate is **7.0%** (Iowa 6% + a single 1%
  LOST). Iowa's Local Option Sales Tax is statutorily capped at **1%**
  (Iowa Code ch. 423B), so no Iowa address can legally exceed 7%. Union
  County LOST is plainly wrong here — Union County is rural south-central
  Iowa (county seat Creston), nowhere near West Des Moines (Polk/Dallas
  Cos.). This is the iter-128-logged "IA West Des Moines LOST dedup bug"; it
  is a genuine customer-facing **over-collection of 2–3%** and was never
  written to a finding file or chipped. Done this run:
  `specs/findings/ia-west-des-moines-lost-dedup-2026-07.md` + chip.

  The `-m liveapi` grid pin `("IA","West Des Moines","50265","0001","7.000")`
  in `tests/integration/test_sst_dor_validation.py` currently **fails**
  against the live engine (returns 9.000%). Do NOT mask it by editing the
  pin — the engine dedup is the fix.

---

## ID (Idaho) — non-SST, flat 6% state, no county sales tax

- **Source:** Idaho State Tax Commission — "City Sales Taxes" / "Local Sales
  Tax" (`tax.idaho.gov/taxes/sales-use/sales-tax/local-sales-tax/`); Idaho
  Code §63-3619 (state rate) and §50-1044 (resort-city local option).
- **Last loaded on prod:** ID module data captured 2026-05-10 (non-SST, no
  quarterly file; `idaho.py` + `id_data.py`).
- **Latest available:** Idaho State Tax Commission confirms the statewide
  rate is **6%** (unchanged since 2006-10-01) and lists 23 cities with a
  local sales tax; the Commission does not publish per-city rate percentages
  online (directs to the cities).
- **Drift summary:** **No drift.** Idaho's 8 largest cities correctly return
  the flat **6.000%** (Idaho has no county sales tax and none of these
  cities levy a local option). All 12 modeled resort cities appear on the
  Commission's current city-sales-tax list and match our stored rates. No
  2026 rate changes surfaced.
- **Recommended action:** None.
- **Details:**

  | City | ZIP | Expected (ID STC) | Actual (engine) | Delta |
  |------|-----|-------------------|-----------------|-------|
  | Boise | 83702 | 6.000% | 6.000% | ✓ |
  | Meridian | 83642 | 6.000% | 6.000% | ✓ |
  | Nampa | 83651 | 6.000% | 6.000% | ✓ |
  | Idaho Falls | 83402 | 6.000% | 6.000% | ✓ |
  | Pocatello | 83201 | 6.000% | 6.000% | ✓ |
  | Caldwell | 83605 | 6.000% | 6.000% | ✓ |
  | Coeur d'Alene | 83814 | 6.000% | 6.000% | ✓ |
  | Twin Falls | 83301 | 6.000% | 6.000% | ✓ |
  | Sun Valley (resort 3%) | 83353 | 9.000% | 9.000% | ✓ |
  | Ketchum (resort 3%) | 83340 | 9.000% | 9.000% | ✓ |
  | McCall (resort 3%) | 83638 | 9.000% | 9.000% | ✓ |
  | Sandpoint (resort 1%) | 83864 | 7.000% | 7.000% | ✓ |
  | Salmon (resort 0.5%) | 83467 | 6.500% | 6.500% | ✓ |

  Note: the Commission's list of 23 local-tax cities is larger than our 12
  modeled resort cities because several of those cities levy the local option
  **only** on lodging / alcohol-by-the-drink / prepared food, not general
  retail. Our `id_data.py` correctly models only the general-retail resort
  sales taxes, per the module docstring. No action.

---

## Sources
- SST rate & boundary file updates — https://www.streamlinedsalestax.org/Shared-Pages/rate-and-boundary-files/rate-and-boundary-file-updates
- SST Iowa state details — https://www.streamlinedsalestax.org/state-details/iowa
- Idaho State Tax Commission, City Sales Taxes — https://tax.idaho.gov/taxes/sales-use/sales-tax/local-sales-tax/city-sales-tax/
- Live engine — https://api.opensalestax.org/v1/calculate (probed 2026-07-07)
