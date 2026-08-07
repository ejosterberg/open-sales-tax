# GA Madison County local rate cut 4% → 3% — engine over-collects (2026-08-06)

**Status:** Confirmed drift. Fix = GA SST quarterly refresh to 2026Q3
(chipped). Regression pin added to the DOR grid.

## Summary

Madison County, Georgia **decreased its local sales tax by 1.0%**
(4% → 3%) effective **2026-07-01**. The production engine is still
loaded from `GAR2026Q2FEB19.csv` (fetched 2026-05-04), whose Madison
row is open-ended at 4%. As a result the engine has **over-collected
1.0% on every Madison County transaction since 2026-07-01** (~37 days
as of this audit).

Combined rate: engine returns **8.000%**, GA DOR publishes **7.000%**.

## Authoritative confirmation

1. **SST quarterly rate file `GAR2026Q3JUN05.csv`** (jurisdiction type
   `00` = county, code `195` = Madison County) carries the change as a
   clean close-out + successor pair:

   ```
   13,00,195,0.03,0.03,0.03,0.03,20110101,20220331
   13,00,195,0.04,0.04,0.04,0.04,20220401,20260630   <- closed
   13,00,195,0.03,0.03,0.03,0.03,20260701,29991231   <- new
   ```

   The Q2 file prod is running has instead a single open-ended row
   `13,00,195,0.04,...,20220401,29991231`.

2. **GA DOR "Georgia Sales and Use Tax Rate Chart", effective July 1,
   2026** (https://dor.georgia.gov/sales-tax-rates-general) — row
   `095 Madison 7 L E S`, i.e. combined 7% (state 4% + local 3%).
   Note GA DOR's own jurisdiction code (`095`) differs from the
   SST/FIPS county code (`195`); both denote Madison County.

3. Independent trade reporting confirms GA DOR issued a bulletin
   announcing a Madison County rate change effective July 1, 2026.

## Live-engine evidence (2026-08-06)

All six Madison County ZIPs probed return 8.000%:

| ZIP | City | Engine | GA DOR Q3 | Delta |
|---|---|---:|---:|---:|
| 30633 | Danielsville | 8.000 | 7.000 | **+1.000** |
| 30629 | Comer | 8.000 | 7.000 | **+1.000** |
| 30646 | Hull | 8.000 | 7.000 | **+1.000** |
| 30647 | Ila | 8.000 | 7.000 | **+1.000** |
| 30628 | Colbert | 8.000 | 7.000 | **+1.000** |
| 30627 | Carlton | 8.000 | 7.000 | **+1.000** |

Jurisdiction breakdown for 30633 shows `Madison County / county /
4.00000` — confirming the stale county row is the sole cause, not a
boundary or stacking defect.

## Scope — this is the ONLY GA change in Q3

A full row-level diff of `GAR2026Q2FEB19.csv` (449 rows) against
`GAR2026Q3JUN05.csv` (450 rows) yields exactly three changed rows, all
for code `195`. Every other GA jurisdiction is byte-identical between
the two quarters. The 11 existing GA pins in the DOR grid all still
match the live engine exactly, so no other GA rate is affected.

The boundary file also advanced (`GAB2026Q2FEB16.zip` →
`GAB2026Q3MAY19.zip`); that was not diffed here and should be picked up
in the same refresh.

## Why the engine did not catch this on its own

GA rates are sourced entirely from the SST quarterly file at load time
— there is no hand-maintained GA rate table to drift. The defect is
purely that prod has not ingested a new SST quarter since 2026-05-04.
Nothing in the code needs to change.

## Fix

Refresh the GA SST quarterly on prod and reload:

```bash
ssh opensalestax-01 "cd /home/ejosterberg/open-sales-tax && \
  docker exec open-sales-tax-api-1 python -m opensalestax data load -s GA -v 2026Q3JUN05"
```

(Chipped as "Refresh GA SST quarterly to 2026Q3" for Eric to apply —
per the daily-audit rule, SST files are not auto-pulled.)

The repo also carries a unit-test fixture copy at
`src/opensalestax/data/fixtures/ga/GAR2026Q2FEB19.csv`, referenced by
name in `tests/unit/test_state_georgia.py` (4 sites) and in
`src/opensalestax/states/georgia.py` docstrings ("449 rows"). Swapping
the fixture to the Q3 file is a follow-on edit that belongs with the
refresh, not with this audit.

## Regression guard added

`tests/integration/test_sst_dor_validation.py` — new DOR-grid pin
`GA / Danielsville (Madison County) / 30633-0001 / 7.000`. It is a
`liveapi` row, so it is excluded from CI (`pytest -m "not liveapi"`)
and will fail under `-m liveapi` until prod ingests the Q3 file —
matching the existing convention for AZ/NC/NY/HI pending-reload pins.

## Broader observation

GA is not alone. Comparing every cached SST file on prod against the
upstream directory listing, **16 of the 24 SST states are a quarter or
more behind** (AR, GA, KS, MN, NC, ND, NE, OK, SD, TN, UT, VT, WA, WI,
WV, WY). The remaining 8 (IA, IN, KY, MI, NJ, NV, OH, RI) are current —
SST hosts exactly one file per state and simply has not republished
those. Madison County is the first case where that lag has been shown
to produce a *wrong answer*, which makes the fleet-wide refresh more
urgent than the individual per-state chips suggest.
