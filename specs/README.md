# OpenSalesTax — specs/

This directory holds the **canonical source of truth** for what
OpenSalesTax is and how it gets built. The pattern is borrowed from
Eric's SC Books project: spec-driven development with flat-file
documents that survive across Claude sessions.

## Why specs

- **Continuity across sessions.** A new Claude session can drop in,
  read these docs, and pick up exactly where the last session
  stopped — no re-deriving the architecture, no re-litigating
  decisions.
- **Contributor onboarding.** A volunteer who wants to add their
  state's module reads `constitution.md` + the relevant phase
  spec and knows exactly how to plug in.
- **Decision provenance.** When someone asks "why did we choose
  Apache 2.0?" or "why FastAPI?" the answer is in the spec, not
  scattered across commit messages.

## Structure

```
specs/
├── README.md            ← this file
├── constitution.md      ← non-negotiable principles. READ FIRST.
├── current-state.md     ← snapshot: what's built, what's open
├── handoff.md           ← what the next session should pick up
│
├── research/            ← background research feeding into design
│   ├── data-sources.md       ← SST + alternatives, with concrete URLs/formats
│   ├── prior-art.md          ← Avalara, TaxJar, TaxCloud, Vertex, Sovos
│   └── state-coverage.md     ← per-state notes, difficulty rating
│
└── phase-NN-<slug>/     ← one directory per work phase
    ├── spec.md          ← user stories + functional requirements (the WHAT)
    ├── plan.md          ← architecture, schema, integration (the HOW)
    └── tasks.md         ← ordered checklist (the EXECUTION ORDER)
```

## Lifecycle

1. **Draft `spec.md`** — describes WHAT and WHY. No implementation talk.
2. **Draft `plan.md`** — describes HOW: architecture, schema, FK
   relationships, security surface. References constitution; flags
   deviations.
3. **Draft `tasks.md`** — ordered atomic checklist. Each task fits
   one focused work block (15-60 minutes).
4. **Implement** — work the task list top-to-bottom. Cross items off
   in commit messages.
5. **Update `current-state.md`** when the phase ships. Add to the
   shipped list.

## Don't

- **Don't edit a `spec.md` after the phase has shipped.** Historical
  record. Add `changes.md` if implementation diverged.
- **Don't bloat specs with code.** Specs describe; code implements.
- **Don't skip `tasks.md`.** A fresh Claude session must be able to
  drop in and execute without re-deriving.

## Where to start a fresh session

```
specs/constitution.md
specs/current-state.md
specs/handoff.md
specs/research/data-sources.md
specs/research/prior-art.md
specs/phase-1-foundation/spec.md     (when it exists)
```

5-10 minute investment that pays back immediately.
