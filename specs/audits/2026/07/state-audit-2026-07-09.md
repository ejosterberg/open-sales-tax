# Daily state sales tax audit — 2026-07-09 (day 9: KS + KY)

## TL;DR
- 2 jurisdictions audited — both SST member states (KS, KY).
- **0 real-world rate changes requiring code/test updates.** All 10
  tier-1 cities (8 KS + 2 KY) match the live engine and the current
  authoritative rates exactly.
- **KS: file-currency refresh only.** Prod caches the Q2 2026 SST files
  (`KSR2026Q2FEB18` / `KSB2026Q2FEB18`); latest is Q3 2026
  (`KSR2026Q3MAY20` / `KSB2026Q3MAY20`, posted 2026-05-20, effective
  2026-07-01). No citywide/ZIP-level drift — every KS July-1-2026 change
  affecting a tier-1 city is a **sub-ZIP CID / STAR-bond special
  district** (out of v1 scope). Refresh chipped for hygiene only.
- **KY: clean and current.** Flat 6% statewide, no local sales tax
  (confirmed: KY's constitution still prohibits local option sales tax;
  the 2024 amendment path did not result in any enacted local tax). The
  SST rate file `KYR2012Q4Aug13.csv` on prod is genuinely the latest KY
  publishes — KY has no local rates to update, so the file has been
  static since 2012. No refresh, no drift, no action.

## KS (Kansas — SST member)
- Source: SST Governing Board rate/boundary directories
  (streamlinedsalestax.org/ratesandboundry/{Rates,Boundary}/) +
  KS DOR "Local Sales Tax Information — Quarterly Updates"
  (ksrevenue.gov/salesratechanges.html, Publication 1700 07/2026) +
  usgeocoder 2026 KS change log. Retrieved 2026-07-09.
- Last loaded on prod: rate `KSR2026Q2FEB18.zip`, boundary
  `KSB2026Q2FEB18.zip` (Q2 2026, effective 2026-04-01).
- Latest available: rate `KSR2026Q3MAY20.zip`, boundary
  `KSB2026Q3MAY20.zip` (Q3 2026, posted 2026-05-20, effective
  2026-07-01). **Prod is one quarter behind.**
- Drift summary: **none at ZIP/citywide granularity.** The July 1, 2026
  changes that touch tier-1 cities are all Community Improvement
  District (CID) / STAR-bond districts imposing tax within a single
  development's footprint, not citywide:
  - Topeka: California Crossing CID, Hotel Topeka CID
  - Shawnee County: Stormont Vail Events Center CID
  - Wichita: Orpheum Theatre CID (+ Apr-1 333 English CID, SoCe Corner CID)
  - Kansas City KS: Homefield/98th & State Ave CID, American Royal CID &
    Northwest Speedway STAR Bond 2, Buc-ee's CID
  - Olathe: Station North CID (Jan-1-2026)

  These are sub-ZIP overlays (same class as the IL Peoria "Glen Hollow
  Business District" — intentionally out of v1 scope). Hays, Lawrence,
  Manhattan, and Salina had **no 2026 changes** at all.
- Recommended action: **chip a file-currency refresh** to
  `KSR2026Q3MAY20` / `KSB2026Q3MAY20` (hygiene; zero rate impact). Do
  not auto-pull SST files — Eric reviews those. No code/test change.

### Tier-1 city cross-check vs. live engine (api.opensalestax.org)
Each probed with a single $100 `general` line; "Expected" = current KS
DOR combined rate for the citywide jurisdiction (post-Jul-1-2026).

| City | ZIP | Expected (KS DOR) | Engine (live) | Delta | Note |
|------|-----|-------------------|---------------|-------|------|
| Topeka | 66603 | 9.350 | 9.350 | 0 | state 6.5 + Shawnee 1.35 + Topeka 1.5; Jul-1 CIDs are sub-ZIP |
| Wichita | 67202 | 7.500 | 7.500 | 0 | state 6.5 + Sedgwick 1.0; no city tax; Jul-1 Orpheum CID sub-ZIP |
| Kansas City | 66101 | 9.125 | 9.125 | 0 | state 6.5 + Wyandotte 1.0 + KC 1.625; Jul-1 CIDs/STAR sub-ZIP |
| Olathe | 66061 | 9.475 | 9.475 | 0 | state 6.5 + Johnson 1.475 + Olathe 1.5; Station North CID sub-ZIP |
| Hays | 67601 | 9.250 | 9.250 | 0 | state 6.5 + Ellis 0.5 + Hays 2.25; no 2026 change |
| Lawrence | 66044 | 9.350 | 9.350 | 0 | state 6.5 + Douglas 1.25 + Lawrence 1.55; no 2026 change |
| Manhattan | 66502 | 9.150 | 9.150 | 0 | state 6.5 + Riley 0.7 + Manhattan; no 2026 change |
| Salina | 67401 | 9.250 | 9.250 | 0 | state 6.5 + Saline 1.5 + Salina; no 2026 change |

All 8 match to the thousandth of a percent. (KS also zero-rated
groceries statewide effective 2026-01-01, but that is a `food`-category
taxability change, not a `general`-rate change — out of scope for this
rate audit and not exercised by the `general` probe.)

## KY (Kentucky — SST member)
- Source: SST Governing Board rate/boundary directories + KY DOR Sales &
  Use Tax pages (revenue.ky.gov) + Kentucky League of Cities / KY Center
  for Economic Policy on the local-option-sales-tax constitutional
  question. Retrieved 2026-07-09.
- Last loaded on prod: rate `KYR2012Q4AUG13.csv`, boundary
  `KYB2013Q2MAR13.csv`; DataVersion per KY SST + ZCTA.
- Latest available: rate `KYR2012Q4Aug13.csv`, boundary
  `KYB2013Q2MAR13.csv` — **identical to prod.** KY publishes a flat
  statewide rate and has no local taxing jurisdictions to update, so its
  SST files have been static since 2012/2013. Prod is fully current.
- Drift summary: **none.** Kentucky levies a flat **6% statewide** sales
  and use tax with **no local (county/city) sales tax**. Kentucky's
  constitution still prohibits local option sales taxes as of 2026; the
  2024 constitutional-amendment effort did not produce any enacted local
  sales tax. Both tier-1 cities return exactly 6.000%.
- Recommended action: **none.** Clean and current.

### Tier-1 city cross-check vs. live engine
| City | ZIP | Expected (KY DOR) | Engine (live) | Delta |
|------|-----|-------------------|---------------|-------|
| Louisville | 40202 | 6.000 | 6.000 | 0 |
| Lexington | 40507 | 6.000 | 6.000 | 0 |

## Actions taken this run
1. **Report only** — no code/test/data change (no correctness drift).
2. **Chip:** "Refresh KS SST quarterly to KSR2026Q3MAY20" — file-currency
   hygiene (Q2 → Q3); zero rate impact since all Q3 changes are sub-ZIP
   CID/STAR-bond districts outside v1 scope.
3. **handoff.md:** added a KS file-currency follow-up under "Open
   follow-ups from daily state-tax audits" (consistent with the GA/IN/
   WV/WY currency-refresh entries).

## Verification notes
- Live engine request schema: `POST /v1/calculate` with
  `{"address":{"zip5":"…"}, "line_items":[{"amount":"100.00",
  "category":"general"}]}`. Effective rate read from the response's
  top-level `lines[].rate_pct`, cross-checked against the per-jurisdiction
  `jurisdictions[].rate_pct` breakdown (e.g. Topeka 66603 returned
  Shawnee County 1.35 + Kansas 6.5 + Topeka 1.5 = 9.35).
- All probes used bare ZIP5. The KS integration grid pins several of
  these with specific ZIP+4s (e.g. Topeka 66603-3304, Olathe 66061-2917);
  bare-ZIP5 and pinned-+4 agree for the citywide rate here, so no ZIP+4
  precision issue surfaced this run.
- No `-m liveapi` pins fail as a result of this audit (no engine change).
