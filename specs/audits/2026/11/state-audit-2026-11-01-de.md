# State audit — DE — 2026-11-01 (full-sweep)

## TL;DR
- **DE: UNCHANGED.** No state or local sales tax. Delaware levies a **gross-receipts tax** on sellers (30 Del. C. ch. 29) in lieu of a sales tax. Prod returns 0% at every probed ZIP. Fully clean, confirmed on 2026-09-21 and re-confirmed here.

## Source
- Delaware Division of Revenue "Business Taxes" page (`revenue.delaware.gov/business-tax-forms`); 30 Del. C. ch. 29. No general sales-tax statute.
- `src/opensalestax/states/no_tax.py` carries DE as a `NoTaxState` instance.

## Prod state (read-only)
- `data_versions` for DE: only ZCTA (`DE-ZCTA-2020`, 2026-05-11). No SST or DOR data expected or needed.
- No DE files cached under `/var/lib/opensalestax/data/`.

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 19901 | Dover | 0.000 | 0.000 | 0.00 |

## Legislation watch
- No pending 2026 legislation to introduce a state sales tax. Delaware has debated this periodically for decades; nothing on the 2026 General Assembly docket.

## Recommended action
- **None.** No change required.
