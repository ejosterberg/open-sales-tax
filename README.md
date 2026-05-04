# OpenSalesTax

> **Open-source US sales tax calculation API.** Free, self-hostable,
> contributor-driven. Apache 2.0.

[![CI](https://github.com/ejosterberg/open-sales-tax/actions/workflows/ci.yml/badge.svg)](https://github.com/ejosterberg/open-sales-tax/actions/workflows/ci.yml)

OpenSalesTax answers one question for any US transaction: **how
much sales tax should I charge?** It uses free public data from
the Streamlined Sales Tax (SST) project plus per-state contributor
modules to cover the messy reality of US sales tax (~13,000 taxing
jurisdictions, every state with its own quirks).

⚠️ **Calculation only. Not legal or tax advice.** Verify against
your state Department of Revenue before remitting.

## Quickstart (recommended): under two minutes

Pre-loaded PostgreSQL database dumps ship with every release tag,
so a fresh install can be live without spending ~50 minutes
fetching SST data and loading every state by hand.

```bash
pip install opensalestax

# 1. Point at any empty PostgreSQL database
export OPENSALESTAX_DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:5432/opensalestax"

# 2. Apply the schema
alembic -c $(python -c "import opensalestax, pathlib, os; print(os.path.join(pathlib.Path(opensalestax.__file__).parent.parent.parent, 'alembic.ini'))") upgrade head

# 3. Restore the latest pre-built dump (all 24 SST states + AZ)
opensalestax data restore

# 4. Serve the API
opensalestax serve --port 8080
```

That's it. ``opensalestax data restore`` downloads
``opensalestax-dump-<latest-tag>-postgres.sql.gz`` from the GitHub
release, validates that the dump's schema matches the migration head
you just applied, then pipes it through ``psql``. A new install is
ready to answer real US sales-tax queries in well under two minutes.

Pin a specific version:

```bash
opensalestax data restore --release v0.23.0
```

Restore from a local file (useful for air-gapped installs):

```bash
opensalestax data restore --file ./opensalestax-dump-v0.23.0-postgres.sql.gz
```

The dump is regenerated on every release tag by the
[``Build data dump`` workflow](.github/workflows/build-data-dump.yml).
It is data-only (no schema, no API keys); the consumer's own
``alembic upgrade head`` is the source of truth for the schema.

**MariaDB users:** the bundled dump is PostgreSQL COPY format;
fall back to the manual ``data fetch`` + ``data load`` workflow
described under "Refresh from source" below.

### Quickstart with Docker (no Python install)

You need [Docker](https://docs.docker.com/get-docker/) +
[Docker Compose](https://docs.docker.com/compose/install/).

```bash
git clone https://github.com/ejosterberg/open-sales-tax.git
cd open-sales-tax

# Bring up API + PostgreSQL (or use --profile mariadb for MariaDB)
docker compose --profile postgres up -d

# Apply migrations + restore the latest published dump
docker compose run --rm api alembic upgrade head
docker compose run --rm api opensalestax data restore

# Hit the API
curl http://localhost:8080/v1/health
curl http://localhost:8080/v1/states | jq '.states[] | select(.tier > 0)'

# Calculate sales tax on a $100 general purchase in Minneapolis
curl -X POST http://localhost:8080/v1/calculate \
  -H 'Content-Type: application/json' \
  -d '{
    "address": {"zip5": "55401"},
    "line_items": [{"amount": "100.00", "category": "general"}]
  }'
```

Visit **http://localhost:8080/v1/docs** for the auto-generated
Swagger UI.

## What's covered (Phase 1, v0.1)

| Coverage tier | Count | States |
|---|---:|---|
| **Tier 1** -- fully maintained (taxability matrix + tests) | 7 | MN, WI, AK, DE, MT, NH, OR |
| **Tier 2** -- rate-only via SST data, default taxability | 22 | AR, GA, IA, IN, KS, KY, MI, NE, NV, NJ, NC, ND, OH, OK, RI, SD, TN, UT, VT, WA, WV, WY |
| **Unsupported** (Phase 2+) | 23 | CA, TX, NY, FL, IL, PA, AL, AZ, CO, CT, DC, HI, ID, LA, MD, MA, MS, MO, NM, PA, PR, SC, VA |

## Refresh from source (current DOR data)

The pre-built dump is rebuilt on every release tag and pinned to
the SST quarterly file current at release time. If you need data
fresher than the latest tag -- typically because a state DOR has
published mid-quarter rate changes -- bypass the bundled dump and
load directly from the upstream sources:

```bash
docker compose run --rm api opensalestax data fetch \
    --state MN --version 2026Q2FEB18
docker compose run --rm api opensalestax data load \
    --state MN --version 2026Q2FEB18
```

The API now returns Minnesota's actual SST rates (state base
6.875% plus any local additions) for any covered ZIP. See
[docs/data-refresh.md](docs/data-refresh.md) for the full
fetch / load / status / purge workflow.

This is the only path supported on **MariaDB** -- the bundled
release dump is PostgreSQL COPY format.

## API reference

Auto-generated OpenAPI 3.x:
- Spec: `GET /v1/openapi.json`
- Swagger UI: `GET /v1/docs` (interactive "Try it out")
- ReDoc: `GET /v1/redoc` (read-optimized)

Endpoints:

| Method | Path | Purpose |
|---|---|---|
| GET | `/v1/health` | Liveness + DB connectivity |
| GET | `/v1/states` | Coverage tier for all 52 jurisdictions |
| GET | `/v1/rates?zip5=&zip4=` | Active jurisdictional rate stack |
| POST | `/v1/calculate` | Tax decomposition for line items |

See [docs/api.md](docs/api.md) for request/response examples.

## Try it out

A live development instance runs at `http://10.32.161.126:8080`.
Open `/v1/docs` in a browser for an interactive Swagger UI with
"Try it out" buttons that prefill realistic request bodies.

Or try these curl recipes:

### 1. Health check

```bash
curl -s http://10.32.161.126:8080/v1/health
# {"status":"ok","version":"0.7.1","database_connected":true}
```

### 2. List tier-1 states

```bash
curl -s http://10.32.161.126:8080/v1/states \
  | jq '.states[] | select(.tier == 1) | .abbrev'
```

### 3. Calculate tax with per-jurisdiction breakdown

```bash
curl -s -X POST http://10.32.161.126:8080/v1/calculate \
  -H 'Content-Type: application/json' \
  -d '{
    "address": {"zip5": "55401"},
    "line_items": [
      {"amount": "100.00", "category": "general"},
      {"amount": "50.00", "category": "clothing"}
    ]
  }' | jq
```

The response includes per-line `jurisdictions[]` with `name`, `type`,
`rate_pct`, and `tax` (dollar amount). The line's `tax` equals the
sum of its jurisdictions' `tax` values exactly -- accounting callers
can reconcile state/county/city/district splits.

### 4. Inspect rate stack for a ZIP

```bash
curl -s 'http://10.32.161.126:8080/v1/rates?zip5=55401' | jq
```

### 5. Holiday-aware calculation (TX back-to-school)

```bash
# A $75 clothing item is exempt during the August holiday in Texas
curl -s -X POST http://10.32.161.126:8080/v1/calculate \
  -H 'Content-Type: application/json' \
  -d '{
    "address": {"zip5": "75201"},
    "line_items": [{"amount": "75.00", "category": "clothing"}]
  }' | jq '.lines[0].note'
```

## Contributing

Yes please! See [CONTRIBUTING.md](CONTRIBUTING.md).

The architectural keystone is the **per-state contributor pattern**:
every state is a Python module implementing a small Protocol.
Maintainers are listed per-state in [MAINTAINERS.md](MAINTAINERS.md).

To add or improve your state's module, see
[docs/state-modules.md](docs/state-modules.md).

## License + provenance

[Apache License 2.0](LICENSE). DCO sign-off
(`git commit -s`) required on every commit.

Built on free public data:
- [Streamlined Sales Tax Project](https://www.streamlinedsalestax.org)
  rates and boundary files (24 member states)
- US Census TIGER/Line shapefiles (planned for Phase 4)
- State Department of Revenue publications (per-state)

We deliberately do **not** ingest paid feeds (Avalara, TaxJar,
Vertex, Sovos, TaxCloud). See [constitution §3](specs/constitution.md).

## Status

**v0.2 in flight.** v0.1 shipped the API + 29-state coverage;
v0.2 lands the data-load CLI (this batch), API-key auth mode,
and the first non-SST tier-1 state. Production self-hosting is
viable today for SST states.
