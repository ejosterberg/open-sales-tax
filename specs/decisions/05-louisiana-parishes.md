# Decision 05 — Louisiana parishes (state-only encoding for v0.7)

**Date:** 2026-05-03
**Status:** ✅ Accepted (Option A — ship state-only, defer parishes to v1.0+)
**Decider:** Per-state research agent (LA), under the orchestrator
brief that explicitly authorizes Option A as the default.
**Recorder:** Claude (Louisiana state-research agent)

## Context

Louisiana's local sales tax landscape is uniquely fragmented in the
United States. Unlike most states, where the state DOR collects both
state and local taxes and remits the local share back to
counties/cities, **each of Louisiana's 64 parishes operates its own
Sales and Use Tax Commission (or comparable body) that independently
administers parish and municipal sales taxes** within its
boundaries. La. R.S. 47:337.1 et seq. ("Uniform Local Sales Tax
Code") provides a uniform definitional framework, but rate-setting,
collection, registration, and audit are parish-level functions.

Compounding the complexity:

- Municipalities within a parish may layer their own rate on top of
  the parish rate.
- Special-purpose districts (school, transportation, tourism, road,
  fire, hospital service, economic development) may layer additional
  rates within sub-parish boundaries.
- The combined state + parish + municipal rate can exceed **12%** in
  certain corners of the state — among the highest combined sales
  tax rates in the nation.

Louisiana has taken **partial** consolidation steps:

- The **Louisiana Sales and Use Tax Commission for Remote Sellers**
  (La. R.S. 47:339.1, established 2018) collects state + local on
  remote-seller transactions only — it does **not** unify in-state
  rates.
- The **Parish E-File** portal lets in-state retailers file state
  and most parishes via one online interface, but the underlying
  rates and ordinances remain parish-specific.
- 2026 Act (combined state-and-parish-return pilot, per LDR Mossadams
  2026-02 announcement) is rolling out a unified return form, but it
  does not change rate authority or rate variability.

**The result:** modeling Louisiana's local taxes correctly requires
encoding 64 parish rate stacks (each with its own historical
schedule), the municipal sub-rates that overlay them, and the
parish-by-parish exemption/taxability deviations from the state
base. None of this is published as a single machine-readable feed
comparable to the SST quarterly files; it requires per-parish
research from each parish's commission website plus periodic LDR
publications.

## Decision

For the v0.7 ratchet bringing Louisiana to **tier 1**, ship the
**state-level rate and statewide taxability matrix only**. Document
the parish limitation prominently in the module docstring and
README. Defer per-parish modeling to **v1.0+** as part of the
broader address-level resolution work (Phase 4 PostGIS roadmap).

This follows precedent already set by:

- **South Carolina (v0.6)** — six categories of local-option taxes
  deferred; state 6% rate only.
- **Virginia (v0.6)** — regional add-ons (Central VA, Hampton Roads,
  Northern VA, Historic Triangle, Southside) deferred; statewide
  minimum 5.3% only.
- **California (v0.2)** — ~1,700 district rates deferred; CDTFA
  loader called out as v0.3 priority.

Louisiana's local fragmentation is more severe than any of these,
which is why it gets its own decision document rather than a
single-line README footnote: a future maintainer building the parish
loader needs to know what trade-off was made and why, and the
"Option B" schema-extension path (below) needs to be on the table
when v1.0 is planned.

## Options considered

### Option A — State-only encoding (CHOSEN)

- Encode the 5% state rate (effective 2025-01-01 per Act 11 of 2024
  3rd Extraordinary Session, sunset 2029-12-31).
- Encode the statewide taxability matrix exactly as it stands at the
  state level (groceries, residential utilities, prescription drugs
  exempt at the state portion only; parishes generally still tax
  these).
- Encode the Second Amendment Weekend Holiday (La. R.S. 47:305.62) —
  the one currently-active LA holiday with no per-item cap — applied
  to firearms / ammunition / hunting supplies.
- Document the parish limitation in the module docstring AND in
  README / references.md so callers cannot mistake the state-only
  rate for a complete answer.

**Pros:**

- Same architectural pattern as CA, SC, VA (no precedent break).
- Ships in this batch; doesn't block the v0.7 release.
- Honest: the docstring tells users they're getting state-portion
  only and they need to add parish rates themselves.
- Keeps the Protocol clean; no schema extensions needed.

**Cons:**

- Returns numerically incomplete tax for any LA address — the
  state 5% is only ~40-55% of the actual combined rate in most
  inhabited LA parishes.
- A naive caller might use the result for compliance and
  under-collect.
- The "deferred parishes" caveat carries more weight in LA than in
  SC/VA because the missing portion is larger (~5-7% vs SC's ~3%
  and VA's ~0.7-1.7%).

### Option B — Schema extension for self-administered sub-jurisdictions

Add a Protocol concept of **"self-administered sub-jurisdictions"**
analogous to Colorado home-rule cities. Each LA parish (and
optionally home-rule-equivalent municipalities) becomes a registered
sub-jurisdiction with its own rate row, taxability rules, and
boundary list. The engine would then compose state + parish +
municipal during calculation.

**Pros:**

- Architecturally honest — Louisiana's structure genuinely doesn't
  fit a "state-only with hidden locals" model the way SST states
  do.
- Sets up CO and AL well too (similar fragmentation).
- Enables correct end-to-end calculation once parish data is loaded.

**Cons:**

- **Schema change** — requires orchestrator approval (per brief).
- Forces a Protocol revision that affects every state module's
  registration, not just LA's.
- The 64 parishes still need data sourced — schema doesn't ship
  data — so the immediate user impact is similar to Option A
  (state-only numbers) until per-parish maintainers are recruited.
- v0.7 is a tier-1 ratchet release, not a schema-revision release.

**Status:** Recommended for **v1.0+ planning** alongside the CO
home-rule and AL independent-locals modeling work. Out of scope for
v0.7. **Flagged here so the orchestrator can sequence it
intentionally.**

### Option C — Hybrid: ship state + Orleans Parish stub

Ship LA state-level + a stub Orleans Parish (New Orleans) module as
a tier-1 demonstration. Defer the other 63 parishes.

**Pros:**

- Demonstrates parish modeling end-to-end with one example.
- New Orleans is the highest-traffic LA jurisdiction.

**Cons:**

- Orleans alone has its own multi-tier rate stack (parish + city +
  several special districts including the Ernest N. Morial
  Convention Center and the Stadium and Exposition District) — the
  "stub" isn't actually small.
- Without a Protocol pattern for sub-jurisdictions (Option B), an
  Orleans stub would be a one-off hack inside the LA module that
  doesn't generalize.
- Users in any of the other 63 parishes get worse-than-Option-A
  results (they may assume Orleans-specific behavior generalizes).
- Honesty cost: shipping one parish makes the deferral of 63 others
  look like neglect rather than a deliberate scope cut.

**Status:** Rejected. If we want one parish encoded, we should do
it properly via Option B; if we don't have time for Option B, we
should not encode any parish.

## Statutory verifications performed

| Item | Citation | Verified against |
|---|---|---|
| State rate 5%, effective 2025-01-01, sunset 2029-12-31 | Act 11 of 2024 3rd Extraordinary Session (HB 10) | LDR FAQ "What is the state sales tax rate?", LegiScan, Sales Tax Institute, Eide Bailly summary |
| Authority for state sales tax | La. R.S. 47:301 et seq. (sales tax act) | LDR statutes index, La. Legislature site |
| State sales tax base rates (multiple statutes) | La. R.S. 47:302, 47:321, 47:321.1, 47:331, 47:332 | LDR FAQ confirms current 5% is the sum of the statutory layers |
| Food for home consumption exempt at state level | La. R.S. 47:305(D)(1)(n)–(r) (post-2025 numbering); LDR FAQ "Is there sales tax on food?" | LDR FAQ confirms maintained by constitutional amendment |
| Residential utilities exempt at state level | La. Const. Art. VII §2.2 (constitutional protection) + R.S. 47:305(D) | LDR FAQ on constitutional amendment effect |
| Prescription drugs exempt at state level | La. R.S. 47:305(D) (post-2025 reorganization) — see also R.S. 47:305.10 | LDR FAQ on constitutional amendment effect |
| Second Amendment Weekend Holiday | La. R.S. 47:305.62 — "first consecutive Friday through Sunday of September" | La. Legislature site (full statute text), LDR Second Amendment landing page, RIB 25-017 |
| Back-to-school holiday status | Suspended 2018-2025; reauthorization HB 551 (2025 Reg. Sess.) **failed** | Yahoo News, Advantous Consulting summary, ITEP report |
| Annual LA Sales Tax Holiday (formerly hurricane prep) | Suspended; not reauthorized for 2026 | Sales Tax Institute, ITEP cross-state summary |
| Digital products taxable as of 2025-01-01 | Act 10 of 2024 3rd Extraordinary Session (HB 8) | Baker Tilly, Moss Adams, Sales Tax Institute, LDR digital products FAQ |
| Parishes administer locally | La. R.S. 47:337.1 et seq. (Uniform Local Sales Tax Code) | LDR Parish E-File portal, LULSTB documentation |
| Remote-seller central collection | La. R.S. 47:339.1 — Louisiana Sales and Use Tax Commission for Remote Sellers | Justia, remotesellers.louisiana.gov |

## What the v0.7 LA module will and will not return

**Will return correctly:**

- State 5% rate for taxable items.
- $0 state tax for groceries, residential utilities, prescription
  drugs (state portion exempt).
- $0 state AND local tax during the September Second Amendment
  Weekend for firearms / ammunition / hunting supplies (the holiday
  statute itself extends to "the state of Louisiana and its
  political subdivisions" per La. R.S. 47:305.62, so the module
  represents the holiday correctly even though we don't model the
  underlying parish rates).
- Taxable status for clothing, prepared food, digital goods at the
  state level.

**Will NOT return:**

- The parish portion of tax (typically 4-7% additional in inhabited
  parishes).
- The municipal portion (additional in cities with home-rule
  municipal taxes).
- Special-district portions (school, transportation, tourism, etc.).
- Parish-specific exemption deviations (e.g., parishes that DO tax
  groceries — most do — vs the few that exempt them locally).

**Caller expectation:** A v0.7 caller calculating tax for a LA
address must layer parish/local rates from their own source. The
README and the LA module docstring both say this prominently.

## When does Option B (schema extension) get reconsidered?

When **any** of the following becomes true:

1. A maintainer volunteers to model 4+ Louisiana parishes (i.e.,
   we have human capacity to populate parish data).
2. A SC Books or other primary consumer needs LA support badly
   enough to fund parish modeling.
3. The Phase 4 PostGIS / address-level work begins (parishes are
   essentially a special case of jurisdiction-overlay modeling that
   PostGIS work will need to handle for many states).
4. A Colorado or Alabama maintainer proposes the same Protocol
   extension for their state's home-rule / independent-local
   landscape and we want one consistent abstraction.

When that happens, this decision document gets a successor
(`06-self-administered-sub-jurisdictions.md` or similar) and the
parish work proceeds under that.

## Cross-references

- `src/opensalestax/states/louisiana.py` — implementation
- `tests/unit/test_state_louisiana.py` — tests (including a test
  that verifies the parish limitation is documented in the module
  docstring)
- `specs/research/references.md` §3 — full LA sources cited
- `specs/agent-briefs/per-state-research-brief.md` — the brief this
  agent worked under
- `specs/decisions/03-database.md` — the dual-DB decision; PostGIS
  work in Phase 4 will be the natural home for parish boundary data
