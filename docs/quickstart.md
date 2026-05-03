# Quickstart

Get OpenSalesTax running locally in 5 minutes.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) + Docker Compose v2
- A free port for the API (default 8080) and the database
  (5432 for Postgres, 3306 for MariaDB)

## 1. Clone and start

```bash
git clone https://github.com/ejosterberg/open-sales-tax.git
cd open-sales-tax

# Choose a database profile
docker compose --profile postgres up -d
# OR
docker compose --profile mariadb up -d
```

The API serves at **http://localhost:8080**. Swagger docs at
**http://localhost:8080/v1/docs**.

## 2. Apply migrations

```bash
docker compose run --rm api alembic upgrade head
```

This creates the six Phase-1 tables in the database. Re-run any
time the schema changes (e.g. when you pull new commits).

## 3. Verify

```bash
# Should return {"status":"ok","version":"0.1.0a2","database_connected":true}
curl http://localhost:8080/v1/health

# Should list 52 jurisdictions; 7 marked tier 1, 22 tier 2, rest tier 0
curl -s http://localhost:8080/v1/states | jq '.total'

# Empty rates response (no data loaded yet)
curl -s 'http://localhost:8080/v1/rates?zip5=55401' | jq
```

## 4. Loading state data (Phase 2)

v0.1 ships the API surface, the schema, the state modules, and a
data fetcher. The end-to-end "fetch upstream → seed database →
queryable rates" pipeline matures in v0.2. Until then, data
seeding is manual:

```bash
# Fetch the current MN SST file into the local cache
docker compose run --rm api opensalestax data fetch MNR2026Q2FEB18.zip

# (Schema for the loader CLI -- not yet wired in v0.1)
# docker compose run --rm api opensalestax data load --state MN \
#     --version MN-SST-2026Q2FEB18
```

For v0.1 you can manually seed the database with the example
rows in [tests/integration/test_api.py](
../tests/integration/test_api.py) `_seed_minnesota_minneapolis()`
to verify the calculation pipeline end-to-end.

## 5. Use a different port or DB URL

The API reads everything from `OPENSALESTAX_*` environment
variables. Set them in a `.env` file at the repo root before
`docker compose up`:

```bash
# .env
OPENSALESTAX_DATABASE_URL=postgresql+asyncpg://user:pass@some-host:5432/db
OPENSALESTAX_RATE_LIMIT_PER_MINUTE=120
OPENSALESTAX_LOG_LEVEL=DEBUG
```

## 6. Tear down

```bash
docker compose --profile postgres down       # stop containers
docker compose --profile postgres down -v    # also delete volumes (lose data)
```

## Next

- Read [docs/api.md](api.md) for endpoint details.
- Read [docs/state-modules.md](state-modules.md) to add or
  improve a state's coverage.
- Read [docs/disclaimer.md](disclaimer.md) for the legal note.
