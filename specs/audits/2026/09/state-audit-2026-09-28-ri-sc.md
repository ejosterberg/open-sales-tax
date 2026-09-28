# Daily state sales tax audit — 2026-09-28 (day 21 pair: RI + SC)

> **Date note.** This run executes the **day-21 pair (RI + SC)**, recorded as
> "owed (today's nominal pair)" in the 2026-09-21 report's rotation-debt table.
> The session opened under a 2026-09-21 clock and the host date advanced to
> **2026-09-28** mid-run; the pair was completed rather than restarted, and the
> report is filed under the date it was written — the same precedent the
> 2026-09-21 (DE + FL) and AR + AZ runs set. Day 28 falls in the 27–31 buffer
> window, so no *additional* pair is owed for the new date.
>
> A separate report for 2026-09-21 already exists and covers DE + FL; this file
> does not replace it.

## TL;DR

- **2 jurisdictions audited. Both are rate-correct on the live engine — no
  over-collection and no under-collection found in either.**
- **Rhode Island — clean.** Flat **7%** statewide, no local general sales tax.
  All 6 RI pins pass live. Its SST file is from **2019Q2**, which looks alarming
  and **is not drift**: RI is a single-rate state that has not changed its rate
  since before 2006-10-01, so SST does not require it to publish rate/boundary
  files, and the pinned file is still the only one upstream. Confirmed by the
  project's own `check_sst_pins.py`.
- **South Carolina — clean on rates, one real test defect fixed.** All **46
  counties** diffed against the live ST-500: **46/46 exact**, Myrtle Beach 9%
  exact. But two `DOR_GRID` pins on the **same ZIP+4** asserted **8.000% and
  9.000%**, so one always failed. The DOR says 9%; the engine returns 9%. The
  stale 8% pin was wrong — it assumed Horry County levies 1% when the ST-500
  has it at 2%. **Fixed this run.**
- **The SC defect generalised into the project's top-owed follow-up.** Sweeping
  all 790 grid rows found **12 ZIP+4s with contradictory pins** across AK, CA
  (7), NM, SC, TX (2). All 12 were probed live: **the engine returns the higher
  pin in every case**, so the low pins are stale pre-city-coverage leftovers.
  **CDTFA independently confirms all 7 California values** — the engine is
  right, the pins are the problem. Written up and chipped; only the in-scope SC
  one was fixed here.
- **Incidental:** `check_sst_pins.py` reports **3 dead SST pins** (AR boundary,
  OH rates + boundary). Outside today's pair; chipped.

## RI — Rhode Island

- **Source:** RI Division of Taxation, Sales & Use Tax —
  <https://tax.ri.gov/tax-sections/sales-excise-taxes/sales-use-tax> (page last
  updated 2025-12-08), plus the SST Rate and Boundary Files page
  <https://www.streamlinedsalestax.org/Shared-Pages/rate-and-boundary-files>.
- **Last loaded on prod:** `RI-SST-2019Q2MAR27` (`data_versions.id=320`, fetched
  2026-05-04); ZCTA boundaries `RI-ZCTA-2020` (id 597).
- **Latest available:** `RIR2019Q2MAR27` / `RIB2019Q2MAR27` — **still the only
  files upstream.** Not stale.
- **Drift summary:** **none.**
- **Recommended action:** none.

### The 2019 file is current, not rotten

The cached SST files being seven years old is the first thing that looks wrong
here, and it is worth writing down permanently so the next RI audit does not
re-investigate it.

The SST Rate and Boundary Files page states, verbatim:

> "Single rate states that have not changed their rate since October 1, 2006,
> are not required to provide a rate or boundary file."

Rhode Island has held **7%** since 1990-07-01 and has no local general sales
tax, so it qualifies and simply stopped republishing. The project already knows
this: commit `5e3a110` ("detect SST pin rot before it breaks a release") names
**RI 2019** as one of six states SST never republished (with IN 2008, KY 2012,
MI 2023, NJ 2018, NV 2025), and notes that an age-based staleness check "would
have flagged all six forever" — which is exactly why the checker compares
against upstream instead.

Running that checker live this session confirms it: **RI is reported current.**

### Rate verification

7% flat, no county or municipal general sales tax. All 6 RI pins pass against
the live engine (`pytest -m liveapi -k RI-` → 6 passed).

| ZIP | Expected (RI DOR) | Actual (engine) | Delta |
|---|---|---|---|
| 02903 Providence (ZIP+4 `2511`) | 7.000% | 7.000% | — |
| 02903 Providence (ZIP+4 `0001`) | 7.000% | 7.000% | — |
| (6 RI pins total, all 7.000%) | 7.000% | 7.000% | — |

### 2026 changes checked — none touch the general retail rate

Rhode Island has been **expanding the tax base** rather than moving the rate:

- **Short-term parking** became subject to the 7% sales tax effective
  **2025-10-01** (the Division published a dedicated FAQ).
- **Other tobacco products** redefined to include tobacco-free nicotine
  pouches, also **2025-10-01**.
- The **local hotel tax** rose **1% → 2%** effective **2026-01-01**.

None of these is a general retail *rate* change, so none affects the engine's
combined-rate output. The hotel and 1% meals-and-beverage taxes are
transaction-type-specific levies outside a general sales-tax rate lookup —
correctly not modeled as part of the combined rate.

**Watch item:** base expansion is the RI pattern to track, and it is a
*taxability* question, not a rate question. If the engine ever grows a
service-taxability matrix, RI's parking and nicotine changes are the test cases.

## SC — South Carolina

- **Source:** SC DOR Form **ST-500**, "South Carolina Local Tax Designation by
  County," effective **May 1, 2026** (**Rev. 3/9/2026**, pub. 5182) —
  <https://dor.sc.gov/sites/dor/files/forms/ST500.pdf>
- **Last loaded on prod:** `SC-SST-2026Q2APR15` (`data_versions.id=481`, fetched
  2026-05-11) — **after** the May 1 2026 effective date, so prod carries the
  current chart.
- **Latest available:** still Rev. 3/9/2026. **No republication** since May.
- **Drift summary:** **no rate drift.** 46/46 counties exact. One contradictory
  test pin fixed.
- **Recommended action:** none for rates. Pin fixed in repo; no prod reload
  needed (SC prod data is current).

### Method: full 46-county diff, not a spot-check

Per the standing rule, this was a wholesale diff rather than a probe of pinned
ZIPs. The live ST-500 PDF was parsed with `pypdf` and **all 46 counties** plus
the Myrtle Beach municipal row were compared against `SC_COUNTY_RATE_PCT`
(state 6% + county local):

```
ST-500 counties: 46   module counties: 46
All 46 counties match the ST-500 exactly.
Myrtle Beach: DOR=9%  module=9.000% (Horry 8.000% + city TD 1.000%) OK
```

**County rates are covered by this same source** — the ST-500 *is* South
Carolina's county-level chart, so SC has no separate municipal-vs-county
publication split of the kind that hid the Cochise County increase in Arizona.
The 1% Williamsburg Capital Projects Tax effective 2026-05-01 (the only change
in the current chart's Special Notice) is already carried correctly.

**Cadence note for future runs:** SC local taxes are referendum-driven and by
statute take effect **May 1** following a November vote. Mid-year drift is not
expected; the **spring** audits (day 21 lands 2027-04-21 and 2027-05-21) are
the ones that must re-pull the ST-500 attentively.

### Finding — two contradictory pins on Myrtle Beach `29577-0001` (FIXED)

`DOR_GRID` carried **two rows for the identical ZIP+4**, asserting different
rates:

| line | expected | citation |
|---|---:|---|
| 3492 | **8.000%** | `iter-65 audit pin: SC DOR (state 6 + Horry 1 + Myrtle Beach 1)` |
| 5771 | **9.000%** | `iter-127 audit pin: SalesTaxHandbook (state 6 + Horry 2 + city 1 TD)` |

One of them has failed on every run since iter-127 landed. Nobody saw it because
`DOR_GRID` is gated behind `-m liveapi`, which CI deselects.

**The ST-500 settles it: "Horry-Myrtle Beach 9%".** The engine returns
**9.00000%**. So:

- The **8.000% pin is wrong.** Its arithmetic assumed **Horry County = 1%**;
  the ST-500 has Horry at **2%** (TT + ECI). It was wrong the day it landed.
- The **9.000% total is right**, but it was cited to **SalesTaxHandbook** — an
  aggregator, which constitution §2 forbids as a rate source.

**No live rate defect:** the engine, the module and the DOR all agree at 9%.
This was a test-integrity defect only. Had anyone "fixed" the engine to satisfy
the 8% pin, it would have created a **1pp under-collection** in Myrtle Beach.

**Fixed:** the stale 8.000% pin removed; both surviving Myrtle Beach pins
(`29577`, `29572`) re-cited to the ST-500 with the component breakdown. The SC
module docstring records the 46/46 re-verification and the May-1 cadence.

`pytest -m liveapi -k "RI- or SC-"` → **25 passed** (was 25 passed / 1 failed).

### Verified correct (no action)

All other SC pins pass, including the three verified-zero-local counties that
are the easiest thing to get wrong (Beaufort, Greenville, Oconee at 6.000%),
and the 9% Berkeley / Charleston / Jasper group.

## Cross-cutting finding — the contradictory-pin class, swept project-wide

The SC defect was not a one-off, so the whole grid was swept. **12 ZIP+4s
carried contradictory pins** (AK 1, CA 7, NM 1, SC 1, TX 2) out of 790 rows
over 774 distinct keys, plus 5 harmless same-rate duplicates.

All 12 were probed live. **The engine returns the higher pin in all 12** — the
low pins are stale leftovers from before city-level coverage landed, several
saying so in their own citations ("post-zip_county", "iter-62 county
expansion", "post-v0.29 ZCTA").

**CDTFA independently confirms all 7 California values** (Burbank 10.500,
Temecula 8.750, San Luis Obispo 8.750, Burlingame 9.625, Napa 8.750, Sausalito
9.250, Eureka 10.250) — matching the engine exactly. California is correct and
its low pins are provably stale.

Four remain unverified and deliberately untouched: **AK Kenai** (a real
borough-suppressed-inside-city modeling question, not a stale value), **NM Rio
Rancho**, and **TX Bastrop + Pflugerville**.

Also counted: **226 of 790 grid rows (29%) cite an aggregator** — CA 159, TX 24,
AL 17, AZ 8, FL 7, MO 4, WY 3, OK 2, SC 2. The existing
aggregator-sourced-rate-errors note tracks ~130 hits in `src/`; **the test pins
were never counted.**

Full write-up, per-item verification status and the recommended fix order:
`specs/findings/dor-grid-contradictory-duplicate-pins-2026-09.md`. **Only the
SC item was fixed here** — the rest need per-state primary sources, and
bulk-adopting them is precisely the AZ mistake.

### Why this keeps happening, and the one test that stops it

`DOR_GRID` runs only under `-m liveapi`, which CI deselects, and in practice
only ever filtered to one state. So a contradiction elsewhere is invisible.

The **offline** consistency test named as the top open item by the 2026-09-05 AZ
audit and run ad hoc against FL (2026-09-21) and SC (2026-09-28) remains
unwritten. Its first assertion — *no two rows for the same ZIP+4 disagree* — is
about 15 lines, needs no network, and would have caught all 12 of these on the
day each landed. **This is the highest-value unwritten test in the project.**

## Incidental — 3 dead SST pins (outside today's pair)

`scripts/check_sst_pins.py` was run to settle the RI question and reported drift
in two other states:

| state | kind | pinned | upstream |
|---|---|---|---|
| AR | boundary | 2026Q4SEP02 | 2026Q4SEP17 |
| OH | rates | 2026Q4AUG27 | 2026Q4SEP17 |
| OH | boundary | 2026Q4SEP01 | 2026Q4SEP17 |

22 states current. Per the checker's own design these pins are **dead (404)**,
so a release-tag data rebuild would fail. Not adopted here — constitution §11
makes data updates explicit, and AR/OH are not today's pair. Chipped.

## Actions taken

1. **Committed:** removed the contradictory 8.000% Myrtle Beach pin; re-cited
   both surviving Myrtle Beach pins to the ST-500; recorded the 46/46
   re-verification, the no-republication-since-May fact and the May-1 referendum
   cadence in the `sc_data.py` docstring.
2. **Wrote:** `specs/findings/dor-grid-contradictory-duplicate-pins-2026-09.md`
   — the 11 remaining contradictory pins with live-probe results, CDTFA
   verification for CA, the per-item fix order, and the offline-test spec.
3. **Chipped:** (a) resolve the 11 remaining contradictory pins + add the
   offline consistency test; (b) refresh the 3 dead AR/OH SST pins.
4. **Handoff:** open follow-ups updated.

## Rotation debt

This run cleared **day 21 (RI + SC)**. Both September runs so far have cleared
one pair each. Still owed from the September cycle:

| Day | Pair | Status |
|----:|------|--------|
| 4 | CT, DC | **owed** |
| 5 | DE, FL | done 2026-09-21 |
| 6 | GA, HI | **owed** — HI Maui 0.5pp under-collection open since 2026-07-06 |
| 7–20 | IA/ID … PA/PR | owed (14 pairs) |
| 21 | RI, SC | **done this run** |
| 22–26 | SD/TN … WV/WY | owed (5 pairs) |
| 27–31 | — | buffer (today is day 28) |

**The rotation is still not keeping up** — 3 of 58 days since 2026-08-06. The
2026-09-21 report asked Eric to confirm whether the daily task is actually
firing (the Claude Code app must be open when the cron fires); the gap pattern
continues to look like missed fires rather than skipped work. **That question is
unanswered and is now the blocking item for the audit programme**, not any
individual state.

## Standing systemic item — the prod-deploy backlog

Unchanged and still the largest source of live wrong rates: HI Maui, GA Madison,
ND Scranton + Drayton, NE Edgar, WA (6), AK (7), AZ Florence, FL Okeechobee +
Palm Beach (2 ZIPs) + Collier, and the multi-county tiebreak fix are **all fixed
in the repo and wrong in production.**

**Neither of today's states adds to that list** — RI and SC are both correct on
the live engine, and SC's prod data (loaded 2026-05-11) already carries the
current ST-500. Today's fix was test-only, so **no reload is required for RI or
SC.**
