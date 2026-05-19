# Finding: SST district code mappings may be wrong (RETRACTED → REFRAMED)

**Original claim (iter-211):** MN transit district authorities have
cross-county ZIP bindings caused by a loader bug.

**RETRACTED in iter-215 (2026-05-19, same session):** Source-CSV
inspection shows the loader is NOT misreading columns. The SST
file's MN boundary CSV binds code 80001 ONLY to 563xx ZIPs
(Stearns/Benton — St. Cloud area), NOT to any 556xx ZIPs (Cook
County's actual prefix). But our `mn_names.py` maps 80001 →
"Cook County Transportation Sales Tax". That's the inconsistency:
**either `mn_names.py`'s label is wrong, OR the SST file is using
a code-numbering convention that we mis-inferred when curating
the friendly-name table.**

For IA, the picture is different: ZIP 50001 (Ackworth, primary
Warren County per Census ZCTA) has SST rows saying county_fips=181
(Union County) and district=98181 (Union LOST). The engine merges
Census ZCTA (Warren) + SST binding (Union LOST), producing a
disagreeing stack. That's a county-identification-source-mismatch
issue, not a loader bug.

**Severity:** Still medium (the rate stacks ARE wrong on the
affected ZIPs — about 0.5-1% over-collection) but the FIX is
different from what iter-211/212/214 originally proposed.

**Discovered:** iter-211 (2026-05-19), during autonomous-loop MN
hand-curation reconnaissance.

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

## Cross-state pattern (iter-214 update)

**This is not just an MN bug.** A second-pass audit found the same
cross-county district-binding pattern in IA and NC. Likely a
generic SST loader bug, not specific to any one state's code path.

### Iowa: "<County> Local Option Sales Tax" district leak

22+ IA "Local Option Sales Tax" district authorities have boundaries
spanning ZIP prefixes outside their county. Examples (each row =
one IA district, observed ZIP prefixes vs the county's actual
prefix span):

| District | ZIPs | Observed prefixes | County actually in |
|---|---|---|---|
| Adair County LOST | 16 | 500, 501, 502, 508 | 500xx / 508xx |
| Carroll County LOST | 19 | 500, 514 | 514xx |
| Iowa County LOST | 24 | 501, 522, 523 | 522xx |
| Polk County LOST | 52 | 500, 501, 502, 503, 509 | 500xx-503xx (Des Moines metro) |
| Story County LOST | 25 | 500, 501, 502 | 500xx (Ames) |

Concrete impact: **ZIP 50001 (Ackworth, Warren Co)** wrongly stacks
"Union County Local Option Sales Tax 1.00%" — returns 7.000%
combined when it should be 6.000% (state only, since Warren Co
itself has 0.00%). **Per-transaction over-collection: 1%.**

### North Carolina: county transit district leak

3+ NC county Public Transportation Sales Tax districts have ZIPs
bound outside their actual county. Example:

- **ZIP 27915 (Avon, Dare Co — Outer Banks)** wrongly stacks
  "Durham County Public Transportation Sales Tax 0.50%" — returns
  7.25% combined when it should be 6.75% (state 4.75 + Dare 2.00).
  **Per-transaction over-collection: 0.5%.** Dare County is ~150
  miles east of Durham.

### Hypothesis revision

The pattern is consistent enough across MN / IA / NC that the bug
is almost certainly NOT in any individual state module. Look in
the shared loader path or shared boundary-record processing.
Candidates:

1. **`_sst_base.parse_boundaries`** or the equivalent shared
   `_authority_bindings` logic — if `record.district_code` is
   being read from the wrong column for some record types, every
   state would inherit the leak.
2. **`parse_boundary_csv` in `opensalestax/data/sst_csv.py`** —
   column offset bug specific to certain SST record types.
3. **The dedup/seen filter** — if `key` tuples collide for
   different (state, authority) pairs, distinct districts could
   collapse onto each other's ZIPs.

## What to investigate (revised)

1. Pick a single concrete repro (ZIP 56301 Stearns Co + Anoka
   district is the cleanest) and trace the binding from the SST
   source CSV row → loader → DB. The leak entry point will be in
   the chain.
2. Counties bind correctly across all states, so compare
   county-binding code path vs district-binding code path looking
   for the asymmetry.
3. Re-run the live ZIP probes after the fix; combined rates
   should drop to the correct values:
   - ZIP 56310 → 7.625% (no Anoka stack)
   - ZIP 56630 → 7.875% (no St. Louis stack)
   - ZIP 50001 → 6.000% (no Union LOST stack)
   - ZIP 27915 → 6.75% (no Durham transit stack)
4. The xfail regression in `tests/integration/test_sst_dor_validation.py`
   (iter-212) covers 4 rows -- extend with IA + NC cases once the
   pattern is confirmed.

## Out of scope for this finding

- Hand-labelling the 65+ MN city placeholders (deferred until
  the district bug is fixed — the rate-mismatch noise from the
  district leak would mask label-vs-rate verification).
- Full audit of WI / OK / KS / TN / GA / IL districts. The MN /
  IA / NC evidence is enough to confirm a generic bug; a per-state
  exhaustive scan can wait until the root cause is identified
  (it'll go away across the board once the shared bug is fixed).

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

## iter-215 update: source-CSV inspection results (REVISED iter-218)

> **iter-218 correction**: The initial scan in iter-215 only looked
> at `cols[30]` (the first triplet position). SST boundary rows can
> carry multiple district codes in repeating triplets at stride 3
> starting at col 29. After fixing the audit script to walk all
> triplet positions, the actual code → prefix coverage is broader
> than originally reported. The corrected scan results are below.

Inspecting `/var/lib/opensalestax/data/MNB2026Q2FEB18.zip` directly
on the production VM (currently-active records only):

```
Code 80001 binds to ZIP prefixes: ['553','563']     ← Anoka + Stearns
Code 80003 binds to ZIP prefixes: ['556']           ← (Brainerd area?)
Code 80004 binds to ZIP prefixes: ['551','553','554','555']  ← Hennepin (likely correct)
Code 80005 binds to ZIP prefixes: ['563','564']     ← Stearns + Mille Lacs
Code 80006 binds to ZIP prefixes: ['557','558']     ← Carlton/Duluth
Code 80008 binds to ZIP prefixes: ['550','551','553','554','555','560']  ← Metro Area
Code 80009 binds to ZIP prefixes: ['550','551','553','554','555','560']  ← Metro Area
Code 80011 binds to ZIP prefixes: ['566','567']     ← Bemidji area
Code 80012 binds to ZIP prefixes: ['553','563']     ← same as 80001
Code 80013 binds to ZIP prefixes: ['559']           ← east-metro / Washington
```

**Notable**: codes 80001 and 80012 bind to the EXACT same ZIP prefix
set (553 + 563). Strongly suggests they're a sales/use tax pair
(or duplicate row format) for the SAME underlying tax. The current
`mn_names.py` labels them as TWO DIFFERENT counties' transportation
taxes (Cook + Anoka) — that's incoherent for codes that share
identical geography.

Codes 80008 + 80009 also share identical geography (550-555 + 560)
which makes sense — those ARE two distinct taxes (Metro Area
Transportation + Metro Area Housing) applied uniformly across the
7-county metro. Same geography is legitimate for that pair.

Compare to `mn_names.py`'s mapping:

| Code | mn_names.py says | SST file shows it on | Likely correct name |
|---|---|---|---|
| 80001 | Cook County Transportation Sales Tax | 563xx (Stearns) | St. Cloud Area Sales Tax? |
| 80003 | Beltrami County Transportation Sales Tax | 556xx | (matches Beltrami?) |
| 80004 | Hennepin County Transit Sales Tax | 551/553/554/555 | Hennepin Co Transit ✓ |
| 80011 | St. Louis County Transportation Sales Tax | 566/567 | Bemidji area? |
| 80012 | Anoka County Transportation Sales Tax | 553+563 | unclear |

**The loader is fine.** It's reading the right columns. Our
`mn_names.py` curated mappings were inferred from limited
evidence (the iter-83 timeframe) and several entries don't match
the SST file's actual code-to-region binding.

For IA, ZIP 50001 (Ackworth) has SST rows with:
- county_fips = 181 (Union County, per IA FIPS)
- district_code = 98181 (Union County LOST per ia_names.py)
- effective_to = 29991231 (active, not historical)

But Census ZCTA says ZIP 50001 is Warren County. This is a
disagreement between IA's SST quarterly boundary file and the
Census ZCTA cross-walk we use for `zip_in_state` / county fallback.
The engine ends up returning Warren County (from Census) AND
Union LOST (from SST), which is internally inconsistent.

## What this means for the xfail tests in iter-212 + iter-214

The xfail tests assert that certain "leaked" district names don't
appear in the response. They will START PASSING (xpass) two ways:

1. **mn_names.py / ia_names.py / nc_names.py corrected** —
   the friendly names update, and "Cook County Transportation
   Sales Tax" no longer appears at ZIP 56301 because we relabeled
   80001 properly. The numeric binding stays the same; only the
   string changes. Most likely outcome.
2. **Loader / data-source resolution change** — we filter
   district bindings to match the county-identification of the
   ZIP (Census ZCTA). The numeric binding goes away too. More
   invasive but more correct.

Either resolution flips the xfail to xpass. The test names should
probably be renamed from `*_district_leak` to something more
neutral like `*_district_label_match` when one of the fixes lands.
