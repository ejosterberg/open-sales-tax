# Daily state sales tax audit — 2026-07-14 (day 14: MT + NC)

## TL;DR
- 2 jurisdictions audited. **1 real-world rate change found** (NC Mecklenburg
  County / Charlotte, +1.00% effective 2026-07-01), requiring a prod SST
  rate-file reload (chipped) + a liveapi test-pin bump (committed).
- **MT: clean** — no statewide sales tax; engine correctly returns 0% for every
  MT ZIP (including resort towns, whose local resort taxes are a documented
  Phase-1 deferral). No action.
- **NC: 1 change** — Mecklenburg County (Charlotte) went **7.25% → 8.25%**
  effective **2026-07-01**. Only NC county change in the 2025-2026 period. Prod
  is on the ~2-year-stale `NCR2024Q3APR26.csv`, so the live engine still returns
  7.25% (under-collects Charlotte by 1.00 pp). SST member → **refresh chipped**,
  liveapi pin bumped to the authoritative 8.25%.

## MT (Montana)
- Source: N/A — Montana levies **no statewide sales tax** (one of the 5 NOMAD
  no-tax states: NH, OR, MT, AK-partial, DE). Modeled by
  `src/opensalestax/states/no_tax.py` (`NoTaxState("MT", …)`), not an SST file.
- Last loaded on prod: N/A (no rate/boundary data to load).
- Latest available: N/A.
- Drift summary: **None possible.** Engine returns 0% combined for all MT ZIPs.
- Recommended action: none.
- Details (live engine `/v1/calculate`, $100 general line):

  | City (ZIP) | Expected | Actual (engine) | Delta |
  |---|---|---|---|
  | Billings (59101) | 0% | 0% | 0 |
  | Bozeman (59718) | 0% | 0% | 0 |
  | Whitefish (59937) | 0%* | 0% | 0 |

  \* Whitefish/Big Sky levy *local resort taxes* (MCA Title 7, Ch. 6, Part 15).
  These are a documented Phase-1 deferral (see the `notes` on the `MONTANA`
  `NoTaxState` instance and the module docstring). Not a general sales tax; out
  of v1 scope. No drift — this is expected, documented behavior.

## NC (North Carolina)
- Source: [NCDOR — Current Sales and Use Tax Rates (Effective 2026-07-01)](https://www.ncdor.gov/taxes-forms/sales-and-use-tax/sales-and-use-tax-rates/current-sales-and-use-tax-rates)
  + [NCDOR Important Notice — Mecklenburg County Sales and Use Tax Increase](https://www.ncdor.gov/taxes-forms/sales-and-use-tax/other-sales-and-use-tax-resources/important-notices-issued-sales-and-use-tax-division/important-notice-mecklenburg-county-sales-and-use-tax-increase)
  + [NCDOR press release 2026-06-24](https://www.ncdor.gov/news/press-releases/2026/06/24/mecklenburg-county-impose-additional-one-percent-sales-tax-beginning-july-1).
  NC is a Streamlined Sales Tax full member; rates flow through the SST
  quarterly rate file.
- Last loaded on prod: rate `NCR2024Q3APR26.csv` (posted 2024-04-26 — **~2
  years stale**); boundary `NCB2026Q2FEB18.zip`.
- Latest available: SST 2026 Q3 rate + boundary files (general Q3 release posted
  **2026-06-01** per the SST rate/boundary-file-updates index; the future-
  effective 2026-07-01 Mecklenburg row rides in the Q3 file). Exact filename
  `NCR2026Q3…` not machine-readable off the SST site's JS-rendered listing, but
  the Q3-2026 vintage is confirmed.
- Drift summary: **Mecklenburg County (Charlotte) 7.25% → 8.25%** effective
  **2026-07-01** — an additional 1.00% local rate, voter-approved in the
  **2025-11-04 referendum** (roads + transit). Live engine still returns 7.25%
  (prod on the stale 2024 Q3 rate file). This is the **only** NC county change
  in the 2025-2026 period; all other sampled counties match exactly.
- Recommended action:
  1. **Refresh NC SST rate + boundary to Q3-2026 on prod** (chipped — SST files
     are Eric-reviewed, not auto-pulled). After reload the engine returns 8.25%
     for Mecklenburg ZIPs and the liveapi pin below xpasses.
  2. **Committed this run:** bumped the Charlotte `28202` liveapi DOR-grid pin
     7.250 → 8.250 with an explanatory note (fails under `-m liveapi` until the
     reload — matching the HI-Maui / IA-WDM precedent in this file).
- Details (live engine `/v1/calculate`, $100 general line, vs NCDOR
  eff-2026-07-01 table):

  | County (city, ZIP) | Expected (NCDOR 2026-07-01) | Actual (engine) | Delta |
  |---|---|---|---|
  | **Mecklenburg (Charlotte, 28202)** | **8.25%** | **7.25%** | **−1.00 pp** ⚠ |
  | Wake (Raleigh, 27601) | 7.25% | 7.25% | 0 ✓ |
  | Guilford (Greensboro, 27401) | 6.75% | 6.75% | 0 ✓ |
  | Durham (Durham, 27701) | 7.50% | 7.50% | 0 ✓ |
  | Forsyth (Winston-Salem, 27101) | 7.00% | 7.00% | 0 ✓ |
  | Cumberland (Fayetteville, 28301) | 7.00% | 7.00% | 0 ✓ |
  | Buncombe (Asheville, 28801) | 7.00% | 7.00% | 0 ✓ |
  | New Hanover (Wilmington, 28403) | 7.00% | 7.00% | 0 ✓ |

  Mecklenburg new stack: state 4.75% + county 2.00% (Art 39/40/42) + transit
  0.50% (Art 43) + **additional 1.00%** (2026-07-01 voter-approved) = 8.25%.

## Actions taken this run
1. **Commit** (this repo): liveapi DOR-grid pin `NC Charlotte 28202` 7.250 →
   8.250 + note. Trivial single-pin data update per NCDOR authoritative table.
2. **Chip** (Eric review): "Refresh NC SST quarterly to Q3-2026 (Mecklenburg
   +1% → 8.25% eff 2026-07-01)".
3. **handoff.md**: added NC Mecklenburg refresh to open follow-ups.

No changes for MT.
