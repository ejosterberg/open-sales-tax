# OpenSalesTax

> **Open-source US sales tax calculation API.** Free, self-hostable,
> contributor-driven. Apache 2.0.

[![CI](https://github.com/ejosterberg/open-sales-tax/actions/workflows/ci.yml/badge.svg)](https://github.com/ejosterberg/open-sales-tax/actions/workflows/ci.yml)
[![Build data dump](https://github.com/ejosterberg/open-sales-tax/actions/workflows/build-data-dump.yml/badge.svg)](https://github.com/ejosterberg/open-sales-tax/actions/workflows/build-data-dump.yml)
[![Latest release](https://img.shields.io/github/v/release/ejosterberg/open-sales-tax?label=release&color=blue)](https://github.com/ejosterberg/open-sales-tax/releases/latest)
[![License](https://img.shields.io/badge/license-Apache_2.0-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11%2B-blue.svg)](https://www.python.org/downloads/)
[![DOR-validated](https://img.shields.io/badge/DOR--validated-754_ZIPs-brightgreen)](tests/integration/test_sst_dor_validation.py)
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

> **Do not `pip install opensalestax`.** That PyPI name belongs to this
> project's thin **client SDK** — a wrapper for calling a *running*
> engine — not to the engine itself. The engine is not on PyPI yet, so
> install it from source or run it with Docker. Both are supported and
> tested.

**Prerequisites:** Python 3.11+, a PostgreSQL server you can reach, and
the `psql` client on your PATH (Debian/Ubuntu: `apt install
postgresql-client`; macOS: `brew install libpq`). `data restore` streams
the dump through `psql`, so it is a hard requirement.

```bash
git clone https://github.com/ejosterberg/open-sales-tax.git
cd open-sales-tax
poetry install

# 1. Point at any empty PostgreSQL database
export OPENSALESTAX_DATABASE_URL="postgresql+asyncpg://USER:PASSWORD@HOST:5432/opensalestax"

# 2. Apply the schema
poetry run alembic upgrade head

# 3. Restore the latest pre-built dump (all 48 taxing jurisdictions)
poetry run python -m opensalestax data restore

# 4. Serve the API
poetry run python -m opensalestax serve --port 8080
```

That's it. ``data restore`` downloads
``opensalestax-dump-<latest-tag>-postgres.sql.gz`` (~47 MiB) from the
GitHub release, validates that the dump's schema matches the migration
head you just applied, then streams it through ``psql``. A new install
is ready to answer real US sales-tax queries in well under two minutes.

**Check that it worked.** This system's failure mode is a *well-formed
empty answer*, not an error — an unloaded jurisdiction returns
`combined_rate_pct: 0` and an empty `jurisdictions` list, which is
indistinguishable from a genuine 0% result. So verify explicitly:

```bash
# Expect 48
curl -s localhost:8080/v1/states | jq '[.states[] | select(.has_sales_tax)] | length'
# Expect California + Los Angeles County + Beverly Hills
curl -s 'localhost:8080/v1/rates?zip5=90210' | jq '.jurisdictions'
```

Or run the project's own release gate against your database, which
probes twelve real ZIPs and every registered state:

```bash
poetry run python scripts/verify_dump_coverage.py
```

Pin a specific version:

```bash
poetry run python -m opensalestax data restore --release v0.59.0
```

Restore from a local file (useful for air-gapped installs):

```bash
poetry run python -m opensalestax data restore --file ./opensalestax-dump-v0.59.0-postgres.sql.gz
```

> Releases before v0.59.0 carry a dump that is missing 23 taxing states
> ([#40](https://github.com/ejosterberg/open-sales-tax/issues/40)). If
> you restored one of those, re-run `data restore` to pick up the
> corrected asset.

The dump is regenerated on every release tag by the
[``Build data dump`` workflow](.github/workflows/build-data-dump.yml).
It is data-only (no schema, no API keys); the consumer's own
``alembic upgrade head`` is the source of truth for the schema.

**MariaDB users:** MariaDB support ships as an optional extra so the
default install stays PostgreSQL-only. Install the driver with
``poetry install --extras mariadb`` and point
``OPENSALESTAX_DATABASE_URL`` at a ``mysql+asyncmy://…`` DSN. (If you
use a MariaDB DSN without the extra, the app fails fast with the exact
install command.) The bundled dump is PostgreSQL COPY format, so on
MariaDB fall back to the manual ``data fetch`` + ``data load`` workflow
described under "Refresh from source" below.

### Quickstart with Docker (no Python install)

You need [Docker](https://docs.docker.com/get-docker/) +
[Docker Compose](https://docs.docker.com/compose/install/).

> **Known gap:** the runtime image does not yet ship the `psql` client,
> so `data restore` fails inside the container with "`psql` not found on
> PATH". Until
> [#41](https://github.com/ejosterberg/open-sales-tax/pull/41) lands
> (which adds `postgresql-client`), either build the image with that
> package added or use the source install above. Everything else in this
> Docker path works.

```bash
git clone https://github.com/ejosterberg/open-sales-tax.git
cd open-sales-tax

# Bring up API + PostgreSQL (or use --profile mariadb for MariaDB)
docker compose --profile postgres up -d

# Apply migrations + restore the latest published dump
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m opensalestax data restore

# Hit the API
curl http://localhost:8080/v1/health
curl http://localhost:8080/v1/states | jq '.states[] | select(.has_sales_tax)'

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

**52 registered jurisdictions** (50 states + DC + Puerto Rico), each
shipping a tier-1 maintained module with a taxability matrix and
regression tests. **48 of them levy a sales tax**; the four that do not
-- DE, MT, NH, OR -- are modeled explicitly with `has_sales_tax=False`.
All 48 taxing jurisdictions are loaded into every published data dump.

**Alaska is not one of the four.** It has no *statewide* sales tax, but
many boroughs and cities levy their own, so AK is modeled as a taxing
jurisdiction with local-only rates.

Coverage by data source -- which is what actually predicts refresh
cadence and failure modes:

| Data source | Count | States |
|---|---|---|
| SST quarterly rate + boundary files | 24 | AR, GA, IA, IN, KS, KY, MI, MN, NC, ND, NE, NJ, NV, OH, OK, RI, SD, TN, UT, VT, WA, WI, WV, WY |
| Self-seeded from state DOR publications (data in-tree) | 24 | AK, AL, AZ, CA, CO, CT, DC, FL, HI, ID, IL, LA, MA, MD, ME, MO, MS, NM, NY, PA, PR, SC, TX, VA |
| No sales tax at any level | 4 | DE, MT, NH, OR |

Known gaps *within* a covered state: **CO** home-rule cities and **LA**
parish-level collectors await the SubJurisdiction Protocol work, so
their sub-state stacking is incomplete. Flat-rate states (CT, DC, MA,
MD) have no locals to model and resolve through the Census ZCTA
ZIP-to-state binding.

**754 ZIPs across all 52 jurisdictions are validated against published
state DOR rates** (791 assertions) on every
release ([the live regression test](tests/integration/test_sst_dor_validation.py)).
CI auto-rebuilds the
[pre-loaded data dump](https://github.com/ejosterberg/open-sales-tax/releases/latest)
on every release tag, gated on a coverage check that fails the build if
any taxing jurisdiction is missing.

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
# {"status":"ok","version":"0.54.0","database_connected":true}
```

### 2. List the jurisdictions that levy a sales tax

```bash
curl -s https://api.opensalestax.org/v1/states \
  | jq '.states[] | select(.has_sales_tax) | .abbrev'   # 48 rows
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

**You don't have to write Python to help.** If you know your state's
sales tax — as a tax preparer, accountant, business owner, or
DOR-watcher — you can report a wrong rate or adopt a state without
touching code. Start with
[Help your state without writing Python](docs/contributing-without-code.md).

The architectural keystone is the **per-state contributor pattern**:
every state is a Python module implementing a small Protocol.
Maintainers are listed per-state in [MAINTAINERS.md](MAINTAINERS.md).

To add or improve your state's module in code, see
[docs/state-modules.md](docs/state-modules.md). For plain-English
explainers of the underlying data files and the non-obvious parts of
each state's tax law, see the
[legislation & data-format field guides](docs/legislation/README.md).

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
