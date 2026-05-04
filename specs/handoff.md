# OpenSalesTax — Session Handoff

**For the next Claude Code session that opens this directory.**

**v0.24.0 is the latest release.** Live at
[github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax)
and prod API at `http://10.32.161.126:8080` (also fronted by
Cloudflare at `https://api.opensalestax.org`). All 52 jurisdictions
are tier-1. SST loader/lookup engine matches every Tier-1 SST
state's published DOR rate within 0.05% across 89 sampled ZIP+4s.

**Pre-built data dumps now ship with every release** (CI workflow
`.github/workflows/build-data-dump.yml`). New users install via
`opensalestax data restore` instead of the 50-minute manual
`data fetch` + `data load` workflow. The manual path remains for
users who want fresher-than-tag DOR data (`Refresh from source`
section in README).

**Multi-agent worktree pattern is the cadence.** When a /loop iter
has multiple independent tracks (e.g. data work + bug fix + CI
infra), spawn 3-6 sub-agents with `Agent({isolation: "worktree"})`,
give each a self-contained brief stating what they CAN'T touch
to avoid file conflicts, then merge their branches. Iter 8
shipped 3 agents in parallel (~1900 lines, 1 hour wall-clock).

**v0.22 deploy gotcha (learned the hard way 2026-05-04):** when the
parser changes (e.g. v0.22's zero-pad of +4 ranges), every SST state
must be RELOADED (`bash ~/sst-load.sh` on the prod VM, ~50 min) —
just rebuilding the container isn't enough because the boundary rows
are baked into the DB at load time. After ANY parser/loader/state-
module change, plan for the full reload window before claiming the
fix is live.

## Where the iter-loop is currently focused

Two parallel tracks:

1. **Friendly authority names** — every batch of states whose
   receipts still read `XX-city-NNNNN` instead of the city name.
   Pattern: probe a known ZIP for that state, identify the missing
   codes, look them up against the state's DOR (or Wikipedia/USPS
   if DOR doesn't publish a code table), build
   `src/opensalestax/states/<state>_names.py`, wire it into the
   state class via `_authority_name`, add a probe unit test, drop
   a row in the DOR-validation grid. Already done: TN, OH, GA, KS,
   NE, WA, OK, NC, WI county, AR, IA (LOST districts), ND, SD,
   UT, WV.
2. **DOR-validation coverage** — keep adding ZIP+4 entries to
   `tests/integration/test_sst_dor_validation.py`. 41 entries as
   of v0.21.0. Each entry is one ZIP+4 + the published DOR rate
   on a specific date.

Remaining major-city friendly-name work (suggestion list, not
exhaustive): UT districts (transit, county options); AR
composite codes; KY non-flat (KY is flat 6%, no work); OH
beyond Cleveland transit; specific NC transit districts; WA
small cities outside Bellevue/Tacoma.

## What to read first

1. `specs/constitution.md` — non-negotiable principles
2. `specs/current-state.md` — what's done, what's next (latest
   release status + feature ladder + v0.6 priorities)
3. `specs/decisions/` — three locked-in decisions (language,
   license, database)
4. `specs/phase-1-foundation/acceptance-walkthrough.md` — honest
   done/deferred per Phase 1 criterion (historical context)

5–10 minutes; saves you from re-deriving anything.

## ⚡ Active session kickoff (if present)

If `specs/NEXT-SESSION-KICKOFF.md` exists, read and execute it
before anything else. Eric reset a session deliberately and that
file contains the immediate next steps.

## If you're spawning state-research agents (Phase 6+)

Eric's directive from 2026-05-03: engage **multiple agents in
parallel**, each researching and implementing one state, with
references documented as we go. The orchestration is documented
in three companion files:

- **`specs/agent-briefs/per-state-research-brief.md`** — the
  canonical instructions for ONE agent assigned to ONE state.
  Spawn each per-state agent with this file as their primary
  brief.
- **`specs/agent-briefs/multi-agent-coordination.md`** — branch
  naming (`feat/state-XX`), worktree strategy, conflict-surface
  files, per-batch checklist for the orchestrator, suggested
  Phase 6/7/8 batching.
- **`specs/research/references.md`** — every external source
  consulted so far, organized by state. Per-state agents MUST
  append their sources here.

## v0.6 candidate priorities (rough order)

Per `specs/current-state.md` "Next-session priorities":

1. **Threshold rules** for NY's <$110 and MA's <$175 clothing
   exemptions. Same shape as the holidays max-amount cap;
   structurally similar to v0.5 work.
2. **`rate_modifier` engine wiring** so IL's 1% reduced grocery
   rate produces correct tax amounts (modifier is stored in v0.4
   but ignored by the engine).
3. **More tier-1 states**: CT, DC, MO, MS, SC, VA — mostly
   mechanical following the CA pattern.
4. **2027 holiday data** for TX, FL, MA, MD once 2027 dates are
   published.
5. **CDTFA loader** for California's ~1,700 district rates --
   first significant non-SST data ingestion.
6. **PostGIS address-level resolution** -- v1.0 territory.
7. **Client SDKs** (Python, JS/TS, PHP for SC Books integration).

## Standing rules (mirror Eric's other projects)

- Standing permission to commit directly to `main`.
- **Push allowed without per-deploy approval** (Eric granted in
  the v0.1 ship-it conversation 2026-05-03).
- No AI co-author trailers in commits.
- **DCO sign-off (`-s`) is required on every commit**, including
  Claude's. CI enforces this on every PR.
- Run the test suite before declaring "done" (`poetry run pytest -q`).
- Run SonarQube scan after each major feature batch
  (~once per section). Token in `~/.claude/sonarqube-playbook.md`;
  scanner CLI lives at
  `/c/Users/ejosterberg/Documents/GITprojects/TicketsCADFixes/sonar-scanner-temp/`.
- Append, don't edit, security audits.

## Tooling notes

- Python 3.11.15 installed via `uv python install 3.11`
- Poetry 2.3.4 installed via `uv tool install poetry`
- Project venv lives in
  `~/AppData/Local/.../pypoetry/Cache/virtualenvs/opensalestax-DTELG93k-py3.11`
- Local Docker not available on Eric's box (CI tests both DBs)
- `gh` token has `gist, read:org, repo, workflow` scopes

## What you do NOT do

- ❌ Re-derive Phase 1 architecture from scratch — read the specs.
- ❌ Add commercial / paid data dependencies (Avalara, TaxJar
  feeds, etc.). Constitution §3.
- ❌ Reverse-engineer commercial sales-tax APIs to derive
  algorithms or schemas. Constitution §2.
- ❌ Skip the disclaimer in any new endpoint. Constitution §13.
- ❌ Promise that v0.1 supports CA, TX, NY, etc. — those are
  Phase 2+. Communicate honestly.
- ❌ Push to GitHub without DCO sign-off (CI will fail and
  embarrass us).
- ❌ Touch `specs/phase-1-foundation/spec.md` after the v0.1.0
  tag — historical record. Add a `changes.md` if implementation
  diverged.

## Where to find things on disk

- Repo root: `C:\Users\ejosterberg\Documents\GITprojects\sales_tax_api_service\`
  (note: local directory name still `sales_tax_api_service`,
  GitHub repo is `open-sales-tax`)
- Settings global: `~/.claude/CLAUDE.md`
- SonarQube playbook: `~/.claude/sonarqube-playbook.md`
- Spec-kit playbook: `~/.claude/spec-kit-playbook.md`

## When you finish

Update `current-state.md` to reflect what shipped. If a phase
completes, mark it ✅ and bump the "Status:" line. Update this
`handoff.md` to point the next session at the next concrete piece
of work. If you discovered something Eric should know but didn't
build, add it to a "Deferred items" section in the next handoff.
