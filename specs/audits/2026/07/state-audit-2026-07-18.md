# Daily state sales tax audit — 2026-07-18 (day 18: NY + OH)

## TL;DR
- 2 jurisdictions audited. **2 findings in NY; OH fully current.**
- **NY — 1 confirmed drift FIXED:** Suffolk County was modeled at 8.625%
  (county 4.25%); NY DTF Publication 718 (eff **March 1, 2025**) lists
  Suffolk at **8¾ = 8.750%** (county 4.375%). Corrected `ny_data.py`
  4.25 → 4.375 and the matching test pins (Brentwood, Huntington,
  Smithtown). **Committed** (leads prod until a NY data reload).
- **NY — 1 new finding, NOT auto-fixed:** non-city Westchester County
  ZIPs under-collect by 1% (engine 7.375% vs Pub 718 8.375%). It's a
  jurisdiction-decomposition restructure → written to
  `specs/findings/ny-westchester-noncity-undercollection-2026-07.md`
  and chipped for human review.
- **OH — no change:** SST confirms **no OH county rate changes effective
  July 1, 2026**; prod's `OHR2026Q1NOV28` is still the current SST file;
  all 7 tier-1 OH cities match the live engine exactly.

## NY (New York) — non-SST, self-seeded module `ny_data.py`

- Source: **NY DTF Publication 718 — Sales and Use Tax Rates by
  Jurisdiction**, revision (2/25), **Effective March 1, 2025**
  (https://www.tax.ny.gov/pdf/publications/sales/pub718.pdf). Cross-ref:
  NY DTF sales-tax rate publications index; usgeocoder 2026 NY fact sheet.
- Last loaded on prod: engine matches repo `ny_data.py` (state 4% + per-
  county + MCTD 0.375% + city model; built/verified 2026-05-04).
- Latest available: Pub 718 (2/25), eff March 1, 2025 — the current
  edition. NY has no fixed update cadence; the last statewide change was
  effective March 1, 2025.

### Drift #1 — Suffolk County (CONFIRMED, FIXED)

Pub 718 lists **Suffolk = 8¾ = 8.750%** (reporting code 4711, an MCTD
county). The module had Suffolk County at **4.250%** → combined 8.625%.
Suffolk's county portion rose to **4.375%** (combined 8.750%) effective
March 1, 2025; the module cited that Pub 718 edition in its comment but
used the pre-increase 4.25 value. All other NY tier-1 jurisdictions
verified correct against Pub 718 (see grid below).

- Recommended action (DONE): `ny_data.py` Suffolk County 4.250 → 4.375;
  updated docstring (Brentwood/West Babylon/Brookhaven 8.625 → 8.750),
  unit-test pin (`test_state_new_york.py` 4.250 → 4.375), and the three
  liveapi grid pins (Brentwood 11717, Huntington 11743, Smithtown 11787
  → 8.750). **Committed this run.**
- **Prod follow-up:** the live engine still returns 8.625% for Suffolk
  ZIPs until `data load -s NY` runs on `opensalestax-01`. The three
  liveapi grid pins now lead prod and will fail under `-m liveapi` until
  that reload (documented in-line, matching the 2026-07-07 IA precedent).
  Chipped.

### Finding #2 — non-city Westchester under-collection (NOT auto-fixed)

Non-city Westchester ZIPs (e.g. Scarsdale 10583) return **7.375%** vs
Pub 718's **8.375%** ("Westchester — except cities" = 8⅜). The four
cities are correct. Root cause: county base modeled at 3.000% + phantom
city taxes that cancel only for the four cities. Multi-entry
decomposition restructure → **finding written + chipped for review**,
not auto-committed. See
`specs/findings/ny-westchester-noncity-undercollection-2026-07.md`.

### NY tier-1 verification grid (Pub 718 vs live engine)

| Jurisdiction | ZIP | Pub 718 | Engine | Delta |
|---|---|---|---|---|
| NYC — Manhattan | 10001 | 8.875 | 8.87500 | 0 |
| NYC — Bronx | 10451 | 8.875 | 8.87500 | 0 |
| NYC — Brooklyn | 11201 | 8.875 | 8.87500 | 0 |
| NYC — Queens | 11354 | 8.875 | 8.87500 | 0 |
| NYC — Staten Island | 10301 | 8.875 | 8.87500 | 0 |
| Buffalo (Erie) | 14202 | 8.750 | 8.75000 | 0 |
| Rochester (Monroe) | 14604 | 8.000 | 8.00000 | 0 |
| Yonkers (Westchester) | 10701 | 8.875 | 8.87500 | 0 |
| Syracuse (Onondaga) | 13202 | 8.000 | 8.00000 | 0 |
| Albany | 12207 | 8.000 | 8.00000 | 0 |
| White Plains (Westchester) | 10601/10605 | 8.375 | 8.37500 | 0 |
| Hempstead (Nassau) | 11550 | 8.625 | 8.62500 | 0 |
| **Brentwood (Suffolk)** | 11717 | **8.750** | **8.62500** | **−0.125** ← fixed in repo |
| New Rochelle (Westchester) | 10801 | 8.375 | 8.37500 | 0 |
| Mount Vernon (Westchester) | 10550 | 8.375 | 8.37500 | 0 |
| **Scarsdale (non-city Westchester)** | 10583 | **8.375** | **7.37500** | **−1.000** ← finding #2 |

## OH (Ohio) — SST full member

- Source: SST Governing Board state rate/boundary files
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates); OH DOR
  "The Finder" county rate tables (thefinder.tax.ohio.gov). OH state rate
  5.75%; counties + transit authorities stack on top (OH has no city
  sales tax).
- Last loaded on prod: **`OHR2026Q1NOV28.csv` / `OHB2026Q1NOV28.zip`**
  (2026 Q1, posted 2025-11-28), confirmed cached in
  `/var/lib/opensalestax/data/`.
- Latest available: SST's Ohio listing shows **`OHR2026Q1NOV28`** as the
  current OH rate file. Independent search confirms **no OH county sales
  tax rate changes effective July 1, 2026** (and none surfaced for
  Apr 1, 2026). No Oct-1-2026 change published yet. **Prod is current.**
- Drift summary: **None.** All 7 tier-1 OH cities match the live engine.
- Recommended action: **No action.** OH is current.

### OH tier-1 verification grid (live engine)

| City | ZIP | Expected (OH DOR stack) | Engine | Delta |
|---|---|---|---|---|
| Cleveland (Cuyahoga + RTA) | 44113 | 8.000 | 8.00000 | 0 |
| Cincinnati (Hamilton + SORTA) | 45202 | 7.800 | 7.80000 | 0 |
| Columbus (Franklin + COTA) | 43215 | 8.000 | 8.00000 | 0 |
| Dayton (Montgomery + GDRTA) | 45402 | 7.500 | 7.50000 | 0 |
| Toledo (Lucas + TARTA) | 43604 | 7.750 | 7.75000 | 0 |
| Akron (Summit + METRO) | 44308 | 6.750 | 6.75000 | 0 |
| Youngstown (Mahoning + WRTA) | 44503 | 7.500 | 7.50000 | 0 |

## Actions taken this run
1. **Committed** NY Suffolk County correction (4.25 → 4.375) + test pins.
2. **Chipped** the prod NY data reload (propagate Suffolk fix to live engine).
3. **Chipped** finding #2 (non-city Westchester restructure) for review.
4. Updated `specs/handoff.md` open follow-ups with both NY items.
