# State audit — MD — 2026-11-01 (full-sweep)

## TL;DR
- **MD: UNCHANGED.** Flat 6.0% statewide confirmed; no county or municipal sales taxes anywhere in Maryland. Prod returns 6.000% at probed ZIPs. Non-SST, self-seeded.

## Source
- Comptroller of Maryland "Sales and Use Tax" (`marylandtaxes.gov/business/sales-use`); Md. Code, Tax-Gen. § 11-104(a): statewide **6%**, in effect since **2008-01-03** (raised from 5% in the 2007 Special Session's Tax Reform Act). No sub-state sales tax rates — the three category-specific rates (9% alcohol, 11.5% short-term vehicle rental, 8% peer-to-peer vehicle sharing) are categorical surcharges, not general sales. Maryland also enacted a new 3% tax on technology / IT / data services effective **2025-07-01**, which is categorical and not touched here.
- `src/opensalestax/states/maryland.py` is self-seeded.

## Prod state (read-only)
- `data_versions` for MD: SST `MD-SST-V0.13` (2026-05-04) + ZCTA (2026-05-11). The SST row is historical only.
- No MD SST file cached under `/var/lib/opensalestax/data/`.

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 21201 | Baltimore (central) | 6.000 | 6.000 | 0.00 |
| 21202 | Baltimore (central) | 6.000 | 6.000 | 0.00 |

## Legislation watch
- Maryland General Assembly's 2026 session begins 2027-01-14. No sales-rate change pending as of 2026-11-01. The 3% tech-services tax (SB 1052 / HB 1515, 2025) remains categorical and is a separate modeling task when the engine supports it.

## Recommended action
- **None.** Verify once the 2027 General Assembly session convenes.
