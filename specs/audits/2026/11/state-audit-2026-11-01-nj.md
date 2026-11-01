# State audit — NJ — 2026-11-01 (full-sweep)

## TL;DR
- **NJ: UNCHANGED.** Flat 6.625% statewide confirmed; no county sales tax. Urban Enterprise Zone 3.3125% half-rate and Salem County 3.5% half-rate are categorical / zone-specific and not modeled at ZIP level. Prod returns 6.625% at probed ZIPs. SST pin `NJR2018Q1OCT16` / `NJB2019Q2MAR27` is still the newest file published upstream (verified live against SST rate+boundary listings 2026-11-01).

## Source
- NJ Division of Taxation (`nj.gov/treasury/taxation`); N.J.S.A. 54:32B-3(a): **6.625%**, effective **2018-01-01** (reduced from 6.875% by Chapter 48, L. 2016 §19). Reduced-rate Urban Enterprise Zones and Salem County half-rate (3.5%) are statutory carve-outs out of scope for the general-rate module.
- SST rate index 2026-11-01 lists `NJR2018Q1OCT16.zip` as the current file; SST boundary index lists `NJB2019Q2MAR27.csv`. Prod matches exactly.

## Prod state (read-only)
- `data_versions` for NJ: SST `NJ-SST-2018Q1OCT16` (2026-05-04) + ZCTA (2026-05-11). Rates loaded from the SST file.
- Cached under `/var/lib/opensalestax/data/`: `NJR2018Q1OCT16.zip`, `NJB2019Q2MAR27.csv`. **Both match the current upstream file.**

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 07001 | Avenel | 6.625 | 6.625 | 0.00 |
| 07102 | Newark | 6.625 | 6.625 | 0.00 |
| 07302 | Jersey City | 6.625 | 6.625 | 0.00 |
| 08540 | Princeton | 6.625 | 6.625 | 0.00 |
| 08608 | Trenton | 6.625 | 6.625 | 0.00 |
| 08901 | New Brunswick | 6.625 | 6.625 | 0.00 |
| 08102 | Camden | 6.625 | 6.625 | 0.00 |

## Legislation watch
- 2026 Legislature: no sales-rate change passed. The periodic push to restore 7.0% (last introduced as A4293 in 2024) did not advance. Nothing pending for 2027-01-01.

## Recommended action
- **None.** The newest SST file for NJ is already loaded; no refresh is owed. Flat 6.625% matches primary source.
