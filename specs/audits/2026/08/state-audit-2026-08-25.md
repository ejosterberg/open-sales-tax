# Daily state sales tax audit — 2026-08-25 (day 25: WA + WI)

## TL;DR
- 2 states audited (both SST members). **6 confirmed rate changes in
  Washington, all live-wrong and all under-collecting**, from the
  unapplied Q3 SST refresh. **7 DOR_GRID pins bumped** to the correct
  post-refresh rates (Olympia carries two pins). Wisconsin is **fully
  clean** — all 9 pins match exactly and WI DOR confirms no county or
  city rate change effective in 2026.
- Both states' SST files are one quarter stale on prod (Q2 → Q3).
  For WA that staleness is now a **proven wrong answer**; for WI it is
  latent boundary risk only.
- No code fix is possible for either state — both are SST, so rates
  come wholly from the SST file. Refresh chips filed.

## WA — Washington

- Source: WA DOR local sales & use tax
  (<https://dor.wa.gov/taxes-rates/sales-use-tax-rates/local-sales-use-tax>),
  rates verified against the WA DOR address-rate API
  (`https://webgis.dor.wa.gov/webapi/AddressRates.aspx`), which reported
  `period="Q32026"` for every query.
- Last loaded on prod: `WAR2026Q2FEB26.zip` / `WAB2026Q2FEB26.zip`
- Latest available: **`WAR2026Q3MAY27.zip` / `WAB2026Q3MAY27.zip`**
- Drift summary: **6 of 13 tier-1 pins under-collect**, by 0.10–0.20pp,
  live and wrong since **2026-07-01 (55 days)**. Every one of the six
  traces to a jurisdiction on WA DOR's published Q3 2026 change list.
- Recommended action: apply the **WA Q3 SST refresh** — chipped. WA is
  SST, so there is no code-side fix.

### Details

| City | ZIP+4 | Loc code | Expected (WA DOR Q3) | Actual (engine) | Delta | Cause (eff 2026-07-01) |
|---|---|---|---|---|---|---|
| Tacoma | 98402-3502 | 2717 | **10.500** | 10.400 | **−0.10** | Pierce County — local law enforcement |
| Bellingham | 98225-1234 | 3701 | **9.200** | 9.100 | **−0.10** | Whatcom County — local law enforcement |
| Federal Way | 98003-1234 | 1732 | **10.400** | 10.300 | **−0.10** | City of Federal Way — local law enforcement |
| Olympia | 98501-1234 | 3403 | **10.000** | 9.800 | **−0.20** | City of Olympia +0.1 **and** Thurston County +0.1 |
| Olympia (Thurston) | 98501-0001 | 3403 | **10.000** | 9.800 | **−0.20** | same as above (second pin on the same ZIP) |
| Lakewood | 98499-0001 | 2721 | **10.300** | 10.100 | **−0.20** | City of Lakewood +0.1 **and** Pierce County +0.1 |
| Yakima | 98901-0001 | 3913 | **8.600** | 8.500 | **−0.10** | City of Yakima — transportation benefit district |

Clean (7 pins, match exactly): Bellevue 98004 (10.300), Vancouver 98660
(8.900), Renton 98055 (10.500), Spokane 99201 (9.100), Everett 98201
(9.900), Spokane Valley 99206 (9.000).

**Verification method / why these are trustworthy.** A ZIP-only query to
the WA DOR API returns `code="5"` — a ZIP-centroid fallback that resolves
to the surrounding county or PTBA rather than the city (e.g. 98402 →
"PIERCE-PTBA RTA", 98901 → "YAKIMA COUNTY"). Those fallback answers are
**not** city rates and were discarded. Every figure in the table above
comes from a full street-address query that resolved to the city's own
location code, and **each of the six drifted cities was confirmed at two
independent street addresses** returning the same location code and the
same rate. The two-address check rules out an address-specific anomaly.

**Q4 2026 (effective 2026-10-01): no tier-1 exposure.** WA DOR lists a
single Q4 local sales/use tax change — City of Mattawa, transportation
benefit district. Mattawa is not a tier-1 pin, so the Q4 file is not
time-critical for the pinned set. (Contrast ND Minot, which *is* pinned
and does need Q4 applied before 2026-10-01.)

**Committed this run:** 7 `DOR_GRID` pins bumped to the correct
post-refresh rates, each annotated with its cause, effective date and WA
DOR location code. Tacoma and Federal Way additionally had their
tolerance tightened `0.10 → 0.05`; both previously carried a loose
tolerance because their comment recorded an approximate local rate
("~3.9%", "~3.8%"). We now have exact DOR figures (local 4.0% and 3.9%),
so the loose tolerance is no longer warranted — and at 0.10 the Tacoma
pin would have absorbed this exact 0.10pp change silently.

All 7 bumped pins **fail under `-m liveapi` until prod loads WA Q3**.
`liveapi` is excluded from CI, so this does not break the pipeline.

## WI — Wisconsin

- Source: WI DOR county & city sales/use tax
  (<https://www.revenue.wi.gov/Pages/FAQS/pcs-county.aspx>, page updated
  2026-02-11)
- Last loaded on prod: `WIR2026Q2FEB18.csv` / `WIB2026Q2FEB18.zip`
- Latest available: **`WIR2026Q3MAY22.csv` / `WIB2026Q3MAY22.zip`**
- Drift summary: **none — all 9 tier-1 pins match exactly.**
- Recommended action: refresh to Q3 for boundary currency only — chipped,
  low priority. No rate exposure.

### Details

| City | ZIP+4 | Expected (WI DOR) | Actual (engine) | Delta |
|---|---|---|---|---|
| Milwaukee | 53202-2402 | 7.900 | 7.900 | 0 |
| Milwaukee | 53202-0001 | 7.900 | 7.900 | 0 |
| Madison | 53703-3505 | 5.500 | 5.500 | 0 |
| Madison | 53703-0001 | 5.500 | 5.500 | 0 |
| Green Bay | 54301-3502 | 5.500 | 5.500 | 0 |
| Green Bay | 54301-0001 | 5.500 | 5.500 | 0 |
| Janesville | 53545-0001 | 5.500 | 5.500 | 0 |
| Eau Claire | 54701-0001 | 5.500 | 5.500 | 0 |
| Portage | 53901-0001 | 5.500 | 5.500 | 0 |

Jurisdiction stacking also verified correct, not just the totals:
Milwaukee returns state 5% + Milwaukee County 0.9% + City of Milwaukee 2%
(WI Act 12), and the other five cities return state 5% + their county's
0.5%.

**WI DOR confirms no 2026 changes.** The most recent Wisconsin local
changes remain Manitowoc County 0.5% (2025-01-01) and Racine County 0.5%
(2025-04-01), with Milwaukee County's 0.9% and the City of Milwaukee's 2%
both dating to 2024-01-01. Milwaukee remains the only Wisconsin
municipality levying a city sales tax. Nothing in the pinned set is
affected.

**Why the stale WI file is lower-risk than WA's.** Wisconsin's local tax
is a flat 0.5% county levy (0.9% in Milwaukee) with one city overlay, so
a stale *rate* file cannot produce a wrong rate while no county changes.
The residual exposure is the *boundary* half: ZIPs whose bindings changed
through annexation would silently keep the old county binding. Since
neighbouring Wisconsin counties overwhelmingly share the same 0.5% rate,
even a wrong binding usually yields the right number — which is exactly
why this needs to be caught by file currency rather than by rate probes.

## Systemic note

The 2026-08-06 audit flagged that **16 of 24 SST states are ≥1 quarter
stale**, with GA the first proven wrong answer from that lag. **WA is now
the second — and the largest so far: 6 wrong rates in one state**, versus
GA's 1 and ND/NE's 3 combined. That brings the running total of live
wrong rates attributable to the SST refresh backlog to **10 across 4
states** (GA 1, ND 2, NE 1, WA 6). This continues to argue for one
batched refresh of all stale SST states rather than per-state chips.
**Decision still pending from Eric.**
