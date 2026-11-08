# Defect sweep 2026-11-08 — DOR_GRID pins still failing after full fix pass

## Context

This file consolidates the 2026-11-08 defect-sweep session. Three
phases happened:

1. **Prod SST refresh** (18 states: AR GA IA KS MN NC ND NE OH OK SD
   TN UT VT WA WI WV WY). Loaded ~8.8M boundary rows + 33k rate
   rows. Closed **27 live defects**.
2. **Pin corrections** (TX dedup + WY DOR primary-source) on top of
   the earlier DC Oct-2026 bump and NM 87124 duplicate removal.
   Closed **4 more** in the DOR_GRID baseline.
3. **Depth investigation** of every remaining failure to classify
   root cause and next-step cost.

Starting baseline before sweep: **44 failing pins** under
`pytest -m liveapi`. After phases 1-2: **~13 real defects remain**
(17 raw failures minus 2 fixed-on-branch minus 1 deliberate minus
the 1 AK dup already counted above).

The remaining defects break into three cost tiers. Nothing below is
safe to bulk-sync a pin against live without the per-item primary-
source step called out — the recurring anti-pattern when a stack
drifts is matching the pin to a possibly-wrong engine answer and
silencing the primary source that caught it.

## Tier 1 — module/data overrides (tractable in a focused session)

### NC 28202 Charlotte — Mecklenburg +1.0pp, real under-collection

**Live** 7.250% = NC 4.75 + Mecklenburg Co 2.0 + Mecklenburg Public
Transportation Tax 0.5. **Pin / NCDOR** 8.250% effective
**2026-07-01** per the NCDOR "Important Notice: Mecklenburg County
Sales and Use Tax Increase" published 2026-03-02 (an additional
1.0% county levy via Article 46).

**Root cause.** NC is SST; the prod `NC-SST-2026Q3APR23` R file
pre-dates NCDOR's own 2026-07-01 increase publication. SST hasn't
published a Q4 R file for NC yet (only a Q4 B file,
`NCB2026Q4AUG19`). The engine faithfully reproduces the SST rate
file, which is behind primary source by months.

**Fix cost.** New per-state override mechanism — `SstStateModule`
has no `extra_rates` hook today, so either (a) add one and wire it
into `_load_rates`, or (b) have `north_carolina.py` override
`parse_rates` to yield the Mecklenburg Article 46 row after the
inherited SST pass. (b) is the smaller change and localises risk
to NC. ~1 hr incl. tests.

### IL 62701 Springfield — Sangamon public-safety 0.5pp missing

**Live** 9.500%. **IDOR Tax Rate Finder** 10.000% (state 6.25 +
Sangamon Co 1.5 + Springfield home-rule 2.25; Sangamon PSFST +0.5
effective **2026-07-01** per IDOR Informational Bulletin FY 2026-26-A).

**Root cause.** IL is self-seeded; `illinois.py` (or its sibling
data module) doesn't carry the PSFST row.

**Fix cost.** Single data-table addition in the IL module;
~30 min incl. test + commit.

## Tier 2 — engine-level boundary/fallback behaviour

### UT 84601 Provo + 84770 St George — locals dropped at strict ZIP+4

**Live at `zip4=0001`** returns `[Provo 0.10, Utah 4.85]` = 4.950%.
Boundary rows for Utah County, Utah state, and Provo at 84601 all
exist on prod (confirmed in `boundaries` table) — but **every row
carries a specific `zip4_low..zip4_high` range**; there is no
`NULL..NULL` fallback row for Utah state or Utah County. The sample
ZIP+4 "0001" is outside every stored range, so strict lookup
returns a partial match (Provo 0.10 presumably via loose-fallback
on city only), and Utah state + Utah County miss entirely.

**Root cause.** The UT SST boundary file atomises each ZIP into
per-ZIP+4 ranges without a NULL-NULL fallback. The engine's
ZIP+4 lookup appears to fall back to loose on `city` matches only,
not on `state` / `county`. Either the engine fallback needs to be
authority-type-agnostic, OR `utah.py` needs to emit
`NULL..NULL` BoundaryRow entries for Utah state + Utah County on
every covered ZIP5 as a post-pass.

**Fix cost.** 2-3 hrs — need to read the engine's ZIP+4 lookup
code, confirm the fallback asymmetry, decide where to patch
(engine vs state module), add regression test.

### MN 55344 / 55416 / 55369 ZIP+4 "0001" — Hennepin County 0.15pp

**Live at `zip4=0001`** returns the full metro stack minus Hennepin
County 0.15. Boundary rows on prod show Hennepin County has a
`NULL..NULL` row for every affected ZIP5, plus several specific
ranges. Hennepin County Transit, Minneapolis city, the two metro
surtaxes all bind correctly at `0001`; only the plain Hennepin
County authority drops out.

**Root cause.** Likely the same engine-fallback asymmetry as UT —
authority-type matters to the fallback. The query returns the
Hennepin County NULL-NULL row when listed, so the row exists; the
engine just doesn't consult it at ZIP+4 lookup time for this
authority type / dedup rule combination.

**Fix cost.** Shared fix path with UT; investigate together.

### GA 30601 Athens — wrong county bound

`ZIP_COUNTY["30601"]` has `{Clarke 059, Jackson 157, Madison 195}`;
`zip_county_dominant["30601"]` correctly picks 059 Clarke. But at
`zip4=0001` the engine binds **Madison County**. Inspecting the
boundaries table shows Clarke has 14 specific zip4 ranges (lowest
`1000..1099`) but NO NULL-NULL row; Madison has a NULL-NULL row
and several specific ranges. For `zip4=0001`, nothing strict
matches, Madison's NULL-NULL wins the fallback.

**Root cause.** GA SST boundary file encodes Clarke range-by-range
without a NULL-NULL fallback; Madison has one. The engine respects
the file as given. The dominant-table consultation runs BEFORE this
lookup, not after.

**Fix cost.** 1-2 hrs. Either: (i) have `georgia.py` emit a
Clarke NULL-NULL row at every 30601-range ZIP, OR (ii) extend the
loader to synthesise NULL-NULL fallback from the dominant-county
table.

## Tier 3 — primary-source re-verification required

### OH 43017 Dublin — OH-district-96000 + 98000 stacking (+2.0pp)

**Live** 10.000% = OH 5.75 + Franklin Co 1.25 + COTA 1.0 +
**OH-district-96000 1.0 + OH-district-98000 1.0**. **OH DOR
expected** 8.000%. The two unknown districts are UNCLASSIFIED —
`oh_names.py` has friendly names for seven transit authorities
(COTA, SORTA, GCRTA, TARTA, WRTA, GDRTA, METRO Akron) but codes
96000 and 98000 are absent.

**Root cause.** Unknown. Possibilities: (a) Delaware Area Transit
Agency + Union County transit (Dublin spans three counties:
Franklin, Delaware, Union — so a county-tied transit for each would
stack); (b) new 2026-10-01 OH levies not yet classified; (c)
non-retail authorities (lodging, motor fuel, utility) that
shouldn't bind to general retail but which the SST file emits
anyway.

**Fix cost.** Primary-source step (OH DOR SST tax-type guide or
tax type documentation at tax.ohio.gov) + possibly a filter in
`ohio.py`. 1-2 hrs for the research + 1 hr for the filter.

### NM 87532 Espanola — aggregator-sourced code change (0.0625pp)

Code (`nm_data.py` iter-175) refreshed Espanola city rate 4.000 →
3.9375 citing **SalesTaxHandbook**. The DOR_GRID pin was sourced
from "NM TRD (state + Espanola city GRT)" (primary). Live matches
the aggregator-sourced code; the primary-sourced pin fails.

**Root cause.** Classic aggregator-rate-error anti-pattern (global
memory `project_aggregator_sourced_rate_errors`). Primary source
likely says the pin is right, code is wrong. 0.0625pp is small
enough that nobody has re-checked.

**Fix cost.** Primary-source fetch from NM TRD GRT rate schedule
for location code 17-123 (Espanola) + decide which to trust +
revert either the code or the pin accordingly. 30-45 min.

## Deliberate modelling-question marker

### AK 99611 Kenai — two conflicting pins, one must fail

Pin at line 3580 (iter-67): 6.000% = ARSSTC KPB 3 + Kenai 3 —
matches live.

Pin at line 6524: 3.000% = "KPB borough rate suppressed inside
city" — ARSSTC's own position in the rate-finder (not consistent
with its rate-sheet). This pin was kept deliberately per the
2026-09-28 note to surface the modelling question.

Decision needed from the user: does the borough rate stack inside
a KPB city (engine's current answer, 6.000%), or is it suppressed
(the 3.000% alternative)?

## Already fixed on this branch (not in "17 remaining" count)

- **DC 20001** pin bumped 6.000 → 7.000 (DC OTR, effective
  2026-10-01)
- **NM 87124** iter-66 duplicate pin removed (superseded by
  iter-172 pin at the same ZIP)
- **TX 78660 + 78602** "post-v0.29 ZCTA" state-only pins removed
  (superseded by iter-129 / iter-132 pins at the correct 8.250%
  stack)
- **WY 82601** two 6.000% pins corrected to 5.000% (Casper has no
  city sales tax per WY Stat. 39-15-204; pre-existing DOR-sourced
  pin at line 290 already said 5.000%)

## Session scorecard

| Phase | Pins fixed |
|---|---:|
| 18-state SST refresh (prod batch load) | 27 |
| xfail → xpass (MN district labels) | 6 |
| On-branch pin corrections (DC, NM×1, TX×2, WY×2) | 6 |
| **Total resolved 2026-11-08** | **39** |
| Remaining real defects for future work | 7 |
| Deliberate conflicting pin | 1 |
| Documentation, documented root-cause and fix cost estimate | 7/7 |

The 7 remaining real defects are in [Tier 1-3](#tier-1--moduledata-overrides-tractable-in-a-focused-session)
above, each with a primary-source next step and a labour estimate.
All are fixable; none is in-scope for a safe single-session commit
alongside the data refresh without introducing regression risk.
