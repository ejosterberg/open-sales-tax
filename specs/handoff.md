# OpenSalesTax — Session Handoff

**For the next Claude Code session that opens this directory.**

Phase 1 is **shipped as v0.1.0**. Live at
[github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax),
publicly visible, Apache 2.0 licensed, CI green on both
PostgreSQL and MariaDB.

## What to read first

1. `specs/constitution.md` — non-negotiable principles
2. `specs/current-state.md` — what's done, what's next (Phase 1 ✅)
3. `specs/phase-1-foundation/acceptance-walkthrough.md` — honest
   done/deferred per criterion + what v0.2 should ship next
4. `specs/decisions/` — three locked-in decisions (language,
   license, database)

5–10 minutes; saves you from re-deriving anything.

## Phase 2 priorities (rough order)

Per the v0.2 plan in
`phase-1-foundation/acceptance-walkthrough.md`:

1. **`opensalestax data load --state <X> --version <Y>`** — wires
   the existing fetcher + state-module parsers into the database.
   This is the missing piece that makes "fetch upstream → query
   the API → get a real rate" work end-to-end without manual SQL
   seeding.
2. **`opensalestax data activate`** — switch the live data
   version per state.
3. **API-key auth mode** — already plumbed in `settings.py` and
   exposed in `/v1/openapi.json`; needs the middleware + an
   `api_keys` table + a key-management CLI.
4. **First non-SST tier-1 state** (California is the
   highest-impact target per Sovos research).
5. **Per-state address-fixture sweep** for the 22 tier-2 modules
   — needs state-maintainer engagement, not just code.

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
