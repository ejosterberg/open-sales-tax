# CLAUDE.md — sales_tax_api_service

This file gives Claude Code sessions the context they need to work on
**OpenSalesTax**, an open-source US sales tax calculation API.

## ⭐ Read these first (in order)

This project uses a **spec-driven workflow** (same pattern as Eric's
SC Books project). Before writing any code or proposing architecture,
read these files in `specs/`:

1. `specs/constitution.md` — non-negotiable principles (license,
   per-state contributor model, free-data-only, API stability)
2. `specs/current-state.md` — what exists now (likely "nothing —
   pre-build" until phase 1 ships)
3. `specs/handoff.md` — where to start
4. `specs/research/data-sources.md` — comprehensive notes on what
   data is actually available from SST + alternatives
5. `specs/research/prior-art.md` — Avalara, TaxJar, TaxCloud,
   Vertex, Sovos — what they do, where they cost too much, where
   the OSS opportunity lies
6. `specs/research/state-coverage.md` — per-state notes (SST
   member status, data availability, difficulty rating)
7. `specs/phase-1-foundation/spec.md` — initial deliverable

If specs and CLAUDE.md disagree, **specs win** — and update
CLAUDE.md to match.

## Project context

**Owner:** Eric Osterberg (ejosterberg@gmail.com), solo developer
who runs a SaaS, a locksmith shop, and an ITSP.

**Why this exists:** Eric's SC Books accounting project (in
`../CRL-NewAccounting/`) needs reliable sales-tax-rate data and
a calculation engine. Commercial options (Avalara / TaxJar) are
prohibitively expensive for small businesses. SST publishes
free, public data covering 24 states. There's no widely-adopted
open-source alternative wrapping this data into a usable API.
This project fills that gap and could become a community
infrastructure piece.

**Stack:** **NOT YET CHOSEN.** The constitution lays out three
candidates (Python+FastAPI recommended; TypeScript+Node second;
Go third) and the rationale for each. **Don't pick the stack
unilaterally** — propose to Eric in the bootstrap session and
get his sign-off before writing code.

**License:** Apache 2.0 recommended (constitution explains why).
Final call by Eric.

**Hosting model:** Self-hostable as primary (Docker, single binary
when possible). Optional hosted SaaS as a future business model;
should not constrain the OSS architecture.

## Per-state contributor pattern (the architectural keystone)

The defining design choice: **every state is a module with a common
interface.** A volunteer who knows their state's tax law can:

1. Drop in their state's data (rates, boundaries, taxability)
2. Implement any state-specific quirks (e.g., MN treats clothing as
   non-taxable; WI treats it as taxable)
3. Ship test fixtures covering edge cases unique to that state

The core engine handles common patterns (origin/destination
sourcing, jurisdiction stacking, exemption certs); state modules
handle deviations.

The 24 SST states should be **easier to bring online first** —
their data is uniform, machine-readable, and quarterly-updated.
Non-SST states (CA, TX, NY, FL, IL, PA — the big ones) require
per-state work and are where community contributions matter most.

## Data update cadence

SST publishes new rates + boundary files **quarterly** with
explicit version dates in filenames (e.g., `MNR2026Q2APR15.zip`).
Pin a build to a specific upstream release for reproducibility;
ship a CLI command + scheduled job for tenants to refresh.

## API design principles (sketched in spec)

- **Versioned** (`/v1/...`) — never break consumers silently.
- **Idempotent** for calculation calls.
- **Stateless** — no session storage; transaction context passed
  in each request.
- **Cache-friendly** — rate lookups should hit a cache aggressively.
- **Privacy-respecting** — don't log transaction details
  unnecessarily. Aggregate metrics only.
- **Multi-tenant** for the SaaS deployment mode; **single-tenant**
  for self-hosters.

## SC Books integration

The eventual primary consumer is SC Books, sitting at
`../CRL-NewAccounting/`. SC Books currently has Phase 23 tax-data
sources scaffolding (ZipTax, MN DOR clients in
`../CRL-NewAccounting/inc/tax-providers/`). Once OpenSalesTax v1
ships, SC Books can add a third provider that calls this API.

Don't tightly couple — OpenSalesTax should be useful to anyone,
not just SC Books.

## Coding conventions (when stack is chosen)

To be added once Eric picks a stack. Until then:

- **English-language docs first.** Code has to be readable by
  contributors from every state.
- **Tests are mandatory** for every state module. A state without
  tests is not officially supported.
- **No proprietary dependencies.** Everything must be installable
  from the language's public package registry under a
  permissive license (MIT/BSD/Apache compatible).
- **Reproducible builds.** Pin every dependency; pin every
  upstream data version.

## Quality pipeline (mandatory before "done")

Per Eric's global standards:

1. **Tests pass** for every state module touched
2. **Security review** for any new endpoint (input validation,
   rate limiting, auth where applicable)
3. **Conventions check** against the constitution
4. **Self-verification** — actually run the calculation against
   known good answers (the SST publishes test fixtures)

## Git / hosting

Like Eric's other projects: **GitHub initially**
(github.com/ejosterberg/sales_tax_api_service when created),
migrating to Eric's self-hosted GitLab CE if/when his GitLab
migration finishes (see `~/.claude/future-tasks.md`).

## What NOT to do

- **Don't pick the stack without asking Eric.** Propose; he decides.
  (Stack settled 2026-05-02: Python 3.11+ + FastAPI. Database
  pending Eric's confirmation on dual MariaDB+PostgreSQL plan.)
- **Don't import paid datasets.** Free public data only — that's
  the whole point of the project.
- **Don't ship a single state in isolation.** The architecture
  must support N states from day one even if only 1-2 land in
  Phase 1.
- **Don't make it impossible to self-host.** Cloud-only would
  defeat the OSS purpose.
- **Don't promise legal/tax advice.** This is a calculation
  engine; users are responsible for compliance. Disclaim clearly.
- **Don't reverse-engineer commercial sales-tax APIs** (Avalara,
  Vertex, Sovos, TaxJar, TaxCloud) to derive algorithms, schemas,
  or data structures. Implement from primary sources only — tax
  law, SST documentation, state DOR publications. Reading their
  public docs to understand "what tax software does" is fine;
  copying their request/response shapes or proprietary methods is
  not. See constitution §2 (patent risk acknowledgment).
- **Don't name features after commercial products.** No
  `/v1/avatax-compatible/...`, no "TaxCloud-style certification."
  Use generic functional names — they're more accurate and avoid
  trademark/patent provocations.
- **Don't accept commits without DCO sign-off** (`git commit -s`).
  CI enforces this; don't bypass. Constitution §14.
