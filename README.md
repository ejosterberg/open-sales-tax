# OpenSalesTax

> **Open-source US sales tax calculation API.** Free, self-hostable,
> contributor-driven. Apache 2.0.

[![CI](https://github.com/ejosterberg/open-sales-tax/actions/workflows/ci.yml/badge.svg)](https://github.com/ejosterberg/open-sales-tax/actions/workflows/ci.yml)
[![Build data dump](https://github.com/ejosterberg/open-sales-tax/actions/workflows/build-data-dump.yml/badge.svg)](https://github.com/ejosterberg/open-sales-tax/actions/workflows/build-data-dump.yml)
[![Latest release](https://img.shields.io/github/v/release/ejosterberg/open-sales-tax?label=release&color=blue)](https://github.com/ejosterberg/open-sales-tax/releases/latest)
[![License](https://img.shields.io/badge/license-Apache_2.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![DOR-validated](https://img.shields.io/badge/DOR--validated-316%2F316_ZIPs-brightgreen)](tests/integration/test_sst_dor_validation.py)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![DCO](https://img.shields.io/badge/DCO-required-blue)](https://developercertificate.org/)

OpenSalesTax answers one question for any US transaction: **how
much sales tax should I charge?** It uses free public data from
the Streamlined Sales Tax (SST) project plus per-state contributor
modules to cover the messy reality of US sales tax (~13,000 taxing
jurisdictions, every state with its own quirks).

**Live demo**: [demo.opensalestax.org](https://demo.opensalestax.org) ·
**Live API**: [api.opensalestax.org](https://api.opensalestax.org/v1/docs)

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

# 3. Restore the latest pre-built dump (all 52 jurisdictions)
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

## What's covered

All 52 US sales-tax jurisdictions (50 states + DC + Puerto Rico) are
**tier-1 maintained** -- meaning each ships a per-state module with
a taxability matrix and is exercised by the regression tests. The
five no-sales-tax states (AK, DE, MT, NH, OR) are correctly modeled
with `has_sales_tax=False`.

Per-locality coverage breakdown:

| Coverage type | States | How |
|---|---|---|
| Full SST data (rates + boundaries from quarterly file) | 24 SST member states | AR, GA, IA, IN, KS, KY, MI, MN, NE, NC, ND, NJ, NV, OH, OK, RI, SD, TN, UT, VT, WA, WI, WV, WY |
| Per-county + per-city seeded from state DOR | 16 non-SST self-seeded | AZ, CA, FL, NY, TX, IL, PA, MO, MS, SC, VA, AL, NM, HI (with county surcharges), PR (with municipal SUT), CT (flat statewide) |
| Statewide flat rate (no locals to model) | 3 | DC, MD, MA |
| Tier-1 no-sales-tax | 5 | AK, DE, MT, NH, OR |
| Pending SubJurisdiction Protocol architectural work | 2 | CO (home-rule cities), LA (parishes) |

**316 ZIPs validated against published state DOR rates** on every
release ([the live regression test](tests/integration/test_sst_dor_validation.py)).
The grid spans every state with locals; CI auto-rebuilds the
[pre-loaded data dump](https://github.com/ejosterberg/open-sales-tax/releases/latest)
on every release tag.

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

A live instance runs at [api.opensalestax.org](https://api.opensalestax.org/v1/docs).
Open `/v1/docs` in a browser for an interactive Swagger UI with
"Try it out" buttons that prefill realistic request bodies.

The [demo site](https://demo.opensalestax.org) has click-to-run
calculators for Minneapolis, Dallas, San Francisco, and NYC.

Or try these curl recipes:

### 1. Health check

```bash
curl -s https://api.opensalestax.org/v1/health
# {"status":"ok","version":"0.52.0","database_connected":true}
```

### 2. List tier-1 states

```bash
curl -s https://api.opensalestax.org/v1/states \
  | jq '.states[] | select(.tier == 1) | .abbrev'
```

### 3. Calculate tax with per-jurisdiction breakdown

```bash
curl -s -X POST https://api.opensalestax.org/v1/calculate \
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
curl -s 'https://api.opensalestax.org/v1/rates?zip5=55401' | jq
```

### 5. Holiday-aware calculation (TX back-to-school)

```bash
# A $75 clothing item is exempt during the August holiday in Texas
curl -s -X POST https://api.opensalestax.org/v1/calculate \
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

Active development. Latest stable: see the
[releases page](https://github.com/ejosterberg/open-sales-tax/releases/latest).
Production self-hosting is viable today for every state listed in the
coverage table above.

Recent releases ship via the [`Build data dump`](https://github.com/ejosterberg/open-sales-tax/actions/workflows/build-data-dump.yml)
workflow that pre-loads every state's data into a PostgreSQL dump and
attaches it as a release asset, so a fresh install can call
`opensalestax data restore` and be live in under two minutes.
