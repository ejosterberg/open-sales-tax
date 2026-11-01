# State audit — PA — 2026-11-01 (full-sweep)

## TL;DR
- **PA: UNCHANGED.** Statewide 6.0% + Allegheny County 1.0% + Philadelphia 2.0% combined-rate structure confirmed; no other PA county or municipality levies a local sales tax. Prod returns 8.000% in Philadelphia, 7.000% in Pittsburgh, 6.000% everywhere else probed. Non-SST, self-seeded.

## Source
- Pennsylvania Dept. of Revenue "Sales, Use & Hotel Occupancy Tax" (`revenue.pa.gov/.../Sales-Use-and-Hotel-Occupancy-Tax.aspx`); 72 P.S. § 7202(a) (state 6%), § 7202(b) (Philadelphia 2%, raised from 1% effective 2009-10-08), and 61 Pa. Code § 60.16. Allegheny County 1% enacted by county ordinance 1994.
- No 2025–2026 General Assembly amendment to § 7202.

## Prod state (read-only)
- `data_versions` for PA: SST `PA-SST-V0.31-STATEWIDE` (2026-05-04) + ZCTA (2026-05-11). Rates loaded from the self-seeded `PA_COUNTY_RATE_PCT` dict.
- No PA SST file cached under `/var/lib/opensalestax/data/` (self-seeded).

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 19102 | Philadelphia (center) | 8.000 | 8.000 | 0.00 |
| 19106 | Philadelphia (Old City) | 8.000 | 8.000 | 0.00 |
| 15222 | Pittsburgh (downtown) | 7.000 | 7.000 | 0.00 |
| 15213 | Pittsburgh (Oakland) | 7.000 | 7.000 | 0.00 |
| 16801 | State College | 6.000 | 6.000 | 0.00 |
| 18102 | Allentown | 6.000 | 6.000 | 0.00 |
| 17101 | Harrisburg | 6.000 | 6.000 | 0.00 |

## Followup: Allegheny suburban ZIPs
- Module docstring still names "a future ratchet should expand to ZIPs in Allegheny County beyond the City of Pittsburgh proper (Monroeville, Bethel Park, McKeesport)". Those ZIPs correctly bind to Allegheny County via ZCTA, so bare-ZIP lookups return 7.000% today; the "ratchet" is really about adding friendly cities. Not a defect — tracked only.

## Recommended action
- **None.** Keep monitoring the Pennsylvania DOR tax-update page quarterly.
