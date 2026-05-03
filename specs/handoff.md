# OpenSalesTax — Session Handoff

**For the next Claude Code session that opens this directory.**

This project is **pre-development**. Specs and research are complete.
Your job is to bootstrap the codebase.

## What to do, in order

### 1. Read the specs

5-10 minutes, in this order:

1. `specs/constitution.md` — non-negotiable principles
2. `specs/current-state.md` — what exists (specs only — no code yet)
3. `specs/research/data-sources.md` — what data is actually available
4. `specs/research/prior-art.md` — what existing solutions do
5. `specs/research/state-coverage.md` — per-state notes
6. `specs/phase-1-foundation/spec.md` — what to build first
7. `CLAUDE.md` (project root) — coding conventions + the "what NOT
   to do" list

### 2. Propose the stack to Eric, get sign-off

The constitution recommends **Python 3.11+ with FastAPI** (with
PostgreSQL 15 + PostGIS). Strong second is **TypeScript + Node**
(Fastify or Hono). Third is Go. Don't ship code until Eric confirms.

Make the proposal concrete:
- Languages compared with one-paragraph trade-off
- Default recommendation: Python + FastAPI
- Reason: data-handling ergonomics + contributor-base size
- Alternative if Eric prefers: Node + TypeScript
- Eric decides; document the choice in
  `specs/decisions/01-stack-choice.md`

### 3. On stack-pick approval, do the bootstrap

Once Eric picks:

1. **Initialize the language scaffold** (e.g., `pyproject.toml` for
   Python+Poetry, or `package.json` for Node).
2. **Create LICENSE** with Apache 2.0 text + copyright line:
   `Copyright 2026 Eric Osterberg and OpenSalesTax contributors`
3. **Initialize git** with first commit message
   `chore: initial scaffold (Phase 1 begin)`
4. **Create the GitHub repo** under `ejosterberg/sales_tax_api_service`
   (or whatever name Eric picks at that moment) and push.
5. **Start Phase 1** per `specs/phase-1-foundation/spec.md`.

### 4. After scaffold, Phase 1 work begins

Phase 1 brings online:

- Database schema (rates, jurisdictions, states, etc.)
- Two SST state modules (recommend MN + WI for the contrast)
- Four API endpoints (calculate, rates, jurisdictions, health)
- Docker image
- CI on GitHub Actions
- Basic OpenAPI docs auto-generated

Roughly 4-6 sessions for Phase 1 if the stack is Python+FastAPI;
5-7 for Node+TS; 6-8 for Go.

### 5. Update `current-state.md` whenever something material ships

The discipline that survives across sessions.

## What you do NOT do

- ❌ Pick the stack without asking Eric.
- ❌ Implement a state module before the core schema + API are in.
- ❌ Add commercial / paid data dependencies (Avalara, TaxJar feeds, etc.).
- ❌ Make it un-self-hostable.
- ❌ Skip the disclaimers (constitution §13).
- ❌ Promise Eric this will replace Avalara on day one — it won't,
  and that's fine. Day one is "free, works for 24 SST states,
  good enough for a small business in those states."

## Standing rules (mirror Eric's other projects)

- Standing permission to commit directly to the default branch.
- Push still asks per-deploy.
- No AI co-author trailers in commits — Eric's project-wide preference.
- Run the test suite (when one exists) before declaring "done."
- Append, don't edit, security audits.

## When you finish

Update `current-state.md` to reflect what shipped. Update this
`handoff.md` to point the next session at the next concrete piece
of work. If you discovered something Eric should know but didn't
build, add it to a "Deferred items" section in the next handoff.
