# State audit — NY — 2026-11-01 (full-sweep)

## TL;DR
- **NY: UNCHANGED.** Pub 718 (2/25, effective 2025-03-01) is still the current rate table at `tax.ny.gov/pdf/publications/sales/pub718.pdf` (fetched 2026-11-01). No county's combined rate has changed since the last audit. All probed combined rates (NYC 8.875%, Westchester 8.375%, Yonkers 8.875%, Mount Vernon / New Rochelle / White Plains 8.375%, Buffalo 8.750%, Rochester 8.000%, Syracuse 8.000%, Albany 8.000%, Utica 8.750%) match Pub 718 exactly.

## Source
- NY DTF **Publication 718** (`tax.ny.gov/pdf/publications/sales/pub718.pdf`, revision 2/25, effective 2025-03-01) — pulled & parsed with `pypdf` on 2026-11-01. Boldface-italic "any items changed from the previous version" markings are **absent** on this revision (nothing changed since the Suffolk 8.625→8.750 correction landed in Pub 718 (3/24) and the Westchester county-base fix landed in-engine 2026-07-18).
- Statutes referenced in `ny_data.py`: N.Y. Tax Law §§ 1105 (state 4%), 1109 (MCTD 0.375%); clothing/footwear exemption § 1115(a)(30).

## Prod state (read-only)
- `data_versions` for NY: SST `NY-SST-V0.31-STATEWIDE` (2026-07-18) + ZCTA (2026-05-11). Rates loaded from the self-seeded `NY_COUNTY_RATE_PCT` + `NY_CITIES` dicts — SST is not the primary source for NY.
- No NY SST file cached under `/var/lib/opensalestax/data/` (self-seeded).

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Pub 718 (combined %) | Actual | Delta |
|---|---|---|---|---|
| 10001 | NYC (Manhattan) | 8.875 (8⅞) | 8.875 | 0.00 |
| 11201 | NYC (Brooklyn) | 8.875 (8⅞) | 8.875 | 0.00 |
| 10701 | Yonkers | 8.875 (8⅞) | 8.875 | 0.00 |
| 10601 | White Plains | 8.375 (8⅜) | 8.375 | 0.00 |
| 10550 | Mount Vernon | 8.375 (8⅜) | 8.375 | 0.00 |
| 10801 | New Rochelle | 8.375 (8⅜) | 8.375 | 0.00 |
| 14202 | Buffalo (Erie) | 8.750 (8¾) | 8.750 | 0.00 |
| 14604 | Rochester (Monroe) | 8.000 | 8.000 | 0.00 |
| 13202 | Syracuse (Onondaga) | 8.000 | 8.000 | 0.00 |
| 12207 | Albany | 8.000 | 8.000 | 0.00 |
| 13501 | Utica (Oneida) | 8.750 (8¾) | 8.750 | 0.00 |

## Notes
- The `*` footnote marker on Dutchess / Orange / Nassau / Suffolk / NYC / Westchester / Rockland / Rockland is the MCTD-inclusion flag, **not** a change marker.
- MCTD 0.375% is correctly surfaced as a separate district authority on all MCTD ZIPs in probes.

## Recommended action
- **None.** Keep monitoring Pub 718 quarterly (the next scheduled release lands as Pub 718-S if the Legislature enacts a mid-cycle local change).
