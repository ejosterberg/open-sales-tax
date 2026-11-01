# Daily state sales tax audit — 2026-11-01 (full-sweep: MT)

## TL;DR

- **Montana has no state sales tax, no county sales tax, and no general
  municipal sales tax** — only resort-area selective sales taxes on
  lodging/alcohol/short-term luxury rentals in a handful of resort
  communities (Big Sky, Red Lodge, West Yellowstone, Whitefish, St. Regis,
  Virginia City, Craig). None of those are modelled, nor are they in scope
  for the engine's general-retail output.
- **Live engine returns 0.00% with zero jurisdictions on a Billings 59101
  probe** — correct.
- **No data load on prod** (MT has no `data_versions` row other than ZCTA);
  no code or data change this run.
- **Status:** UNCHANGED.

## Procedure

Spot-check only, per the briefing: MT is a no-sales-tax state.

- `POST /v1/calculate {"address":{"zip5":"59101"}, line_items:[{"amount":"100.00"}]}`
  → `tax_total: "0"`, `jurisdictions: []`. Matches expectation.
- Prod `data_versions` shows only `MT-ZCTA-2020` (ZIP boundaries); no
  state/local rate data to load.

## Known gaps (not drift)

Resort-tax communities above levy local resort/accommodation taxes
(typically 3% on lodging and some retail categories, authorized by
Mont. Code Ann. 7-6-1501 et seq.) that the engine does not model — and
that are not applicable to the general-retail category it returns. If a
future consumer needs resort-tax handling, that is a scope expansion,
not a defect against the current contract.

## Actions taken

None. Audit report only.
