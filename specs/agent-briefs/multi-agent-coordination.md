# Multi-Agent Coordination Plan

> How to parallelize state-by-state work across multiple Claude
> agents without merge conflicts or duplicate effort.

## The model

For each state-buildout phase (Phase 6 onwards):

1. The **orchestrator session** (the human + a "lead" Claude)
   plans the phase, picks the states to work on, and spawns
   per-state agents.
2. Each **per-state agent** receives:
   - A copy of `specs/agent-briefs/per-state-research-brief.md`
   - The state assignment (USPS abbrev + full name)
   - The current branch / commit hash
   - A worktree or branch identifier (see "Branch strategy" below)
3. The orchestrator **collects and merges** the agents' work,
   resolving any cross-state changes (e.g., shared file edits in
   `states/__init__.py`).
4. After every batch of N merges, the orchestrator runs a
   **SonarQube scan** + **CI verification** + **version bump +
   release tag**.

## Branch strategy

To minimize merge conflicts, every per-state agent works on a
**dedicated branch** off `main`:

```
main
├── feat/state-co (Colorado agent)
├── feat/state-ct (Connecticut agent)
├── feat/state-dc (DC agent)
├── feat/state-hi (Hawaii agent)
└── ...
```

- Branch name: `feat/state-<lowercase-abbrev>`
- One agent per branch; one branch per state
- Agent commits, signs off (`git commit -s`), pushes the branch,
  opens a PR back to main
- Orchestrator squash-merges the PR (one commit per state) so
  the release notes can cite each state's commit cleanly

## Worktree alternative (preferred when running multiple agents
locally on Eric's machine)

Use git worktrees so multiple agents work in parallel without
fighting over the same checkout:

```bash
git worktree add ../open-sales-tax-co feat/state-co
git worktree add ../open-sales-tax-ct feat/state-ct
git worktree add ../open-sales-tax-dc feat/state-dc
```

Each agent runs `poetry install && poetry run pytest` in their
own worktree directory; no checkout collisions, no shared
`__pycache__`.

## Files agents WILL touch (potential conflict surface)

| File | Conflict risk | Mitigation |
|---|---|---|
| `src/opensalestax/states/__init__.py` | High -- all agents add their import here | Each agent inserts ONE line (alphabetically sorted) and signs off; orchestrator resolves alphabetical order on merge |
| `src/opensalestax/states/_tier2.py` | Medium -- only when promoting a tier-2 state to tier 1 | Agents removing a state from `_tier2.py` add a removal note in the PR description so the orchestrator knows what to expect |
| `src/opensalestax/states/catalog.py` | Low -- mostly stable; only changes if a state's notes need updating | Agents avoid touching unless necessary |
| `tests/integration/test_api.py` | Medium -- the parametrized tier-0/tier-1 lists need updating when states promote | Agents add their state to the tier-1 list and remove it from the tier-0 list in their PR |

## Files agents will NOT touch (orchestrator-only)

- `src/opensalestax/__init__.py` (version bump is a release commit)
- `pyproject.toml` (version bump is a release commit)
- `specs/current-state.md` (orchestrator updates after batch ships)
- `specs/handoff.md` (orchestrator updates after batch ships)
- Anything in `src/opensalestax/db/` (schema changes are
  cross-cutting and need explicit coordination)

If an agent thinks it needs to touch one of these, it should
**stop and flag it** in the PR description rather than proceed.

## Suggested phase batching

Each batch should be small enough to review + ship as a single
release tag. Suggested batches:

### Phase 6 — Tier-0 → Tier-1 ratchet (no-state-tax & easy ones first)

Work on the simplest unsupported states first to build muscle
memory. These have minimal local-jurisdiction complexity:

- **Batch A** (~1 hour, 4 states): CT, DC, MD-recheck, RI-recheck
  (CT and DC are state-only; MD/RI are quick verifications of
  existing tier-1/tier-2 status)
- **Batch B** (~1.5 hours, 5 states): SC, VA, MO, MS, ID
  (statewide-only or simple county-add states)
- **Batch C** (~2 hours, 4 states): CO (home-rule complexity),
  LA (parishes), AL (independent locals), HI (GET model)

After Phase 6: 14 + 4 + 5 + 4 = could clear remaining tier-0
states (~13 of 14, since PR is unique).

Tag as **v0.6.0** when Batch A merges; **v0.7.0** at Batch B;
**v0.8.0** at Batch C. Don't conflate batches.

### Phase 7 — Tier-2 → Tier-1 promotion (the 22 SST states)

Promote each tier-2 SST state to tier 1 by adding a full
taxability matrix. This is mostly mechanical because the SST
data already loads:

- One agent per state, one branch per state
- 22 agents could run in parallel if Eric wanted maximum throughput
- More realistically: 4-6 batches of 4-5 states each
- Tag a release after each batch

### Phase 8 — Threshold rules + reduced-rate engine + 2027 holidays

Single-orchestrator phase (cross-cutting feature work, not
state-by-state). Once threshold rules ship, agents can revisit
NY and MA to encode the <$110 / <$175 clothing exemptions.

### Phase 9 — Address-level resolution via PostGIS

Single-orchestrator phase. Affects schema, loader, engine,
boundary parser. Per-state work follows once the framework is in.

### Phase 10 — Client SDKs + hosted SaaS layer

Out of scope for the state-buildout phases. Plan separately.

## Per-batch checklist (orchestrator)

After spawning a batch of agents:

- [ ] Each agent received a copy of `per-state-research-brief.md`
- [ ] Each agent has a unique branch name `feat/state-XX`
- [ ] After all agents complete, fetch every branch and verify
      no two touched the same line of `states/__init__.py`
- [ ] Resolve any conflicts in alphabetical order
- [ ] Run the full local test suite (`poetry run pytest -q`)
- [ ] Run SonarQube scan; address any new findings before tagging
- [ ] Bump version + tag + release notes (cite each state's
      commit in the release notes)
- [ ] Update `specs/current-state.md` coverage table
- [ ] Update `specs/handoff.md` next-priorities section

## Spawning an agent (mechanics)

When using the Claude Agent / Subagent tool, the orchestrator's
prompt to the per-state agent should look like:

```
You are a state-research-and-implementation agent for the
OpenSalesTax project. Your assignment: bring **<STATE NAME>**
(<ABBREV>) up to tier 1.

Before any code:
1. Read specs/agent-briefs/per-state-research-brief.md COMPLETELY
2. Read the example modules cited there
3. Read specs/research/references.md to see what we already know

Then: research, implement, test, document. Sign off every commit.
Push to branch feat/state-<lowercase-abbrev>. Open a PR back to
main with a clear summary of what you verified against external
sources.

Stop and ask the orchestrator if you encounter:
- A schema change that would affect other states
- A statutory ambiguity you can't resolve from primary sources
- A reference that costs money or requires registration
- An existing module that needs refactoring (the `_tier2.py`
  removal case is fine; broader refactors are not)
```

The agent is fully autonomous within those bounds.

## Quality bar all agents must meet

(These are NOT negotiable per agent; they're the project's
constitution + the v0.5 quality bar carrying forward.)

- 0 bugs / 0 vulnerabilities / 0 code smells in SonarQube
- All tests pass on PostgreSQL AND MariaDB in CI
- DCO sign-off on every commit
- Statutory citations in every TaxabilityRule.notes
- references.md updated with every external source consulted
- ruff clean / mypy clean

If an agent's PR doesn't meet the bar, the orchestrator sends it
back rather than merging. Don't let standards slip mid-buildout.
