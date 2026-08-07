# Daily state sales tax audit — 2026-08-06 (day 6: GA + HI)

## TL;DR

- 2 jurisdictions audited. **2 rate defects confirmed, both currently
  live on prod**, both traceable to data that has not been reloaded
  rather than to engine logic.
- **GA — NEW:** Madison County cut its local rate 4% → 3% effective
  2026-07-01. Prod is still on the Q2 SST file, so the engine
  **over-collects 1.0%** across all 6 Madison County ZIPs. Confirmed
  against both the SST Q3 file and the GA DOR Q3 rate chart.
  Regression pin added; SST refresh chipped.
- **HI — RECURRING:** the Maui County 0.5% GET surcharge fix has been
  correct in the repo since 2026-07-06 but prod has **still not been
  reloaded** (HI DataVersion fetched 2026-05-05). Kahului 96732 returns
  4.000% instead of 4.500% — a **0.5% under-collection on every Maui
  transaction, now 31 days past the fix**. No new HI rate change; the
  DOTAX schedule is unchanged.
- Both defects are blocked on the same class of action: a prod data
  reload. See "Systemic note" at the bottom — 16 of 24 SST states are a
  quarter or more stale, and GA is the first proven wrong answer from it.

Note on timing: this run began on day 6 of the month (GA + HI per the
rotation table) and crossed midnight during execution. The report is
filed under its start date; day 7 (IA + ID) is unaffected.

## GA — Georgia (SST member)

- **Source:** SST quarterly index
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates/) +
  GA DOR rate chart (https://dor.georgia.gov/sales-tax-rates-general)
- **Last loaded on prod:** `GA-SST-2026Q2FEB19`, fetched 2026-05-04
  (rate `GAR2026Q2FEB19.csv`, boundary `GAB2026Q2FEB16.zip`)
- **Latest available:** rate **`GAR2026Q3JUN05.csv`**, boundary
  **`GAB2026Q3MAY19.zip`**
- **Drift summary:** exactly one jurisdiction changed between Q2 and
  Q3 — **Madison County (SST code 195) 4% → 3%, effective 2026-07-01**
  — and the engine has been over-collecting 1.0% there since.
- **Recommended action:** REFRESH NEEDED — load GA 2026Q3 on prod
  (chipped). No code change required; GA rates come wholly from the
  SST file.

### Madison County detail

Row-level diff of the two quarterly files (449 → 450 rows) shows three
changed rows, all code `195`:

```
-13,00,195,0.04,0.04,0.04,0.04,20220401,29991231     (Q2: open-ended 4%)
+13,00,195,0.04,0.04,0.04,0.04,20220401,20260630     (Q3: closed out)
+13,00,195,0.03,0.03,0.03,0.03,20260701,29991231     (Q3: new 3%)
```

GA DOR's Q3 2026 chart (effective July 1, 2026) row: `095 Madison 7`
— combined 7% = state 4% + local 3%. (GA DOR's jurisdiction code `095`
and the SST/FIPS code `195` both denote Madison County.)

| City | ZIP | Expected (GA DOR Q3) | Actual (engine) | Delta |
|---|---|---:|---:|---:|
| Danielsville | 30633 | 7.000 | 8.000 | **+1.000** |
| Comer | 30629 | 7.000 | 8.000 | **+1.000** |
| Hull | 30646 | 7.000 | 8.000 | **+1.000** |
| Ila | 30647 | 7.000 | 8.000 | **+1.000** |
| Colbert | 30628 | 7.000 | 8.000 | **+1.000** |
| Carlton | 30627 | 7.000 | 8.000 | **+1.000** |

Engine jurisdiction breakdown for 30633 confirms the cause precisely:
`Georgia / state / 4.00000` + `Madison County / county / 4.00000`. The
stale county row is the whole story — no boundary or stacking defect.

### Existing GA pins — all still correct

All 11 GA rows in the DOR grid match the live engine exactly, consistent
with the diff showing no other GA jurisdiction changed:

| City | ZIP+4 | Expected | Actual | Delta |
|---|---|---:|---:|---:|
| Atlanta | 30303-1015 | 8.900 | 8.900 | 0 |
| Roswell (synthetic +4) | 30075-0001 | 7.750 | 7.750 | 0 |
| Alpharetta | 30022-1234 | 7.750 | 7.750 | 0 |
| Savannah | 31401-0001 | 7.000 | 7.000 | 0 |
| Macon | 31201-0001 | 8.000 | 8.000 | 0 |
| Athens | 30601-0001 | 8.000 | 8.000 | 0 |
| Albany | 31701-0001 | 8.000 | 8.000 | 0 |
| Marietta | 30060-0001 | 6.000 | 6.000 | 0 |
| Columbus | 31901-0001 | 9.000 | 9.000 | 0 |
| Suwanee | 30024-0001 | 6.000 | 6.000 | 0 |
| Athens-Clarke | 30605-0001 | 8.000 | 8.000 | 0 |

Spot-checked against the same GA DOR Q3 chart: `025 Chatham 7`
(Savannah ✓) and `029 Clarke 8` (Athens ✓).

## HI — Hawaii (non-SST, self-seeded)

- **Source:** HI DOTAX county surcharge schedule
  (https://tax.hawaii.gov/geninfo/countysurcharge/), page last updated
  2024-01-09
- **Last loaded on prod:** `HI-SST-V0.32-COUNTIES`, fetched
  **2026-05-05** — i.e. predating the 2026-07-06 Maui correction
- **Latest available:** n/a (self-seeded from `hi_data.py`; no upstream
  file)
- **Drift summary:** no new rate change. DOTAX still publishes all four
  inhabited counties at 0.5%. But the **known Maui defect is still live
  on prod** because the HI reload chipped on 2026-07-06 has not run.
- **Recommended action:** re-surface the pending prod HI reload (chip
  refreshed). Repo data is already correct — this is purely a deploy.

### DOTAX schedule as published (unchanged)

| County | Surcharge | Effective | Combined GET |
|---|---:|---|---:|
| Honolulu (Oahu) | 0.5% | 2007-01-01 → 2030-12-31 | 4.5% |
| Kauai | 0.5% | 2019-01-01 → 2030-12-31 | 4.5% |
| Hawaii | 0.5% | 2020-01-01 → 2030-12-31 | 4.5% |
| Maui | 0.5% | 2024-01-01 → 2030-12-31 | 4.5% |
| Kalawao | none | — | 4.0% |

Surcharge applies only to activities taxed at the 4.0% rate (not the
0.5% wholesaling rate or the 0.15% insurance-commission rate) — matches
how `hawaii.py` models it.

### Live-engine cross-check

| City | ZIP+4 | Expected (DOTAX) | Actual (engine) | Delta |
|---|---|---:|---:|---:|
| Honolulu | 96813-0001 | 4.500 | 4.500 | 0 |
| Hilo | 96720-0001 | 4.500 | 4.500 | 0 |
| Lihue | 96766-0001 | 4.500 | 4.500 | 0 |
| **Kahului (Maui)** | 96732-0001 | 4.500 | **4.000** | **−0.500** |
| Pearl City | 96782-0001 | 4.500 | 4.500 | 0 |
| Kaneohe | 96744-0001 | 4.500 | 4.500 | 0 |
| Waipahu | 96797-0001 | 4.500 | 4.500 | 0 |
| Kailua-Kona | 96740-0001 | 4.500 | 4.500 | 0 |

7 of 8 correct; the one failure is exactly the row flagged 31 days ago
in `specs/findings/hi-maui-county-surcharge-2026-07.md`.

## Actions taken

1. **Commit** — added a DOR-grid regression pin for GA Madison County
   (`30633-0001 → 7.000`). It is a `liveapi` row, excluded from CI
   (`pytest -m "not liveapi"`), so it will fail only under an explicit
   live run until prod ingests GA Q3 — matching the existing convention
   for the AZ/NC/NY/HI pending-reload pins.
2. **Finding written** —
   `specs/findings/ga-madison-county-rate-cut-2026-08.md`.
3. **Chips** — (a) refresh GA SST quarterly to 2026Q3; (b) re-surface
   the still-pending HI Maui prod reload.
4. **Handoff** — open follow-ups updated for both.

Deliberately **not** done: the repo's GA unit-test fixture
(`src/opensalestax/data/fixtures/ga/GAR2026Q2FEB19.csv`) was left on Q2.
It is referenced by filename in `tests/unit/test_state_georgia.py` (4
sites) and in `georgia.py` docstrings ("449 rows"), so swapping it is a
multi-file edit that belongs with the reviewed SST refresh, not with an
automated audit. Per the daily-audit rule, SST files are not auto-pulled.

## Systemic note — SST fleet staleness

Comparing every SST file cached on prod against the upstream directory
listing:

- **16 of 24 SST states are a quarter or more behind:** AR, GA, KS, MN,
  NC, ND, NE, OK, SD, TN, UT, VT, WA, WI, WV, WY.
- **8 are current:** IA, IN, KY, MI, NJ, NV, OH, RI. (Several of these
  look ancient — `INR2008Q4`, `KYR2012Q4`, `RIR2019Q2` — but SST hosts
  exactly one file per state and simply has not republished them. They
  are not stale.)

Prior audits chipped these state-by-state (AR, SD, TN, WV, WY were
already outstanding). GA is the **first case where the lag has been
demonstrated to produce a wrong answer to a real query**, which argues
for treating the refresh as one batched operation rather than 16
independent chips. Worth Eric's decision.

Related: a large backlog of "fixed in repo, prod deploy PENDING" items
has accumulated in `specs/handoff.md` (AZ, NC, NY, IL, IA, FL, HI, and
the 2026-08-01 engine fixes). Both of today's defects are instances of
it. The audit keeps finding correct code that users are not getting.
