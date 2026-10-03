# Daily state sales tax audit — 2026-10-01 (day 1: AK + AL)

Run started 2026-10-01 and finished early 2026-10-02 (local); the rotation
day is 1.

## TL;DR

- 2 jurisdictions audited, each with a **full diff of the primary source**
  (every ARSSTC ZIP row; every ALDOR county row plus every modelled city)
  rather than a pin spot-check.
- **1 real rate change, now fixed in the repo: Autauga County, AL, 2.0% → 2.5%
  effective 2026-09-01** (Act 2026-362). Every Autauga ZIP has been
  **under-collecting by 0.5pp for a month**, including modelled Prattville
  (36066/36067: 9.5% → **10.0%**). `al_data.py` and the Prattville pin are
  updated. **The live engine stays wrong until prod reloads AL.**
- **AK: no rate changes.** The 7-1, 8-1 and 9-1-2026 ARSSTC ZIP sheets are
  identical, and there is no 10-1 sheet yet. All 7 AK ZIPs that disagree with
  ARSSTC are **exactly** the ones fixed in the repo on 2026-08-01 (`e99237f`).
- **🔴 The 2026-08-01 fixes are deployed in prod's code but AK and AL were
  never reloaded — two months later.** Prod is on `091d9ba` (2026-09-09),
  which includes `e99237f`, but the data rows were never rebuilt:
  - **99928 Ward Cove still over-collects 3.00pp** (5.5% vs 2.5%), and six AK
    ZIPs still return 0.000% (99824, 99836, 99850, 99903, 99918, 99950).
  - **Calera AL 35040 still binds Chilton County 3.0% and over-collects
    2.00pp.** The area-majority helper in the repo picks Shelby (`117`).
  - AZ *was* reloaded (Florence 85132 returns the fixed 10.200%), so this is a
    missed step for some states, not a broken deploy.
  - Chipped: "Reload AK + AL on prod". Prod is also 18 commits behind `main`.
- Prod healthy: both containers `Up 3 weeks (healthy)`.

---

## AK (Alaska) — non-SST, no state tax — ✅ no rate changes; ⏳ 7 ZIPs await prod reload

- **Source:** ARSSTC "Sales Tax Rate Sheet with Zip Codes" for **7-1, 8-1 and
  9-1-2026** (`arsstc.org/wp-content/uploads/2026/0{7,8}/ARRSTC-…`), parsed
  with openpyxl and diffed row by row.
- **Last loaded on prod:** self-seeded `ak_data.py`, label
  `AK-SST-V0.54-ARSSTC`. **Not reloaded since the 2026-08-01 fix.**
- **Latest available:** 9-1-2026 (no 10-1-2026 sheet as of this run).
- **Drift summary:** 7-1 → 8-1 → 9-1 sheets are identical for all 84 ZIPs, so
  no Alaska jurisdiction changed a rate. 77 of 84 ZIPs fall inside ARSSTC's
  inside/outside-city bracket. The 7 that do not are the 2026-08-01 set.
- **Recommended action:** reload AK on prod (`data load -s AK -v
  AK-SST-V0.54-ARSSTC`, the existing label). No code change needed.

| ZIP | ARSSTC (min–max) | Live engine | Repo after `e99237f` |
|---|---|---|---|
| 99928 Ward Cove | 2.500 | **5.500** (over 3.00pp) | 2.500 |
| 99903 / 99918 / 99950 | 2.500–8.000 | 0.000 | 8.000 |
| 99824 Douglas | 5.000 | 0.000 | 5.000 |
| 99836 | 6.000 | 0.000 | 6.000 |
| 99850 Excursion Inlet | 4.500 | 0.000 | 4.500 |

**Pins:** 26 AK `DOR_GRID` rows; 18 match live. The 7 above fail under
`-m liveapi` by design until the reload. The 8th is **Kenai 99611 pinned at
3.000** (live 6.000): the already-known contradictory pair, which the handoff
calls a modelling decision rather than a stale value. Not touched.

**Seasonal note (documented limitation, not drift):** 2026-10-01 is the start
of the off-season band for several boroughs. ARSSTC's 8-1 summary lists Haines
townsite 7.0% (Apr–Sep) / 4.5% (Oct–Mar) and Haines rural 5.0% / 3.0%. The
engine's single Haines value of 5.5% matches neither rate and is above both
winter rates. `ak_data.py` documents that seasonal rates are not modelled. The
5.5% is still inside the year-round ZIP bracket (4.5–7.0), so it is not
flagged. Worth revisiting if seasonal modelling is ever taken up.

**Audit-tooling gotcha (recorded in data-sources.md):** ARSSTC rows with no
city name, such as Haines townsite and Haines rural on 99827, collide if the
script keys rows by (ZIP, city, in/out). The collision shrank 99827's bracket
to 4.5–5.0 and produced a phantom over-collection. Key by borough as well.

---

## AL (Alabama) — non-SST — 🔧 1 county rate change fixed in repo

- **Sources:**
  1. ALDOR machine-readable rate file
     `revenue.alabama.gov/wp-content/uploads/2024/03/taxrates.csv`
     (`Last-Modified: 2026-09-01`, 54,035 rows). Diffed **all 67 counties**
     with `scripts/extract_al_county_rates.py`, plus every `AL_CITIES` entry
     against its `ST`/`GENER` current row.
  2. ALDOR Local Tax Notices, read through the RSS feed (pages 1–5, back to
     March 2026). The web page shows only the newest 15. 48 notices were
     reviewed, and their PDFs parsed with pypdf.
- **Last loaded on prod:** self-seeded `al_data.py`, label
  `AL-SST-V0.31-STATEWIDE-COUNTY`. **Not reloaded since 2026-08-01.**
- **Drift summary:** 1 real change (Autauga County). Fixed in the repo; prod
  reload pending.

### The change

| Jurisdiction | Old | New | Effective | Source | Engine (live) | Repo now |
|---|---|---|---|---|---|---|
| **Autauga County** | 2.000 | **2.500** | **2026-09-01** | Act 2026-362; ALDOR notice `Autauga-County_20260824.pdf`; CSV locality 7001 `RC` row active 20260901 (the prior row closes 20260831) | 2.000 → Prattville 36066 **9.500** | 2.500 → Prattville **10.000** |

There is only one Autauga County row, with no `CL` variant, so the increase
applies inside Prattville as well as outside it. The grocery rate stays at
2.0%. The act also adds a new 3% county rental tax; rental tax is not
modelled.

### County diff, all 67

The extractor and `AL_COUNTY_RATE_PCT` disagree on 5 counties:

- **Autauga**: the real change above.
- **Lauderdale, Lee, Mobile, Morgan**: a convention difference, not drift.
  The extractor picks the county *base* rate, which applies to
  unincorporated areas. The module deliberately uses the inside-city `CL`
  rate for anchor cities, and the CSV confirms it:
  - Lauderdale: CL Florence 1.0
  - Lee: `LEE CO CL AUB & OPE & PHENIX` 1.0
  - Mobile: CL Prichard & Mobile 1.0
  - Morgan: Decatur has no CL row in the CSV, so its 1.0 can't be confirmed
    from this file. It is still Avalara-sourced; see the follow-ups.

  The other 62 counties match exactly.

### City diff, all 30 modelled cities

27 match their ALDOR `ST`/`GENER` row exactly. The other three are listed in
the CSV under different names, and all three reconcile on the combined rate:

- **Tuscaloosa**: `TUSCALOOSA CITY` 3.0 ✓
- **Phenix City**: `PHENIX CITY WITHIN LEE/RUSSELL CO` 4.75 ✓
- **Madison**: `MADISON CITY` 3.5. Madison County is 0.5 county-wide plus
  1.0 outside Huntsville, so the total is 4 + 3.5 + 1.5 = 9.0. The module
  splits it as 4 + 4.5 (city) + 0.5 (county). The combined 9.0 is correct;
  only the breakdown differs.

### Notices since the 2026-08-01 audit

Only general-rate changes affect the engine.

| Place | Effective | Change | Modelled? | Action |
|---|---|---|---|---|
| **Autauga County** | 2026-09-01 | general 2.0 → 2.5 | **yes** | **fixed** |
| Dadeville | 2026-10-01 | general 3.5 → 4.0 | no | coverage gap |
| Pike Road | 2026-10-01 | general 2.25 → 3.50 | no | coverage gap |
| Semmes | 2026-10-01 | general 4.0 → 4.5 (and rental 2.5 → 4.5) | no | coverage gap |
| Tuscumbia | 2026-06-01 | general 3.5 → 4.0 | no (pin covers state + county only) | coverage gap |
| Irondale | 2026-10-01 | autos only 2.0 → 2.25; general unchanged at 4% | — | none |
| Moody | 2026-10-01 | admissions/machine/auto rates only; general unchanged at 4%; lodgings 6 → 10 | — | none |
| Birmingham | 2026-10-01 | consumer-use-tax discount removed | yes | none (not a rate) |
| Huntsville, Madison, Gadsden, Montevallo, Blount County | 2026-10-01 | lodgings only | — | none |
| Walker County, Grimes, Newton, Brantley, Brewton, Harpersville, Etowah County | 2026-08/09/10 | administration (collector) change only | — | none |

Mountain Brook (3 → 4, 2026-04-01) is already modelled at 4.0, which is
correct.

### Pins

25 AL `DOR_GRID` rows. 24 match live. **Prattville 36066** is now pinned at
10.000 and fails until the AL reload.

---

## Actions taken

1. **Commit** `data(AL): daily-audit 2026-10-01 Autauga County 2.0->2.5
   (eff 2026-09-01)`. Changes `al_data.py` (rate, comment, docstring) and the
   Prattville pin.
2. **Chip: "Reload AK + AL on prod"**, with the exact commands. It also asks
   for a check of which of the other 10 states affected by the 08-01
   county-tiebreak fix were reloaded.
3. `specs/research/data-sources.md`: recorded the ALDOR CSV, the RSS-feed
   route to old notices and the ARSSTC key gotcha, so the next AL/AK run
   doesn't have to rediscover them.

## Open follow-ups (carried forward)

- **AL coverage gap is growing.** Dadeville, Pike Road and Semmes joined
  Rogersville, Bay Minette, Calera, Priceville, Hackleburg and Tuscumbia as
  2026 general-rate changes in unmodelled cities. The ALDOR CSV now makes
  wholesale city seeding practical. Its `ST`/`GENER` current rows cover every
  state-administered city, which is most of the long tail.
- **AL Avalara-sourced anchor-county values** (handoff: AL carries 17
  aggregator-cited grid rows). This run confirmed Lauderdale, Lee and Mobile
  against ALDOR `CL` rows. **Morgan County inside Decatur (1.0)** remains
  unconfirmed from a primary source.
- **AL `coverage_warning` still claims city overlays are not modelled**, while
  30 cities are. Carried forward from 2026-07-31.
- **AK Kenai contradictory pin**: decision still pending (see
  `specs/findings/dor-grid-contradictory-duplicate-pins-2026-09.md`).
