# Daily state sales tax audit — 2026-10-28 (buffer-day catch-up: UT + VT)

## TL;DR

- **Day 28 is a buffer day**, used for catch-up. October's rotation has run only
  once (day 1, AK + AL); days 2–26 were all missed. **UT and VT** were picked
  because they were the least recently audited pair: last audited 2026-06-29,
  four months ago, against the "at least monthly" requirement.
- **Both states are two quarters behind on prod** (Q2 2026 loaded; Q4 2026
  published), and **both have live rate changes that the engine does not know
  about yet.** Both are SST states, so rates come only from the SST file and there
  is no code fix. The fix is the refresh.
- **UT: 6 confirmed live under-collections** were probed, each confirmed by UT
  State Tax Commission Tax Bulletin 15-26. Among them, **every Weber County
  location under-collects 0.2pp** (from 2026-10-01). The largest gap is
  **Hanksville under-collecting 1.40pp**. The Q4 file also carries 7 new or
  changed local rates effective 2026-07-01. These were not matched to a
  bulletin by name in this run.
- **VT: 9 new 1% local option taxes.** Eight took effect on 2026-07-01 and one,
  Peru, on 2026-10-01. The VT Department of Taxes list confirms all nine. At least
  **5 of the 9 towns under-collect 1.00pp** on a bare-ZIP lookup.
- The only repo change is the Ogden pin, moved 7.250 → 7.450 (fails under
  `-m liveapi` until the UT Q4 refresh is loaded). UT/VT cross-check sources are
  now recorded in `specs/research/data-sources.md`.
- This adds **≥ 11 live wrong-rate locations** to the stale-SST backlog (UT 6
  probed, VT 5 probed). Eric's decision on one batched refresh of all stale SST
  states is still pending.

## Rotation gap context

| Days | Pairs | Ran? |
|---|---|---|
| 1 | AK, AL | ✅ (2026-10-01) |
| 2–26 | AR/AZ … WV/WY | ❌ none ran in October |
| 28 | buffer | catch-up: UT + VT (this run) |

Before this run the states were last audited as follows. From 2026-06-29 to
2026-07-31: UT, VT, TX, VA, CA, CO, NH, NJ, CT, DC, IL, IN, KS, KY, LA, MA, MD,
ME, MI, MN, MO, MS, MT, NC, NM, NV, NY, OH, OK, OR, PA, PR, SD, TN, WV, WY. Most
of these are now more than 3 months stale. The next buffer days (29–31) should
continue down this list. TX + VA would come next, as the other states last
audited on 06-29.

---

## UT (Utah) — SST member

- **Source:** SST Governing Board rate/boundary index
  (`streamlinedsalestax.org/ratesandboundry/Rates/`, `/Boundary/`), cross-checked
  against UT State Tax Commission Tax Bulletins (`tax.utah.gov/tax-bulletins/`):
  **15-26** "Sales Tax Rate Changes" (eff 2026-10-01) and **11-26** "Corrected
  Tax Rates" (eff 2026-07-01).
- **Last loaded on prod:** `UTR2026Q2MAR20.zip` / `UTB2026Q2MAR20.zip`
  (data_version 620, `UT-SST-2026Q2MAR20`, fetched 2026-05-15).
- **Latest available:** **`UTR2026Q4AUG11.csv` / `UTB2026Q4AUG11.csv`**. The Q3
  file (`UTR2026Q3MAY11`) was chipped on 2026-06-29 and never applied. Apply Q4
  and skip Q3.
- **Drift summary:** 6 probed locations under-collect by 0.20–1.40pp. The causes
  are a county highways/transit tax (Weber) and new or raised city taxes in
  Washington City, Toquerville, Hildale, Delta and Hanksville.
- **Recommended action:** REFRESH NEEDED → UT Q4 (chipped). There is no
  code-side fix.

### Q2 → Q4 rate-file diff (every row)

| Code | Type | Q2 (prod) | Q4 | Effective | Bulletin match |
|---|---|---|---|---|---|
| 057 Weber County | county | 2.40 | **2.60** | 2026-10-01 | 15-26: county highways + transit +0.2% |
| 81960 Washington City | city | 0.30 | **0.63** | 2026-10-01 | 15-26: emergency services +0.33% |
| 76900 Toquerville | city | 0.33 | **0.63** | 2026-10-01 | 15-26: highways + transit +0.3% |
| 35300 | city | — | **0.33** | 2026-10-01 | matches Hildale emergency services 0.33% |
| 18910, 20503 | city | — | **0.30** each | 2026-10-01 | matches Delta / Hanksville highways 0.3% (not attributed code by code) |
| 22701, 33100 | city | — | **1.40** each | 2026-10-01 | matches Hanksville 0.3% + resort 1.1% (two codes, not attributed) |
| 97019 | district | 0.35 | **0.10** (new row) | 2026-07-01 | a *decrease*, likely the 11-26 Santaquin South mass-transit correction (-0.25) — not confirmed by code |
| 07501, 19501 | city | — | 0.40 each | 2026-07-01 | not matched in this run |
| 25505, 97012 | city/district | — | 0.10 each | 2026-07-01 | not matched in this run |
| 68650 | city | — | 0.30 | 2026-07-01 | not matched in this run |
| 73050 | city | — | 1.00 | 2026-07-01 | not matched in this run |

New codes only take effect once the matching Q4 **boundary** file binds them to
addresses, so the rate file and the boundary file must be loaded together.

### Live engine (`/v1/calculate`, bare ZIP5, $100)

| City | Expected (UT bulletin / SST Q4) | Actual (engine) | Delta |
|---|---|---|---|
| Ogden 84401 (Weber) | 7.45 | 7.25 | **−0.20** |
| North Ogden 84414 (Weber) | 7.45 | 7.25 | **−0.20** |
| Roy 84067 (Weber) | 7.65 | 7.45 | **−0.20** |
| Washington City 84780 | 7.08 | 6.75 | **−0.33** |
| Toquerville 84774 | 7.08 | 6.78 | **−0.30** |
| Hildale 84784 | 6.78 | 6.45 | **−0.33** |
| Delta 84624 | 6.65 | 6.35 | **−0.30** |
| Hanksville 84734 | 9.05 | 7.65 | **−1.40** |
| Salt Lake City 84111-2202 | 8.45 | 8.45 | 0.00 |
| Provo 84601 | 7.45 | 7.45 | 0.00 |
| St George 84770 | 6.75 | 6.75 | 0.00 |
| Clearfield 84015 | 7.25 | 7.25 | 0.00 |
| Santaquin 84655 | 7.45 | 7.45 | 0.00 (city-centre ZIP; the "Santaquin South" sub-area correction was not probed) |

Note on the 2026-06-29 finding: bare-ZIP Provo now returns 7.45, which is
correct. The `-0001` county-drop finding
(`specs/findings/ut-zip4-0001-county-drop-2026-06.md`) was not re-tested.

## VT (Vermont) — SST member

- **Source:** SST index, cross-checked against the Vermont Department of Taxes
  "Local Option Tax" page (`tax.vermont.gov/business/local-option-tax`), which
  lists 38 active 1% municipalities. Vermont has no county sales tax.
- **Last loaded on prod:** `VTR2026Q2FEB20.zip` / `VTB2026Q2FEB20.zip`
  (data_version 398, `VT-SST-2026Q2FEB20`, fetched 2026-05-06).
- **Latest available:** **`VTR2026Q4AUG20.zip` / `VTB2026Q4AUG20.zip`**.
- **Drift summary:** **9 new local option taxes** — Bristol, Fair Haven,
  Mendon, Morristown, Pomfret, Swanton, Vergennes and Waitsfield from 2026-07-01,
  and Peru from 2026-10-01. The Q4 SST rate file adds exactly 9 open-ended
  type-1 rows at 1% (8 dated 20260701, 1 dated 20261001: code 09025, 25375,
  44125, 46675, **55000 [Oct = Peru]**, 56350, 71725, 74650, 75325). The counts
  and dates match the Vermont list. The Q4 file also drops one long-expired row
  (`50,02,00507`, ended 2018), which has no effect.
- **Recommended action:** REFRESH NEEDED → VT Q4 (chipped together with UT).
  There is no code-side fix. After the refresh, add the 9 codes to
  `vt_names.py`, but only after verifying each one by probe, per that file's
  own rule.

### Live engine (`/v1/calculate`, bare ZIP5, $100)

| Town (ZIP) | Expected (VT DoT) | Actual (engine) | Delta | Note |
|---|---|---|---|---|
| Fair Haven 05743 | 7.00 | 6.00 | **−1.00** | |
| Morristown / Morrisville 05661 | 7.00 | 6.00 | **−1.00** | |
| Pomfret 05053 | 7.00 | 6.00 | **−1.00** | |
| Vergennes 05491 | 7.00 | 6.00 | **−1.00** | |
| Waitsfield 05673 | 7.00 | 6.00 | **−1.00** | |
| Bristol 05443 | 7.00 | 7.00 | 0.00 | right total, **wrong authority**: shows "Middlebury" |
| Mendon 05701 | 7.00 | 7.00 | 0.00 | the ZIP is mostly Rutland City, so this is not a Mendon test |
| Swanton 05488 | 7.00 | 7.00 | 0.00 | binds `VT-city-61750`, apparently a neighbouring town's code |
| Peru 05152 | 7.00 | 7.00 | 0.00 | binds `VT-city-85075`, apparently a neighbouring town's code |
| Burlington 05401 | 7.00 | 7.00 | 0.00 | |
| Montpelier 05602 | 7.00 | 7.00 | 0.00 | |
| Bennington 05201 (no LOST) | 6.00 | 6.00 | 0.00 | |

Vermont ZIPs routinely span several towns, so a bare-ZIP lookup is a
heuristic. Bristol, Swanton and Peru show 7.00% only because a neighbouring
LOST town's code sits on the same ZIP. The authority names in the response are
wrong for those three. This is the known VT ZIP/town limitation, not a new
defect. After the Q4 boundary file is loaded, addresses with a real ZIP+4
should resolve to the right town.

## Actions taken

1. `tests/integration/test_sst_dor_validation.py`: Ogden 84401 pin moved
   7.250 → 7.450, with the source cited (Bulletin 15-26 and SST county 057). It
   fails under `-m liveapi` until prod loads UT Q4. CI excludes `liveapi`.
2. `specs/research/data-sources.md`: UT and VT cross-check sources recorded.
3. Chip: "Refresh UT + VT SST to 2026 Q4" (`UTR/UTB2026Q4AUG11`,
   `VTR/VTB2026Q4AUG20`). No SST file was replaced on prod.
4. `specs/handoff.md`: open follow-up added.
