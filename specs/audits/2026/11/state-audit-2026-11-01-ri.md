# State audit — RI — 2026-11-01 (full-sweep)

## TL;DR
- **RI: UNCHANGED.** Flat 7.0% statewide confirmed; no county or municipal sales taxes. SST pin `RIR2019Q2MAR27` / `RIB2019Q2MAR27` is still the only file published upstream (verified against SST rate+boundary listings 2026-11-01); this is intentional under SST's "no republish for stable single-rate states" convention, not a stale pin. Prod returns 7.000% at probed ZIPs.

## Source
- RI Division of Taxation (`tax.ri.gov`); R.I. Gen. Laws § 44-18-18: **7%**, in effect since **1990-07-01**. No sub-state sales tax rates. The 1% "state meals and beverage tax" (§ 44-18-18.1) and 5% "state hotel tax" are categorical and not touched here.
- SST rate index 2026-11-01 lists only `RIR2019Q2MAR27.csv`; SST boundary index lists only `RIB2019Q2MAR27.csv`. Prod matches.

## Prod state (read-only)
- `data_versions` for RI: SST `RI-SST-2019Q2MAR27` (2026-05-04) + ZCTA (2026-05-11).
- Cached under `/var/lib/opensalestax/data/`: `RIR2019Q2MAR27.csv`, `RIB2019Q2MAR27.csv`. **Both match the current upstream file.**

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 02903 | Providence | 7.000 | 7.000 | 0.00 |

## Legislation watch
- 2026 General Assembly: no change to § 44-18-18. Governor McKee's FY27 budget proposal does not raise or lower the rate.

## Recommended action
- **None.** Fully clean, confirmed 2026-09-28 and re-confirmed here.
