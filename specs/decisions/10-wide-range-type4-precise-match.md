# Decision 10: Wide-range type-4 records and the precise-match assumption

**Status:** **RESOLVED 2026-05-08** in commits `0418403` + `d68c023`
(iter-62 third attempt). The fix lives in `lookup.py`'s soft-add-
dominant-city path, gated on `not has_narrow_precise`. See "Iter-62
resolution" section at the end of this doc.

**Original status:** Open (deferred) -- recorded 2026-05-05 during iter 43.

## Context

The strict ZIP+4 lookup (``lookup_jurisdictions_by_zip``) treats
any type-4 boundary record whose ``[zip4_low, zip4_high]`` range
contains the supplied ``zip4`` as a "precise match" -- meaning the
matched authority's binding is authoritative for that address, and
type-z (zip-wide) records for OTHER county/city authorities get
suppressed.

This works correctly when type-4 ranges are narrow (e.g. Casper
WY's per-block ranges 4762-4765, 4767-4767, etc.). But the SST
file from some states ships **wide-range type-4 records that act
like type-z** -- they cover essentially every +4 in the ZIP, but
encoded as a single type-4 range.

Empirical audit 2026-05-05 (per-state count of distinct ZIPs with
a type-4 record where ``zip4_low='0000'`` and ``zip4_high>='0900'``):

| State | ZIPs affected | Notes |
|---|---:|---|
| KY | 2786 | Flat statewide rate -- no impact |
| IN | 1997 | Flat statewide rate -- no impact |
| NV | 436 | County-only local; no impact (verified) |
| WY | 196 | **Affected** -- impacts Casper, Cheyenne, etc. |
| WA | 28 | Possibly affected; not yet investigated |
| NC | 26 | Possibly affected; not yet investigated |
| ND | 3 | Likely no impact |

## Concrete repro

For Casper WY 82601:

- ``Wyoming`` (state authority) has a type-4 row covering
  ``zip4_low='0000', zip4_high='0999'``.
- ``Natrona County`` likewise has a type-4 row covering
  ``0000-0999``.
- ``Casper`` (city) has only narrow type-4 rows (4762-4765,
  4767-4767, ..., 9000ish-9100ish).

For ``zip4='0001'`` (synthetic), the precise-match query finds
Wyoming and Natrona County's wide-range type-4 records --
``precise_county_city_ids`` becomes ``{Natrona.id}`` (and
implicitly Wyoming via the state passthrough). The merge then
filters out Casper city because Casper isn't in
``precise_county_city_ids``.

Result: 82601-0001 returns 5.00% (state + county) instead of the
correct 6.00% (state + county + city).

For real Casper +4s in the 4762+ range, precise_county_city_ids
includes BOTH Natrona AND Casper, and the rate stack is correct.

## Why deferred

The blast radius is bounded:

1. **Real +4 addresses work correctly.** In production traffic,
   integrators supply real ZIP+4s, which match the narrow type-4
   ranges; the wide-range county/state records also match, and
   ``precise_county_city_ids`` ends up with both county AND city.
2. **Loose lookup (no +4) works correctly.** Anyone calling
   ``POST /v1/calculate {address: {zip5: "82601"}}`` (no zip4)
   gets the right answer via ``lookup_jurisdictions_by_zip5_loose``.
3. The bug only surfaces with **synthetic / fake +4 values** that
   fall in the wide range but not in any narrow city range.

The fix needs careful design: distinguish "narrow" vs "wide"
type-4 records. Candidates:

- **Heuristic threshold**: treat type-4 records with range >= 100
  +4s as "wide" and ignore them in the precise-match query
  (forcing a fall-through to the loose-lookup dedup). Pros:
  simple. Cons: arbitrary cutoff; the SST file may ship 0001-0099
  as a legitimately narrow range in some states.
- **Use county_fips**: type-4 records on a state-level or
  county-level authority are inherently "wide"; only city/district
  authorities should populate ``precise_county_city_ids``. This is
  cleaner but requires changing the query to join on authority_type.
- **Detect the conflict**: if any city authority has type-4 records
  for the ZIP, but none match the supplied +4, fall back to the
  loose lookup. Pros: catches the issue precisely. Cons: extra
  query.

## Workaround until fixed

Live test grids should use **real** ZIP+4 ranges, not synthetic
values like ``0001``. The Casper entry in the live DOR grid was
moved from ``82601-0001`` to ``82601-4800`` in iter-43.

For production callers, the recommendation is the same as it
already is: prefer real ZIP+4s when available; fall back to
zip5-only when the +4 is unknown (the loose lookup correctly
resolves these cases).

## How to apply when ready

1. Pick one of the design options above (recommended: the
   ``authority_type`` filter -- only city/district authorities
   should populate ``precise_county_city_ids``).
2. Update ``lookup_jurisdictions_by_zip``'s precise type-4 query
   to filter by ``TaxAuthority.authority_type.in_(("city",
   "district"))``.
3. Add the synthetic ``82601-0001`` and ``82001-0001`` rows back
   to the live DOR grid as regression tests.
4. Audit WA/NC for any user-facing impact and add representative
   rows to the grid.

## Iter-60 attempt (reverted)

A first attempt landed in commits ``0fe69be`` + ``5f69a3f`` (then
reverted in ``08c5d46`` + ``b44c5d6``):

1. Width filter on the precise type-4 query: drop matching boundary
   rows whose ``[zip4_low, zip4_high]`` span >= 1000 +4s.
2. Per-type loose fallback: when precise was empty, run the closest-
   match loose lookup separately for whichever of (county, city) was
   missing from the type-z layer.

The combination correctly fixed Casper 82601-0001 (5% -> 6%) but
regressed GA Roswell 30075-0001 (7.75% -> 6.75% with the WRONG
county). Root cause of the regression: pre-fix, Fulton County's
wide-range (0000-9999) type-4 record was the precise match that
covered 0001; the merge filter dropped Cobb's type-z. Post-fix,
the wide-range filter excluded Fulton from precise, leaving precise
empty; the closest-county loose fallback then picked Cobb because
Cobb's narrow ranges sit closer to +4 0001 than Fulton's narrow
ranges. The distance-based picker that protects OK Norman vs Moore
does the wrong thing when a state uses wide ranges as the dominant
encoding (GA Fulton) instead of as a type-z-equivalent (WY Natrona).

**Lessons for the next attempt:**

- A single global threshold is too coarse. WY's wide ranges ARE
  type-z-equivalent; GA's wide ranges are the dominant signal that
  the ZIP belongs to that county. Same shape, different semantics.
- The closest-+4 loose fallback assumes both candidate counties
  legitimately serve the ZIP. In the synthetic-+4 case for a
  cross-border ZIP, the BORDER county's narrow ranges sit closer
  to e.g. 0001 than the DOMINANT county's narrow ranges, so
  distance picks the wrong county.
- A correct fix probably needs to use **row count** (how many
  boundaries that authority has for this ZIP) as the cross-county
  tiebreaker, falling back to distance only for intra-county
  city-vs-city (Norman/Moore) decisions.
- OR: keep wide-range type-4 in the precise set BUT mark them as
  "weak precise" so the merge filter prefers narrow precise over
  wide precise but still keeps wide as a signal that the authority
  claims the ZIP.

## Iter-61 attempt (also reverted)

Took the iter-60 lesson and added a row-count-aware loose fallback
(`_pick_loose_fallback`): cities still pick by closest +4 distance
(preserves OK Norman/Moore), counties pick by most type-4 rows
on the ZIP (intends to fix GA Roswell). Reverted in commit `d19d974`.

The fix worked for Casper 82601-0001 (5% -> 6%, with Casper city
correctly surfaced via the city loose fallback) but **still didn't
fix GA Roswell 30075-0001**. Trace:

1. Width filter excludes Fulton's wide-range type-4 row.
2. Cobb's narrow type-4 rows cover +4 0001 (border-spillover ranges).
3. precise_county_city_ids = {Cobb} -- non-empty, so the loose
   fallback gate (which requires `not precise_county_city_ids`)
   never runs.
4. Merge keeps Cobb (in precise) + drops Fulton-z (Fulton not in
   precise). Result: state + Cobb + TSPLOST = 6.75%, wrong.

**The actual blocker:** when Cobb's narrow type-4 rows cover the
synthetic +4 (which they do, by spillover), those become precise
matches. The width filter only addresses cases where Fulton's
wide row is the ONLY match -- it doesn't help when narrow rows
from a non-dominant county fire too. The pre-fix behavior worked
because Fulton's wide row was ALSO precise and won by row-count
dedup against Cobb's narrows, but excluding Fulton's wide leaves
Cobb alone in precise.

A correct fix probably needs to ALSO change the merge filter:
when a wide-range type-4 row exists for some county, treat that
county as a "z-equivalent claimant" that competes for the type-z
fallback dedup -- even when narrow-range matches from another
county are in precise. That's a meaningfully more invasive change
than what's been tried so far.

## Iter-62 resolution

The third attempt finally landed. The lessons from the two reverts
were necessary -- they shaped the design that worked.

**Empirical analysis (2026-05-08).** Inspecting the type-z vs type-4
split for each canonical case revealed the actual structure:

| ZIP | Authority | type-z rows | type-4 rows |
|---|---|---:|---:|
| 73034 (Edmond OK) | Oklahoma County | 0 | 533 |
| 73034 | Edmond city | 0 | 475 |
| 73034 | Logan County | 0 | 279 |
| 30075 (Roswell GA) | Fulton County | 0 | 107 |
| 30075 | Cobb County | **1** | 18 |
| 82601 (Casper WY) | Natrona County | **1** | 1233 |
| 82601 | Casper city | **0** | 616 |

The pattern: **Casper has 616 narrow type-4 ranges and ZERO type-z
records**, while Natrona has both. For a synthetic +4 like 0001:

1. Precise picks Natrona via Natrona's wide-range type-4 (0000-0999).
2. Merge filter drops every type-z that isn't in precise -- but
   Casper has NO type-z to drop. Casper simply never enters the
   pipeline.
3. Loose-fallback gate fails (Natrona IS in z), so the loose path
   that picks Casper by row-count never fires.

The loose lookup (no +4) correctly picks Casper because it
considers every type-4 row regardless of +4 coverage and uses
row-count dominance. The strict lookup with +4 needs the same
signal -- but only when no narrow type-4 row covered the +4.

**The fix.** After precise + z + loose all resolve and BEFORE merge,
check whether any city ended up in precise or z. If not AND no
narrow (< 1000 +4s wide) type-4 row covered the +4, query the
ZIP's dominant city by total type-4 row count and append it to
precise. Three properties matter:

- **Soft-add only when needed.** ZIPs where precise + z + loose
  already provide a city skip the soft-add entirely.
- **Gated on `not has_narrow_precise`.** Real unincorporated +4s
  (Natrona 2401-2402 narrow rows) keep their state+county-only
  stack. Only synthetic +4s (covered solely by wide-range rows)
  reach the dominant-city lookup.
- **Cross-county isolation.** GA Roswell 30075 has no city
  authority at all; the soft-add no-ops; Cobb's narrow type-4
  rows are still the wrong precise pick but that's a county
  decision, separate from city dominance.

**Verified across the canonical cases (commit `d68c023`):**

| Case | Pre-fix | Post-fix | Matches |
|---|---:|---:|---|
| WY Casper 82601-0001 (synthetic) | 5.0% | **6.0%** | loose-lookup parity |
| WY Casper 82601-2401 (real unincorporated) | 5.0% | 5.0% | unchanged |
| WY Casper 82601-3504 (real in-Casper) | 6.0% | 6.0% | unchanged |
| GA Roswell 30075-0001 (cross-county) | 7.75% | 7.75% | unchanged |
| OK Edmond 73034-1234 (cross-county) | 9.0% | 9.0% | unchanged |
| WY Cheyenne 82001-3504 | 5.0% | 5.0% | unchanged |

Full live DOR grid: **389/389 green** (387 prior + Casper synthetic
+4 + Roswell synthetic +4 regression-pin).
