# Refreshing SST data

The Streamlined Sales Tax (SST) project publishes per-state rate
and boundary files **quarterly**. This page covers how to keep
your OpenSalesTax deployment current.

## What's published when

| Quarter | Effective | Typical publication window |
|---|---|---|
| Q1 | Jan 1 -- Mar 31 | mid-Dec to mid-Jan |
| Q2 | Apr 1 -- Jun 30 | mid-Feb to mid-Apr |
| Q3 | Jul 1 -- Sep 30 | mid-May to mid-Jul |
| Q4 | Oct 1 -- Dec 31 | mid-Aug to mid-Oct |

Files appear at:

- https://www.streamlinedsalestax.org/ratesandboundry/Rates/
- https://www.streamlinedsalestax.org/ratesandboundry/Boundary/

Filename pattern: `<STATE><R|B><YEAR>Q<QUARTER><MONTH><DAY>.<csv|zip>`

Example: `MNR2026Q2FEB18.zip` = Minnesota Rates, 2026 Q2,
published Feb 18.

The publication date in the filename pins to a specific upstream
version per [constitution §6](../specs/constitution.md), so you
can always reproduce a calculation by re-fetching that file.

## Fetching files (v0.1)

Use the bundled CLI:

```bash
docker compose run --rm api opensalestax data fetch MNR2026Q2FEB18.zip
docker compose run --rm api opensalestax data fetch WIR2026Q2FEB18.csv
```

Files are cached under `~/.opensalestax/data/` inside the
container (override via `OPENSALESTAX_DATA_DIR`). Re-fetching a
cached file is a no-op unless the SHA-256 changes.

List what's cached:

```bash
docker compose run --rm api opensalestax data list-versions
```

## Loading data into the database

End-to-end: fetch → load → query.

```bash
# 1. Fetch the SST file (constructs the filename for you)
docker compose run --rm api opensalestax data fetch \
    --state MN --version 2026Q2FEB18

# 2. Load it into the database (idempotent; safe to re-run)
docker compose run --rm api opensalestax data load \
    --state MN --version 2026Q2FEB18

# 3. Verify
docker compose run --rm api opensalestax data status
# state  version                                  fetched_at
# MN     MN-SST-2026Q2FEB18                       2026-05-03T...

# 4. Query the API -- rates now flow from the loaded data
curl 'http://localhost:8080/v1/rates?zip5=55401'
```

### Idempotency

Re-running `data load` for the same `(state, version)` pair
**drops the existing data version and re-inserts** -- safe to
script in a cron job. Cascade rules on the schema clean up the
dependent rates / boundaries automatically.

### Cleanup

```bash
docker compose run --rm api opensalestax data purge \
    --state MN --version 2026Q2FEB18
```

Removes the named data version and cascades to its rates,
boundaries, and any taxability rules tied to it.

### Skipping boundaries

For very large boundary files (or when you want a fast
iteration loop), pass `--skip-boundaries`:

```bash
docker compose run --rm api opensalestax data load \
    --state WI --version 2026Q2FEB18 --skip-boundaries
```

Rate calculations for ZIPs you've separately seeded still work;
ZIPs without a boundary entry return zero with a "no
jurisdictions found" note.

## Recommended cadence

For self-hosted deployments:

- Subscribe to the SST mailing list to catch announcements:
  https://www.streamlinedsalestax.org
- Schedule a cron job that runs `opensalestax data fetch ...` for
  every state you support, weekly. Most weeks the file hash won't
  change (cached) and the fetch is fast.
- After a successful fetch of a NEW quarterly file, manually
  review the parser output before activating -- per
  constitution §11, **data updates are explicit operations, not
  silent background polls.**

## Troubleshooting

**"connection error" or 404 from SST:** the filename may be wrong
(SST uses uppercase 3-letter month abbreviations: JAN, FEB, MAR,
…). Check the directory listing in your browser.

**"Unknown jurisdiction-type code" in logs:** Your state's SST
file uses a code OpenSalesTax doesn't recognize yet. The parser
will skip those rows and continue. Open an issue with the row
sample and your state maintainer can add the code mapping.

**SHA-256 mismatch:** the cached file got corrupted. Delete it
(`rm ~/.opensalestax/data/<filename>`) and re-fetch.
