# State audit — ME — 2026-11-01 (full-sweep)

## TL;DR
- **ME: UNCHANGED.** Flat 5.5% statewide general-tangible rate confirmed; no county or municipal sales taxes anywhere in Maine. Prod returns 5.500% at probed ZIPs. Non-SST, self-seeded.

## Source
- Maine Revenue Services (`maine.gov/revenue/taxes/sales-use`); 36 M.R.S. § 1811: statewide general rate **5.5%**, in effect since **2013-10-01** (`Public Law 2013, ch. 368, part M`). The category-specific rates — 8% prepared food & lodging, 10% short-term auto rental, 5.5% service-provider tax base — have not changed.
- `src/opensalestax/states/maine.py` is self-seeded.

## Prod state (read-only)
- `data_versions` for ME: SST `ME-SST-V0.13` (2026-05-04) + ZCTA (2026-05-11). The SST row is historical only.
- No ME SST file cached under `/var/lib/opensalestax/data/`.

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 04101 | Portland | 5.500 | 5.500 | 0.00 |
| 04401 | Bangor | 5.500 | 5.500 | 0.00 |

## Legislation watch
- Maine Legislature's 132nd session (2026) adjourned 2026-07-16 — no change to § 1811 enacted. The 2026 session's two sales-related items (LD 1 cannabis excise, LD 1800 adult-use delivery) are categorical.

## Recommended action
- **None.** Keep monitoring MRS tax alert releases quarterly.
