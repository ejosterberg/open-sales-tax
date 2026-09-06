# `data purge` was broken for every state with boundaries (i.e. every SST state)

**Found:** 2026-09-05, while applying the Arkansas Q4 SST refresh to production
**Status:** FIXED (`passive_deletes=True` on `DataVersion.boundaries`) + regression test added
**Severity:** high — it broke the quarterly-refresh path, which is the project's
core recurring maintenance operation

## Symptom

Running the documented purge step on production:

```
docker exec open-sales-tax-api-1 python -m opensalestax data purge -s AR -v AR-SST-2026Q2MAR02
```

aborted with a NOT NULL violation:

```
DETAIL:  Failing row contains (99443072, 53, 72160, null, null, null, null).
[SQL: UPDATE boundaries SET data_version_id=$1::INTEGER WHERE boundaries.id = $2::INTEGER]
[parameters: [(None, 99443072), (None, 99443073), ...
   ... displaying 10 of 1529489 total bound parameter sets ...
```

SQLAlchemy was trying to set `boundaries.data_version_id = NULL` on 1.53 million
rows.

## Root cause

`Boundary.data_version_id` is declared **NOT NULL** with a **DB-level
`ON DELETE CASCADE`**:

```python
data_version_id: Mapped[int] = mapped_column(
    Integer, ForeignKey(_FK_DATA_VERSIONS_ID, ondelete="CASCADE"), nullable=False
)
```

But the parent side did not tell SQLAlchemy to defer to that cascade:

```python
boundaries: Mapped[list[Boundary]] = relationship(back_populates="data_version")
```

Without `passive_deletes=True`, SQLAlchemy's default behaviour on
`session.delete(parent)` is to **load every child row and nullify its foreign
key** — which is impossible against a NOT NULL column. The DB was already
configured to do the right thing; the ORM was overriding it with something the
schema forbids.

This is the classic mismatch between an ORM-level cascade and a DB-level one.
`Rate` was unaffected because its FK is `ON DELETE SET NULL` and nullable, so
nullification is legal there.

## Why no test caught it

`tests/integration/test_loader.py::test_purge_removes_data_version` has existed
for a long time and even asserts:

```python
boundary_count = len((await async_session.execute(select(Boundary))).scalars().all())
assert boundary_count == 0
```

It passed **vacuously**. No fixture load in the test suite ever creates a
`Boundary` row, so the count was already 0 before the purge and the nullify path
was never exercised. The MN boundary fixture exists on disk as
`MNB2026Q2FEB18-sample.csv`, but `resolve_filename` looks for
`MNB2026Q2FEB18.csv`, so the loader never finds it and silently loads rates only.

A grep confirms it: `Boundary` appears in that test file exactly twice — the
import, and the assert-zero.

So the suite had a test named for the behaviour, asserting the right invariant,
that could not fail.

## Impact

`data purge` was unusable for any state with boundary rows — that is, **every SST
state**. Since an SST quarterly refresh changes the version label
(`AR-SST-2026Q2MAR02` → `AR-SST-2026Q4AUG28`), the loader's built-in
"same-label purge and reinsert" does not apply; the old version must be purged
explicitly or its boundaries double-stack with the new ones and the engine
returns wrong (summed/duplicated) rates.

This may well be part of why the seven-state Q3 SST refresh backlog (AR, ND, NE,
SD, TN, WV, WY) sat unapplied through audits on 07-22, 07-26, 07-31, 08-01,
08-02 and 09-05.

## What actually happened on prod

The purge errored, but the DataVersion row was nevertheless removed — the
DB-level `ON DELETE CASCADE` did the real work, and the ORM's redundant nullify
step is what raised. Post-run integrity was verified clean:

| Check | Result |
|---|---|
| Orphan boundaries (FK to a missing version) | **0** |
| Rates with `data_version_id IS NULL` | **0** |
| AR data versions remaining | `AR-ZCTA-2020`, `AR-SST-2026Q4AUG28` (Q2 gone) |
| AR boundaries on the new version | 1,538,225 |
| Live AR probes (6 corrected + 9 tier-1) | **15/15 exact** |

So Arkansas landed correctly. But that was the database's cascade saving a
broken code path, not the code working.

## Fix

```python
# passive_deletes=True is REQUIRED here, not cosmetic. ...
boundaries: Mapped[list[Boundary]] = relationship(
    back_populates="data_version", passive_deletes=True
)
```

Besides being correct, this is dramatically faster: the DB deletes 1.5M child
rows itself instead of SQLAlchemy loading them all into the session to issue
per-row UPDATEs.

### Regression test

`test_purge_removes_data_version_with_boundaries` builds a `State` +
`DataVersion` + `TaxAuthority` + two `Boundary` rows directly (rather than via a
fixture that silently loads none), then purges and asserts both the version and
its boundaries are gone. It reproduces the production failure exactly and fails
against the unfixed model.

Note this test only runs where `OPENSALESTAX_DATABASE_URL` is set — locally it
skips, but CI runs it on **both** the PostgreSQL and MariaDB legs.

## Follow-ups

1. **The vacuous-assertion pattern is worth hunting elsewhere.** A test that
   asserts `count == 0` after an operation, in a suite where the count was never
   made non-zero, proves nothing. This is the second such structural gap found on
   2026-09-05 — the other being `DOR_GRID` gated behind `-m liveapi` so CI never
   ran it (see `az-aggregator-sourced-rate-errors-2026-09.md`).
2. **Consider loading the MN boundary fixture.** Either rename
   `MNB2026Q2FEB18-sample.csv` to the name `resolve_filename` expects, or teach
   the loader about the sample suffix, so end-to-end loads actually cover the
   boundary path.
3. **Document the purge-then-load sequence for SST refreshes** in the audit
   skill / runbook, including that purge-first is the safe ordering (a missing
   version degrades to a coverage gap; double-stacked versions silently return
   wrong rates).
