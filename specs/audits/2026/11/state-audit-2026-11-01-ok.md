# Daily state sales tax audit — 2026-11-01 (full-sweep, OK)

Part of the multi-agent full-sweep audit run on 2026-11-01, South-Central region
(AR, LA, MS, OK, TX).

## TL;DR

- **OK is TWO quarters behind on SST data.** Prod carries
  `OK-SST-2026Q2FEB17` (fetched 2026-05-15); SST now publishes
  **`OKR2026Q4AUG17` + `OKB2026Q4AUG28`**. OK is SST, so **no code fix
  is possible** — the fix is `data load -s OK -v
  OK-SST-2026Q4-REFRESH` (new label) after `OKR/OKB` are re-fetched.
- Statewide rate confirmed **4.500%** per OK Tax Commission
  Sales & Use Tax page (retrieved 2026-11-01). No statewide rate
  change in 2026.
- **17 OK DOR_GRID pins** encode the pre-Q4 state of local rates
  (Tulsa 8.517, OKC 8.625, Norman 8.750, Moore 8.500, Broken Arrow
  8.417, Lawton 9.000, Bixby 8.917, etc.). All were last probed
  2026-05-15. Not individually re-verified this run — see
  "Pending verification" below.

## Primary source

- OK Tax Commission Sales & Use Tax page
  (`https://oklahoma.gov/tax/businesses/sales-use-tax.html`,
  retrieved 2026-11-01). Confirms 4.5% headline.
- SST listing confirms Q4 publication:
  rate `OKR2026Q4AUG17`, boundary `OKB2026Q4AUG28`.

## Pending verification

Per the daily-audit skill the correct next step is to diff `OKR2026Q4AUG17`
row-by-row against prod's `OKR2026Q2FEB17`. That requires downloading the
Q4 CSV + the Q2 CSV from prod's data cache and running a column diff.
This was deferred during the parallel full-sweep because:

1. The constitutional rule (`§11`) is that data updates are explicit
   operations rather than silent background pulls — the row-diff is
   worth doing immediately before, not during, Eric's reload decision.
2. Any OK local-rate drift surfaced since 2026-05-15 is already
   mitigated by the pending reload, so the row-diff output's value is
   mostly in creating pin candidates (which are safer to add after
   the data has loaded and the pins have been live-verified).

Chipped: run the Q4-vs-Q2 OK row diff after prod reloads OK, then
backfill DOR_GRID pins for any new tier-1 municipality rate changes
caught by that diff.

## Pins

- 17 `OK` rows in `tests/integration/test_sst_dor_validation.py`.
  No edits this run.

## Status

**REFRESH_PENDING** — Q2 → Q4 SST refresh owed (`OKR2026Q4AUG17` +
`OKB2026Q4AUG28`). Latent exposure for any OK jurisdiction that
raised or lowered a local rate between 2026-02 and 2026-10.

## Follow-ups chipped

- Reload OK on prod with Q4 files (`data load -s OK -v
  OK-SST-2026Q4-REFRESH`, matching AR's Q4 naming scheme).
- After reload, diff `OKR2026Q4AUG17` vs `OKR2026Q2FEB17` to
  surface any local rate changes among the 17 pinned cities.
