# OpenSalesTax — Constitution

> Non-negotiable principles. Every architectural decision, every PR,
> every state-module contribution must align with these. Changes to
> the constitution itself require explicit owner approval.

## 1. Mission

OpenSalesTax exists to give US small businesses a free, self-hostable,
open-source way to **calculate sales tax correctly** for any
transaction. We are not a tax-filing service; we are a calculation
engine and rate-data infrastructure.

## 2. Open source — Apache 2.0

**License:** Apache 2.0.

Rationale:
- **Patent grant** — sales tax is a software-patent minefield (look
  at Avalara's portfolio). Apache 2.0's explicit patent grant
  protects contributors and downstream users.
- **Permissive** — businesses can integrate the code without GPL-
  style copyleft obligations. This maximizes adoption.
- **Industry-standard** — every major OSS infrastructure project
  uses it; contributors are familiar with its terms.
- **Compatible with MIT/BSD downstream** — users can wrap and
  re-license.

GPL-family licenses (GPL, AGPL) were considered and rejected: the
copyleft constraint would discourage commercial accounting software
from integrating, defeating the project's purpose.

## 3. Free public data only

We **only** ingest data that is freely and publicly available without
license fees. Acceptable sources:

- **Streamlined Sales Tax Project** rates + boundary files (24 states)
- **State Department of Revenue** publicly-published rate files
- **US Census Bureau TIGER/Line** geographic boundary data
- **OpenStreetMap** address geocoding (for self-hosters who want it)
- **Government PDFs** (with reasonable web-scraping where ToS permits)

**Not acceptable** — even if cheap:
- TaxCloud/Avalara/TaxJar/Vertex/Sovos paid feeds
- Any data with a "redistribution prohibited" license clause
- Any data behind a registration wall that prohibits caching

A future SaaS deployment of OpenSalesTax may layer on commercial data
for paying customers, but the **OSS core must work without it**.

## 4. Per-state contributor module pattern

This is the architectural keystone:

**Every state is a module with a common interface.** A maintainer who
knows their state's tax law can:

1. Drop in their state's data (rates, boundaries, taxability matrix)
2. Implement state-specific quirks (e.g., MN clothing non-taxable;
   WI clothing taxable; some states tax shipping, some don't)
3. Ship test fixtures covering edge cases unique to that state

The core engine handles common patterns (origin/destination sourcing,
jurisdiction stacking, exemption certs); state modules handle
deviations.

A state without a module is **not officially supported.** A state
module without tests is **not officially supported.**

## 5. API stability

- **Versioned URI prefix** (`/v1/...`).
- **Backward compatibility within a major version** is mandatory.
- **Deprecation requires 12 months notice** with sunset headers.
- **Breaking changes** require a new major version (`/v2/...`).
- Response format documented in OpenAPI 3.x; version every change.
- Idempotent calculation calls — same inputs MUST yield same output
  for the same data version.

## 6. Reproducibility

- **Pin every upstream data version.** A build that ran fine yesterday
  must run fine tomorrow if no inputs changed.
- **SST data files** are pinned to specific quarterly releases
  (e.g., `MN-2026Q2-APR15`).
- **Data refresh** is a deliberate, version-bumping operation —
  not a silent background fetch.
- **Deterministic test outputs** — given pinned data, every test
  yields the same result on every machine.

## 7. Privacy

- **Don't log transaction details unnecessarily.** Aggregate
  metrics only.
- **No PII required** to call the calculation API. An address +
  amount is enough; never demand customer identity.
- **For self-hosters:** logs stay local; nothing exfiltrates.
- **For the eventual SaaS:** explicit per-tenant retention policy;
  customer can purge their request history.
- **GDPR / CCPA awareness** — though most US sales tax doesn't touch
  EU/CA residents, the operator might. Don't paint ourselves into a
  corner.

## 8. Self-hostable as primary deployment

The project must be installable and runnable by any technically-
competent operator on commodity infrastructure:

- **Docker image** as the primary distribution channel (single
  `docker run`).
- **Single binary** if the language permits (Go especially).
- **Docker Compose** example for the full stack (API + database
  + cache).
- **No mandatory cloud dependencies.** No "you must use AWS RDS";
  no "you must have a Stripe account."
- **Optional hosted SaaS** is a future business possibility but
  must not constrain the OSS architecture.

## 9. Stack candidates (decision pending)

The implementation language is **not yet chosen**. Current ranking:

### Recommended: Python 3.11+ with FastAPI

**Pros:**
- Massive contributor base (data-science / web-dev overlap).
- FastAPI gives auto-generated OpenAPI docs + type-safe request/
  response models via Pydantic.
- Excellent CSV / Excel / data-handling library ecosystem (pandas,
  polars, openpyxl) — perfect for ingesting SST quarterly files.
- Async I/O for high-throughput rate lookups.
- PostgreSQL + asyncpg is a mature stack.
- Docker images are straightforward.

**Cons:**
- Single-binary distribution requires `pyinstaller` workarounds.
- GIL limits CPU-bound throughput (mostly N/A for I/O-bound
  rate lookups).

### Strong alternative: TypeScript + Node.js (Fastify or Hono)

**Pros:**
- Aligns with web-developer contributor pool.
- Type safety with TypeScript.
- Excellent OpenAPI tooling (zod-to-openapi, Hono OpenAPI).
- Easy integration target for SC Books (which is PHP but talks
  to JS-friendly APIs constantly).

**Cons:**
- Data ingestion ergonomics weaker than Python.
- Larger contributor pool but skewed away from tax-domain
  expertise.

### Third option: Go

**Pros:**
- Single static binary deploy. Excellent Docker images.
- High performance for rate-lookup workload.
- Standard library covers HTTP, JSON, PostgreSQL well.
- `golang-migrate` mature.

**Cons:**
- Smaller contributor pool than Python or Node.
- Tax-domain Python ecosystem (parsing IRS forms, scientific
  computing) doesn't transfer.
- More verbose for data manipulation.

### Not recommended: PHP, Ruby, Rust, .NET

- **PHP** — Eric's home turf, but narrows OSS contributor base
  significantly. Saved for SC Books integration glue, not the
  core API.
- **Ruby** — declining contributor pool; Rails carries operational
  weight without commensurate benefit.
- **Rust** — performance overkill for I/O-bound workload; tiny
  contributor pool dilutes the per-state-volunteer goal.
- **.NET** — enterprise-y; deters OSS contributors.

**Decision rule:** propose Python+FastAPI in the bootstrap session.
If Eric overrides, document the override in a `decisions/` directory
with rationale.

## 10. Database

Recommended: **PostgreSQL 15+** with **PostGIS** extension for
boundary geometry queries.

Why PostGIS specifically: address-to-jurisdiction lookup is fundamentally
a geometric query ("which polygons contain this point?"). PostGIS is
the mature, free, open standard. Alternatives (in-memory R-trees,
S2 cells) work but reinvent the wheel.

For tenants who don't need address-level resolution (ZIP-only is
"good enough"), PostgreSQL alone with B-tree indexes suffices —
PostGIS becomes optional.

## 11. Data update cadence

- **Quarterly** matching SST publication schedule.
- **Each upstream release** (e.g., `2026Q2APR15`) is a tagged data
  version in the data layer.
- **Data updates are explicit operations** — a CLI command + an
  optional cron, not a silent background poll.
- **Tenants can pin** to a specific quarterly release for
  reproducibility.

## 12. Testing

- **Every state module ships with test fixtures.** A state without
  tests is not officially supported.
- **SST publishes test cases** for member states ("if you compute
  $X for transaction Y, you're correct"). Use these as the gold
  standard.
- **Per-jurisdiction smoke tests** — for each known taxing
  jurisdiction, a known address yields the expected rate.
- **CI runs the full test suite on every PR.** Coverage threshold
  to be set per language.

## 13. What this project is NOT

- **NOT a tax-filing service.** Calculation only. Filing is the
  user's responsibility (or their CPA's, or a paid service like
  TaxCloud's filing arm).
- **NOT legal or tax advice.** Every API response and the
  documentation must clearly disclaim this.
- **NOT a nexus-determination service.** We answer "what's the
  rate at this address" — not "do you owe tax in this state."
  Nexus is a separate, more complex question.
- **NOT for international tax.** US sales tax / use tax only.
  VAT is a different beast.
- **NOT a free hosted service for unlimited use.** The eventual
  SaaS will have rate limits and pricing tiers; the OSS code is
  free to self-host without restriction.

## 14. Governance

- **Initial maintainer:** Eric Osterberg.
- **Per-state maintainers:** community volunteers, listed in
  `MAINTAINERS.md` (to be created).
- **Decision-making:** consensus-seeking; Eric breaks ties until
  the project has 3+ active maintainers.
- **Code of conduct:** Contributor Covenant 2.1 (standard).
- **PR review:** every PR needs at least one maintainer approval;
  state-specific PRs prefer the relevant state maintainer's review.

## 15. What changes to this document need

Anything in this constitution can change — it's not chiseled in
stone — but changes need:

1. A documented rationale (PR description or `decisions/` doc).
2. Owner approval (Eric).
3. Update to any spec that referenced the prior version.
4. Migration plan if existing code/data violates the new rule.
