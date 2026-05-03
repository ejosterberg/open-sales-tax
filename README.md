# OpenSalesTax — open-source US sales tax calculation API

> **Status: pre-development.** Project specification + research complete (2026-05-02).
> Ready for an implementation session to bootstrap.

## Why this project exists

US sales tax is one of the most complex compliance burdens for small
businesses. There are **~13,000 distinct taxing jurisdictions** in the US
(state + county + city + special district), each with its own rate, its
own definitions of what's taxable, and its own filing schedule.

Commercial solutions (Avalara, Vertex, Sovos, TaxJar) charge **$50-500+
per month** for small-business plans, and far more at scale. Their data
is closed; their APIs proprietary.

The **Streamlined Sales Tax (SST) project** has produced *free, public,
machine-readable* rates and boundary data for **24 member states** since
2005, updated quarterly. **TaxCloud** offers free filing for those 24
states under SST certification but is otherwise commercial.

**The gap:** there is no widely-adopted, self-hostable, open-source API
that small businesses or other accounting projects can drop into their
stack to calculate sales tax correctly. This project aims to be that.

## What this is (vision)

- An **API server** that calculates sales tax for any US transaction.
- Self-hostable (Docker / single binary), **OR** consumable as a SaaS
  for users who don't want to host.
- Per-state coverage starting with the 24 SST states (free public
  data) and growing to non-SST states via community contributions.
- **Per-state contributor module** pattern — one volunteer per state
  can maintain that state's data, taxability matrix, and edge cases.
- License: **Apache 2.0** (recommended — strong patent grant, broad
  contributor friendliness).
- Reference implementation that other accounting projects (including
  [SC Books](https://github.com/ejosterberg/scbooks)) can integrate.

## Status

**Not built yet.** What exists today:

- Detailed spec + research in `specs/`
- Architectural recommendations
- Phase-1 implementation plan ready for a Claude session to execute

## How to start (next session)

If you're a Claude session bootstrapping this project, **read in order:**

1. `specs/constitution.md` — non-negotiable principles
2. `specs/current-state.md` — what exists now (nothing — pre-build)
3. `specs/handoff.md` — what to do first
4. `specs/research/data-sources.md` — what data is actually available
5. `specs/research/prior-art.md` — what existing solutions do
6. `specs/research/state-coverage.md` — per-state notes
7. `specs/phase-1-foundation/spec.md` — what to build first

Then propose the language / framework choice (the constitution gives
recommendations but leaves the call open) and walk Eric through it
before writing any code.

## Related projects

- **SC Books** (`../CRL-NewAccounting/`) — Eric's open-source accounting
  platform; the eventual primary consumer of this API.
- **Streamlined Sales Tax (SST)** — multi-state government project
  providing the free upstream data. https://www.streamlinedsalestax.org

## License

To be confirmed by maintainers — recommendation **Apache 2.0** (see
`specs/constitution.md` for rationale).
