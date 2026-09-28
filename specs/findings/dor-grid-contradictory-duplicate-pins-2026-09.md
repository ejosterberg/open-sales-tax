# DOR_GRID contradictory duplicate pins — 11 ZIP+4s assert two different rates

**Found:** 2026-09-28, daily audit (day-21 RI + SC rotation).
**Status:** open. 1 of 12 fixed (the SC one, in scope that day); **11 remain**.
**Severity:** no live rate defect found. This is a **test-integrity** defect —
but it is the one that hides rate defects, and it is how the AZ
over-collections survived months of audits.

## The defect

`tests/integration/test_sst_dor_validation.py::DOR_GRID` has **790 rows over
774 distinct ZIP+4 keys**. Sixteen keys carry more than one row. Of those,
**11 carry rows that assert *contradictory* rates** for the same ZIP+4, so
**one of the two always fails** — whichever way the engine answers.

They have never been noticed because `DOR_GRID` is gated behind
`@pytest.mark.liveapi`, which CI deselects. The grid is only ever run by hand,
usually filtered to one state, so a contradiction in another state stays
invisible.

This is the check the 2026-09-05 AZ audit named as the project's
highest-value open item, and the 2026-09-21 FL audit ran ad hoc against
Florida only. This is the first sweep across all 52 jurisdictions.

## What the engine actually returns

Every one of the 11 was probed against the live engine on 2026-09-28. The
result is uniform:

**In all 11 cases the engine returns the HIGHER pin.** There is no case where
the engine returns the lower value, and none where it returns neither.

So the lower pins are **stale leftovers from before city-level coverage
landed** — most of them say so in their own citation text ("post-zip_county",
"iter-62 county expansion", "post-v0.29 ZCTA"). They recorded a county-only
engine and were never removed when the city stack was added.

## Primary-source verification

**California (7 of 11) — VERIFIED, engine correct.** CDTFA's own rate table
(rate schedule effective 2026-07-01) agrees with the engine on every one:

| ZIP | City | CDTFA | Engine | Stale low pin |
|---|---|---|---:|---:|
| 91501 | Burbank | **10.500%** | 10.500% | 9.500 |
| 92590 | Temecula | **8.750%** | 8.750% | 7.750 |
| 93401 | San Luis Obispo | **8.750%** | 8.750% | 8.250 |
| 94010 | Burlingame | **9.625%** | 9.625% | 9.375 |
| 94559 | Napa | **8.750%** | 8.750% | 7.750 |
| 94965 | Sausalito | **9.250%** | 9.250% | 8.250 |
| 95501 | Eureka | **10.250%** | 10.250% | 9.500 |

**Not yet verified (4 of 11)** — each needs its own primary source, and none
should be touched before that:

| ZIP | City | Pins | Engine | Source to check |
|---|---|---|---:|---|
| AK 99611 | Kenai | 3.000 / 6.000 | 6.000% | ARSSTC monthly xlsx — is the Kenai Peninsula Borough 3% suppressed inside Kenai city limits? The two pins encode **opposite answers to a real modeling question**, not a stale value. Resolve the question first. |
| NM 87124 | Rio Rancho | 7.6875 / 7.875 | 7.875% | NM TRD GRT location table. The higher pin says "iter-172 refresh from 7.687", so the lower one looks simply superseded. |
| TX 78602 | Bastrop | 6.250 / 8.250 | 8.250% | TX Comptroller city rate file |
| TX 78660 | Pflugerville | 6.250 / 8.250 | 8.250% | TX Comptroller city rate file |

## The trap to avoid when fixing this

**Engine-agrees-with-pin is not verification when the pin may have seeded the
engine.** Eight of the 11 higher pins cite **SalesTaxHandbook** — an
aggregator, forbidden as a rate source by constitution §2. If an aggregator
number seeded both the state module and its pin, the two agree while both are
wrong, and the grid reports green. That is exactly what happened in Arizona:
the 2026-09-05 audit found five live over-collections precisely because the
pins had been derived from the same bad data they were supposed to be checking.

California came out clean here **only because CDTFA was consulted
independently** — not because the engine and the pin agreed.

## Recommended fix, in order

1. **CA (7) — safe now.** Delete the 7 stale lower pins. Verified above
   against CDTFA; the engine and the surviving pins both match.
2. **NM (1) — near-certain.** Confirm against the NM TRD location table, then
   delete the superseded 7.6875 pin.
3. **TX (2) — verify first.** Check Bastrop and Pflugerville against the TX
   Comptroller rate file, then delete whichever pin contradicts it.
4. **AK (1) — decide, don't delete.** This is a genuine
   borough-suppressed-inside-city modeling question. Settle it against the
   ARSSTC sheet and record the answer; the loser becomes a comment, not a
   silent deletion.
5. **Re-cite the 226 aggregator-sourced pins.** `DOR_GRID` has **226 of 790
   rows (29%)** citing SalesTaxHandbook / Avalara / TaxJar: CA 159, TX 24,
   AL 17, AZ 8, FL 7, MO 4, WY 3, OK 2, SC 2 (SC's two were re-cited to the
   ST-500 on 2026-09-28). This is the same population as the ~130 `src/` hits
   already tracked in the aggregator-sourced-rate-errors note — the pins were
   never counted.

## The durable fix — an offline CI-time consistency test

All of the above is cleanup. The reason it accumulated is that **nothing runs
offline**. Add a unit test (no network, so CI runs it) asserting:

- **no two `DOR_GRID` rows for the same `(state, zip5, zip4)` disagree on the
  expected rate** — this finding, permanently;
- every expected rate is **reproducible from the state module's own rate
  tables** plus the ZIP→county bindings, the check run ad hoc against FL on
  2026-09-21 (29 pins, 0 contradictions) and against SC on 2026-09-28;
- **no citation matches** `salestaxhandbook|avalara|taxjar|taxcloud`, so
  constitution §2 is enforced mechanically rather than by reviewer memory.

The first of those three is ~15 lines and would have caught all 12 of these
the day each landed. It is the highest-value unwritten test in the project.

## Also noted — 5 redundant (non-contradictory) duplicates

Same ZIP+4, same rate, harmless but worth collapsing:
AL 35630, AL 36830, GA 30075, GA 31901, MS 39201.
