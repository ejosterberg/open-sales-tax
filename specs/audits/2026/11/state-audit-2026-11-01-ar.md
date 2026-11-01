# Daily state sales tax audit — 2026-11-01 (full-sweep, AR)

Part of the multi-agent full-sweep audit run on 2026-11-01, South-Central region
(AR, LA, MS, OK, TX).

## TL;DR

- **AR is rate-current for 2026-10-01 changes** — the Q4 refresh
  (`ARR2026Q4AUG28` + `ARB2026Q4SEP02`) was already loaded 2026-09-06
  per handoff. Alpena, Hempstead, Logan, Stone changes effective
  2026-10-01 are in the loaded dataset. **15/15 AR probes still exact**
  per prior audit.
- **🔔 AR boundary file ONE patch behind on prod**:
  prod has `ARB2026Q4SEP02`, upstream now serves **`ARB2026Q4SEP17`**
  (the SEP02 variant is 404 — superseded). Flagged as a dead SST pin
  in handoff item 2026-09-28. **Boundary-only drift**: AR has a flat
  6.5% state rate and all local layers come from the rate file
  (which is current), so no live rate is wrong. Chipped: reload AR
  boundary on next refresh pass.
- **📣 AR 2027-01-01 changes already announced**: Harrison 1.000%
  (decrease), Boone County 1.000% (decrease), Lafayette County
  1.625% (decrease), plus multiple annexations (Siloam Springs,
  Gentry, Gravette, Pea Ridge, Mammoth Spring, Salem, Manila,
  Prairie Grove, Searcy). These land in the Q1 2027 SST file;
  deliberately NOT applied. **Harrison 05-12 is in `AR_CITIES`**
  as a modeled jurisdiction, so the Q1 2027 refresh is time-critical.
- **Placeholder AR names persist** (chipped multiple times already):
  `AR-city-13570` Chester, `-54650` Perry, `-21070` El Dorado,
  `-77090` Cross County, `-49580` Jackson County. Not touched this run
  — cosmetic, repeat chip.

## Primary source

- AR DFA "Recent Changes for Local Taxes"
  (`https://www.dfa.arkansas.gov/office/taxes/excise-tax-administration/
  sales-use-tax/recent-changes-in-sales-use-tax/recent-changes-for-local-taxes/`,
  retrieved 2026-11-01).
- SST file listing (`https://www.streamlinedsalestax.org/ratesandboundry/
  Rates/` and `.../Boundary/`, retrieved 2026-11-01).

## Boundary dead-pin detail

Upstream rotated AR boundary from `ARB2026Q4SEP02.zip` to
`ARB2026Q4SEP17.zip` sometime between prod's 2026-09-06 fetch and
now (SEP17 is listed first in the directory listing today; SEP02 is
gone). The handoff already notes this as one of three dead pins
(AR boundary 2026Q4SEP02, OH 2026Q4AUG27, OH 2026Q4SEP01). A
release-tag data rebuild would 404; a routine `data load -s AR -v
AR-SST-2026Q4AUG28` on prod would NOT 404 because the loader
reuses the existing label (per the data-loader-refresh-gotchas
memory). But adopting the newer boundary explicitly is cleaner.

## Pins

- 6 `AR` rows in `tests/integration/test_sst_dor_validation.py`;
  consistent with the Q4-loaded dataset. **No pin edits this run.**

## Status

**REFRESH_PENDING** — boundary-only drift (SEP02 → SEP17); no live
rate error. Q1 2027 refresh will be the next time-critical reload
(Harrison, Boone, Lafayette changes).

## Follow-ups chipped

- Reload AR boundary to `ARB2026Q4SEP17` on next refresh pass
  (defensive: avoids a release-tag 404 and anchors boundary
  bindings to the latest annexation set).
- When Q1 2027 SST file publishes (expected 2026-12 per prior
  cadence), apply it before 2027-01-01 so Harrison, Boone,
  Lafayette, and the ~9 annexations go live on effective date.
- Label the 5 placeholder AR city names (cosmetic, repeat chip).
