# IA state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **IA boundary is now 3 quarters stale on prod** (`IAB2026Q1DEC09`); latest
  upstream is **`IAB2026Q4AUG31`**. Rate file `IAR2025Q3MAY30` is still the
  most recent published by SST (IA has not republished rates since
  2025-Q3). Apply Q4 boundary only.
- **Rate exposure: NONE on probed cities.** Iowa City 52240 live-probed
  7.000% (state 6% + Johnson County LOST 1%) -- matches expected. The
  2026-07-01 Johnson County LOST impositions (Coralville, Iowa City, North
  Liberty, Oxford, Shueyville) already surface correctly on the live engine,
  likely because the Q1 boundary file bound these ZIPs ahead of the
  effective date.
- **iter-221 IA district friendly-name corrections (98175/98181/98173 FIPS
  fix) still unapplied on prod.** Mechanically rate-neutral but surfaces
  wrong county names in `tax_authorities.name`.
- **IA LOST is a flat 1% countywide cap**, so a stale boundary **cannot
  produce a wrong rate** on an already-bound ZIP; the only exposure is new
  LOST adoptions or discontinuances. The IA DOR update log confirmed no
  2026-10-01 impositions; Conway (Taylor Co.) disincorporated 2026-04-01.
- All 10 IA tier-1 pins (Des Moines, Cedar Rapids, etc.) match the live
  engine at 7.000%.
- **Status: UNCHANGED** -- no new drift this run. Open items (name
  corrections + boundary refresh) are inherited.

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| sst | `IA-SST-2025Q3MAY30` | 2026-05-10 |
| zcta-census-2020 | `IA-ZCTA-2020` | 2026-05-11 |

## Upstream (SST Governing Board, 2026-11-01)

- Rate: `IAR2025Q3MAY30.zip` -- unchanged (IA uniquely holds a 2025-Q3 rate file
  with no 2026 republish).
- Boundary: `IAB2026Q4AUG31.zip` (vs prod Q1DEC09, 3 quarters stale).

## IA DOR primary-source check (2026-11-01)

- `revenue.iowa.gov/.../updates-iowa-local-option-lost-tax-jurisdictions` --
  dated 2026-06-18. Effective 2026-07-01: 5 new LOST impositions in Johnson
  County (verified live). Effective 2026-10-01: **none**.
- `revenue.iowa.gov/.../local-option-sales-tax` -- LOST FAQ. State rate 6%,
  LOST exactly 1% countywide-or-city, impositions only on 1/1 or 7/1,
  repeals only on 6/30 or 12/31.

## Live probes

| City | ZIP | Expected | Actual | Delta |
|---|---|---|---|---|
| Iowa City | 52240 | 7.000 | 7.000 | 0.00 |
| Des Moines | 50309 | 7.000 | (pin passes) | 0.00 |

## Open follow-ups (inherited)

- Load `IAB2026Q4AUG31` on prod (rate file unchanged, boundary only).
- Deploy iter-221 `ia_names.py` corrections (98175 Union, 98181 Warren,
  98173 Taylor) and re-run `data load -s IA` to surface them.
- Cosmetic: `IA-district-98049` (Dallas County LOST) still an unlabelled
  placeholder.
