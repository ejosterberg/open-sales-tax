# Published data dump shipped without 23 taxing states (issue #40)

**Found:** 2026-09-16 (weekly software-improvement sweep)
**Reported by:** external contributor, GitHub issue
[#40](https://github.com/ejosterberg/open-sales-tax/issues/40), 2026-08-15
**Status:** FIXED IN REPO — takes effect on the next release tag (or a
`workflow_dispatch` rebuild of an existing tag)
**Severity:** high — the advertised install path silently returned
"no tax" for roughly half the country

## Symptom

A contributor installed OpenSalesTax two ways (quickstart and Docker)
and reported that ZIP `90210` returned no tax data locally, while the
hosted demo answered correctly. Other ZIPs they tried "appear to work
fine" — the example they load-tested was `55401` (Minneapolis).

## Root cause

`.github/workflows/build-data-dump.yml` builds the published
`opensalestax-dump-<tag>-postgres.sql.gz` release asset. It loaded:

1. Census ZCTA ZIP → state boundaries,
2. the 24 SST states, from their pinned quarterly files,
3. **Arizona** — and no other self-seeded state.

The project ships **24 self-seeded (non-SST) state modules** that carry
their rate data in-tree. Only Arizona had a load step. The other 23 —
every one of them tier-1, every one levying a sales tax — were absent
from every dump the project has ever published:

```
AK AL CA CO CT DC FL HI ID IL LA MA MD ME MO MS NM NY PA PR SC TX VA
```

That is California, Texas, New York, Florida, Pennsylvania and Illinois
among them. `55401` worked because Minnesota is an SST state; `90210`
did not because California is not.

The failure is silent by construction. An unloaded state is not an
error condition — the ZCTA load gives the ZIP a state binding, so the
lookup succeeds and returns an empty jurisdiction list. The API answers
`200` with `combined_rate_pct: 0`. A consumer integrating against it
under-collects 100% of the tax due and sees nothing wrong.

## Why the existing gate did not catch it

The workflow's verification step was:

```bash
if [ "$rates" -lt 1000 ]; then
  echo "::error::Suspiciously low rate count ($rates); aborting"
fi
```

The 24 SST states clear 1,000 rate rows between them, so the check
passed on a dump missing 23 states. It measured a global total when the
property that mattered was per-state presence — a threshold gate
standing in for a coverage gate.

This is the "passes vacuously" smell: the check was real, ran on every
release, and could not fail for the reason it existed.

## Fix

Two changes, both in this commit.

**1. Load every self-seeded state.** A new workflow step loads the
remaining 23. The list is **derived from the state registry at build
time**, not hardcoded:

```bash
mapfile -t SELF_SEEDED < <(poetry run python -c "... all_states() ... self_seeded ...")
```

Self-seeded modules need no upstream fetch — the version label is just
a tag — so the registry is sufficient to load them. A newly contributed
self-seeded state is therefore picked up automatically instead of
silently missing the next dump. Arizona keeps its own step because its
version label is tied to the AZ DOR TPT Rate Table refresh and is
surfaced in the release summary.

**2. Replace the threshold check with a coverage gate.**
`scripts/verify_dump_coverage.py` asserts:

- every registered state module with `has_sales_tax` has at least one
  rate row — registry-derived, so it extends itself as states are added;
- 12 real ZIPs resolve to a non-empty jurisdiction list in the expected
  state, exercised through the same `lookup_jurisdictions_by_zip` the
  API serves from, spanning SST and self-seeded sources and both
  stacked-local and flat-statewide jurisdiction shapes.

It deliberately does **not** assert rate values. Rates change quarterly
by design; asserting them here would duplicate the `DOR_GRID` suite and
turn every legitimate rate change into a release-pipeline failure. The
gate answers "is the data there?", not "is the data current?".

## Verification

- All 23 states confirmed to produce data through the same
  `parse_rates` / `parse_boundaries` path the loader uses: **1,830
  rates and 32,136 boundary rows** in total.
- California's boundary rows for `90210` resolve to exactly
  `California (state)`, `Los Angeles County (county)`,
  `Beverly Hills (city)` — matching what the hosted API returns for
  that ZIP (10.500%).
- Each of the 12 probe ZIPs was checked against the live API before
  being encoded, so the gate ships no unverified expectation.
- The gate was run against a simulation of the exact v0.59.0 dump
  contents (24 SST states + AZ) and correctly reported all 23 missing
  states with an actionable message. That simulation is committed as
  `tests/unit/test_dump_coverage.py::test_gate_rejects_the_dump_that_shipped_with_v0_59_0`.
- The workflow's `mapfile` construct was executed locally in bash and
  returns exactly the 23 expected abbrevs.

## Related: `data restore` was also broken (issue #40, part 3)

The same issue reports `opensalestax data restore` failing with psql
choking on binary garbage. That reproduces and has an independent root
cause, **confirmed but not fixed here** — the contributor's
[PR #41](https://github.com/ejosterberg/open-sales-tax/pull/41) already
fixes it and should get the credit.

`stream_dump_to_psql` passed a `gzip.GzipFile` as `subprocess.run(stdin=...)`.
`subprocess` requires a real OS file descriptor, so it calls
`.fileno()` — and `GzipFile.fileno()` returns the descriptor of the
**underlying compressed file**. Decompression is bypassed entirely and
psql receives gzip magic bytes. Reproduced directly:

```python
fh = gzip.open("t.sql.gz", "rb")
subprocess.run([...], stdin=fh)   # child receives b'\x1f\x8b\x08...'
```

The unit tests could not catch this: they inject a fake `runner`, so
nothing ever exercises the real `subprocess` file-descriptor semantics.

`restore.py` has exactly one commit in its history, so this path has
**never worked** — the "live in under two minutes" flagship install has
been broken since it shipped. Both halves of issue #40 therefore share
a theme: the release-install path had no end-to-end test, only
unit-level mocks and a threshold check.

**Follow-up for whoever merges PR #41:** its fix reads the whole
decompressed dump into memory (`fh.read()`) and passes it via `input=`.
That is correct and a large improvement over broken, but this commit
grows the dump by 23 states, so a future dump could be large enough
that buffering it whole is worth avoiding. Streaming via
`Popen(stdin=PIPE)` + `shutil.copyfileobj` would fix that without
changing behaviour. Not a blocker.

## Open items

- **Existing releases still carry the incomplete dump.** The fix
  applies to the next tag. Republishing the v0.59.0 asset is possible
  via `workflow_dispatch` with `tag: v0.59.0`, which would silently
  improve every future `data restore --release v0.59.0`. Eric's call.
- **PR #41 is unmerged** and unanswered since 2026-08-15. It is a
  well-reasoned first-time external contribution (restore fix, three FK
  indexes with per-index rationale, Dockerfile fixes). It needs a DCO
  sign-off check before merge per constitution §14.
- Issue #40 can be closed on the data question once a dump built from
  this commit is published; the restore question closes with PR #41.
