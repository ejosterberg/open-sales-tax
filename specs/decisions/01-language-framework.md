# Decision 01 — Language and framework

**Date:** 2026-05-02
**Status:** ✅ Accepted
**Decider:** Eric Osterberg
**Recorder:** Claude (bootstrap session)

## Decision

OpenSalesTax will be implemented in **Python 3.11+** using **FastAPI**
as the web framework.

## Rationale

The bulk of the v1 work is not HTTP serving — it's:

1. Parsing 24 quarterly SST data drops in mixed CSV/ZIP formats
2. Normalizing them into a relational schema
3. Building per-state taxability matrices
4. Serving rate lookups + calculation requests over a versioned REST API

Python's strengths align with the work:

- **Data-handling ecosystem.** pandas/polars for tabular wrangling,
  openpyxl for Excel oddities, BeautifulSoup for the SST taxability
  matrix that's HTML-only.
- **FastAPI = OpenAPI 3.x for free.** Constitution §5 mandates a
  versioned, documented API; FastAPI auto-generates OpenAPI from
  Pydantic request/response models. Zero extra work.
- **Pydantic doubles as the API contract.** The same type that
  defines a request validates it at runtime. Eliminates schema-drift
  bugs.
- **Largest contributor base of the three candidates.** Python
  developers outnumber Node-TS and Go developers; the overlap with
  the data-science / civic-tech crowd is high — exactly the people
  most likely to volunteer a per-state module.
- **PostgreSQL + asyncpg / MariaDB + asyncmy** are mature, performant,
  async-friendly stacks.

## Alternatives considered

| Option | Pro | Con | Verdict |
|---|---|---|---|
| **Node + TypeScript** (Fastify or Hono) | Type safety; SC Books JS clients could share types | Data-ingestion ergonomics weaker; ~1 extra session in Phase 1 for SST parser | Strong second; revisit only if SC Books integration becomes the dominant priority |
| **Go** | Single static binary; best ops story; high perf | Smallest contributor pool; ~2 extra sessions in Phase 1 for data-ingestion verbosity | Reject for v1; revisit if scale becomes the binding constraint |
| **PHP** | Eric's home turf | Constitution §9 explicitly recommends against; narrows OSS contributor base significantly | Reject |
| **Ruby / Rust / .NET** | Various | Constitution §9 details; tl;dr smaller pool or wrong-fit | Reject |

## Consequences

- **Tooling:** Poetry for dependency management, ruff for lint+format,
  pytest for tests, pre-commit for local hooks, GitHub Actions for CI.
- **Distribution:** Docker image as primary distribution channel
  (constitution §8). Single-binary distribution is not viable for
  Python without `pyinstaller` workarounds; deferred indefinitely.
- **PostGIS deferred to Phase 4.** Phase 1 ZIP+4 lookup uses plain
  B-tree indexes; no GIS-strong language requirement in v1.

## Open follow-ups

- **Database choice (Decision 03)** — pending Eric's confirmation on
  the dual MariaDB+PostgreSQL plan discussed 2026-05-02. Once
  confirmed, recorded as `03-database.md`.
- **Async runtime details** — `uvicorn` vs `hypercorn`; `asyncpg`
  vs `psycopg3`; etc. — deferred to bootstrap session, not
  architecturally significant.

## References

- `specs/constitution.md` §9 (stack candidates)
- `specs/handoff.md` §2 (stack proposal step)
- Conversation log 2026-05-02 (Claude session)
