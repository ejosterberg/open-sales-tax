# The Streamlined Sales Tax (SST) quarterly file format

*A field guide for contributors. Last verified against 2026 Q2/Q3
quarterly files.*

The [Streamlined Sales Tax Governing Board](https://www.streamlinedsalestax.org)
publishes free, public rate and boundary files for its 24 member
states. These two files per state are the backbone of every SST-state
module in OpenSalesTax. This page explains what those files actually
look like — the parts the official specification glosses over and the
parts we only learned by loading real data from 24 states across
several quarters.

If you are bringing a new SST state online (see
[state-modules.md](../state-modules.md)) or debugging why a ZIP
resolves to the wrong rate, read this first.

> **Scope.** This describes the *file format*, not tax law. It is not
> legal or tax advice. It is also not the SST Governing Board's
> official specification (which is published on their members' area);
> it is an empirical description compiled from primary-source data by
> the OpenSalesTax project, cross-checked against state Department of
> Revenue rate lookups.

---

## Where the files live

| File | Directory |
|---|---|
| Rates | `https://www.streamlinedsalestax.org/ratesandboundry/Rates/` |
| Boundary | `https://www.streamlinedsalestax.org/ratesandboundry/Boundary/` |

Note the directory is spelled `ratesandboundry` (no `a` in "boundry")
on the live site — a wart worth copying exactly, because a corrected
spelling 404s.

## The filename tells you the version

Every file is named with a self-describing, sortable convention:

```
<STATE><KIND><YEAR>Q<QUARTER><MONTH><DAY>.<ext>
```

| Part | Meaning | Example |
|---|---|---|
| `<STATE>` | Two-letter USPS abbreviation, uppercase | `MN` |
| `<KIND>` | `R` = rates, `B` = boundary | `R` |
| `<YEAR>` | 4-digit calendar year | `2026` |
| `Q<QUARTER>` | Quarter `1`–`4` | `Q2` |
| `<MONTH>` | 3-letter month, uppercase | `FEB` |
| `<DAY>` | Day of month, **1 or 2 digits** | `18` |
| `<ext>` | `csv` or `zip` | `zip` |

So `MNR2026Q2FEB18.zip` is *Minnesota, rates, 2026 Q2, published
Feb 18*. Its boundary sibling is `MNB2026Q2FEB18.zip`.

**The date in the filename is the version.** OpenSalesTax pins each
build to a specific filename so a load is reproducible: two people who
load `MNR2026Q2FEB18` get byte-identical data. This is why the loader
derives its version label (`MN-SST-2026Q2FEB18`) straight from the
filename rather than from the current date.

### Filename gotchas that have actually bitten us

- **Single-digit days.** Most files zero-pad the day, but some don't:
  `WYR2026Q2APR1.csv`, `INR2008Q4MAY7.csv`. The parser accepts a
  1-or-2-digit day. A regex that hard-codes `\d{2}` will silently miss
  these.
- **`.csv` vs `.zip` is per-state and changes over time.** Some states
  publish a bare CSV; others wrap the identical CSV in a ZIP; and an
  individual state migrates between the two across quarters. The
  downloader asks for the extension you specified and, on a 404,
  retries with the other extension — then caches whichever one actually
  exists upstream.
- **UTF-8 BOM.** Vermont's files ship with a byte-order mark (`﻿`) at
  the very start. Read naively, that BOM glues itself to the first
  row's record-type column, turning a boundary row's leading `A` into
  `﻿A`, which fails validation and drops the *entire first record*.
  Left unhandled, VT loaded zero boundaries and Burlington (05401)
  silently fell back to the state-only 6% rate. The reader opens CSVs
  as `utf-8-sig` (and strips the BOM manually when reading from inside
  a ZIP) to defuse this.

---

## The rates file

A headerless CSV, comma-delimited, **9 columns** per row.

| Col (1-idx) | Field | Notes |
|---:|---|---|
| 1 | State FIPS | `27` = Minnesota, `55` = Wisconsin |
| 2 | Jurisdiction **type** | State-specific code — see below |
| 3 | Jurisdiction **code** | 5-digit, usually FIPS-derived |
| 4 | General rate | Decimal, e.g. `0.06875` = 6.875% |
| 5 | Food rate | Often equals col 4 |
| 6 | Drug rate | Often equals col 4 |
| 7 | Residential utility rate | Often equals col 4 |
| 8 | Effective from | `YYYYMMDD` |
| 9 | Effective to | `YYYYMMDD`; sentinel = open-ended |

Sample rows (Minnesota, 2026 Q2):

```
27,45,27,0.06875,0.06875,0.06875,0.06875,20090701,29991231   # state base 6.875%
27,01,39878,0.0050,0.0050,0.0050,0.0050,20051001,29991231    # a city +0.5%
27,63,52630,0.0150,0.0150,0.0150,0.0150,20250701,29991231    # special district +1.5%
```

### The jurisdiction-type code (column 2) is NOT standardized

This is the single most important thing to internalize about SST
files: **column 2 means different things in different states.** In
Minnesota's file the observed codes are:

| Type | Apparent meaning |
|---|---|
| `45` | State base rate (exactly one row per file) |
| `00` | County |
| `01` | City / local municipality |
| `63` | Special district / transit authority |

Other states reuse, omit, or repurpose these numbers. There is no
row that says "type 01 means city" — you infer it from the data shape
and confirm it against the state DOR's published rate lookup. That is
exactly why a state has to be *validated* before it is trusted, and
why OpenSalesTax splits SST states into
[coverage tiers](../state-modules.md#coverage-tiers): a tier-2 module
uses default type-code assumptions; a tier-1 module encodes
state-specific knowledge of what each code actually is.

### The "no end date" sentinel has two spellings

Column 9 marks a still-active rate with a far-future date. States
don't agree on which one:

- `29991231` — year 2999 (used by Minnesota)
- `99991231` — year 9999 (used by Wisconsin; the more common ISO
  convention)

Either must be treated as "open-ended / no expiry." Hard-coding only
one of them will make half the country's rates look expired.

### Blank rate columns are a trap

Some legacy rows carry a real value in the general-rate column but
leave food/drug/utility blank. It is tempting to treat a blank as
zero and keep the row — but doing so once pulled genuine
local-improvement-district rows into states that shouldn't have them
and added ~6% of phantom tax to several Kansas cities on general
retail. OpenSalesTax parses all four rate columns strictly, so a row
with a blank rate column is dropped rather than half-interpreted. The
handful of legitimately-blank rows this loses are all long-expired.

---

## The boundary file

A headerless CSV, comma-delimited, historically **89 columns** per
row — newer quarterlies (e.g. SD and WA in 2026 Q2) ship **90**. The
parser rejects a row only if it is *too short* to index the core
fields; extra trailing columns are tolerated.

The boundary file is what maps a **ZIP code to the set of
jurisdictions** whose rates apply there. Each row's first column is a
record-type marker:

| Marker | Meaning |
|---|---|
| `z` | Covers a whole ZIP5 range — no ZIP+4 narrowing |
| `4` | Carries a ZIP+4 range for address-level precision |
| `a` | Address-level row (used by Vermont) |

SST publishes these markers in mixed case (`z`/`Z`, `a`/`A`); the
parser lowercases them so downstream code can compare without
worrying about per-file casing.

### The columns that matter

Column numbers below are 1-indexed as SST publishes them; the
0-indexed Python list position (what the parser actually uses) is
one less.

| Col (1-idx) | Field | Notes |
|---:|---|---|
| 1 | Record type | `z` / `4` / `a` |
| 2 | Effective from | `YYYYMMDD` |
| 3 | Effective to | `YYYYMMDD`; same two sentinels as the rate file |
| 18 | ZIP5 low | Start of ZIP5 range |
| 19 | ZIP+4 low | Only meaningful on `4` rows |
| 20 | ZIP5 high | End of ZIP5 range |
| 21 | ZIP+4 high | Only meaningful on `4` rows |
| 23 | State FIPS | |
| 25 | County FIPS | Blank on VT `a` rows |
| 26 | City / local jurisdiction code | Maps to a city rate row's col-3 code |
| 30, 31, 32 | First special-district triplet | class, code, type — see below |

(`a` rows are the exception: they carry a single ZIP+4 near col 16
instead of the col 18–21 range, and OpenSalesTax collapses them to a
ZIP5-wide binding so a state's millions of per-street rows don't bloat
the boundary table.)

### One ZIP can stack many districts (the repeating triplets)

From column 30 onward, the row carries **repeating triplets** of
`(intra-state class, jurisdiction code, jurisdiction type)`, each one
binding the ZIP to an additional special district. A single ZIP can
be layered with several:

```
z,20240401,29991231,,,,,,,,,,,,,,,55001,,55003,,,27,27,163,,,,,,,,,,,ST,80008,63,ST,80009,63,,,...
```

That row reads: ZIP **55001–55003**, state **27** (MN), county
**163**, with two special-district authorities — **80008** and
**80009**, both type **63** — layered on top. The parser walks the
tail in steps of three and yields one boundary record per non-blank
triplet, so each district produces its own binding; a row with no
triplets still yields a single record so the state/county/city
bindings are emitted.

### The gotchas that cost real debugging time

- **Phantom "type 45" location codes.** Washington's boundary rows
  carry `L`-prefixed alternate location IDs (e.g. `L1704`, `L1708`)
  as triplets whose type is `45` — the same code the *rate* file uses
  for the state base. Treated as districts, they each re-applied the
  state rate: Bellevue would have returned ~29.3% from five phantom
  "districts" stacked on the real state + city. The parser skips any
  triplet whose type is `45`.
- **ZIP+4 ranges need zero-padding.** SST writes `1` instead of
  `0001` when the leading digits are zero. Compared as strings without
  padding, `"1015"` sorts *between* `"1"` and `"7"`, so a ZIP+4 like
  `73072-1015` spuriously matched Norman ranges `1..7` and McClain
  ranges `1..11` simultaneously. The parser left-pads ZIP+4 values to
  four characters so range comparisons behave numerically.
- **The 90th column.** Don't assume exactly 89 columns. Validate on a
  *minimum* count and index defensively; states have already started
  shipping a wider row.

### One column that is a per-state bonus, not a standard

The SST format lets states populate non-required columns however they
like, so some states smuggle useful data into the tail:

- **West Virginia** puts the plain-text city name in one of its
  boundary columns (e.g. `CHARLESTON`), which let us auto-label all
  98 WV jurisdictions straight from the source file.
- **Kansas** and **Washington** carry short place codes (`CAMCL`,
  `02600`) further along the row.
- Most states leave these columns blank.

Do not build a general labeling strategy on any of these — a column
holding a city name is a *West Virginia* convention, not an SST
feature, and the exact column position differs by state. Survey a
specific state's file (roughly columns 12–21) before assuming anything
lives there. The exact positions we have found so far are tabulated in
[`specs/findings/sst-source-file-quirks.md`](../../specs/findings/sst-source-file-quirks.md)
for the per-state survey.

---

## How OpenSalesTax consumes all this

The parser layer does the least interpretation it safely can:

1. **Filename → version label.** Reproducibility is automatic.
2. **Split, validate column count, yield raw records.** One corrupt
   row is logged and skipped, never fatal to a 40,000-row file.
3. **Drop rows whose effective-to date is in the past**, so a load
   reflects only currently-active rates and boundaries.
4. **Emit one record per district triplet**, leaving the actual
   jurisdiction-stacking math to the calculation engine.

Everything state-specific — what type `01` means, whether a district
applies inside city limits, how to resolve a cross-county ZIP — lives
in the per-state module, not the parser. That separation is what lets
a volunteer add their state without touching shared code.

---

## Further reading

- [Adding or improving a state module](../state-modules.md) — the
  contributor workflow this format underpins.
- [`specs/research/sst-file-format.md`](../../specs/research/sst-file-format.md)
  — the original empirical research notes (column indices, sample
  rows) this page is distilled from.
- [`specs/findings/sst-source-file-quirks.md`](../../specs/findings/sst-source-file-quirks.md)
  — the per-state survey of which bonus columns each state populates.
- The parser itself:
  [`src/opensalestax/data/sst_parser.py`](../../src/opensalestax/data/sst_parser.py)
  and the downloader
  [`src/opensalestax/data/sst.py`](../../src/opensalestax/data/sst.py)
  — every gotcha above is annotated at the line that handles it.
