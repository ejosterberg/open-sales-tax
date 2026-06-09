# SST boundary file quirks — per-state column conventions

**Discovered:** iter-225 (2026-05-19), as a follow-up to the
iter-224 WV breakthrough (cols[14] plain-text city name).

The Streamlined Sales Tax (SST) boundary CSV format has a
documented core (cols 0-23 hold the row type, effective dates,
ZIP fields, state FIPS, county FIPS, city code, etc.) plus a
variable tail (cols 29+) for repeating (class, code, type)
triplets covering special districts. States are free to populate
non-required columns however they like.

**The takeaway: the SST boundary CSV is NOT a uniform interface
across states. Each state's per-row columns 12-21 may carry
state-specific data the loader is free to ignore or exploit.**

## Survey results (2026-05-19, current quarterly files)

Sampling a representative type-z or type-4 row from each state's
most recent boundary file:

| State | File | Plain-text name @ col 14? | Other notable cols |
|---|---|---|---|
| **WV** | WVB2026Q1SEP02 | **YES** (`'CHARLESTON'`) | -- |
| UT  | UTB2026Q2MAR20 | no | col 21 = numeric (e.g. `'25000'`) |
| WI  | WIB2026Q2FEB18 | no | -- |
| KS  | KSB2026Q2FEB18 | no | col 21 = 5-letter shortcode (`'CAMCL'`) |
| AR  | ARB2026Q2MAR02 | no | col 26 = 2-char tag (`'C1'`) |
| OK  | OKB2026Q2APR01 | no | -- |
| TN  | TNB2026Q2FEB23 | no | -- |
| ND  | NDB2026Q2FEB19 | no | very sparse |
| SD  | SDB2026Q2FEB23 | no | -- |
| NE  | NEB2026Q2APR20 | no | -- |
| WA  | WAB2026Q2FEB26 | no | col 21 = place code (`'02600'`) |
| MN  | MNB2026Q2FEB18 | no | -- |
| NC  | not surveyed | -- | -- |

**Only WV puts city names in plain text.** The iter-224 mass
WV-labelling trick exploits a WV-specific column convention, not
a general SST feature.

## Implications

1. **`wv_names.py` could theoretically be generated FROM the SST
   source** rather than hand-curated. The cols[14] column has the
   authoritative friendly name. A loader-level refinement could
   make this automatic, dropping `wv_names.py` to zero entries
   (the loader just reads cols[14] when present).

2. **For other states, hand-curation still requires external
   sources.** Each needs its own authoritative code → name
   lookup (the equivalent of MN's tax-type-codes.xlsx). Found so
   far in this project:
   - MN: revenue.state.mn.us/media/document/58036
   - IA: revenue.iowa.gov/taxes/tax-guidance/sales-use-excise-tax/streamlined-sales-tax
   - NC: ncdor.gov SST participants page (4 codes only;
         99055 not listed)

3. **The 5-letter shortcodes in KS / WA cols[21] (e.g. KS's
   `'CAMCL'`)** could be a different per-state convention worth
   chasing. They're abbreviated city names, not friendly labels,
   but might be cross-referenceable to KS DOR rate tables.

## What this changes about future hand-curation strategy

For each remaining state with unlabelled placeholders:

1. **First**, run a quick survey of cols 12-21 in that state's
   SST CSV to see if a usable name/code column exists.
2. **If no**, identify the authoritative DOR cross-reference
   table via deep-research (the MN/IA/NC pattern from iter-220
   and iter-221).
3. **Otherwise**, fall back to ZIP-probe + FIPS Place matching
   (the iter-180/183/185 / iter-187/203..210 patterns).

This three-tier approach should be the default for any state-
level hand-curation iter going forward.
