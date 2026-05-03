# Decision 02 — License, contributor agreement, patent posture

**Date:** 2026-05-02
**Status:** ✅ Accepted
**Decider:** Eric Osterberg
**Recorder:** Claude (bootstrap session)

## Decisions

1. **License:** Apache License 2.0
2. **Copyright line:** `Copyright 2026 Eric Osterberg and OpenSalesTax contributors`
3. **Contributor agreement:** **DCO sign-off** (`git commit -s`) on
   every commit. No CLA.
4. **NOTICE file:** stub at repo root, populated as third-party
   dependencies require attribution.
5. **Per-file headers:** SPDX one-liner —
   `# SPDX-License-Identifier: Apache-2.0` at the top of every Python
   source file. No full Apache header per file.
6. **Patent posture:** acknowledge risk explicitly in constitution §2;
   adopt mitigation rules (no reverse-engineering of commercial APIs;
   no naming features after commercial products; vet contributions
   from current/former commercial-vendor employees). For v1's scope
   the risk is low.

## Why Apache 2.0 over alternatives

Constitution §2 lays out the rationale; the key points:

- **Patent grant.** Apache 2.0's explicit patent license protects
  contributors and downstream users in a domain (sales tax) where
  patent portfolios held by Avalara, Vertex, and Sovos are real
  considerations. MIT/BSD have no patent grant; GPL has a weaker one.
- **Permissive integration.** Commercial accounting software can
  embed OpenSalesTax without GPL-style copyleft obligations. This
  unlocks the "QuickBooks / Xero / SC Books / Shopify app
  integration" story that drives adoption.
- **Trademark protection.** Apache 2.0 §6 reserves the project name —
  a commercial fork can exist but cannot call itself "OpenSalesTax."
- **Industry-standard.** Same license as Kubernetes, TensorFlow,
  Cassandra, Spark, and most modern Linux Foundation infrastructure
  projects. Contributors are familiar with its terms; lawyers approve
  on sight.

## Why NOT AGPL (the SaaS contribute-back question)

Eric raised the question: should the license force SaaS providers to
publish their modifications? AGPL-3.0 is the license designed for
that purpose. Considered and **rejected** for these reasons:

- **Cuts off commercial integrators.** Many companies have blanket
  AGPL bans (Google, Apple, much of the enterprise PHP/Java
  ecosystem). The integration story dies.
- **Weaker patent grant** than Apache 2.0 — net negative on a
  patent-sensitive project.
- **Limited practical effect for THIS project.** The SST data is
  public; a determined SaaS freeloader would just use the SST files
  directly without touching our code. AGPL would force the rare
  "forked our state module and won't share back" actor to publish,
  but those are uncommon vs. the common "embed our library in our
  closed product" use case.
- **Asymmetric reversibility.** Apache → "also offered under AGPL"
  (dual licensing) is feasible later if norms prove insufficient.
  AGPL → Apache requires every contributor's consent and is
  essentially impossible at scale. Pick the license you can move
  *from*, not the one you'd have to move *to*.

**Substituted mitigations** (engineered into governance instead of
license):

- Public **MAINTAINERS.md** crediting per-state maintainers + recurring
  contributors.
- Public **USERS.md** / deployer registry — SaaS providers who deploy
  OpenSalesTax get listed *if they contribute back*. Recognition is
  currency.
- Quarterly "what's been contributed lately" updates (blog posts,
  release notes) — public visibility of who's helping.
- **Reserved right to dual-license later** — if norms fail, add an
  AGPL option for new contributions going forward.

## Why DCO over CLA over nothing

| | DCO sign-off | ICLA (signed agreement) | Nothing |
|---|---|---|---|
| Provenance assertion | ✅ per-commit | ✅ per-contributor (signed once) | ⚠️ relies on Apache 2.0 §5 default |
| Friction for contributors | Low (`git commit -s`) | High (legal doc to sign) | None |
| Defends against later patent claims | ✅ paper trail | ✅✅ stronger | ⚠️ implicit only |
| Used by | Linux kernel, GitLab, Docker, CNCF | Apache Software Foundation, Google projects | Many small projects |
| Compatible with later dual-licensing | Limited (each contributor must re-consent) | ✅ pre-grants the rights | ❌ no |

DCO is the **right balance** for OpenSalesTax now. ICLA is overkill at
this scale and would add real adoption friction. "Nothing" gives up a
useful provenance defense for no real reason.

## Patent risk — explicit acknowledgment

Sales tax software exists in a patent minefield. Avalara and Vertex
hold large portfolios; Sovos and TaxJar smaller ones. Most software
patents from the 2000–2014 era are weak post-*Alice v. CLS Bank*
(2014), but not zero.

**Risk for v1 (SST data parsing, ZIP+4 lookup, basic taxability,
REST API):** **low.** The methods are textbook; the data is public;
the API patterns are commodity REST.

**Risk for later phases (address-level GIS resolution, ML-driven
product categorization, automated nexus determination):** **real and
worth re-evaluating** when those phases approach.

### Mitigation rules adopted

- Implement from primary sources (tax law, SST docs, state DOR
  publications) — never reverse-engineer commercial APIs to derive
  algorithms or schemas.
- Don't name features after commercial products.
- Flag novel algorithms for review before merging; document prior
  art in `specs/`.
- Vet contributions from current/former commercial-vendor employees
  for invention-assignment / non-compete obligations.
- Apache 2.0 patent grant + DCO sign-off = standard mitigation stack.
- Public design docs in `specs/` serve as dated prior art.

### Personal-liability summary

- **As OSS project initiator/maintainer:** very low. OSS contributors
  are essentially never primary targets of patent suits — no money
  to extract.
- **As eventual SaaS operator:** real liability addressable with
  patent insurance + legal review at SaaS launch (not before).
- **As end user (running OpenSalesTax for own business):** the
  Apache 2.0 patent grant from contributors flows downstream.

## Consequences

- Bootstrap session creates `LICENSE` (Apache 2.0 text), `NOTICE`
  (stub), `CONTRIBUTING.md` (with DCO instructions), `MAINTAINERS.md`
  (Eric initial).
- CI must enforce DCO (`Signed-off-by:` trailer) on every commit
  in every PR.
- All new Python files start with `# SPDX-License-Identifier: Apache-2.0`.
- CLAUDE.md "what NOT to do" updated with reverse-engineering ban,
  commercial-naming ban, DCO requirement.
- Constitution §2 expanded with the AGPL-rejection rationale and
  patent risk acknowledgment.
- Constitution §14 expanded with DCO requirement + recognition-over-
  enforcement principle.

## References

- `specs/constitution.md` §2 (license rationale, patent risk),
  §14 (governance, DCO)
- `CLAUDE.md` "what NOT to do"
- DCO text: https://developercertificate.org
- Apache 2.0 text: https://www.apache.org/licenses/LICENSE-2.0
- *Alice Corp. v. CLS Bank Int'l*, 573 U.S. 208 (2014)
