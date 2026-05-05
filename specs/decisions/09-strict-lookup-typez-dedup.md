# Decision 09: Strict ZIP+4 lookup needs type-z dedup on fallback

**Status:** RESOLVED in v0.45.0 (2026-05-05). Decision recorded
during iter 27, fix shipped same iter -- documented for future
maintainers as the "why" behind the strict-lookup dedup logic.

## Context

The v0.44 fix (TN code-63 skip + cross-county IMPROVE Act dedup)
applies inside ``lookup_jurisdictions_by_zip5_loose`` (the
loose ZIP-5-only lookup that ``calculate_tax`` uses when no
``zip4`` is supplied). All major TN cities now return correct
combined rates on ``POST /v1/calculate`` with ``{zip5: "..."}``
(no zip4).

**Strict lookup (``lookup_jurisdictions_by_zip``) still over-
collects** when the supplied zip4 doesn't match any real type-4
range and the lookup falls back to type-z bindings. The fallback
returns EVERY type-z authority for the ZIP without applying the
loose-lookup dedup, so synthetic test +4 values (e.g.
``37601-1234`` for Johnson City) yield 17.75% combined:

```
state    Tennessee            7.00%
city     TN-city-23500        2.75%   (Johnson City)
city     TN-city-75820        2.75%   (a neighboring city, also type-z bound to 37601)
county   Carter County        2.75%
county   Washington County    2.50%
                              -----
                              17.75%
```

The right behavior in the type-z fallback case is to apply the
same ``_pick_one_city_county_per_zip5`` + TN district dedup as
the loose lookup. The merge step in
``lookup_jurisdictions_by_zip`` doesn't currently do this.

## Why deferred

- Real-world ZIP+4s (the 308 entries already in the
  ``test_sst_dor_validation.py`` grid) hit precise type-4 matches
  and don't trigger the fallback path. Production traffic mostly
  supplies real +4s; the bug primarily affects synthetic test
  inputs and any address whose +4 isn't covered by the SST file.
- The fix needs careful design: the precise-type-4 path SHOULD
  return precise (sometimes multiple) authorities; only the
  type-z FALLBACK should dedup. Distinguishing those at merge
  time without breaking existing test coverage requires a small
  refactor.
- Iter 27 spent its budget shipping v0.44 + auditing other SST
  states (KS / OK / WA / NV) for the same TN pattern. None
  showed a similar bug, so the immediate user-facing risk is
  bounded to TN strict-lookup queries with non-real +4s.

## Workaround until fixed

- Use zip5-only queries (``POST /v1/calculate {address: {zip5:
  "XXXXX"}}``) for TN. Those go through the loose lookup which
  has the v0.44 dedup.
- Real zip4 values (matching the SST type-4 ranges) hit precise
  bindings and avoid the over-stack.

## How to apply when ready

1. Refactor ``lookup_jurisdictions_by_zip`` to detect when
   ``precise_county_city_ids`` is empty AND ``z_authorities``
   contains multiple cities or counties; in that case, route the
   z-fallback through ``_pick_one_city_county_per_zip5`` (passing
   the existing ``total_zip_counts`` query).
2. Apply the TN-specific district-dedup from the loose lookup
   (lines 364-388 of ``lookup.py``) to the merged-in districts.
3. Add a regression test: ``TN 37601-1234 -> 9.75%``.
4. Re-add the Johnson City row to
   ``tests/integration/test_sst_dor_validation.py`` once the
   strict path is fixed.
