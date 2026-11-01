# Daily state sales tax audit — 2026-11-01 (full-sweep: CO)

## TL;DR

- **CO state rate 2.9% returned exactly** on Denver 80202 and Boulder
  80301 probes, with the standing `coverage_warning` for home-rule
  cities surfaced as designed.
- **Home-rule cities (~70) remain deferred** per decision 04. No change
  to this policy in this run.
- **No code or data change this run.** The `CO-SST-V0.13` DataVersion
  on prod (fetched 2026-05-04) remains fit for purpose because the only
  thing it carries is the 2.9% state rate; CO is not an SST member for
  rate-file purposes and the state-portion rate has not changed since
  2000-01-01.
- **Status:** UNCHANGED.

## Source

- CO Dept. of Revenue, Sales Tax Rates
  (`https://tax.colorado.gov/sales-use-tax-rates`) — state rate 2.9%
  (unchanged since 2000-01-01).
- Decision log: `specs/decisions/04-colorado-home-rule.md`.

## Procedure

- Live probes:
  - `80202` (Denver, home-rule) → `tax_total: "2.9000"` with
    `coverage_warning` set. Correct.
  - `80301` (Boulder, home-rule) → `tax_total: "2.9000"` with
    `coverage_warning` set. Correct.
- No new 2026 state-rate legislation identified during this spot
  cross-check against the CO DOR Sales Tax page.
- Prod `data_versions`: `CO-SST-V0.13` (sst), `CO-ZCTA-2020` (zcta).
  No upstream SST file for CO — CO is not an SST member. The pin
  reflects the state-portion-only module version.

## Known gaps (standing)

- ~70 home-rule cities self-administer (Denver, Boulder, Colorado
  Springs, Fort Collins, Aurora, Lakewood, Thornton, Arvada, Pueblo,
  Greeley, etc.). The engine returns the 2.9% state portion with a
  `coverage_warning`. This is a documented coverage decision, not drift.
- Statutory-city local rates (RTD, cultural district, county) are also
  not modelled. Same policy, same warning.

## Actions taken

None. Audit report only.
