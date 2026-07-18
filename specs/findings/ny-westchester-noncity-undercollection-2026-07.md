# Finding: NY non-city Westchester County ZIPs under-collect by 1%

**Date:** 2026-07-18 (surfaced during the NY leg of the daily state
tax audit, day 18: NY + OH)
**State:** New York (non-SST, self-seeded module `ny_data.py`)
**Status:** RESOLVED in repo 2026-07-18 (prod reload tracked below) —
fix applied after review of the 0%-city-row behavior; see "Resolution".
**Severity:** Medium — 1% under-collection on every Westchester ZIP
outside the four incorporated cities. Under-collection = under-remittance
risk for self-hosters relying on the engine.

## Summary

The four incorporated cities in Westchester County return the correct
combined rate, but **unincorporated / village Westchester ZIPs return
7.375% instead of the authoritative 8.375%** — a 1% shortfall.

NY DTF **Publication 718 (effective March 1, 2025)** lists:

| Jurisdiction | Pub 718 | Engine | OK? |
|---|---|---|---|
| Westchester — except cities | 8⅜ = **8.375%** | **7.375%** | ✗ (−1.0%) |
| Mount Vernon (city) — 10550 | 8⅜ = 8.375% | 8.375% | ✓ |
| New Rochelle (city) — 10801 | 8⅜ = 8.375% | 8.375% | ✓ |
| White Plains (city) — 10605 | 8⅜ = 8.375% | 8.375% | ✓ |
| Yonkers (city) — 10701 | 8⅞ = 8.875% | 8.875% | ✓ |

Live-engine probe (2026-07-18): Scarsdale **10583 → 7.37500%** (a
representative non-city Westchester ZIP; the Town/Village of Scarsdale
is not one of the four cities). Same result expected for Rye, Harrison,
Mamaroneck, Ossining, Yorktown, Greenburgh, etc.

## Root cause

`src/opensalestax/states/ny_data.py` models Westchester with a
**county base rate of 3.000%**:

```python
"Westchester County": Decimal("3.000"),  # cities Yonkers, NR, Mt. V, WP add city tax
```

…and layers a per-city tax on the four cities (Yonkers +1.5%,
White Plains / New Rochelle / Mount Vernon +1.0% each). That
decomposition happens to produce the correct combined rate **for the
four cities**:

- Yonkers: 4 (state) + 0.375 (MCTD) + 3.0 (county) + 1.5 (city) = 8.875 ✓
- WP/NR/Mt.V: 4 + 0.375 + 3.0 + 1.0 = 8.375 ✓

…but a non-city Westchester ZIP receives only the county base:

- Non-city: 4 + 0.375 + 3.0 = **7.375** ✗ (Pub 718 says 8.375)

The true structure per Pub 718 is: **Westchester county-wide combined =
8.375%** (state 4 + MCTD 0.375 + county **4.000**). Every part of the
county is 8.375% **except Yonkers**, which adds an extra 0.5% city tax
(→ 8.875%). Mount Vernon, New Rochelle, and White Plains are already at
the county rate (8.375%) and add **nothing** extra — the current model
gives them a phantom +1.0% city tax offset by a −1.0% county base
under-count, so the two errors cancel *only for those three cities* and
*only coincidentally*.

This is a code-smell of the exact kind Eric's root-cause discipline
flags: a comment ("cities … add city tax") stating a design as fact,
where the numbers happen to work for the tested cities but are wrong on
the underlying decomposition — so anything not on the tested path
(unincorporated Westchester) reads the wrong value.

## Proposed fix (needs review — do NOT auto-apply)

Re-decompose Westchester to match Pub 718's actual jurisdiction model:

1. `NY_COUNTY_RATE_PCT["Westchester County"]`: **3.000 → 4.000**
2. City-tax increments in the NY city table:
   - Yonkers: **1.5 → 0.5** (4 + 0.375 + 4.0 + 0.5 = 8.875 ✓)
   - White Plains / New Rochelle / Mount Vernon: **1.0 → 0.0**
     (they equal the county rate: 4 + 0.375 + 4.0 = 8.375 ✓)
3. After the code change, **reload NY on prod** (`data load -s NY …`)
   so the live engine picks it up.
4. Add non-city Westchester ZIP pins to
   `tests/integration/test_sst_dor_validation.py` (e.g. Scarsdale
   10583 → 8.375, Rye 10580 → 8.375) so the regression is guarded.

Caveat for the implementer: confirm how the NY module stores city-tax
increments (single field vs. combined-with-county) before editing, and
verify that dropping WP/NR/Mt.V to a 0.0 city increment doesn't remove
their authority rows entirely (they may need to stay as named
zero-rate city authorities so the friendly name still resolves). This
is why it's a review item, not a mechanical audit commit.

## Resolution (2026-07-18)

Applied the proposed fix in `src/opensalestax/states/ny_data.py`:

- `NY_COUNTY_RATE_PCT["Westchester County"]`: 3.000 → **4.000**
- Yonkers city increment: 1.5 → **0.5**
- New Rochelle / Mount Vernon / White Plains city increment: 1.0 → **0.0**

**Verified the reviewer's concern first:** `NEW_YORK.parse_rates`
yields a city `RateRow` for **every** `NY_CITIES` entry unconditionally
(no skip for a 0.0 rate) — Rochester, Syracuse, Albany, Utica, etc. are
already seeded at 0.000. So dropping New Rochelle / Mount Vernon / White
Plains to a 0.0 city rate keeps their named city authority rows and ZIP
bindings (friendly names still resolve); their combined rate is now
state 4 + Westchester 4 + MCTD 0.375 = **8.375%**. Yonkers = + 0.5 city
= **8.875%**. Non-city Westchester (Scarsdale, Rye, …) now also resolves
to **8.375%**.

Tests: updated the NY unit assertions (Westchester county 4.0, Yonkers
city 0.5, new test asserting NR/Mt.V/WP are 0%-city rows) and added
liveapi regression pins for Scarsdale 10583 and Rye 10580 (both 8.375).
Full gate green (ruff, mypy, pytest -m "not liveapi" 1573 passed);
SonarQube: no new BLOCKER/CRITICAL. Committed with DCO sign-off.

**Prod:** the live engine needs a `data load -s NY` reload to pick up
the corrected Westchester county rate (same non-SST reload path used for
the Suffolk fix). Tracked in `specs/handoff.md`.
