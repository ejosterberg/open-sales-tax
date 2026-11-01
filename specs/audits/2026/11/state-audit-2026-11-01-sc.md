# Full-sweep state audit — SC — 2026-11-01

## TL;DR

- **SC is self-seeded from SC DOR Form ST-500** (prod version label
  `SC-SST-2026Q2APR15` is a self-seeded loader label — SST publishes no
  per-SC rate/boundary file; verified by SST file-index scrape this
  run). Latest `sc_data.py` build cites **ST-500 Rev. 3/9/2026, eff
  May 1, 2026**, re-verified against the live DOR page by the 2026-09-28
  daily audit (46/46 counties + Myrtle Beach exact).
- **No new drift since 2026-09-28.** SC local-tax changes are
  referendum-driven and by statute take effect on **May 1** following a
  November vote, so the next expected movement is **May 2027**. The
  2026-11-04 ballot cycle is still ahead; its results are a **spring
  audit (May 2027) action item**, not an immediate one.
- **Live engine probes match ST-500 exactly** at the three tier-1
  verification sites (Columbia, Myrtle Beach, Rock Hill).
- **No commit from this audit on SC.** No code change.
- **Open item from 2026-09-28 still unresolved** (project-wide, not
  SC-specific): the offline `DOR_GRID` consistency CI test. Not in
  scope for this audit.

## Prod data version

```
SC | sst              | SC-SST-2026Q2APR15 | 2026-05-11
SC | zcta-census-2020 | SC-ZCTA-2020       | 2026-05-11
```

The `sst` source label is a convention; **SC is not an SST file source**
(SST publishes no SCR / SCB files, confirmed in today's directory
listing). The SC loader reads from `sc_data.py` + an internal fixture.

## SST file-index check (2026-11-01)

Directory listings for `/ratesandboundry/Rates/` and `/Boundary/` show
no files beginning with `SC`. SC thus **cannot** be stale against SST
upstream — it has no upstream file.

## SC DOR ST-500 re-verification

The 2026-09-28 audit ran a full 46-county + Myrtle Beach diff against
the live ST-500 PDF (Rev. 3/9/2026, eff 2026-05-01) and found 46/46
exact. SC DOR has not republished the chart since, per that audit's
note. This full-sweep run spot-checked three tier-1 sites and found all
three correct — consistent with no republication.

## Live engine probes (bare ZIP, `/v1/rates`)

| ZIP | City (county) | Engine | ST-500 expected | Delta |
|---|---|---|---|---|
| 29201 | Columbia (Richland) | 8.000 (6 + Richland 2) | 8.000 | 0.00 ✓ |
| 29577 | Myrtle Beach (Horry) | 9.000 (6 + Horry 2 + MB 1) | 9.000 | 0.00 ✓ |
| 29730 | Rock Hill (York) | 7.000 (6 + York CP 1) | 7.000 | 0.00 ✓ |

## November 2026 referendum watch

SC counties routinely place CP/ECI/TT referenda on the November ballot;
any that pass take effect **2027-05-01**. The May 2027 audit is the
right place to re-sweep. Chip for the spring 2027 daily rotation.

## Status

- **UNCHANGED** — fully clean against the authoritative ST-500 chart.
- **No code change** this audit.
