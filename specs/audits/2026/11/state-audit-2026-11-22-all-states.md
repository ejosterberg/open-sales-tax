# All-state sales tax audit — 2026-11-22 (all 52 jurisdictions, scripted)

Run on request, in place of the day-22 rotation (SD + TN). This is also the
first run of the leaner weekly method that replaced the daily 2-state
rotation (see `weekly-state-tax-audit` scheduled task). Prior full sweep:
2026-11-01.

## TL;DR

- **52 jurisdictions checked.** 805 of 805 DOR-verified live-engine pins pass.
- **1 live over-collection found and fixed in code: Winslow, AZ** (city
  retail rate 3.00% → 2.00%, retroactive to 2026-07-01). Engine charges
  9.43% at 86047 today; correct is 8.43%. **Prod needs an AZ reload** to
  pick up the fix (not done by this run).
- **1 new district not encoded: Palo District, Mesa AZ** (effective
  2026-12-01, parcel-level). See
  `specs/findings/az-palo-district-mesa-2026-12.md`.
- **1 SST file newer than the workflow pin: NE boundary** `2026Q4NOV10`
  (pin `2026Q4OCT20`, dead upstream). Rate file `NER2026Q4AUG21` is current.
- Alaska: the 11-1-2026 ARSSTC sheet (applied 2026-11-01) is still the newest.

## Method (token-economical)

1. `scripts/check_sst_pins.py` + one `data_versions` query on prod — SST
   refresh status for all 24 SST states in two commands.
2. `pytest -m liveapi tests/integration/test_sst_dor_validation.py` — all
   805 pinned DOR-verified ZIP+4 rows across all 52 jurisdictions against
   `https://api.opensalestax.org/v1/calculate` (13 min).
3. Monthly-changing non-SST sources diffed month over month: AZ DOR
   `TPT_RATETABLE_11012026.pdf` vs `TPT_RATETABLE_12012026.pdf` (every `▲`
   line), and the ARSSTC listing for AK.
4. Quarterly non-SST states (the other 26): no new effective date since the
   2026-11-01 full sweep (next is 2027-01-01). Their wholesale DOR diff is
   scheduled for the quarter-boundary weekly runs; not repeated today.

## SST states (24)

Prod rate labels match the only upstream rate file for all 24 states
(AR, GA, IA, IN, KS, KY, MI, MN, NC, ND, NE, NJ, NV, OH, OK, RI, SD, TN, UT,
VT, WA, WI, WV, WY).

| State | Prod rate label | Upstream rate | Upstream boundary | Status |
|---|---|---|---|---|
| NE | `NE-SST-2026Q4AUG21` | `2026Q4AUG21` | `2026Q4NOV10` (pin `2026Q4OCT20`, 404) | REFRESH NEEDED (boundary) |

23 other states: current.

## Live-engine sweep

- 805 passed, 0 failed, 0 xfail, 0 xpass.

## Arizona

- Source: AZ DOR `TPT_RATETABLE_12012026.pdf` ("Effective December 1, 2026
  (Revised)"); compared with `TPT_RATETABLE_11012026.pdf`.
- Changes listed by DOR for 2026-12-01: Palo District, Camp Verde, Winslow.
- County rates (Table 1, code 017): no change November → December.

| Item | DOR (Dec) | Engine / module | Delta | Action |
|---|---|---|---|---|
| Winslow 017 Retail (86047) | 2.00 (combined 8.43) | 3.00 (combined 9.43) | −1.00 | Fixed in `az_data.py`; prod reload owed |
| Camp Verde 144 Hotel/Motel additional | 8.00 | n/a (lodging, not general retail) | — | None |
| Palo District (Mesa) 017 Retail | 7.30 (new) | not modeled | — | Finding written |

DOR note on Winslow: the rate sunset in July 2026 and the 2% rate applies
from 2026-07-01; DOR is updating its system to apply it retroactively.

## Alaska

- Source: `https://arsstc.org/business-sellers/tax-rates/`. Newest sheet is
  `ARRSTC-Sales-Tax-Rate-Sheet-with-Zip-Codes-11-1-2026.xlsx`, the one loaded
  on prod 2026-11-01. No change.

## Actions

- `az_data.py`: Winslow 3.000 → 2.000 with source comment.
- `specs/findings/az-palo-district-mesa-2026-12.md` written.
- Chip: NE boundary refresh + AZ prod reload.

## Follow-up 2026-11-23 (prod applied)

- Prod deployed to `7a213da`; AZ reloaded under the same label
  `AZ-SST-V0.55.4` (data_version 668, 79 rates). 86047 now 8.43%
  (was 9.43%); Phoenix 85003 9.10% and Scottsdale 85251 8.00% unchanged.
- NE boundary pin bumped to `2026Q4NOV10` (`b9e6bb0`) and loaded with rate
  `2026Q4AUG21` under the same label `NE-SST-2026Q4AUG21` (data_version
  669, 535,089 boundaries). The new file differs from `2026Q4OCT20` by one
  row only: Hastings 68901-3111 gains a historical place-code segment ending
  2026-10-20; the current assignment is unchanged. Omaha 7.00%, Lincoln
  7.25%, Hastings 7.00% unchanged.
- Winslow added to `tests/integration/test_sst_dor_validation.py`; live
  AZ+NE rows 64/64 pass. Prod `~/sst-load.sh` NE line refreshed (the rest of
  that array is still the 2026-05-04 snapshot).
