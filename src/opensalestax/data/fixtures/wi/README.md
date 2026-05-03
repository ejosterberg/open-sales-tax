# Wisconsin SST fixtures

Real upstream SST files used as test inputs. Captured from
https://www.streamlinedsalestax.org/ on 2026-05-03.

| File | Source | Rows | Purpose |
|---|---|---:|---|
| `WIR2026Q2FEB18.csv` | full upstream rates file (publishes as plain CSV, not ZIP) | 1,941 | rate-parser tests + WI module |

WI's rate file is bigger than MN's because WI represents every
sub-county jurisdiction individually (most US counties have far
more sub-jurisdictions than MN does).

Boundary file is omitted from the bundled fixtures -- WI's
boundary file is several MB and not yet needed for v0.1 testing.

Refresh procedure: see `../mn/README.md`.

These are public-domain government data; no copyright concerns
with bundling them in the repo.
