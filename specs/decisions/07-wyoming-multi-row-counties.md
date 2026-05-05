# Decision 07: Wyoming multi-row county taxes + misclassified "city"

**Status:** Open (deferred) -- recorded 2026-05-05 during iter 21 spot-check.

## Context

Wyoming's SST quarterly file ships **multiple authority rows per county**
encoding the layered county-level levies that Wyo. Stat. section
39-15-204 authorizes:

- The "5th penny" general-purpose county sales tax (up to 1%)
- The "6th penny" specific-purpose county sales tax (up to 1%, sunsets
  with the project)
- Lodging tax + economic-development overlays under section
  39-15-204(a)(iv)-(vii)

Querying the live engine after iter-20 (v0.37.0) shows the expected
multi-row pattern in our DB but **the engine resolves the wrong
combined rate** for at least two cities:

| ZIP | City | Engine rate | Published WY DOR rate | Delta |
|---|---|---|---|---|
| 82001 | Cheyenne (Laramie County) | 5.00% | 6.00% | -1.00% |
| 82601 | Casper (Natrona County) | 6.00% | 5.00% | +1.00% |

Two distinct underlying problems:

1. **Loose lookup dedupes county-level rows that should sum.** The
   `_pick_one_city_county_per_zip5` helper picks ONE authority per
   `(authority_type, ZIP)` pair using "has type-z then most rows then
   lowest id" tiebreakers. That's correct for NE Papillion (multiple
   competing city authorities, one is right) but wrong for WY Laramie
   County, which has 4 distinct rows in `tax_authorities` (1% + 2% + 2%
   + 1%) all named "Laramie County" -- they encode the four legal
   levies that should ALL apply.

2. **A "WY-city-13150" row exists at 1%** despite Wyoming statute not
   authorizing city-level sales tax. This appears to be a misclassified
   county sub-jurisdiction (the SST file's jurisdiction-type code for
   one of the county levies maps to "city" under our default
   `_DEFAULT_JURISDICTION_TYPE` mapping, but in WY's file that code
   represents a county overlay).

## Why deferred

Fixing this correctly requires:

1. **Capturing the actual SST WY rate file** (e.g. `WYR2026Q2APR15.zip`)
   and decoding which jurisdiction-type codes WY uses (the docstring on
   `wyoming.py` already flags this as "presumed" identical to MN/WI;
   empirical verification was deferred).
2. **Choosing a canonical encoding for layered county taxes** -- either
   collapse multiple rows for the same (state, county_name) into a
   single summed `Rate`, or differentiate them via name suffixes
   ("Laramie County (5th Penny)", "Laramie County (6th Penny)") so the
   dedup picks the right one.
3. **Either way, override `Wyoming.jurisdiction_types`** so the engine
   never produces a "WY-city-XXXXX" authority -- WY has none.

This is **WY-specific and isolated**: no other state shows the
multi-row symptom in the same way, and no SST member has both
"city" pseudo-authorities and county multi-rows. Fixing it here
won't ripple to the rest of the per-state machinery.

## Workaround until fixed

Document in the README's coverage table that WY combined rates may
be off by +/- 1% pending a full WY data audit. Existing tests that
cover other SST states are unaffected.

## How to apply when ready

1. Capture a WY SST quarterly file from
   https://www.streamlinedsalestax.org/ratesandboundary
2. Run the parser with logging enabled on the WY file; print every
   distinct (jurisdiction_type_code, name, rate) tuple.
3. Decide on the canonical encoding (single summed row vs. distinct
   suffixed rows). Update `wyoming.py` accordingly:
   - Override `Wyoming.jurisdiction_types` if any code currently maps
     to "city" but represents a county levy.
   - If summing, override `Wyoming.parse_rates` to coalesce.
4. Add a Cheyenne 82001 + Casper 82601 row to
   `tests/integration/test_sst_dor_validation.py` with the published
   WY DOR rate (verify against
   https://revenue.wyo.gov/divisions/excise-tax/excise-tax-publications
   on the same day).
5. Reload WY data in prod and bump the version label.
