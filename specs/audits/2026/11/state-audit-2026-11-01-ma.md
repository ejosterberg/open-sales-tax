# State audit — MA — 2026-11-01 (full-sweep)

## TL;DR
- **MA: UNCHANGED.** Flat 6.25% statewide confirmed; no local sales taxes anywhere in the Commonwealth. Prod returns 6.250% at probed ZIPs. Non-SST, self-seeded.

## Source
- Mass. DOR "Sales/Use Tax Rate" (`mass.gov/sales-tax`) and Mass. G.L. c. 64H § 2: statewide **6.25%**, in effect since **2009-08-01** (originally raised from 5.0% in Chapter 27 of the Acts of 2009). No county or municipal sales tax. The separate 6.25% local-option **meals** tax (max 0.75% add-on) remains categorical, not general sales.
- `src/opensalestax/states/massachusetts.py` is self-seeded; `parse_rates` ignores any upstream file and yields a single 6.250% row.

## Prod state (read-only)
- `data_versions` for MA: SST `MA-SST-V0.13` (2026-05-04) + ZCTA (2026-05-11). The SST row is historical only.
- No MA SST file cached under `/var/lib/opensalestax/data/`.

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 02101 | Boston | 6.250 | 6.250 | 0.00 |

## Category rates (not modeled in v0.6, documented for future)
- Clothing: items ≤ $175 per item exempt; portion over $175 taxable at 6.25%.
- Meals (restaurant): 6.25% state + up to 0.75% local meals excise.
- Lodging / rooms: 5.7% state + local caps.
No category-rate changes have been announced for 2026-10-01 or 2027-01-01. **Nothing to do** at the general-rate level.

## Recommended action
- **None.** Keep monitoring DOR TIR releases quarterly.
