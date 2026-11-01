# TN — full-sweep audit 2026-11-01

## TL;DR
Workflow pin **matches upstream** (`TNR2026Q4AUG21` / `TNB2026Q4AUG21`).
**Prod data is 6 quarters stale** — `TN-SST-2025Q1MAR07`, fetched
2026-05-15. All 4 tier-1 TN DOR_GRID pins (Nashville, Memphis,
Knoxville, Chattanooga) still match the live engine, so no proven
drift found in this sweep. IMPROVE Act 0.5% transit stacking (fixed
in v0.44) is working — Nashville 37203 and 37206 both return
**9.750%** as expected. Flag: REFRESH_PENDING.

## Facts

- SST member. Workflow pins: `"TN 2026Q4AUG21 2026Q4AUG21"`.
- Upstream listing (fetched 2026-11-01):
  - Rates: `TNR2026Q4AUG21.csv`
  - Boundary: `TNB2026Q4AUG21.zip`
  - **Pin equals upstream.** No `check_sst_pins.py` drift.
- Prod data: `TN-SST-2025Q1MAR07`, fetched **2026-05-15**. The May-2026
  fetch loaded the Q1-2025 file that was still then-current; TN has
  published three quarterly files since (Q2 / Q3 / Q4-2026) that prod
  has never pulled.
- Live probes (via `/v1/rates?zip5=…`):
  | ZIP | City | Live | DOR_GRID expected | Delta |
  |---|---|---|---|---|
  | 37203 | Nashville | 9.750% | 9.750% | 0 |
  | 37206 | Nashville | 9.750% | 9.750% | 0 |
  | 38103 | Memphis | 9.750% | 9.750% | 0 |
  | 37902 | Knoxville | 9.250% | 9.250% | 0 |
  | 37402 | Chattanooga | 9.250% | 9.250% | 0 |

## Drift

None **proven today**, but a 6-quarter gap is exactly the window in
which GA Madison, WA 6 cities, and ND Scranton/Drayton all slipped
through on tier-1-passing pins. TN is a non-trivial-local-option state
(the state portion is 7.0% but counties stack 2.25–2.75% and a few
cities add 0.25–0.5%), so an obscure county move between MAR 2025 and
AUG 2026 is plausible and would not surface on these five pins.

## Recommended action

1. **CHIP (carry forward from 2026-07-22):** `data load -s TN -v
   TN-SST-2026Q4AUG21` on `opensalestax-01` after the next api
   redeploy. No code change (TN rate data lives entirely in the SST
   file). The TN pin bump is lower risk than OH because the pin is
   not dead.
2. **Follow-up after reload:** re-run the IMPROVE Act stacking
   assertion (Nashville + Memphis `-m liveapi`) to confirm the 0.5%
   transit continues to resolve on the Q4 file, since Q4 is where
   TN DOR occasionally rejigger district codes.

## Status

**REFRESH_PENDING.**
