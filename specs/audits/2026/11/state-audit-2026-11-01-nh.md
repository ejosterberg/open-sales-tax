# State audit — NH — 2026-11-01 (full-sweep)

## TL;DR
- **NH: UNCHANGED.** No state or local general sales tax. Prod returns 0% at every probed ZIP. New Hampshire's **9% meals & rentals tax** (RSA 78-A) is a categorical excise, not a general sales tax, and is not modeled.

## Source
- NH Department of Revenue Administration (`revenue.nh.gov`); no RSA chapter imposes a general sales tax. The 2026 General Court made no change.
- `src/opensalestax/states/no_tax.py` carries NH as a `NoTaxState` instance.

## Prod state (read-only)
- `data_versions` for NH: only ZCTA (`NH-ZCTA-2020`, 2026-05-11). No SST or DOR data expected or needed.
- No NH files cached under `/var/lib/opensalestax/data/`.

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 03101 | Manchester | 0.000 | 0.000 | 0.00 |

## Legislation watch
- The 2024 reduction of the Meals & Rentals Tax (9% → 8.5% effective 2024-10-01, HB 1 2023-NH) is categorical, outside the general-sales model. No general sales tax has been introduced in the 2025 or 2026 sessions; HB 2 (2025) did not revive the proposal.

## Recommended action
- **None.** No change required.
