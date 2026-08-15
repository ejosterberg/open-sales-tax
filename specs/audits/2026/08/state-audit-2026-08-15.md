# Daily state sales tax audit — 2026-08-15 (day 15: ND + NE)

> **Run note.** This run began under a host clock reading 2026-08-07 (day 7 =
> IA + ID) and the clock advanced to 2026-08-15 (day 15 = ND + NE) partway
> through. The **day-15 pair (ND + NE) is the primary audit** below; the
> already-completed and fully-verified IA + ID results are kept as an
> addendum rather than discarded. IA/ID were last audited 2026-07-07, so
> they remain inside the monthly-coverage requirement either way.

## TL;DR

- **4 jurisdictions audited** (ND, NE primary; IA, ID addendum).
- **3 confirmed rate drifts, all under-collections, all in today's pair**:
  ND Scranton (−1.00pp), ND Drayton (−2.00pp), NE Edgar (−0.50pp). All three
  are SST-sourced — **no code fix is possible**; the fix is the Q3 refresh
  that has been chipped since 2026-07-31 and never applied.
- **Every tier-1 pin in all four states matches the live engine exactly**
  (4 ND, 14 NE, 10 IA, 16 ID = 44 rows).
- **🔔 New forward-dated change: ND Minot 2.0% → 2.5% effective 2026-10-01**
  (ordinance confirmed from the ND permit-holder notice). Minot is a tier-1
  pin; the rotation would catch it 14 days late. Chipped.
- **New find in the addendum: IA boundary file is 2 quarters stale**
  (`IAB2026Q1DEC09` on prod vs `IAB2026Q3MAY19` published). The 2026-07-07
  audit recorded IA boundaries as current — that was wrong.
- **Resolved: the IA West Des Moines LOST dedup fix is now live on prod.**
  50265 and 50266 both return 7.000% with a single LOST. Closes the
  "prod redeploy PENDING" item outstanding since 2026-07-07.
- 5 commits' worth of mechanical fixes applied: 4 friendly-name additions
  (3 ND + 1 NE, all FIPS-verified from primary sources) and 3 new DOR_GRID
  regression pins encoding the correct post-refresh rates.

---

## ND — North Dakota (SST member)

- **Source (rates):** ND Office of State Tax Commissioner, *Local Taxes by
  Location Guideline — Rates Effective July 1, 2026*
  (`tax.nd.gov/sites/www/files/documents/guidelines/business/sales-use/local-taxes-by-location.pdf`)
- **Source (codes):** *North Dakota FIPS Codes, January 1, 2026*
  (`.../local-jurisdiction-rates/2026-jurisdiction/fips-codes-1-1-2026.pdf`)
- **Source (changes):** `tax.nd.gov/city-and-county-local-tax-rate-changes`
  and the per-city permit-holder notices linked from it
- **Last loaded on prod:** `NDR2026Q2FEB11` / `NDB2026Q2FEB19`
  (DataVersion `ND-SST-2026Q2FEB11`, fetched 2026-05-15)
- **Latest available:** `NDR2026Q3MAY19` / `NDB2026Q3MAY19`
- **Drift summary:** **2 real under-collections** (Scranton, Drayton), both
  effective 2026-07-01, both flowing from the unapplied Q3 refresh. All 4
  tier-1 pins correct.
- **Recommended action:** apply the Q3 SST refresh (already chipped
  2026-07-31, still unapplied 45 days on). Separately watch Minot for
  2026-10-01.

### Tier-1 pins — all match

| City | ZIP+4 | Expected (ND guideline) | Actual (engine) | Delta |
|---|---|---|---|---|
| Fargo | 58102-3703 | 7.750 (5 + Cass 0.5 + Fargo 2.25) | 7.750 | ✅ 0 |
| Fargo | 58102-0001 | 7.750 | 7.750 | ✅ 0 |
| Minot | 58701-0001 | 7.500 (5 + Ward 0.5 + Minot 2.0) | 7.500 | ✅ 0 |
| Grand Forks | 58201-0001 | 7.250 (5 + GF 2.25) | 7.250 | ✅ 0 |

Fargo 2.25%, Minot 2.0%, Grand Forks 2.25%, Cass County 0.5% and Ward County
0.5% were each read off the guideline's total-rate column and independently
confirmed against the FIPS-codes table.

### Drift — 2026-07-01 changes still unapplied

| Jurisdiction | ZIP | Engine | Correct (ND guideline) | Delta |
|---|---|---|---|---|
| **Scranton** (Bowman Co) | 58653 | **6.000** | **7.000** | **−1.00pp under** |
| **Drayton** (Pembina Co) | 58225 | **6.500** | **8.500** | **−2.00pp under** |
| Oakes (Dickey Co) | 58474 | 7.000 | 7.000 | ✅ 0 (cap-only change) |

- **Scranton** — guideline total local **2%** effective 2026-07-01. The old
  1% (in force since 4-1-02) sat on a *sales-and-gross-receipts-only* base;
  the new 2% is on the full *sales, use, and gross receipts* base and
  replaces it. Engine still carries the 1%.
- **Drayton** — guideline total local **3.5%** effective 2026-07-01
  (1% 10-1-97 + 0.5% 10-1-10 + 2% 7-1-26, all on the same base, so
  cumulative). Engine carries 1.5%. **This corrects the 2026-07-31 audit**,
  which recorded Drayton as a maximum-tax/refund-cap change only; the cap did
  move ($25 → $50/sale) but the *rate* moved too, and by 2.00pp.
- **Oakes** — genuinely cap-only (max tax removed 7-1-26). Rate unchanged at
  2%. The 2026-07-31 characterization holds here.

Neither Bowman nor Pembina County appears in the guideline's county table, so
both are 0% and combined = 5% state + city. The engine agrees on the county
component.

### 🔔 Forward-dated — NOT applied (not yet effective)

**City of Minot: 2.0% → 2.5%, effective 2026-10-01.** Verbatim from the ND
permit-holder notice: the city "has adopted an ordinance to increase its city
sales, use, and gross receipts tax by 0.5%," giving a combined in-city rate of
**8% (5% state + 2.5% city + 0.5% county)**. Combined 58701 therefore goes
**7.500% → 8.000%**.

Deliberately **not** applied, per the AZ-Kingman precedent (2026-08-02): a
published-but-future rate is not drift. But it needs attention because **the
rotation catches it late** — day 15 falls on 2026-09-15 (before) and
2026-10-15 (14 days after it takes effect). ND is SST, so the mechanism is the
**Q4 file**, due from SST by ~2026-09-01. Chipped.

Two other 2026-10-01 ND items are **not** rate drift: **Kindred** and
**Walhalla** are maximum-tax (refund-cap) removals, and the engine has no
concept of ND's local tax cap at all — the documented capability gap first
raised in the 2026-07-31 audit. **Fargo** and **Ellendale** have
boundary/annexation changes effective 2026-10-01 (Fargo per Resolution
1756025, Ellendale per Article 5.0309); these change which addresses are
in-city, not the rate, and will ride in on the Q4 boundary file.

---

## NE — Nebraska (SST member)

- **Source:** NE DOR, *Local Sales and Use Tax Rates, Effective July 1, 2026*
  (`revenue.nebraska.gov/sites/default/files/doc/tax-forms/2026/salestax/slstax_rates_07-01-2026.pdf`)
- **Last loaded on prod:** `NER2026Q2FEB25` / `NEB2026Q2APR20`
  (DataVersion `NE-SST-2026Q2FEB25`, fetched 2026-05-05)
- **Latest available:** `NER2026Q3MAY26` / `NEB2026Q3JUN08`
- **Drift summary:** **1 real under-collection** (Edgar, −0.50pp). All 14
  tier-1 pins correct.
- **Recommended action:** apply the Q3 SST refresh (chipped 2026-07-31, still
  unapplied). **No changes are scheduled for the quarter beginning
  2026-10-01**, so after the Q3 refresh Nebraska is clean through year-end.

### Tier-1 pins — all 14 match

Every city below was read off the NE DOR July-1-2026 listing (which publishes
the local rate, the combined rate, and the FIPS code per city) and matches the
live engine exactly.

| City | ZIP+4 | Expected (NE DOR) | Actual (engine) | Delta |
|---|---|---|---|---|
| Omaha | 68102-1718 / -0001 | 7.000 (5.5 + 1.5) | 7.000 | ✅ 0 |
| Lincoln | 68508-2802 / -0001 | 7.250 (5.5 + 1.75) | 7.250 | ✅ 0 |
| Norfolk | 68701-1234 | 7.500 (5.5 + 2.0) | 7.500 | ✅ 0 |
| Kearney | 68845-1234 | 7.000 (5.5 + 1.5) | 7.000 | ✅ 0 |
| North Platte | 69101-1234 | 7.500 (5.5 + 2.0) | 7.500 | ✅ 0 |
| Grand Island | 68803-1234 | 7.500 (5.5 + 2.0) | 7.500 | ✅ 0 |
| Fremont | 68025-1234 | 7.000 (5.5 + 1.5) | 7.000 | ✅ 0 |
| Beatrice | 68310-1234 | 7.500 (5.5 + 2.0) | 7.500 | ✅ 0 |
| Columbus | 68601-1234 | 7.000 (5.5 + 1.5) | 7.000 | ✅ 0 |
| McCook | 69001-1234 | 7.500 (5.5 + 2.0) | 7.500 | ✅ 0 |
| La Vista | 68128-1234 | 7.500 (5.5 + 2.0) | 7.500 | ✅ 0 |
| Gretna | 68138-5000 | 7.500 (5.5 + 2.0) | 7.500 | ✅ 0 |

### Drift — 2026-07-01 change still unapplied

| Jurisdiction | ZIP | Engine | Correct (NE DOR) | Delta |
|---|---|---|---|---|
| **Edgar** (Clay Co) | 68935 | **6.500** | **7.000** | **−0.50pp under** |

NE DOR's July-1-2026 listing gives `Edgar 1.5% 7.0% (.07) 102-161 14450`. The
engine still carries 1.0%. Confirms the 2026-07-31 finding; 45 days unapplied.

---

## Actions taken

### Committed (mechanical, primary-source-verified)

1. **`nd_names.py` — 3 friendly names added.** `ND-city-20340` → **Drayton**,
   `ND-city-58740` → **Oakes**, `ND-city-71500` → **Scranton**. All three
   were rendering as raw placeholders in live engine output. Codes verified
   against ND's own FIPS-codes table, which publishes the FIPS Place code
   next to the ND local code (Drayton 20340/157, Oakes 58740/146, Scranton
   71500/190). Rate-neutral.
2. **`ne_names.py` — 1 friendly name added.** `NE-city-14450` → **Edgar**.
   FIPS code 14450 comes straight out of the NE DOR listing's FIPS column.
   Closes the placeholder half of the 2026-07-31 Edgar item. Rate-neutral.
3. **`test_sst_dor_validation.py` — 3 DOR_GRID pins added** encoding the
   correct post-refresh rates: ND Scranton 58653-0001 → 7.000, ND Drayton
   58225-0001 → 8.500, NE Edgar 68935-0001 → 7.000. Each carries a
   "fails under `-m liveapi` until the Q3 refresh" note, matching the
   GA-Madison / NC-Charlotte / AZ-Huachuca precedent. `liveapi` is excluded
   from CI (`ci.yml` runs `-m "not liveapi"`), so these do not break the
   pipeline; they become the regression guard that flips to passing the
   moment prod loads Q3.

**Deliberately not changed:** the Minot pin stays at 7.500. The 2.5% rate is
not effective until 2026-10-01, and pinning a future rate would make the grid
wrong for the next 47 days.

### Chipped (human review / prod action)

- **Refresh ND + NE SST quarterlies to Q3** — carries the file names and load
  sequence.
- **ND Minot 2.0% → 2.5% effective 2026-10-01** — apply via the Q4 SST file
  when SST publishes it (~2026-09-01), ahead of the 2026-10-15 rotation day.
- **Refresh IA SST boundary file** to `IAB2026Q3MAY19` (see addendum).

---

## Addendum — IA + ID (day-7 pair, completed before the clock advanced)

Both were last audited 2026-07-07. Results below are fully verified and
current as of this run.

### IA — Iowa (SST member)

- **Source:** SST Governing Board state-file directories
  (`streamlinedsalestax.org/ratesandboundry/{Rates,Boundary}/`)
- **Last loaded on prod:** rate `IAR2025Q3MAY30` (DataVersion
  `IA-SST-2025Q3MAY30`, fetched 2026-05-10) / boundary `IAB2026Q1DEC09`
- **Latest available:** rate `IAR2025Q3MAY30` (**current** — SST hosts one
  rate file per state and has not republished Iowa's) / boundary
  **`IAB2026Q3MAY19`**
- **Drift summary:** **no rate drift** — all 10 tier-1 pins match at 7.000%.
  But the **boundary file is 2 quarters behind**.
- **Recommended action:** refresh the IA boundary file. Chipped.

**⚠️ Corrects the 2026-07-07 audit**, which recorded "Rate file
`IAR2025Q3MAY30` + boundary `IAB2026Q1DEC09` on prod are current (match latest
SST posting); no IA data refresh needed." The rate half was right; the boundary
half was not. `IAB2026Q3MAY19` was posted 2026-05-19, so it was already
available on 2026-07-07 and was missed. Iowa's LOST is a flat 1% statewide
cap, so a stale boundary file cannot produce a wrong *rate* for a ZIP that is
already bound — the exposure is ZIPs whose city/county bindings changed
(annexations, new LOST adoptions), which would silently keep the old binding.

| City | ZIP | Expected | Actual | Delta |
|---|---|---|---|---|
| Des Moines | 50309 | 7.000 | 7.000 | ✅ 0 |
| Cedar Rapids | 52401 | 7.000 | 7.000 | ✅ 0 |
| Davenport | 52801 | 7.000 | 7.000 | ✅ 0 |
| Sioux City | 51101 | 7.000 | 7.000 | ✅ 0 |
| Waterloo | 50703 | 7.000 | 7.000 | ✅ 0 |
| Council Bluffs | 51501 | 7.000 | 7.000 | ✅ 0 |
| Dubuque | 52001 | 7.000 | 7.000 | ✅ 0 |
| Iowa City | 52240 | 7.000 | 7.000 | ✅ 0 |
| **West Des Moines** | **50265** | **7.000** | **7.000** | ✅ **0 (was 9.000)** |
| **West Des Moines** | **50266** | **7.000** | **7.000** | ✅ **0 (was 10.000)** |

**✅ RESOLVED — the West Des Moines LOST dedup fix is live on prod.** Both
ZIPs now return a single 1% LOST:

- `50265` → Iowa 6% + Polk County 0% + **Polk County Local Option Sales Tax 1%** = 7.000%
- `50266` → Iowa 6% + Dallas County 0% + **IA-district-98049 1%** = 7.000%

This closes the "FIXED IN REPO, prod redeploy PENDING" item that had been open
since 2026-07-07 (`specs/findings/ia-west-des-moines-lost-dedup-2026-07.md`).
The two `-m liveapi` pins that were failing by design now pass. The
over-collection of 2–3pp on West Des Moines transactions is over.

**Cosmetic follow-up still open:** `IA-district-98049` (Dallas County LOST)
remains an unlabelled placeholder in `ia_names.py`, exactly as the finding
predicted. Rate is correct; only the display name is missing.

### ID — Idaho (non-SST)

- **Source:** Idaho State Tax Commission, *City Sales Taxes*
  (`tax.idaho.gov/taxes/sales-use/sales-tax/local-sales-tax/city-sales-tax/`)
- **Last loaded on prod:** DataVersion `ID-SST-V0.7-RESORT-CITIES`, fetched
  2026-05-10 (self-seeded — Idaho is not an SST member)
- **Drift summary:** **fully clean.** All 16 pins match exactly.
- **Recommended action:** none.

| Tier | Cities | Expected | Actual |
|---|---|---|---|
| Statewide only | Boise 83702, Twin Falls 83301, Idaho Falls 83401, Coeur d'Alene 83814 | 6.000 | ✅ 6.000 |
| Resort 3% | Sun Valley 83353, Ketchum 83340, McCall 83638, Stanley 83278, Donnelly 83615, Cascade 83611 | 9.000 | ✅ 9.000 |
| Resort 1% | Sandpoint 83864, Driggs 83422, Riggins 83549, Lava Hot Springs 83246, Crouch 83622 | 7.000 | ✅ 7.000 |
| Resort 0.5% | Salmon 83467 | 6.500 | ✅ 6.500 |

**Coverage note (not drift).** The Idaho State Tax Commission lists **23**
cities with a local option sales tax: Bellevue, Bonners Ferry, Cascade,
Crouch, Donnelly, Driggs, Hailey, Harrison, Irwin, Kellogg, Ketchum, Lava Hot
Springs, Mackay, McCall, Ponderay, Riggins, Salmon, Sandpoint, Stanley, Sun
Valley, Swan Valley, Tetonia and Victor. The engine models **12** of them.
The other 11 (Bellevue, Bonners Ferry, Hailey, Harrison, Irwin, Kellogg,
Mackay, Ponderay, Swan Valley, Tetonia, Victor) are a coverage-expansion
candidate, not drift — no modelled Idaho rate is wrong.

Idaho publishes no consolidated rate table; the Commission directs filers to
contact each city, which is why per-city expansion here needs primary-source
work per city rather than one table parse. Worth recording as the reason this
gap persists.

---

## Systemic note

ND and NE join the standing Q3-refresh backlog. As of this run the SST refresh
queue has been chipped and unapplied across **five** separate audits
(07-22, 07-26, 07-31, 08-02, 08-06) and today makes six. Today produced the
**second and third proven wrong answers** attributable to that lag (after GA
Madison on 08-06): ND Scranton, ND Drayton and NE Edgar are all real
under-collections that no code change can fix. The argument for one
fleet-wide refresh pass instead of per-state chips keeps getting stronger.
**Decision still needed from Eric.**
