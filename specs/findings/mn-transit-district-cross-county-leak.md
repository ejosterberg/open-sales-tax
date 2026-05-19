# Finding: MN transit district authorities have cross-county ZIP bindings

**Discovered:** iter-211 (2026-05-19), during autonomous-loop MN
hand-curation reconnaissance.

**Severity:** Medium — incorrect rate stack returned for many MN ZIPs.
Over-collection on the order of 0.3-0.6% for affected ZIPs.

**Scope:** At least 6 MN transit district authorities have
incorrect boundary→ZIP bindings spanning ZIP prefixes outside
the county the district name claims.

## Evidence

`tax_authorities`+`boundaries` query against the prod DB:

| Authority (district) | ZIPs bound | ZIP prefixes | Expected prefix |
|---|---|---|---|
| Anoka County Transportation Sales Tax | 44 | 553, **563** | 553xx only |
| Cook County Transportation Sales Tax | 20 | **553, 563** | 556xx only |
| St. Louis County Transportation Sales Tax | 21 | **566, 567** | 557xx, 558xx |
| Beltrami County Transportation Sales Tax | 6 | 556 | 566xx (Bemidji area) |
| Washington County Transportation Sales Tax | 14 | 559 | 550xx (east metro) |
| Metro Area Transportation Sales Tax | 264 | 550, 551, 553, 554, 555, 560 | 550-554 only |

(Bolded prefixes are clearly outside the county the district claims.)

## Concrete impact (live engine probes against api.opensalestax.org)

ZIP 56310 (Avon, Stearns Co — not Anoka Co):
```
state MN     6.875%
county Stearns 0.25%
city Avon (MN-city-03070) 0.50%
district Anoka County Transportation Sales Tax 0.375%   ← WRONG
combined 8.000%
```

ZIP 56630 (Blackduck, Beltrami Co — not St. Louis Co):
```
state MN     6.875%
county Beltrami 0.50%
city (MN-city-06256) 0.50%
district St. Louis County Transportation Sales Tax 0.625%   ← WRONG
combined 8.50%
```

## Hypothesis

The MN data loader is likely binding district boundaries by
indexing the wrong column from the SST type-63 rows (or
applying a stale state-default-bind to district boundaries that
should be county-scoped). Each affected district appears to
have ~14-44 stray ZIPs, suggesting a small number of bad rows
rather than a wholesale bug.

The COUNTY-level authorities (e.g. "Beltrami County 0.50%") are
bound correctly — only `district`-type authorities are affected.

## What to investigate

1. Find the loader code that creates type-63 (district) authority
   bindings in `src/opensalestax/states/minnesota.py` or whichever
   module handles MN type-63 rows.
2. Compare against type-01 (county) handling — counties bind
   correctly so the working code path is right there.
3. Re-run the live ZIP probes above after the fix; combined
   rates should drop to the correct values:
   - ZIP 56310 → 7.625% (no Anoka stack)
   - ZIP 56630 → 7.875% (no St. Louis stack)
4. Pin a regression test under `tests/unit/test_state_minnesota.py`:
   ```python
   def test_mn_district_no_cross_county_leak():
       # Avon ZIP 56310 must NOT include Anoka County district
       result = lookup("56310")
       authority_names = {j.name for j in result.jurisdictions}
       assert "Anoka County Transportation Sales Tax" not in authority_names
   ```

## Out of scope for this finding

- Hand-labelling the 65+ MN city placeholders (deferred until
  the district bug is fixed — the rate-mismatch noise from the
  district leak would mask label-vs-rate verification).
- Investigating whether OTHER states have similar district leaks
  (worth a 1-hour audit by running the same prefix-vs-name check
  for KS / IA / WI / TN special-purpose districts).

## Cross-references

- Engine probe: `curl https://api.opensalestax.org/v1/rates?zip5=56310`
- Loader entry point: `src/opensalestax/states/minnesota.py`
- DB query that surfaced the issue (run on opensalestax-01):
  ```sql
  SELECT ta.name, COUNT(DISTINCT b.zip5),
         STRING_AGG(DISTINCT SUBSTRING(b.zip5,1,3), ',' ORDER BY SUBSTRING(b.zip5,1,3))
  FROM tax_authorities ta
    JOIN states s ON s.id = ta.state_id
    JOIN boundaries b ON b.authority_id = ta.id
  WHERE s.abbrev = 'MN' AND ta.name LIKE '%Transportation%'
  GROUP BY ta.id, ta.name
  ORDER BY ta.name;
  ```
