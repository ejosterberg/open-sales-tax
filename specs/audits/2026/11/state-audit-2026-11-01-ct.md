# State audit — CT — 2026-11-01 (full-sweep)

## TL;DR
- **CT: UNCHANGED.** Flat 6.350% statewide confirmed; prod returns 6.350% at every probed ZIP. CT is self-seeded (non-SST); no reload owed.

## Source
- CT DRS tax rate page (`portal.ct.gov/DRS`) and Conn. Gen. Stat. §12-408(1)(A): statewide rate **6.35%**, in effect since 2011-07-01. No sub-state sales taxes anywhere in CT per statute.
- `src/opensalestax/states/connecticut.py` is self-seeded; `parse_rates` ignores any upstream file and yields a single 6.350% row.

## Prod state (read-only)
- `data_versions` for CT: SST `CT-SST-V0.25-LOCALS` (2026-05-04) + ZCTA (2026-05-11). The SST row is historical only — the CT module is self-seeded, so SST files are not consulted at calc time.
- No CT SST file is cached under `/var/lib/opensalestax/data/`.

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | City | Expected | Actual | Delta |
|---|---|---|---|---|
| 06103 | Hartford | 6.350 | 6.350 | 0.00 |
| 06902 | Stamford | 6.350 | 6.350 | 0.00 |

## Legislation watch (through 2026-11-01)
- 2025 General Assembly: no changes to the general 6.35% rate. The 2011 7.75% luxury / 7.35% meals / 15% lodging / 9.35% short-term rental / 1% computer-services / 2.99% vessels categories are unchanged and remain deferred to the threshold/modifier engine. **Nothing to do.**

## Recommended action
- **None.** `DOR_GRID` has a 6.350% Hartford guard already; it still passes.
