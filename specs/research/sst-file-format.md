# Research — SST file format (rates + boundaries)

> Empirical notes from inspecting real SST files. Compiled
> 2026-05-03 by direct download + analysis of MN's
> `MNR2026Q2FEB18.zip` (rates) and `MNB2026Q2FEB18.zip`
> (boundaries).

## Source URLs

| Type | URL pattern |
|---|---|
| Rates | https://www.streamlinedsalestax.org/ratesandboundry/Rates/ |
| Boundary | https://www.streamlinedsalestax.org/ratesandboundry/Boundary/ |

## Filename convention

`<STATE><TYPE><YEAR>Q<QUARTER><MONTH><DAY>.<ext>`

- `<STATE>` — two-letter USPS abbreviation (uppercase)
- `<TYPE>` — `R` for rates, `B` for boundary
- `<YEAR>` — 4-digit calendar year
- `<QUARTER>` — `1`, `2`, `3`, or `4`
- `<MONTH>` — 3-letter abbreviation (uppercase: JAN, FEB, ...)
- `<DAY>` — zero-padded day of month
- `<ext>` — `csv` for plain, `zip` for archived

Examples: `MNR2026Q2FEB18.zip`, `WIR2026Q2APR15.csv`.

## Rates file format

CSV, **no header row**, comma-delimited, 9 columns per row.

| Col | Field | Notes |
|---:|---|---|
| 1 | State FIPS code | e.g. `27` for Minnesota |
| 2 | Jurisdiction type | empirically: `00`, `01`, `45`, `63` (MN); semantics below |
| 3 | Jurisdiction code | 5-digit code (FIPS-derived) |
| 4 | General sales-tax rate | decimal, e.g. `0.06875` for 6.875% |
| 5 | Food rate | usually same as col 4 |
| 6 | Drug rate | usually same as col 4 |
| 7 | Residential utility rate | usually same as col 4 |
| 8 | Effective from | `YYYYMMDD` |
| 9 | Effective to | `YYYYMMDD`; `29991231` = open-ended |

### Jurisdiction type codes (MN sample, 2026Q2)

Empirical distribution in `MNR2026Q2FEB18.csv` (147 rows total):

| Type | Count | Apparent meaning | Evidence |
|---|---:|---|---|
| `00` | 64 | County | Codes are short; combined with `01` city additions, sums match published locality rates |
| `01` | 73 | City / local jurisdiction | Most rows; rates are typically 0.5%–1.5% (local additions atop state base) |
| `45` | 1 | **State** | Single row per state file; MN's row carries `0.06875` (6.875% state base) |
| `63` | 10 | Special district / transit | Includes the Twin Cities metro area transit tax |

> **WARNING** — the codes are not labeled in the file; the meanings
> above are inferred from data shape + cross-referencing against
> published MN DOR rate lookups. Other states may use different
> codes. SST publishes a full layout spec on their members-only
> page; we have not located the public version yet. **Always
> validate a state's rate output against its DOR's official
> lookup tool before relying on a tier-2 module's parser.**

### Sample rows (MN, 2026Q2)

```
27,45,27,0.06875,0.06875,0.06875,0.06875,20090701,29991231   # MN state base 6.875%
27,01,39878,0.0050,0.0050,0.0050,0.0050,20051001,29991231    # local +0.5%
27,63,52630,0.0150,0.0150,0.0150,0.0150,20250701,29991231    # special district +1.5%
```

## Boundary file format

CSV, **no header row**, comma-delimited, **89 columns per row**.

Two record types are interleaved (col 1):

| Marker | Count (MN 2026Q2) | Meaning |
|---|---:|---|
| `4` | 39,212 | FIPS + 9-digit ZIP record (granular) |
| `z` | 1,346 | ZIP5 range record (less granular but covers the ZIP5 case) |

### Common columns observed (for `z` records)

| Col | Field | Notes |
|---:|---|---|
| 1 | Record type | `z` = ZIP-based |
| 2 | Effective from | `YYYYMMDD` |
| 3 | Effective to | `YYYYMMDD`; `29991231` = open-ended |
| 18 (idx 17) | ZIP5 low | Start of ZIP5 range |
| 20 (idx 19) | ZIP5 high | End of ZIP5 range |
| 23 (idx 22) | State FIPS | e.g. `27` for MN |
| 24 (idx 23) | State FIPS (duplicate) | unclear; always equals col 23 in MN data |
| 25 (idx 24) | County FIPS | 3-digit county code |
| 33, 36, 39 (idx 32/35/38) | Authority code triplets | `ST,80008,63` style: prefix + jurisdiction-id + type |

(Column numbers are 1-based as published by SST; the index column
shows the corresponding 0-based Python list index used by the
parser.)

For `4` records, the layout is similar but with extra columns
covering ZIP+4 ranges and street-level address ranges. Phase 1
focuses on `z` records for ZIP+4 lookup; `4` records become
relevant for Phase 4 (address-level resolution).

### Sample rows (MN, 2026Q2)

```
z,20240401,29991231,,,,,,,,,,,,,,,55001,,55003,,,27,27,163,,,,,,,,,,,ST,80008,63,ST,80009,63,,,,,,,,,,,,,,,
z,20210101,29991231,,,,,,,,,,,,,,,55005,,55009,,,27,27,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,
```

The first row says: ZIP 55001-55003, state 27 (MN), county 163,
with two special-district / transit authorities (`80008`,
`80009`, both type `63`) layered on.

## Parsing strategy for Phase 1

Given the format complexity and the lack of an authoritative
public spec, OpenSalesTax's Phase 1 parser:

1. **Treats the SST CSV as a fixed-column source** based on the
   above empirical layout. Each state module declares which type
   codes it uses (since the codes aren't standardized across
   states).
2. **Yields :class:`~opensalestax.states.protocol.RateRow` and
   :class:`~opensalestax.states.protocol.BoundaryRow` records**
   from raw CSV rows; does no jurisdiction-stack reconstruction
   in the parser layer (that's the engine's job after data load).
3. **Uses the filename to derive the version label** (e.g.
   `MN-SST-2026Q2FEB18`) so reproducibility per constitution §6
   is automatic.
4. **Skips rows with effective_to in the past**, so the loaded
   data set only reflects currently-active rates and boundaries.
   Historical analysis is out of scope for v0.1.
5. **Logs and skips** rows that don't parse — better to load
   what we can and warn about the rest than to fail the whole
   batch.

For tier-2 SST states (the 22 we don't deeply validate in
Phase 1), the parser uses **default type-code mappings**:

- A row with the highest rate for the state is assumed to be the
  state base; all others are local additions.
- Boundary rows assign all overlapping authorities to a ZIP5
  range; the engine combines them at calculation time.

Tier-1 states (MN, WI) override these defaults with state-
specific knowledge.

## Open questions

1. **What does jurisdiction type `00` mean in MN data?** Currently
   inferred as "county"; needs MN DOR confirmation.
2. **Are type codes uniform across SST states?** Probably not.
   The Section G2 rapid rollout will need per-state validation.
3. **Where is the official SST layout spec published?** Not
   located yet. The SST Governing Board likely has a member-
   accessible doc; we may have to email them.
4. **How are sales-tax holidays encoded in the rates file?** Not
   apparent from MN's quarterly file. Likely covered by separate
   per-state DOR notices; punted to Phase 5.

## Sample files for testing

The Phase 1 test suite includes truncated copies of these MN
files as fixtures under
`src/opensalestax/data/fixtures/mn/`. Re-fetch and replace as
needed when validating against new quarters; the file naming
convention pins the upstream version.
