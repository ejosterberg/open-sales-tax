# Decision 03 — Database

**Date:** 2026-05-02
**Status:** ✅ Accepted
**Decider:** Eric Osterberg
**Recorder:** Claude (bootstrap session)

## Decision

OpenSalesTax supports **both MariaDB 11+ and PostgreSQL 15+** as
first-class production databases via a single SQLAlchemy 2.x
abstraction layer. **PostGIS is recommended (not required) for
Phase 4+ address-level production deployments**; MariaDB users get a
documented R-tree fallback at that point.

This is "Pattern A" from the 2026-05-02 conversation: dual
first-class support from day one, with the architectural keystone
that **the dialect difference must live in SQLAlchemy + Alembic,
never in handwritten conditionals in business logic.**

## Concrete stack

| Layer | Choice |
|---|---|
| ORM | SQLAlchemy 2.x (async support) |
| Migrations | Alembic |
| PostgreSQL driver | `asyncpg` |
| MariaDB driver | `asyncmy` (preferred) or `aiomysql` (fallback) |
| Spatial extensions (Phase 4+) | GeoAlchemy2 with PostGIS for Postgres; native `ST_*` + R-tree spatial index for MariaDB |
| Connection pooling | SQLAlchemy's built-in `AsyncEngine` pool |

## Why both, not just one

**Why include MariaDB:**

- Eric's existing infrastructure runs on MariaDB; he's a fan and
  knows it well.
- The LAMP / PHP contributor base (which OpenSalesTax wants to
  attract — many state-DOR developers and small-biz tooling
  contributors live in this world) is comfortable with MariaDB.
- SC Books (the eventual primary integration target) runs MariaDB.
- One fewer database to provision for self-hosters who already run
  MariaDB.

**Why also include PostgreSQL:**

- PostGIS is the industry-standard for GIS work; Phase 4 +
  performance-sensitive deployments will want it.
- Many OSS infrastructure shops standardize on PostgreSQL; not
  supporting it would be a real adoption tax.
- FastAPI / SQLAlchemy / asyncpg is the dominant Python web stack;
  contributors expect it to work.

**Why not pick one:**

- Picking only PostgreSQL alienates the MariaDB / LAMP world Eric
  is connected to.
- Picking only MariaDB caps the project's ceiling on serious GIS
  work and signals "not enterprise-ready" to PostgreSQL-default
  organizations.

## Cost / risk

This decision adds real ongoing tax. Documenting it openly so
future contributors don't think it's free:

- **Migration authoring:** ~10–15% extra effort. Every Alembic
  migration must work on both engines. Some PostgreSQL features
  (JSONB-specific operators, advanced index types, `LATERAL` joins)
  are off-limits unless we add a dialect-specific branch with
  documented rationale.
- **CI cost:** test matrix doubles (run every test against both
  engines). ~50–80% longer CI runs. Acceptable for
  correctness confidence.
- **Phase 4 fork:** address-level GIS will diverge. The Phase 4
  spec needs to acknowledge: PostGIS gets full point-in-polygon
  with GiST indexes; MariaDB gets `ST_Contains` + R-tree spatial
  index with documented performance caveats. We'll re-evaluate
  whether MariaDB's spatial story is sufficient at that point with
  real performance data instead of speculation.
- **Dependency surface:** two database driver libraries instead of
  one. Both are mature; not a real concern.

## Architectural rules (non-negotiable)

1. **No `if engine == "postgres": ... else: ...` in business logic.**
   The minute that pattern appears, dual-support has failed. All
   dialect differences must live inside SQLAlchemy models, Alembic
   migrations, or a thin `db/dialects/` shim if absolutely needed.
2. **Schema migrations use the portable subset** — INTEGER, VARCHAR,
   TEXT, JSON, BOOLEAN, NUMERIC, TIMESTAMP, DATE, BYTEA/BLOB,
   B-tree and unique indexes. No `JSONB`-only operators (use
   SQLAlchemy `JSON` type which maps to JSONB on Postgres and JSON
   on MariaDB). No PostGIS DDL until Phase 4.
3. **Tests run against both engines.** A test that passes only on
   PostgreSQL is a bug; either fix the test or fix the schema.
4. **Connection-string config is the only place engine selection
   happens** — `OPENSALESTAX_DATABASE_URL=postgresql+asyncpg://...`
   or `mysql+asyncmy://...`. Application code never branches.
5. **Phase 4 PostGIS additions are additive, not replacement.**
   When PostGIS-specific spatial indexes get added, they live in
   their own migration with a `if dialect == 'postgresql'` Alembic
   conditional — the only acceptable place for that pattern.

## Phase-by-phase impact

| Phase | Does dual support cost anything here? |
|---|---|
| 1 (foundation, MN+WI, ZIP+4) | No — schema is plain integer/varchar/JSON; B-tree indexes only |
| 2 (24 SST states) | No — same shape, more rows |
| 3 (CA, first non-SST) | No — still ZIP+4 + state-specific quirks |
| **4 (address-level GIS)** | **Yes** — fork point. PostGIS native vs MariaDB R-tree |
| 5 (taxability matrix) | No — JSON queries work on both |
| 6 (perf + scale) | Maybe — heavy spatial workloads benefit more from PostGIS |
| 7 (client SDKs) | No |

## Consequences for Phase 1 scaffolding

- `pyproject.toml` includes `sqlalchemy[asyncio]>=2.0`, `alembic`,
  `asyncpg`, and `asyncmy` as dependencies.
- `docker-compose.yml` ships **two services** for local dev:
  `postgres:15` and `mariadb:11` (or developer can pick one via
  profiles).
- CI matrix in GitHub Actions runs every test job against both
  engines.
- README quickstart shows both `DATABASE_URL` examples.
- `phase-1-foundation/spec.md` schema updated: `JSONB` → `JSON`;
  forward-reference (rates → data_versions) fixed.

## Alternatives considered

**Pattern B — Postgres-first with "MariaDB-compatible" subset:**
Same SQLAlchemy + Alembic setup but only Postgres in CI. Would
ship v1 faster and require less testing, but the MariaDB story
becomes "almost works, contributor patches welcome" rather than
"officially supported." Rejected because Eric explicitly asked
for first-class MariaDB support.

**SQLite as a third option:** considered for development /
single-binary self-hosters, but rejected because Phase 4 GIS work
on SQLite is meaningfully worse than even MariaDB's spatial story,
and SQLite's concurrent-write story doesn't match production sales-
tax-API workloads. Could be revisited as a "developer convenience"
target if demand emerges.

**Single-database via DuckDB or similar:** novel but immature for
this use case; doesn't have the contributor familiarity advantage.
Rejected.

## References

- `specs/constitution.md` §10 (database) — updated by this decision
- `specs/phase-1-foundation/spec.md` schema — updated
- 2026-05-02 conversation log (Claude session)
- SQLAlchemy 2.x async docs: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- GeoAlchemy2: https://geoalchemy-2.readthedocs.io/
- MariaDB spatial reference: https://mariadb.com/kb/en/spatial-data-types/
