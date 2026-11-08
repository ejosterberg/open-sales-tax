# Defect sweep 2026-11-08 — 17 DOR_GRID pins still failing against live

## Context

Full-sweep audit 2026-11-01 reloaded 7 states; pin-refresh PR #45 (2026-11-01)
refreshed 5 dead upstream SST files and corrected 2 stale pins (DC +1pp
Oct-2026 bump, NM 87124 iter-66 duplicate removed). Prod batch load on
2026-11-08 reloaded 18 SST states to the current upstream pins (AR, GA, IA,
KS, MN, NC, ND, NE, OH, OK, SD, TN, UT, VT, WA, WI, WV, WY).

Before the batch: **44 DOR_GRID pins failed** under `pytest -m liveapi`
against `api.opensalestax.org`.

After the batch: **17 pins failed**, **6 xfailed tests flipped to xpass**
(the MN district-label regressions — xfail marker can now be removed).

Net: **27 live defects closed**, 6 xfail markers obsolete, 17 remain.

This file catalogs the 17, grouped by root-cause class, so a later session
can work them with primary-source verification. The defects are a mix of
genuine new engine/data drift, stale pins in `test_sst_dor_validation.py`,
and one deliberate conflicting pin.

## Already addressed on branch `defect-sweep-20261101` / PR #45

- **DC 20001**: pin 6.000 → 7.000 (effective 2026-10-01 per DC OTR). Fixed.
- **NM 87124** iter-66 pin: superseded duplicate of the iter-172 pin at
  the same ZIP; removed. Fixed.

Both will pass once PR #45 merges. They appear in the 17-failure count
because the liveapi run was executed against `main`, which does not yet
carry the PR commits.

## Category A — real new live defects introduced by the Q4 refresh (6)

### 1. OH 43017 Dublin — over-collects 2.00pp

Live returns 10.000%; pin expects 8.000% (OH DOR state 5.75 + Franklin
1.25 + COTA 1). Live authority list includes two unknown-labeled
authorities, **`OH-district-96000`** and **`OH-district-98000`**, stacking
on top of the normal retail stack. The OH Q4 SST file
(`OHR2026Q4SEP17.csv`) is the newly-applied data; before the refresh OH
pins passed, so one or both of these district codes is a new addition
that should be filtered out of the retail-sales lookup, or classified
as a non-retail authority (e.g. motor-fuel, utility, or lodging).

**Next step:** read the OH SST rates file, identify what 96000 / 98000
correspond to in the OH DOR tax-type schedule, and either rename them
to their authoritative friendly names + ensure they don't bind to
general retail, or add them to an OH-module authority-filter list.

### 2. UT 84601 Provo — under-collects 2.50pp

Live returns 4.950% (state 4.85 + 0.10 only, no Utah County/city
locals); pin expects 7.450% (state 4.85 + Utah County locals). All
UT county/city local rates appear to have been dropped by the Q4
refresh for this ZIP. The Q4 data file (`UTR2026Q4AUG11.csv`) is
newly applied.

### 3. UT 84770 St George — under-collects 1.60pp

Same pattern as 84601: live 5.150%, pin 6.750%. Washington County
locals missing.

**Shared next step (both UT pins):** diff the UT Q4 R file against
the prior UT prod version (`UT-SST-2026Q2MAR20`) to find whether
Provo/St George bindings are missing, mis-categorized, or in a
different authority type. If the Q4 data genuinely dropped the
locals (unlikely — they're published on UT TAP), there's a loader
parser issue specific to UT Q4.

### 4. GA 30601 Athens — under-collects 1.00pp, wrong county bound

Live returns 7.000% (Georgia + **Madison County**); pin expects
8.000% (Georgia + Athens-Clarke). `ZIP_COUNTY["30601"]` is
`{Clarke 059, Jackson 157, Madison 195}`;
`zip_county_dominant["30601"]` correctly picks `059` (Clarke).
But the engine returns Madison, which means the GA Q4 SST boundary
file (`GAB2026Q4AUG20.zip`) is binding 30601 directly to Madison
and overriding the Census dominant rule.

**Next step:** inspect the GA SST boundary file for ZIP 30601's
entries. If it does bind Madison, decide: does GA DOR consider the
Madison binding authoritative, or is the SST file carrying a
mis-encoded row?

### 5. IL 62701 Springfield — under-collects 0.50pp

Live returns 9.500% (Illinois + Sangamon + Springfield); pin expects
10.000% (per IDOR Tax Rate Finder, including Sangamon public-safety
+0.5% effective 2026-07-01, IDOR FY 2026-26-A). The Sangamon
public-safety component is missing from the IL module. IL is
self-seeded (`IL-SST-V0.31-STATEWIDE`), so the fix is a code change
in `src/opensalestax/states/illinois.py` or its data table.

### 6. WY 82601 Casper ZIP+4 "0001" and "4800" — under-collect 1.00pp

Live returns 5.000% (Wyoming + Natrona County); pins expect 6.000%
(including a Casper city 1%). But **WY DOR does NOT list a general
sales tax for the City of Casper** — only Natrona County's 1%
local. The pin may actually be **stale**: 5.0% is the correct
Casper retail rate. This is the aggregator-rate-error anti-pattern
(the pin's source says "WY DOR / SalesTaxHandbook" — hybrid, and
SalesTaxHandbook has over-reported Wyoming city rates in other
investigations).

**Next step:** verify directly against revenue.wyo.gov. If 5.0% is
the correct rate, both pins should be updated to 5.0 with the
over-collection note removed.

### 7. NC 28202 Charlotte ZIP+4 "1402" — under-collects 1.00pp (likely stale pin)

Live 7.250% (NC + Mecklenburg + Mecklenburg Public Transportation);
pin expects 8.250% including an "additional 1%" transit tax. Current
NCDOR Mecklenburg rate is state 4.75 + county 2 + transit 0.5 = 7.25,
so live matches NCDOR exactly. The pin's "additional 1%" appears to
be an obsolete reference (possibly to the MTC-rejected 2019-era
proposed transit tax).

**Next step:** verify against ncdor.gov Mecklenburg rate page. If
confirmed, update pin 8.250 → 7.250.

### 8. MN Hennepin ZIP+4 "0001" lookups — three ZIPs under-collect 0.15pp

Live for 55416 / 55344 / 55369 with explicit `zip4=0001` returns
8.875%; same ZIPs with no `zip4` query return 9.025%. Hennepin
County's 0.15% is bound to the ZIP but only resolves on loose
(zip5-only) lookups, not on strict ZIP+4 "0001" lookups. Compare:

```
MN 55416 zip5-only:     ['Minneapolis', 'Hennepin County', 'Minnesota', ...]  9.025%
MN 55416 zip4=0001:     ['Minneapolis', 'Minnesota',       ...]               8.875%
```

The engine's ZIP+4 range matching may be filtering out the Hennepin
County boundary because its boundary row's zip4 range doesn't cover
the "0001" synthetic. Three pins hit this: 55344, 55369, 55416.

**Next step:** inspect `boundaries` rows for Hennepin County where
state='MN' and zip5 in ('55416','55344','55369'); check what zip4
range (if any) they carry. The likely fix is that the Hennepin
boundary row should have `zip4_low IS NULL AND zip4_high IS NULL`
(matches all ZIP+4) instead of a specific range.

## Category B — stale pins unrelated to the refresh (3)

### 9. TX 78660 Pflugerville — pin 6.250 → should be 8.250

Pin assumes "state 6.25% + Travis 0%" (`post-v0.29 ZCTA; was
state-only before`). Live returns 8.250% with Texas + Travis County
+ Pflugerville, matching the TX Comptroller's `comptroller.texas.gov`
rate for 78660 (state 6.25 + Pflugerville 1.0 + Capital Metro
Transit 1.0). The pin is a leftover from when Pflugerville wasn't
seeded as a city.

### 10. TX 78602 Bastrop — pin 6.250 → should be 8.250

Same pattern as 78660. Live returns 8.250% with Texas + Bastrop
County + Bastrop. Current TX Comptroller rate is 8.250%.

## Category C — deliberate test fixture artefact (1)

### 11. AK 99611 Kenai second pin (line 6524) — 3.000% expected

The test file has **two conflicting pins** on Kenai 99611:
- Line 3580 (iter-67): 6.000% — ARSSTC KPB 3 + Kenai 3 (what live returns)
- Line 6524: 3.000% — ARSSTC "KPB borough rate suppressed inside city"

The 3.000% pin was kept deliberately per the 2026-09-28 note as a
modelling-question marker: does the Kenai Peninsula Borough rate
apply inside Kenai city limits, or is the borough rate suppressed
when a city with its own rate overlays it? The cities' ordinances
disagree with ARSSTC's rate-finder on this. **Not a live defect** —
one of the two pins must fail until the modelling question is
decided.

## Category D — aggregator-sourced rate concerns (2)

### 12. NM 87124 Rio Rancho iter-66 (3480) — already fixed on branch

Pin 7.6875 was superseded by the iter-172 pin at the same ZIP
(7.875). Duplicate. Deleted in PR #45.

### 13. NM 87532 Espanola — chip for primary-source audit

Live 8.8125%; pin 8.875%. The 0.0625pp drift traces to a code
change in `nm_data.py` iter-175 that cited **SalesTaxHandbook** (an
aggregator) to drop Espanola's city rate from 4.000 to 3.9375. This
is the global-memory aggregator-rate-error anti-pattern. The pin
sourced from "NM TRD (state + Espanola city GRT)" (primary) may be
the correct value; the code change is the suspect.

**Next step:** fetch the current NM TRD GRT rate schedule for
location code 17-123 Espanola and decide whether the code change
or the pin is right. Do not simply update the pin to match live —
that silences the primary source.

## Already corrected in this sweep (not counted in the 17 above)

- 27 ZIPs across AK/AL/FL/HI/MN/IA/NC (the 2026-11-01 reload-missed
  category)
- 16+ ZIPs across IA LOST / MN metro / WA Q3 / ND Q3-Q4 / NE Q3 / GA
  Q4 / UT Q4 pins that went green with the 18-state batch
- 6 MN district-label xfail cases (now xpass; marker can be removed)
- DC 20001 and NM 87124 iter-66 duplicate (both fixed on branch)

## Summary

| Category | Count | Nature |
|---|---:|---|
| A. Real defects needing investigation | 8 | Loader, module, or data-shape |
| B. Stale pins (TX Comptroller confirms live) | 2 | Test-file update |
| C. Deliberate fixture artefact | 1 | No action |
| D. Aggregator-sourced concerns | 2 | Primary-source re-verification |
| Fixed on branch (count here for completeness) | 2 | DC, NM 87124 |
| Not addressed in this session | 2 | WY ×2 (likely stale, needs WY DOR verify) |

Total remaining to action in a later session: **~11 items**.

The batch load deployed 2026-11-08 closed 27 live defects; the
remaining 17 should be worked individually with per-item primary-
source confirmation, not bulk-updated.
