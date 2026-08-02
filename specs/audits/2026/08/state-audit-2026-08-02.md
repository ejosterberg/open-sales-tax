# Daily state sales tax audit — 2026-08-02 (day 2: AR + AZ)

## TL;DR

- 2 jurisdictions audited. **1 new rate change found and fixed**, 1 pre-existing
  backlog re-confirmed unchanged.
- **AZ — Huachuca City 1.9% → 2.9%, effective 2026-08-01 (yesterday).**
  Real drift, caught one day after it took effect. Ordinance 2026-06, confirmed
  against the AZ DOR Model City Tax Code rate table (`Retail Sales 017 1.90
  2.90`, region code HC). Combined 85616: 8.000% → **9.000%**. **Fixed in repo
  + pin added.** 42 of the other 43 AZ pins match exactly.
- **AR — no new drift, but the six 2026-07-01 changes found on 2026-07-31 are
  still live and unfixed.** All 6 AR pins match; the 6 known-wrong jurisdictions
  return exactly the same wrong rates as two days ago because **prod is still on
  `ARR2026Q2MAR02` / `ARB2026Q2MAR02`** — one quarter stale. AR is an SST state,
  so this is a **file refresh, not a code fix**; it is item 1 of the seven-state
  Q3 backlog that has now survived five audits without being applied.
- **New forward-looking finding: Arkansas has already published its 2026-10-01
  change set** (Alpena +, Hempstead County +, Logan County −, Stone County −,
  plus ~13 annexations). Not actionable today; it lands in the Q4 SST file, due
  from SST by 2026-09-01.
- **Three AZ changes are published but not yet effective:** Kingman 2026-09-01
  (modelled — will drift), Tusayan and San Tan Valley 2026-10-01 (not modelled —
  coverage, not drift).
- Prod healthy: both containers `Up 6 days (healthy)`; every probe served.

---

## AR (Arkansas) — SST member — ⚠️ no new drift; Q3 refresh still unapplied

- **Source:** Arkansas DFA "Local Sales & Use Tax Rate Changes"
  (`dfa.arkansas.gov/office/taxes/excise-tax-administration/sales-use-tax/
  recent-changes-in-sales-use-tax/recent-changes-for-local-taxes/`).
- **Last loaded on prod:** `ARR2026Q2MAR02.csv` / `ARB2026Q2MAR02.zip`.
- **Latest available:** `ARR2026Q3JUN02` (published 2026-06-02, effective
  2026-07-01). **No Q4 file yet** — SST requires quarterly files to be posted by
  the first day of the month preceding the quarter, so Q4 is not due until
  2026-09-01. Q3 remains the correct target.
- **Drift summary:** zero drift in the pinned set; the six jurisdictions that
  changed on 2026-07-01 are all still wrong, unchanged from the 2026-07-31 audit.
- **Recommended action:** apply the Q3 refresh. **No code change** — every one of
  these rates lives in the SST rate file.

### Pinned rows — all 6 match

| City (ZIP+4) | Expected (DFA) | Actual (engine) | Delta |
|---|---|---|---|
| Fort Smith (72901-2402) | 9.500% | 9.500% | 0.000 |
| Fayetteville (72701-5501) | 9.750% | 9.750% | 0.000 |
| Hot Springs (71901) | 9.500% | 9.500% | 0.000 |
| Jonesboro (72401) | 8.500% | 8.500% | 0.000 |
| Conway (72032) | 9.125% | 9.125% | 0.000 |
| Fayetteville (72701) | 9.750% | 9.750% | 0.000 |

Four more unpinned tier-1 cities were probed and are consistent with DFA:
Little Rock 72201 8.625%, Springdale 72762 9.750%, Rogers 72756 9.500%,
Pine Bluff 71601 9.375%.

### The six 2026-07-01 changes — all still live on prod

| Jurisdiction | ZIP probed | DFA (eff 7/1/2026) | Engine city/county component | Combined now | Combined should be | Direction |
|---|---|---:|---:|---:|---:|---|
| Van Buren (city) | 72956 | 2.500% | 1.500% | 9.250% | 10.250% | under 1.000pp |
| El Dorado (city) | 71730 | 1.750% | 1.250% | 9.750% | 10.250% | under 0.500pp |
| Chester (city) | 72934 | 1.000% *(enacted)* | 0.000% | 7.750% | 8.750% | under 1.000pp |
| Perry (city) | 72125 | 1.000% *(enacted)* | 0.000% | 9.250% | 10.250% | under 1.000pp |
| **Cross County** | 72396 | **2.125%** | **3.000%** | **10.500%** | **9.625%** | **OVER 0.875pp** |
| **Jackson County** | 72112 | **1.875%** | **2.250%** | **10.250%** | **9.875%** | **OVER 0.375pp** |

The two county rows are the ones that matter most — they **over-collect**, which
is the failure direction that creates liability for an integrator rather than
just a shortfall.

One bookkeeping nuance: DFA lists Jackson County's old rate as 2.000% while the
engine holds 2.250%, so the engine appears to be a further step behind than a
single quarter on that row. The target is 1.875% either way; the Q3 file
supersedes both values.

Chester, Perry, El Dorado and Cross County also still carry unlabelled
placeholder authority names (`AR-city-13570`, `AR-city-54650`, `AR-city-21070`,
`AR-city-77090`) — the same friendly-name gap tracked for WV/UT/WI/NE. Cosmetic;
the Q3 reload may or may not resolve them.

### Already published, effective 2026-10-01 (not actionable today)

Arkansas has posted its October change set. **Increases:** Alpena → 2.250%
(Boone), Hempstead County → 2.750%. **Decreases:** Logan County 1.750% →
1.500%, Stone County 1.250% → 1.000%. Plus ~13 annexation-only updates
(Rogers, Bentonville, Pea Ridge, Avoca, Highfill, Conway, Salem, Sheridan,
Manila, Maumelle, Pocahontas, Benton, Greenwood).

These arrive in the Q4 SST file. **If the Q3 refresh is still unapplied by
October, Arkansas will be two quarters behind and carrying two independent sets
of wrong county rates** — including two more over-collections (Logan, Stone).

---

## AZ (Arizona) — non-SST — 🔴 one real change, effective yesterday, FIXED

- **Source:** AZ DOR Model City Tax Code "Rate and Code Updates"
  (`azdor.gov/business/transaction-privilege-tax/model-city-tax-code/
  rate-and-code-updates`).
- **Last loaded on prod:** self-seeded module (`az_data.py`); Arizona is not an
  SST state and has no quarterly file.
- **Drift summary:** **1 real change** (Huachuca City, effective 2026-08-01).
  42 of 43 pinned rows match; the 43rd is the known Florence fix awaiting a prod
  reload, not new drift.
- **Recommended action:** committed the one-line rate fix + a DOR-grid pin. The
  live engine keeps returning 8.000% for 85616 until prod is redeployed.

### 🔴 Huachuca City — 1.9% → 2.9%, effective 2026-08-01

On **2026-05-28** the Mayor and Council of the Town of Huachuca City passed
**Ordinance No. 2026-06**, raising multiple privilege-tax business
classifications and use tax from 1.9% to 2.9%, and Rental/Leasing/Licensing for
Use of Real Property from 1.0% to 2.9%, effective **2026-08-01**.

The AZ DOR rate table for region code **HC** lists the retail line the engine
models as:

> `Retail Sales 017 1.90 2.90`

| ZIP | Component | Before | After |
|---|---|---:|---:|
| 85616 | Arizona (state) | 5.600% | 5.600% |
| 85616 | Cochise County | 0.500% | 0.500% |
| 85616 | **Huachuca City** | **1.900%** | **2.900%** |
| 85616 | **Combined** | **8.000%** | **9.000%** |

Live engine at the time of audit returned **8.000%** (city 1.900) — under-collecting
by 1.00pp since yesterday.

**Fixed:** `az_data.py` Huachuca City `1.900` → `2.900` with the ordinance cited
in a comment, plus a new `DOR_GRID` pin (`85616-0001` → 9.000) following the
Florence precedent from `e99237f`. The pin **fails under `-m liveapi` until prod
reloads AZ**, same as Florence and the seven AK rows.

### Pinned rows — 42 of 43 match

Phoenix 85042/85003 9.100 · Chandler 85225/85224 7.800 · Gilbert 85234/85296
8.300 · Peoria 85345 8.100 · Scottsdale 85251 8.000 · Tucson 85701 8.700 · Mesa
85201 8.300 · Glendale 85301/85308 9.200 · Tempe 85281 8.100 · Flagstaff 86001
9.386 · Yuma 85364 8.412 · Lake Havasu City 86403 7.600 · Surprise 85388 9.100 ·
Goodyear 85338 8.800 · Sierra Vista 85635 8.050 · Nogales 85621 8.600 · Page
86040 9.900 · Show Low 85901 8.430 · Apache Junction 85119 9.100 · Queen Creek
85140 8.550 · Maricopa 85138 9.200 · Globe 85501 9.900 · Payson 85541 10.480 ·
Sedona 86336 9.850 · San Luis 85349 10.712 · Sun City/Peoria 85382 8.100 · Green
Valley 85622 6.100 · Vernon 85936 6.100 · Sun City 85351 9.300 · Vail 85641
8.700 · Bisbee 85603 9.600 · Cave Creek 85327 9.300 · Fountain Hills 85268 9.200
· Paradise Valley 85253 9.100 · Eagar 85925 9.100 · Tolleson 85353 9.100 ·
Parker 85344 10.600 · Quartzsite 85346 9.100 — every one delta 0.000.

**The one miss is expected:** Florence 85132 pins 10.200, engine returns 8.700
(city still 2.000). That is the 2026-08-01 fix sitting in the repo un-deployed,
not new drift.

### Published but not yet effective — watch list

| Town | Change | Effective | Modelled? | Consequence |
|---|---|---|---|---|
| **Kingman** | 2.50% → 3.00% (ord. 2003, passed 2026-06-16) | **2026-09-01** | **yes** (86401, 86409 @ 2.500) | **will drift on 9/1** — next AZ rotation day is 2026-09-02, so the daily audit catches it one day late unless done sooner |
| Tusayan | 2% → 4%; restaurants/bars 4% → 6% (ord. 2026-02, passed 2026-07-14) | 2026-10-01 | no | coverage gap, not drift |
| San Tan Valley | ord. 2026-06 | 2026-10-01 | no | coverage gap, not drift |

**Not drift, re-confirmed:** Oro Valley's ordinance 26-10 (eff 2026-07-01) sets a
**use tax** rate of 2.50% and adopts a charitable-donation exemption — it does
not change the retail privilege-tax rate the engine models. Same conclusion as
the 2026-07-31 audit.

---

## Actions taken

| Action | Detail |
|---|---|
| Report | this file |
| Commit | `az_data.py` Huachuca City 1.900 → 2.900 + `DOR_GRID` pin 85616 → 9.000 |
| Chips | AR Q3 refresh already chipped (fleet-wide 7-state chip) — re-flagged, not re-chipped; AZ prod deploy folded into the existing pending-deploy item |
| SST refresh | AR: `ARR2026Q3JUN02` / `ARB2026Q3JUN04` still required. AZ: n/a (non-SST) |

## Operational note

`open-sales-tax-api-1` and `open-sales-tax-postgres-1` both `Up 6 days
(healthy)`; `api.opensalestax.org` served every probe in this run. The
2026-07-26 outage has not recurred, but the compose services **still carry no
`restart:` policy** — that chip remains open and unapplied.

## Carried forward, still unapplied

- **The AZ prod deploy + reload from 2026-08-01 is still pending** (Florence,
  the AK borough bindings, and the area-majority county rule). Today's Huachuca
  City fix joins the same queue — it will not reach the live engine until that
  deploy runs. Blocked in the 2026-08-01 session by the permission classifier
  (`docker compose build` / `data load` denied; read-only ssh works).
- **The seven-state Q3 SST refresh backlog (AR, ND, NE, SD, TN, WV, WY)** is
  untouched. AR is one of the seven, and today's audit re-measured six live wrong
  rates that the refresh would fix — two of them over-collections. This backlog
  has now survived audits on 07-22, 07-26, 07-31, 08-01 and 08-02.
