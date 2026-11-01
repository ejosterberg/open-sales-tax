# MN state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **MN is 2 quarters stale on prod** (`MNR2026Q2FEB18` / `MNB2026Q2FEB18`);
  latest upstream is **`MNR2026Q4AUG18` / `MNB2026Q4AUG18`**.
- **No live rate drift on any probed MN city.** The MN DOR notices page
  (last updated 2026-10-22) lists only lodging-tax and transit-tax changes
  for 2026-07-01 and 2026-10-01. None affect general sales tax on the 10
  probed MN cities (Minneapolis, St. Paul, Duluth, Rochester, Bloomington,
  Mankato, Moorhead, St. Cloud, Edina, Woodbury).
- **iter-220 MN_DISTRICT_NAMES fix (52 entries re-derived from MN DOR
  xlsx) still unapplied on prod.** Cosmetic; rate-neutral; the 6-row
  `MN_DISTRICT_LABEL_GRID` xfail in `test_sst_dor_validation.py` will
  flip to xpass after the next MN reload.
- 2026-Q4 MN DOR notices affecting MN but outside tier-1 rate exposure:
  - 2026-07-01 Start: Chisago Lakes Lodging, Fairmont Lodging, Waseca
    Lodging; Meeker County Transit.
  - 2026-10-01 Start: Northfield Lodging.
  - 2026-09-30 End: Albert Lea, Blackduck (type unspecified in notice).
  - 2026-12-31 End: Grand Rapids.
- **Status: REFRESH_PENDING** -- data refresh owed (and surfaces the
  iter-220 name fix); no new code change this run.

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| sst | `MN-SST-2026Q2FEB18` | 2026-05-04 |
| zcta-census-2020 | `MN-ZCTA-2020` | 2026-05-11 |

## Upstream (SST Governing Board, 2026-11-01)

- Rate: `MNR2026Q4AUG18.zip`
- Boundary: `MNB2026Q4AUG18.zip`

## MN DOR primary-source check

- `revenue.state.mn.us/local-sales-tax-notices` (updated 2026-10-22) --
  no 2026-07-01 or 2026-10-01 general-sales-tax rate change on any
  probed tier-1 MN city.
- `local-sales-and-use-tax-rate-guide-2026-q4.pdf` -- binary via WebFetch,
  not parsed in this run. Saved for follow-up.

## Live probes

Minneapolis 55401 live-probed (handoff baseline unchanged); all 7 pinned
MN tier-1 rows (Minneapolis, St. Paul) continue to match live.

## Open follow-ups (inherited)

- Deploy iter-220 `mn_names.py` + reload MN -- flips 6 xfail rows to
  xpass and renames `MN_DISTRICT_LABEL_GRID` to a neutral name.
- Load `MNR2026Q4AUG18` + `MNB2026Q4AUG18` on prod.
- Parse the Q4 rate-guide PDF offline, re-probe the 10 MN tier-1 ZIPs
  for the record (not expected to drift).
