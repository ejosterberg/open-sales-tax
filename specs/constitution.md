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
from integrating, defeating the project's purpose. AGPL specifically
would force SaaS providers to publish modifications — desirable in
isolation, but the cost of cutting off commercial integrators
(QuickBooks, Xero, ERPs, e-commerce platforms) is too high. We accept
that some SaaS deployers will not contribute back; we engineer
**strong contributor norms** (recognition, public deployer registry,
per-state-maintainer credit) instead of legal enforcement. We
**reserve the right to add a dual-license option later** (Apache OR
AGPL) if norms prove insufficient — going Apache → dual is feasible;
going AGPL → Apache is essentially impossible once contributors
arrive.

### Patent landscape — risk acknowledgment

Sales-tax software exists in a patent minefield. Avalara, Vertex, and
Sovos all hold portfolios. Most "implemented on a computer" patents
from the 2000–2014 era are weak post-*Alice v. CLS Bank* (2014), but
not zero. To minimize risk:

- **Implement from primary sources** — tax law, SST documentation,
  state DOR publications. Do **not** reverse-engineer commercial
  APIs (Avalara, Vertex, Sovos, TaxJar, TaxCloud) to derive
  algorithms or data structures.
- **Don't name features after commercial products.** No
  "AvaTax-compatible," no "TaxCloud-style." Use generic functional
  names.
- **Flag novel algorithms for review** before merging. Textbook
  approaches (rate lookup by ZIP, per-state taxability rules,
  jurisdiction stacking) are safe. Anything described as "a new
  method for…" warrants a quick patent search and documented prior
  art in `specs/`.
- **Vet contributions from current/former employees** of commercial
  tax-software vendors — they may have invention-assignment or
  non-compete obligations that complicate the contributor patent
  grant. Not a blanket exclusion; a documented vetting step.
- **Public design docs in `specs/` serve as dated prior art.** Every
  architectural decision recorded here defends against later
  patent claims.

For the v1 scope (SST data ingestion, ZIP+4 lookup, basic taxability
matrix, REST API), patent risk is **low** — the methods are textbook
and the data is public. Risk grows as the project moves into
address-level GIS resolution, ML-driven product categorization, or
nexus-determination analytics — at which point this section gets
revisited and expanded.

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

OpenSalesTax supports **both PostgreSQL 15+ and MariaDB 11+** as
first-class production databases via SQLAlchemy 2.x. See
`specs/decisions/03-database.md` for the full rationale.

**For Phase 4+ address-level production deployments,** PostgreSQL +
**PostGIS** is recommended for performance and feature reasons
(GiST indexes, `ST_Transform`, ~1000+ spatial functions). MariaDB
deployments at that scale get a documented R-tree fallback using
MariaDB's native `ST_*` functions; sufficient for small-to-mid
production loads but with known performance ceilings.

**For Phase 1–3 deployments** (ZIP+4 lookup, no address-level
spatial), both engines are equivalent. Plain B-tree indexes do
the work; PostGIS / spatial extensions are not required.

### Architectural rules for dual-engine support

These are non-negotiable constraints that keep dual support from
collapsing into spaghetti:

1. **No engine-specific branches in business logic.** All dialect
   differences live inside SQLAlchemy models, Alembic migrations,
   or a thin `db/dialects/` shim. The minute application code has
   `if engine == "postgres": ...`, dual support has failed.
2. **Schema migrations use the portable subset.** INTEGER, VARCHAR,
   TEXT, BOOLEAN, NUMERIC, TIMESTAMP, DATE, BYTEA/BLOB, B-tree
   and unique indexes, SQLAlchemy's generic `JSON` type. No
   PostgreSQL-only `JSONB` operators in queries (use the generic
   JSON path syntax). No PostGIS DDL until Phase 4.
3. **CI runs every test against both engines.** A test that passes
   only on PostgreSQL is a bug; either fix the test or fix the
   schema.
4. **Engine selection is purely connection-string config.**
   `OPENSALESTAX_DATABASE_URL=postgresql+asyncpg://...` or
   `mysql+asyncmy://...`. Application code never branches.
5. **Phase 4 PostGIS additions are additive, not replacement.**
   PostGIS-specific spatial indexes get their own migration with
   an Alembic dialect conditional — the only acceptable place for
   that pattern.

### Cost / risk acknowledgment

Dual-engine support is not free: ~10–15% extra effort on migration
authoring, ~50–80% longer CI runs, and a Phase 4 fork point for
GIS work. The project accepts these costs in exchange for a wider
self-hoster pool (LAMP/PHP devs comfortable with MariaDB) and
clean integration with Eric's MariaDB-based SC Books.

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
- **Verify CI is green after every GitHub update — the work is not
  "done" until it is.** This is a hard rule: **any commit or PR pushed
  to any OpenSalesTax GitHub repository that has CI Actions configured
  must have its resulting CI run watched to completion and confirmed
  successful.** "Pushed" is not "done"; only "CI green" is done.
  Whenever we push a commit or open/update a PR, we must confirm the
  resulting CI run **succeeds** (all jobs green, across the full test
  matrix — e.g. both PostgreSQL and MariaDB legs), not merely that it
  was triggered. Watch the run to completion (`gh run watch <id>
  --exit-status` / `gh pr checks <n>`). A red or errored CI run is
  treated as an incident: stop, diagnose, and fix it (or revert) **in
  the same working session** before moving on or telling Eric the work
  is complete. A local quality gate passing is necessary but NOT
  sufficient — CI exercises engine/matrix conditions (e.g. the MariaDB
  `[mariadb]` extra) that a local run may not. This applies equally to
  autonomous/scheduled runs that push to `main`.
- **A CI-failure notification is never ignored, and never assumed.**
  When GitHub (or Eric) reports a failed run, open the failed job and
  read the actual cause before reacting. Distinguish a **transient
  infrastructure flake** (e.g. `Failed to resolve action download
  info`, runner/network/container-startup errors, registry timeouts)
  from a **real regression** (test/lint/type failure). For a transient
  flake, re-run the failed jobs and confirm the re-run goes green —
  then the requirement is met. For a real regression, treat it as the
  incident above. Either way the run must end green; a failed run left
  un-triaged is a constitution violation.
- Rationale: on 2026-07-04 a locally-green change (making `asyncmy`
  optional) was pushed and a PR opened without watching CI; the MariaDB
  matrix leg failed because CI installed dependencies without the new
  optional extra. The regression was invisible locally and would have
  shipped a broken `main` had CI not been checked. On 2026-07-13 the
  PR #39 merge commit `f6eb0de` sent a "Run failed" notification whose
  first attempt failed on the MariaDB leg at `Failed to resolve action
  download info` — a GitHub-side infrastructure error, not a code fault;
  a re-run (attempt 2) went green. Both cases show why the run must be
  watched *and* the failure cause actually read, not guessed at.

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
- **Contributions require DCO sign-off.** Every commit must include
  a `Signed-off-by:` trailer (`git commit -s`) per the Developer
  Certificate of Origin v1.1 (https://developercertificate.org).
  The sign-off is the contributor's assertion that they have the
  right to submit the contribution under the project's Apache 2.0
  license. This is enforced via a CI check on every PR.
- **No CLA.** Apache 2.0 §5 already grants the project a license to
  inbound contributions; DCO covers provenance. A signed CLA is
  unnecessary friction for a project this size and would not be
  added unless dual-licensing becomes necessary.
- **Recognition over enforcement.** Per-state maintainers, recurring
  contributors, and public deployers are listed in `MAINTAINERS.md`
  / `USERS.md`. This is the project's primary mechanism for
  encouraging contribute-back behavior from SaaS deployers — the
  constitution accepts that some commercial users will not
  contribute, and substitutes social/recognition incentives for
  legal enforcement (see §2 license rationale).

## 15. What changes to this document need

Anything in this constitution can change — it's not chiseled in
stone — but changes need:

1. A documented rationale (PR description or `decisions/` doc).
2. Owner approval (Eric).
3. Update to any spec that referenced the prior version.
4. Migration plan if existing code/data violates the new rule.
