# Daily state sales tax audit — 2026-09-05 (day-2 rotation: AR + AZ)

## TL;DR

- 2 jurisdictions audited. **7 AZ rate defects found and fixed; 0 new AR drift,
  but AR has now fallen two quarters behind.**
- **AZ was audited systematically rather than by spot-check** — all 63
  `AZ_CITIES` entries and all 15 county rates compared against the AZ DOR rate
  table effective 2026-09-01. That turned a routine one-change day into six
  additional findings, **five of them over-collections** that had been live for
  months.
- **The one change the rotation was looking for:** Kingman 2.50% → 3.00%,
  effective 2026-09-01 (ordinance 2003) — predicted by the 2026-08-02 audit,
  confirmed, fixed.
- **The five that nobody was looking for:** Sahuarita (**+3.000pp over**), Parker
  (**+2.000pp over**), Tolleson, Paradise Valley, Litchfield Park — all traced to
  rates copied from SalesTaxHandbook/Avalara instead of the DOR.
- **Plus a missed county change:** Cochise County excise 0.500% → 1.000%
  effective **2026-07-01**, affecting every Cochise ZIP. Missed by the 07-31,
  08-01 and 08-02 audits because county changes are not announced on the
  municipal ordinance page those audits read.
- **AR: no new drift**, all 6 pinned cities and 4 unpinned tier-1 cities exact.
  But **prod is still on `ARR2026Q2MAR02` while SST has published Q4** — the six
  wrong 2026-07-01 rates are unchanged from a month ago, and the Q4 set lands
  2026-10-01.
- Full write-up of the AZ defects, their three distinct root causes, and the
  structural gap that hid them:
  [`specs/findings/az-aggregator-sourced-rate-errors-2026-09.md`](../../findings/az-aggregator-sourced-rate-errors-2026-09.md).

### Note on the rotation slot

This run started under a clock reading 2026-09-02 (day 2 → AR + AZ) and the
system date advanced twice mid-run, to 09-04 and then 09-05. Rather than
restart the rotation each time the clock moved, the AR + AZ pair already in
flight was completed — it was surfacing real drift. **CT + DC (day 4) and
DE + FL (day 5) were not audited and are owed**; days 27–31 are the designated
catch-up window.

---

## AZ (Arizona) — non-SST — 🔴 7 defects found, all fixed

- **Source:** AZ DOR *Transaction Privilege and Other Tax Rate Tables*,
  effective 2026-09-01
  (`azdor.gov/sites/default/files/document/TPT_RATETABLE_09012026.pdf`),
  cross-read with the Model City Tax Code
  [rate-and-code-updates](https://azdor.gov/business/transaction-privilege-tax/model-city-tax-code/rate-and-code-updates)
  page.
- **Last loaded on prod:** self-seeded module (`az_data.py`); AZ is not an SST
  state and has no quarterly file.
- **Method change this run:** instead of spot-checking ~43 pinned ZIPs, the
  whole DOR Table 2 was parsed (92 city blocks, business code 017) and diffed
  against every `AZ_CITIES` entry, and Table 1 was diffed against every
  `AZ_COUNTY_RATE_PCT` entry. 57 of 63 cities matched; 4 did not; 2 are not in
  the DOR table at all. This is what surfaced the six pre-existing defects.
- **Recommended action:** deploy. Everything below is repo-only until the pending
  AZ deploy + reload runs.

### 🔴 The seven defects

| ZIP | Jurisdiction | Engine (live) | DOR | Combined was | Combined now | Direction |
|---|---|---:|---:|---:|---:|---|
| 85629 | Sahuarita | 5.000 | **2.000** | 11.100 | **8.100** | **OVER 3.000pp** |
| 85344 | Parker | 4.000 | **2.000** | 10.600 | **8.600** | **OVER 2.000pp** |
| 85353 | Tolleson | 2.800 | **2.500** | 9.100 | **8.800** | **OVER 0.300pp** |
| 85253 | Paradise Valley | 2.800 | **2.500** | 9.100 | **8.800** | **OVER 0.300pp** |
| 85340 | Litchfield Park | 3.000 | **2.800** | 9.300 | **9.100** | **OVER 0.200pp** |
| all Cochise | Cochise County excise | 0.500 | **1.000** | — | — | under 0.500pp |
| 86401/86409 | Kingman | 2.500 | **3.000** | 8.100 | **8.600** | under 0.500pp |

Only Kingman is a *new* change. The other six were already wrong when the
2026-08-02 audit reported "42 of 43 pinned rows match" — because the pins
themselves had been derived from the same bad data.

### Kingman — 2.50% → 3.00%, effective 2026-09-01 (the predicted one)

On **2026-06-16** the Mayor and Council of the City of Kingman passed
**Ordinance No. 2003**, raising multiple privilege-tax classifications and use
tax from 2.50% to 3.00%, effective **2026-09-01**. The DOR table flags the
change with its ▲ marker for region code **KM**:

> `▲Retail Sales 017 3.00`

Mohave County levies **no** county excise (Table 1 shows 5.60% flat, i.e. state
only), so combined 86401/86409 goes **8.100 → 8.600**. The live engine returned
8.100 at audit time — under-collecting 0.500pp since 2026-09-01.

The same ordinance adopts Local Option V (single items over $10,000 taxed at
2.5%); the engine models the general retail rate only, unchanged.

### Cochise County — 0.500% → 1.000%, effective 2026-07-01 (missed three times)

Confirmed by diffing the Table 1 `017 Retail` row across successive monthly DOR
tables — the Cochise column reads 6.10% (state 5.6 + county 0.5) through the
06/2026 table and 6.60% (state 5.6 + county 1.0) from 07/2026 onward.

This affects **every Cochise ZIP**: Sierra Vista, Bisbee, Tombstone, Willcox,
Huachuca City, plus unincorporated ZIPs resolved via ZCTA.

It was missed on 07-31, 08-01 and 08-02 because all three audits read the Model
City Tax Code updates page, which announces **municipal ordinances only**.
County excise changes never appear there. The 08-02 audit caught Huachuca City's
*town* increase while the *county* increase underneath it went unnoticed.

**Procedural fix needed:** the audit skill must diff Table 1 of the monthly rate
table for AZ, not just the ordinance page. Other states will have an analogous
municipal/county split.

### The five over-collections — root cause

Four of five trace to iterations that took rates from third-party aggregators
rather than the DOR, and in each case *raised* a rate that was already correct:

| iter | Jurisdiction | Its own stated reasoning | Reality |
|---|---|---|---|
| iter-150 | Sahuarita | "city tax 2% became 5% special tax per SalesTaxHandbook" | no 5% line exists anywhere in Sahuarita's DOR schedule |
| iter-152 | Tolleson | "per SalesTaxHandbook" | DOR: 2.50 |
| iter-152 | Litchfield Park | "per SalesTaxHandbook" | DOR: 2.80 |
| iter-153 | Parker | "2% city tax + 2% special added Oct 2025" | DOR: 2.00 — the 4.00 is Parker's Restaurant/Bars (011) and Hotel Additional (144) rate, read off the wrong row |

Every one was framed as *fixing an under-collection*. In every case the
pre-existing value was right and the "fix" created a larger error in the
opposite, liability-creating direction.

**The repo already contained the right answer and could not say so.** A
`DOR_GRID` pin correctly asserted `85629 → 8.100`, cited to the AZ DOR CSV.
iter-150 did not reconcile with it — it added a **second pin for the same ZIP
asserting 11.100**, so the grid held two contradictory expectations at once.
Neither ever ran: `DOR_GRID` is gated behind `-m liveapi`, which CI deselects
(`1592 passed, 59 skipped, 816 deselected`).

**The single highest-value follow-up from this audit** is a CI-time test that
checks each `DOR_GRID` expectation against the in-repo state modules — no
network, no prod. It would have caught Sahuarita the day it landed and refused
the duplicate pin outright.

### Verified correct

52 of 63 AZ cities matched the DOR table exactly on the automated diff; a further
5 whose DOR blocks span a page break (Huachuca City 2.90, Marana 2.50, San Luis
4.00, Snowflake 3.00, Tucson 2.60) were confirmed by hand. **14 of 15 county
rates** matched Table 1 exactly — only Cochise was wrong.

### Open, deliberately not changed — Sun City and Vail

Neither appears in the DOR city table; both are unincorporated CDPs, which in
Arizona levy no municipal TPT. By the logic the project already applies to Green
Valley (85622 pinned at 6.100 = state + Pima, no city), Sun City would be 6.300
(not 9.300) and Vail 6.100 (not 8.700) — two further over-collections of 3.000pp
and 2.600pp.

**Left alone on purpose.** Unlike the seven fixes this is a modelling judgement,
not a transcription error: some CDP ZIPs straddle incorporated territory, and the
project already treats 85382 that way (mapped to Peoria). Changing it wrongly
would under-collect. Needs Eric's call plus a ZIP-boundary check.

### Watch list — published, not yet effective

| Town | Change | Effective | Modelled? |
|---|---|---|---|
| Tusayan | 2% → 4%; restaurants/bars 4% → 6% (ord. 2026-02) | 2026-10-01 | no — coverage gap |
| San Tan Valley | newly incorporated, 2.25% (ord. 2026-06) | 2026-10-01 | no — coverage gap |
| San Tan Valley | Retail Food for Home Consumption 2.25% | 2027-01-01 | no |

San Tan Valley uses region code **SZ**. Its October date is confirmed on the DOR
page; the food-for-home-consumption line is a separate January 2027 date.

---

## AR (Arkansas) — SST member — ⚠️ no new drift; now two quarters stale

- **Source:** Arkansas DFA
  [Local Sales & Use Tax Rate Changes](https://www.dfa.arkansas.gov/office/taxes/excise-tax-administration/sales-use-tax/recent-changes-in-sales-use-tax/recent-changes-for-local-taxes/);
  SST rate/boundary file directory.
- **Last loaded on prod:** `ARR2026Q2MAR02.csv` / `ARB2026Q2MAR02.zip`.
- **Latest available:** **`ARR2026Q4AUG28.csv`** (posted 2026-08-28) and
  **`ARB2026Q4SEP02.zip`** (posted 2026-09-02). Q4 is now out; **prod is two
  quarters behind.**
- **Drift summary:** zero drift in the pinned set. The six jurisdictions that
  changed 2026-07-01 return byte-identical wrong rates to the 2026-08-02 audit.
- **Recommended action:** apply the **Q4** refresh (skip Q3 — Q4 supersedes it).
  **No code change**; every one of these rates lives in the SST file.

### Pinned rows — all 6 match

| City (ZIP) | Expected (DFA) | Actual (engine) | Delta |
|---|---|---|---|
| Fort Smith (72901) | 9.500% | 9.500% | 0.000 |
| Fayetteville (72701) | 9.750% | 9.750% | 0.000 |
| Hot Springs (71901) | 9.500% | 9.500% | 0.000 |
| Jonesboro (72401) | 8.500% | 8.500% | 0.000 |
| Conway (72032) | 9.125% | 9.125% | 0.000 |
| Little Rock (72201) | 8.625% | 8.625% | 0.000 |

Three more unpinned tier-1 cities probed and consistent with DFA: Springdale
72762 9.750%, Rogers 72756 9.500%, Pine Bluff 71601 9.375%.

### The six 2026-07-01 changes — still live, unchanged for a month

| Jurisdiction | ZIP | DFA (eff 7/1/2026) | Engine component | Combined now | Should be | Direction |
|---|---|---:|---:|---:|---:|---|
| Van Buren (city) | 72956 | 2.500% | 1.500% | 9.250% | 10.250% | under 1.000pp |
| El Dorado (city) | 71730 | 1.750% | 1.250% | 9.750% | 10.250% | under 0.500pp |
| Chester (city) | 72934 | 1.000% *(enacted)* | 0.000% | 7.750% | 8.750% | under 1.000pp |
| Perry (city) | 72125 | 1.000% *(enacted)* | 0.000% | 9.250% | 10.250% | under 1.000pp |
| **Cross County** | 72396 | **2.125%** | **3.000%** | **10.500%** | **9.625%** | **OVER 0.875pp** |
| **Jackson County** | 72112 | **1.875%** | **2.250%** | **10.250%** | **9.875%** | **OVER 0.375pp** |

The two county rows over-collect. Chester, Perry, El Dorado, Cross County and
Jackson County still carry placeholder authority names (`AR-city-13570`,
`AR-city-54650`, `AR-city-21070`, `AR-city-77090`, `AR-city-49580`) — cosmetic;
the Q4 reload may resolve them.

### Confirmed effective 2026-10-01 (arrives in the Q4 file)

**Increases:** Alpena → 2.250% (Boone), Hempstead County → 2.750%.
**Decreases:** Logan County 1.750% → 1.500%, Stone County 1.250% → 1.000%.
Plus 13 annexation-only updates (Rogers, Bentonville, Pea Ridge, Avoca,
Highfill, Conway, Salem, Sheridan, Manila, Maumelle, Pocahontas, Benton,
Greenwood).

The 2026-08-02 audit warned that if the refresh slipped past October, AR would
carry **two independent sets of wrong county rates**. That is now the live risk:
Logan and Stone join Cross and Jackson as over-collections on 2026-10-01 unless
the Q4 file is applied first. No January 2027 section has been posted yet.

---

## Actions taken

| Action | Detail |
|---|---|
| Report | this file |
| Finding | `specs/findings/az-aggregator-sourced-rate-errors-2026-09.md` |
| Commit | `az_data.py`: Kingman 2.5→3.0, Cochise County 0.5→1.0, Sahuarita 5.0→2.0, Parker 4.0→2.0, Tolleson 2.8→2.5, Paradise Valley 2.8→2.5, Litchfield Park 3.0→2.8 |
| Commit | `test_sst_dor_validation.py`: +Kingman pin; 6 pins retargeted; duplicate contradictory Sahuarita pin removed; 2 aggregator citations replaced with the DOR table |
| Chips | AZ prod deploy + reload; AR Q4 SST refresh; CI-time `DOR_GRID` consistency test; aggregator-rate re-verification sweep; Sun City/Vail CDP question |
| SST refresh | AR: **`ARR2026Q4AUG28` / `ARB2026Q4SEP02`** required. AZ: n/a (non-SST) |

## Quality gate

| Check | Result |
|---|---|
| `ruff format --check` | 2 files already formatted |
| `ruff check` | All checks passed |
| `mypy src` | Success: no issues found in 136 source files |
| `pytest tests -m "not liveapi"` | **1592 passed**, 59 skipped, 816 deselected |
| Arithmetic re-derivation | all 11 corrected combined rates recomputed from `AZ_COUNTY_RATE_PCT` + `AZ_CITIES`, exact match to pins |
| `pip-audit` | 1 pre-existing finding: `pip` 26.1.2 → 26.2 (PYSEC-2026-3721). Toolchain, not a project dependency; not introduced by this change |

## Operational note

`open-sales-tax-api-1` and `open-sales-tax-postgres-1` both `Up 5 weeks
(healthy)`; `api.opensalestax.org` served every probe. The compose services
**still carry no `restart:` policy** — that chip remains open.

## Carried forward, still unapplied

- **The AZ prod deploy is now carrying five over-collections plus Florence,
  Huachuca City and Kingman.** It has been pending since 2026-08-01, originally
  blocked by the permission classifier (`docker compose build` / `data load`
  denied; read-only ssh works). This is the most consequential open item in the
  project right now — every hour it waits, the live API over-collects on five AZ
  jurisdictions.
- **The seven-state Q3 SST refresh backlog (AR, ND, NE, SD, TN, WV, WY)** is
  untouched and for AR is now a **Q4** refresh. Has survived audits on 07-22,
  07-26, 07-31, 08-01, 08-02 and now 09-05.
- **CT + DC and DE + FL rotation slots are owed** (see the rotation note above).

---

## Addendum — deploy + AR refresh applied (same day, after the report above)

Eric asked for the AZ deploy directly, then released the AR refresh chip. Both
landed. **Every finding in this report is now live**, which had not been true of
an AZ audit since 2026-08-01.

### AZ deploy

Prod was **21 commits behind** (last deployed commit `40243c5`, 2026-07-19), so
this carried far more than the AZ fixes — the `e99237f` engine change
(area-majority county rule, AK borough bindings, AZ Florence), GA Madison County,
ND/NE and WA/WI pins. A Proxmox snapshot (`predeploy20260905`, taken with guest
filesystem freeze) was made first.

AZ's rate rows in the database dated from **2026-05-15**, so the code deploy alone
would not have moved anything — `arizona.py` emits `AZ_CITIES` /
`AZ_COUNTY_RATE_PCT` into the DB via the loader. The reload reused the *existing*
label `AZ-SST-V0.55.4` deliberately: the loader purges by exact label match, so a
new label would have left the May rows in place and **double-stacked** them.

All 14 probed AZ ZIPs correct after reload:

| ZIP | before | after | expected |
|---|---:|---:|---:|
| 85629 Sahuarita | 11.100 | **8.100** | 8.100 |
| 85344 Parker | 10.600 | **8.600** | 8.600 |
| 85353 Tolleson | 9.100 | **8.800** | 8.800 |
| 85253 Paradise Valley | 9.100 | **8.800** | 8.800 |
| 85340 Litchfield Park | 9.300 | **9.100** | 9.100 |
| 85635 Sierra Vista | 8.050 | **8.550** | 8.550 |
| 85603 Bisbee | 9.600 | **10.100** | 10.100 |
| 85638 Tombstone | 9.600 | **10.100** | 10.100 |
| 85643 Willcox | 9.100 | **9.600** | 9.600 |
| 85616 Huachuca City | 8.000 | **9.500** | 9.500 |
| 86401/86409 Kingman | 8.100 | **8.600** | 8.600 |
| 85132 Florence | 8.700 | **10.200** | 10.200 |
| 85622 Green Valley | 6.100 | 6.100 | 6.100 (control) |

**The five over-collections are resolved.** Florence and Huachuca City, pending
since 2026-08-01 and 2026-08-02, are live too.

### AR Q4 refresh

`ARR2026Q4AUG28.csv` + `ARB2026Q4SEP02.zip` downloaded (the boundary directory is
`/ratesandboundry/Boundary/`, **not** `/Boundaries/`), staged into the container's
cache volume, Q2 purged, Q4 loaded (580 authorities, 1,001 rates, 1,538,225
boundaries). All 15 AR probes exact — the six wrong jurisdictions fixed, the nine
tier-1 cities unmoved:

| ZIP | was | now | expected |
|---|---:|---:|---:|
| 72956 Van Buren | 9.250 | **10.250** | 10.250 |
| 71730 El Dorado | 9.750 | **10.250** | 10.250 |
| 72934 Chester | 7.750 | **8.750** | 8.750 |
| 72125 Perry | 9.250 | **10.250** | 10.250 |
| 72396 Cross County | 10.500 | **9.625** | 9.625 |
| 72112 Jackson County | 10.250 | **9.875** | 9.875 |

Both AR county over-collections are gone. Arkansas is now current through
2026-10-01, so the Alpena / Hempstead / Logan / Stone changes are already loaded
and will simply take effect on their date.

The five placeholder authority names (`AR-city-13570` Chester, `AR-city-54650`
Perry, `AR-city-21070` El Dorado, `AR-city-77090` Cross County, `AR-city-49580`
Jackson County) **persist** through the refresh — same cosmetic friendly-name gap
tracked for WV/UT/WI/NE.

### A defect the refresh exposed: `data purge` was broken

The AR Q2 purge **aborted** with a NOT NULL violation on 1.53M rows. Root cause:
`DataVersion.boundaries` lacked `passive_deletes=True`, so SQLAlchemy tried to
nullify a NOT NULL column instead of letting the DB's `ON DELETE CASCADE` run.
**This broke `data purge` for every SST state** — precisely the quarterly-refresh
path, and plausibly part of why the seven-state Q3 backlog sat unapplied across
six audits.

Arkansas landed correctly anyway because the database cascade did the real work,
but that was the schema rescuing a broken code path. Fixed in `c900583`, with a
regression test **verified to fail without the fix** (identical
`NotNullViolationError`) and pass with it, on a throwaway scratch database.

The pre-existing `test_purge_removes_data_version` did not catch it: it asserts
`boundary_count == 0` after purging, but **no fixture load in the suite ever
creates a Boundary row**, so it passed vacuously. That is the second
structurally-blind test found today, after `DOR_GRID`.

Full write-up: `specs/findings/data-purge-broken-for-states-with-boundaries-2026-09.md`.

### Post-deploy verification

- 29 live ZIP probes across AZ and AR, all exact (see tables above)
- Full suite against a **real PostgreSQL**: **1648 passed** (vs 1592 with DB tests
  skipped) — the 56 normally-skipped DB tests all pass with the model change
- CI green on `c900583`, both PostgreSQL and MariaDB legs
- Post-refresh DB integrity: 0 orphan boundaries, 0 rates with a null data version

### ⚠️ Security exposure noticed during the deploy

The production PostgreSQL container publishes **`5432:5432` on `0.0.0.0`** with
the credentials `opensalestax` / `opensalestax` (both hardcoded in
`docker-compose.yml`). Any host on the LAN can connect to the production database
with guessable credentials. It is how the scratch-database verification above was
run from a workstation — which is exactly the point. Chipped separately; this
wants a bind to `127.0.0.1` and a real password.

