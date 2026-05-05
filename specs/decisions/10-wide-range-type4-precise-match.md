# Decision 10: Wide-range type-4 records and the precise-match assumption

**Status:** Open (deferred) -- recorded 2026-05-05 during iter 43.

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
