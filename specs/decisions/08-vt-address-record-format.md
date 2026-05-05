# Decision 08: Vermont 'A' (address-level) boundary records

**Status:** Open (deferred) -- recorded 2026-05-05 during iter 22 spot-check.

## Context

Vermont's local sales tax landscape is mechanically simple: ~17
incorporated municipalities have adopted a flat 1% Local Option
Sales Tax (LOST) under 24 V.S.A. section 138, layered on top of
the 6% state rate (32 V.S.A. section 9771). Burlington 05401
should therefore return 7%, not the 6% currently observed on the
live API.

The VT module
([`vermont.py`](../../src/opensalestax/states/vermont.py)) docstring
already flags this as a known v1 limitation
("under-collects by 1 percentage point for LOST municipalities").
Iter-22 surfaced the **root cause** by inspecting the upstream SST
quarterly file (`VTB2026Q2FEB20.zip`):

- The VT rate file (`VTR...csv`) **does** ship 28 active type-01
  rows at 1% each, including FIPS Place 10675 (Burlington), 70750
  (Stowe), 84475 (Wilmington), etc. Our loader picks these up
  (visible in the DB as `VT-city-10675`, etc.).
- The VT boundary file (`VTB...csv`) ships records of type **'A'**
  (address-level, full street + ZIP+4 + city) instead of the
  type 'z' (zip-wide) and type '4' (ZIP+4 range) records used by
  every other SST state we've loaded so far.
  [`sst_parser.py`](../../src/opensalestax/data/sst_parser.py)
  rejects unknown record types with a warning, so all VT 'A' rows
  are silently dropped -- which is why no VT city authority has
  any boundary rows in the DB and why Burlington 05401 returns
  state-only.

The 'A' format also uses different column positions than 'z'/'4'
records (zip5 is at column 15 in 'A', column 17 in 'z'/'4'), so
naively accepting the record type would extract garbage.

## Why deferred

Two viable fixes; neither fits cleanly into a single ratchet iter:

**Option A: Add 'A' record handling to the parser.** Cleanest
long-term answer. Lets the SST file stay the source of truth for
VT (and any other state that switches to 'A' records). Requires:

1. Extending `SstBoundaryRecord` and `parse_boundary_csv` to
   recognize record_type == 'a'.
2. Parsing the 'A'-specific column layout (zip5 at col 15, city
   code at col 25, state/county FIPS at cols 22/23).
3. Collapsing the millions of street-level rows into a single
   per-(zip5, city_code) boundary row at load time (otherwise
   we'd insert millions of redundant rows per state).
4. Tests that exercise both 'z'/'4' and 'A' fixtures.

**Option B: Hardcode VT LOST cities** in a vt_data.py table,
mirroring the AZ/CA/AL pattern. Faster but state-scoped:

1. Curate the ~17 LOST cities + their ZIP coverage from VT Dept of
   Taxes (`https://tax.vermont.gov/business/lot/municipalities`).
2. Override `Vermont.parse_boundaries` to emit zip-wide bindings
   for each LOST municipality.
3. Ship friendly names directly (no FIPS placeholders).

## Recommendation

When the next contributor touches VT, prefer **Option A** -- the
'A'-record handling helps any future state on the same format.
**Option B** is fine as a short-term workaround if VT compliance
becomes urgent before someone has time for the parser work; it
should ship behind a follow-up TODO to migrate to the SST-driven
path once Option A lands.

## Workaround until fixed

The VT module's docstring already disclaims this:

> For the LOST-adopted edge case the v1 calculation under-
> collects by 1 percentage point on transactions in those 17
> municipalities; the seller in such a municipality would need to
> manually collect the additional 1% to remain compliant with
> 24 V.S.A. section 138.

No code change required for the workaround; this decision doc just
captures the diagnosis so the next session doesn't re-derive it.

## How to apply when ready (Option A path)

1. Add a new test fixture under `tests/data/sst-fixtures/vt/`
   carrying ~50 sample 'A'-record rows from `VTB2026Q2FEB20.csv`.
2. Extend `parse_boundary_csv` to recognize `record_type == "a"`
   and read columns at the 'A'-specific positions.
3. Add a coalesce step in the loader: for 'A' rows, group by
   (zip5, city_code) and emit one Boundary row per group.
4. Reload VT in prod and verify Burlington 05401 returns 7.0%
   on `/v1/calculate`.
5. Add Burlington 05401 to
   `tests/integration/test_sst_dor_validation.py` with a 7.0%
   expected rate.
