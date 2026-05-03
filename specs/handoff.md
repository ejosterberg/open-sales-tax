# OpenSalesTax — Session Handoff

**For the next Claude Code session that opens this directory.**

**v0.5.0 is the latest release.** Live at
[github.com/ejosterberg/open-sales-tax](https://github.com/ejosterberg/open-sales-tax),
publicly visible, Apache 2.0 licensed, CI green on both
PostgreSQL and MariaDB. SonarQube 0/0/0/0 clean on 3601 LOC.

Five releases shipped in the autonomous 2026-05-03 build session
(v0.2 through v0.5). 16 of 52 jurisdictions at tier 1; 22 more at
tier 2. Sales-tax holidays integrated end-to-end.

## What to read first

1. `specs/constitution.md` — non-negotiable principles
2. `specs/current-state.md` — what's done, what's next (latest
   release status + feature ladder + v0.6 priorities)
3. `specs/decisions/` — three locked-in decisions (language,
   license, database)
4. `specs/phase-1-foundation/acceptance-walkthrough.md` — honest
   done/deferred per Phase 1 criterion (historical context)

5–10 minutes; saves you from re-deriving anything.

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
