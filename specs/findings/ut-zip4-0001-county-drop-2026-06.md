# Finding: UT `-0001` placeholder ZIP+4 drops county binding for some ZIPs

**Discovered:** 2026-06-29 (buffer-day catch-up audit, day-23 pair UT)
**Severity:** Low real-world impact / medium test-grid impact
**Status:** Open — needs investigation, not auto-fixed
**State:** UT (Utah, SST member)

## Summary

For a handful of Utah ZIP5s, calling `/v1/calculate` with the
**synthetic `-0001` ZIP+4 placeholder** drops the **county**
jurisdiction from the result, under-collecting by the county rate.
The same ZIP5 with **no ZIP+4**, or with **any other ZIP+4**,
returns the correct combined rate. Real-world callers are therefore
almost always unaffected — but two DOR-validation pins that use the
`-0001` convention now mismatch the engine.

## Evidence (live engine, 2026-06-29)

| Address | rate | jurisdictions returned |
|---|---|---|
| Provo `84601` (no +4) | **7.450%** ✓ | Utah County, Provo, Utah |
| Provo `84601-9999` (fake +4) | **7.450%** ✓ | Utah County, Provo, Utah |
| Provo `84601-2802` (real +4) | **7.450%** ✓ | Utah County, Provo, Utah |
| **Provo `84601-0001`** | **4.950%** ✗ | Provo, Utah — **Utah County (2.5%) dropped** |
| St George `84770` (no +4) | **6.750%** ✓ | Washington County, St. George, Utah |
| **St George `84770-0001`** | **5.150%** ✗ | St. George, Utah — **Washington County (1.6%) dropped** |
| Clearfield `84015` (no +4) | **7.250%** ✓ | Davis County, Clearfield, Utah |
| **Clearfield `84015-0001`** | **4.950%** ✗ | Clearfield, Utah — **Davis County (2.5%) dropped** |

Not all UT ZIPs exhibit it — `-0001` resolves correctly for
Sandy `84070-0001` (7.45%), Orem `84057-0001` (7.45%), Logan
`84321-0001` (7.30%), and SLC `84101-3020`/`84111-2202` (8.45%).
So the bug is **per-ZIP**, depending on whether an actual `0001`
ZIP+4 micro-boundary exists for that ZIP5 in the loaded data and
how that boundary is bound (city-only vs city+county).

## Likely root cause (to confirm)

When an exact ZIP+4 boundary row exists for `<zip5>-0001`, the
lookup engine prefers that precise match over the ZIP5-level
fallback. For the affected ZIPs, the `0001` micro-boundary is
bound to the **city authority only** and not the parent county,
so the precise-match path returns city + state but omits the
county. The ZIP5 fallback (used when no exact +4 matches, e.g.
`-9999`) correctly stacks city + county + state.

This is plausibly an artifact of the **iter-226..230 UT Census
Gazetteer buildout** (UT `*_names` / authority rows grew 21 → 120),
which may have introduced `0001`-suffixed rows, OR a long-standing
SST boundary-file quirk that only now surfaces because these two
cities became DOR-grid pins. Note prod is still running
`UTR2026Q2MAR20` / `UTB2026Q2MAR20` (one quarter behind — see the
Q3 refresh chip); confirm whether the Q3 load changes the behavior.

## Investigation steps

1. On prod, inspect the boundary rows for the affected ZIPs:
   ```bash
   ssh opensalestax-01 "docker exec open-sales-tax-postgres-1 \
     psql -U opensalestax opensalestax -c \
     \"SELECT b.zip5, b.zip4_lo, b.zip4_hi, a.name, a.authority_type \
       FROM zip_boundaries b JOIN tax_authorities a ON a.id=b.authority_id \
       WHERE b.zip5 IN ('84601','84770','84015') ORDER BY b.zip5, b.zip4_lo;\""
   ```
   (Adjust table/column names to the actual schema.) Look for a
   `0001`-anchored row bound only to the city authority.
2. Compare against a ZIP that resolves correctly with `-0001`
   (e.g. `84070` Sandy) to see what's structurally different.
3. Decide the fix location:
   - **Engine**: when an exact ZIP+4 boundary is found but it is a
     city-only authority, still stack the parent county for that
     ZIP5 (county is geographically inclusive of all +4 ranges).
     This is the more correct general fix.
   - **Loader**: ensure `0001` micro-boundaries inherit the county
     binding when emitted.
4. Re-verify the 6 affected probes above all return the
   no-+4 rate.

## Impact on the test grid

`tests/integration/test_sst_dor_validation.py` `DOR_GRID` has two
UT pins using the `-0001` convention that **currently fail** under
`pytest -m liveapi`:

- `("UT", "Provo", "84601", "0001", "7.450", ...)` → engine 4.950
- `("UT", "St George", "84770", "0001", "6.750", ...)` → engine 5.150

Do **not** simply change these pins to a real ZIP+4 to make them
pass — that would mask the underlying resolution asymmetry. Resolve
the engine/loader behavior first, then the `-0001` pins pass as-is
(consistent with how `-0001` already works for Sandy/Orem/SLC).
These live pins do not gate normal CI (they require the `liveapi`
marker), so they are not currently breaking the build.

## Related

- [[sst-source-file-quirks]] — cross-state SST CSV column conventions
- UT buildout history: handoff "Overnight 2026-05-19" (iter-226..230)
