# State audit — DC — 2026-11-01 (full-sweep)

## TL;DR
- **DC: UNCHANGED.** General rate **7.0% effective 2026-10-01**; prod returns 7.000% at every probed ZIP. The `district_of_columbia.py` module ships both effective-dated rows (6.0% through 2026-09-30, 7.0% from 2026-10-01); the engine is now resolving to the 7% row for post-2026-10-01 transactions.

## Source
- DC OTR "Notice of Oct. 1, 2025 Tax Changes" (`otr.cfo.dc.gov/release/notice-oct-1-2025-tax-changes`) — originally scheduled two steps (6→6.5 on 2025-10-01, 6.5→7 on 2026-10-01); the **Sales Tax Increase Delay Amendment Act of 2025** cancelled the 6.5% step. General rate therefore stayed at 6.0% through 2026-09-30 and moved directly to **7.0% on 2026-10-01**. Module docstring already carries the audit-trap note against third-party aggregators still showing 6.5%.
- Statute: D.C. Official Code § 47-2002.

## Prod state (read-only)
- `data_versions` for DC: SST `DC-SST-V0.13` (2026-05-04) + ZCTA (2026-05-11). DC's module is self-seeded; the SST row is historical only.
- No DC SST file cached under `/var/lib/opensalestax/data/`.

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| ZIP | Expected | Actual | Delta |
|---|---|---|---|
| 20001 | 7.000 | 7.000 | 0.00 |
| 20005 | 7.000 | 7.000 | 0.00 |

## Category rates (not modeled in v0.6, documented for future)
- 10% restaurant / alcohol-for-off-premises / soft drinks
- 10.25% liquor on-premises
- 14.95% hotel / parking
- 10% rental of motor vehicles
None of these have been reported to change on 2026-10-01; only the general rate did. No code change required.

## Recommended action
- **None.** DC general rate transition landed correctly on 2026-10-01 as the module already encoded. Keep monitoring the OTR tax-change notice page quarterly.
