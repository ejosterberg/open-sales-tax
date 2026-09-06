# AZ — five over-collections from aggregator-sourced rates, plus a missed county change

**Found:** 2026-09-05 daily audit (AR + AZ rotation)
**Status:** all defects FIXED in repo; **still live on prod until AZ is redeployed + reloaded**
**Severity:** high — five of the seven are **over-collections**, the direction
that creates liability for an integrator rather than a shortfall

## Summary

A systematic comparison of all 63 `AZ_CITIES` entries against the AZ DOR
*Transaction Privilege and Other Tax Rate Tables* effective 2026-09-01 found
**five wrong city rates and one wrong county rate**, on top of the one genuine
new rate change the rotation was looking for. The five wrong city rates had been
wrong for months and were never caught because of a structural gap in how the
project validates rates (see "Why CI could not catch this").

| ZIP | Jurisdiction | Engine | DOR | Combined was | Combined now | Direction |
|---|---|---:|---:|---:|---:|---|
| 85629 | Sahuarita (city) | 5.000 | **2.000** | 11.100 | **8.100** | **OVER 3.000pp** |
| 85344 | Parker (city) | 4.000 | **2.000** | 10.600 | **8.600** | **OVER 2.000pp** |
| 85353 | Tolleson (city) | 2.800 | **2.500** | 9.100 | **8.800** | **OVER 0.300pp** |
| 85253 | Paradise Valley (city) | 2.800 | **2.500** | 9.100 | **8.800** | **OVER 0.300pp** |
| 85340 | Litchfield Park (city) | 3.000 | **2.800** | 9.300 | **9.100** | **OVER 0.200pp** |
| *all Cochise* | Cochise County (excise) | 0.500 | **1.000** | — | — | under 0.500pp |
| 86401/86409 | Kingman (city) | 2.500 | **3.000** | 8.100 | **8.600** | under 0.500pp (new, eff 2026-09-01) |

The five over-collections were live on `api.opensalestax.org` at audit time and
remain live until the pending AZ deploy runs.

## Primary source

AZ DOR, *Arizona State, County and City Transaction Privilege and Other Tax Rate
Tables*, **effective September 1, 2026** —
`azdor.gov/sites/default/files/document/TPT_RATETABLE_09012026.pdf`.
Table 1 carries the state+county rates; Table 2 carries per-city rates by region
code and business code. Retail is **business code 017**.

Verified line by line, e.g.:

```
Sahuarita SA   PMA          Parker PK   LAP
...                         ...
Retail Sales 017 2.00       Restaurant and Bars 011 4.00
                            Retail Sales 017 2.00
```

## Root cause 1 — rates taken from third-party aggregators

Four of the five city errors trace to three iterations that sourced rates from
**SalesTaxHandbook** or **Avalara** instead of the DOR, and each *raised* a rate
that was already correct:

| iter | Jurisdiction | Change made | Reality |
|---|---|---|---|
| iter-150 | Sahuarita | 2.000 to 5.000, *"city tax 2% became 5% special tax per SalesTaxHandbook"* | No 5% line exists anywhere in Sahuarita's DOR schedule |
| iter-152 | Tolleson | 2.500 to 2.800, *"per SalesTaxHandbook"* | DOR: 2.50 |
| iter-152 | Litchfield Park | 2.800 to 3.000, *"per SalesTaxHandbook"* | DOR: 2.80 |
| iter-153 | Parker | 2.000 to 4.000, *"2% city tax + 2% special added Oct 2025"* | DOR: 2.00. The 4.00 is Parker's **Restaurant and Bars (011)** and **Hotel/Motel Additional (144)** rate — read off the wrong row |

Each of these was framed in its own comment as *fixing an under-collection*. In
every case the pre-existing value was right and the "fix" introduced a larger
error in the opposite direction. This is the shape the root-cause playbook warns
about: the symptom (a suspected under-collection) went away, but nothing
confirmed the new number against a primary source.

Paradise Valley (2.800 vs DOR 2.50) carries no aggregator citation but is the
same class of error.

The constitution requires primary sources — state DOR publications and SST files
— precisely because aggregators carry transcription errors. **`grep -rniE
"salestaxhandbook|avalara" src/` currently returns 130 hits across AL, AZ, CA and
others.** Every one of those is an unverified rate.

## Root cause 2 — the correct answer was already in the tree and could not object

`tests/integration/test_sst_dor_validation.py` carried a `DOR_GRID` pin asserting
`85629 -> 8.100` combined, correctly cited to *"AZ DOR May 2026 CSV (state 5.6% +
Pima 0.5% + Sahuarita 2.0%)"*. That pin has been right all along and directly
contradicted `az_data.py`.

Rather than surfacing the conflict, **iter-150 added a *second* pin for the same
ZIP asserting 11.100**, cited to SalesTaxHandbook. The grid therefore contained
two mutually exclusive expectations for ZIP 85629 simultaneously. That duplicate
has been removed.

### Why CI could not catch this

`DOR_GRID` is the project's richest correctness oracle — 46 AZ rows alone — but
it is gated behind the `-m liveapi` marker, which requires the deployed API. The
default suite deselects it:

```
1592 passed, 59 skipped, 816 deselected     # -m "not liveapi"
```

So the grid never runs in CI, and a pin can silently disagree with the data
module it is supposed to validate — indefinitely.

## Root cause 3 — county-level changes are not being checked at all

Cochise County's excise rate rose **0.500% to 1.000% effective 2026-07-01**,
affecting every Cochise ZIP (Sierra Vista, Bisbee, Tombstone, Willcox, Huachuca
City, plus unincorporated ZIPs via ZCTA). Confirmed from the Table 1 `017 Retail`
row across successive monthly DOR tables:

| Table | Cochise column | Implied county rate |
|---|---:|---:|
| `TPT_RATETABLE_01012026.pdf` | 6.10% | 0.500% |
| `TPT_RATETABLE_06012026.pdf` | 6.10% | 0.500% |
| `TPT_RATETABLE_07012026.pdf` | **6.60%** | **1.000%** |
| `TPT_RATETABLE_09012026.pdf` | **6.60%** | **1.000%** |

**Three prior audits (2026-07-31, 08-01, 08-02) missed this**, including the
08-02 audit that correctly caught Huachuca City's *town* increase effective the
same quarter. All three read the Model City Tax Code "Rate and Code Updates"
page, which announces **municipal** ordinances only. County excise changes do not
appear there — they appear in Table 1 of the rate table PDF, which no audit had
been opening.

All other 14 AZ county rates were checked against Table 1 and are correct.

## Fixes applied

`src/opensalestax/states/az_data.py`

- `Cochise County` 0.500 to 1.000, with the Table 1 evidence in a comment
- `Sahuarita` 5.000 to 2.000
- `Parker` 4.000 to 2.000
- `Tolleson` 2.800 to 2.500
- `Paradise Valley` 2.800 to 2.500
- `Litchfield Park` 3.000 to 2.800
- `Kingman` 2.500 to 3.000 (the one genuine new change, ordinance 2003)
- Stale inline "Cochise 0.5" combined-rate comments corrected

`tests/integration/test_sst_dor_validation.py`

- Removed the contradictory duplicate Sahuarita pin (11.100)
- Retargeted pins whose expected value was derived from a now-corrected rate:
  Sierra Vista 8.050 to 8.550, Huachuca City 9.000 to 9.500, Bisbee 9.600 to
  10.100, Tolleson 9.100 to 8.800, Paradise Valley 9.100 to 8.800, Parker 10.600
  to 8.600
- Added a Kingman pin (86401 -> 8.600)
- Re-cited two pins that credited SalesTaxHandbook to the DOR table instead

All eleven corrected combined rates were recomputed from `AZ_COUNTY_RATE_PCT` +
`AZ_CITIES` and match their pins exactly.

## Open — deliberately NOT changed

**Sun City (85351, 9.300) and Vail (85641, 8.700) do not appear in the DOR city
table at all.** Both are unincorporated CDPs, which in Arizona pay state + county
only and levy no municipal TPT. By the same reasoning the project already applies
to Green Valley (85622 pinned at 6.100 = state 5.6 + Pima 0.5, no city
component), Sun City would be 6.300 and Vail 6.100 — implying further
over-collections of 3.000pp and 2.600pp.

This was **not** changed, because unlike the fixes above it is a modelling
judgement, not a transcription error: some CDP ZIPs straddle incorporated
territory (the project already treats 85382 that way, mapping it to Peoria's
rate), and getting it wrong in the other direction would under-collect. Both
entries cite SalesTaxHandbook. **This needs Eric's call and a ZIP-boundary check,
not an autonomous edit.**

## Recommended follow-ups

1. **Add a CI-time `DOR_GRID` consistency test.** Evaluate each grid row's
   expectation against the *in-repo* state modules — no network, no prod. This
   would have caught Sahuarita the day iter-150 landed, and would have refused
   the duplicate contradictory pin outright. Highest-value fix here by a wide
   margin.
2. **Re-verify every aggregator-sourced rate against its DOR** (130 hits for
   `salestaxhandbook|avalara` in `src/`). AZ is now clean; AL and CA carry the
   heaviest remaining concentrations.
3. **Add county-rate verification to the daily audit procedure.** The audit skill
   currently points at municipal rate-change pages; for AZ it must also diff
   Table 1 of the monthly rate table. Other states will have the analogous split.
4. **Resolve the Sun City / Vail CDP question** (above).
5. **Deploy.** All of this is repo-only until the pending AZ deploy + reload runs.
