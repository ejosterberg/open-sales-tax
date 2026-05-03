# Decision 04 — Colorado home-rule cities, v0.7 scope

**Status:** Decided 2026-05-03 (per-state agent for CO; confirmed by orchestrator brief).
**Scope of decision:** how OpenSalesTax v0.7 models Colorado given that ~70 home-rule
cities self-administer their own sales taxes with their own rates, bases, and exemptions.
**Decision:** **Option A** — encode the **state-level** rate and taxability matrix only,
document the home-rule limitation prominently in the module docstring and references,
and defer per-home-rule-city modeling to v1.0+ when a "self-administered sub-jurisdiction"
abstraction lands.

This decision is reversible: when the schema gains a "tax regime" or "self-administered
sub-jurisdiction" concept (Option B), Colorado will be the canonical first consumer of
that feature. Until then, the state module ships the truthful state-only answer with a
loud caveat.

## Background

Colorado's sales tax landscape is the most complex in the United States outside of
Louisiana. The state has three distinct tax regimes operating concurrently:

1. **State-administered state tax** — 2.9% statewide rate per
   [C.R.S. § 39-26-106](https://law.justia.com/codes/colorado/title-39/specific-taxes/sales-and-use-tax/article-26/part-1/section-39-26-106/),
   in effect since January 1, 2001.
2. **State-administered local taxes** — counties, special districts (e.g., RTD, SCFD,
   Football Stadium District), and **state-collected** municipalities have CDOR collect
   on their behalf at locally-set rates.
3. **Home-rule self-collecting municipalities** — approximately **70 cities** under
   Article XX of the Colorado Constitution have charter authority to administer their
   own sales tax. Each defines its own:
   - **Rate** (e.g., Denver 5.15% city portion; Boulder ~3.86%; Aurora ~3.75%)
   - **Tax base** — many home-rule cities tax categories the state exempts (most notably
     groceries; some tax services the state does not).
   - **Exemptions** — separately enumerated by each city's tax code.
   - **Filing / registration** — a separate license from the state's CDOR account.

The CDOR publishes the **DR 1002** rate schedule listing both state-collected and
home-rule jurisdictions, but the rate-schedule entries for home-rule cities are
informational only — CDOR does not collect or remit on their behalf, and the cities
publish authoritative rate updates on their own websites.

### The 12 most populous home-rule cities (illustrative, not exhaustive)

Combined effective rates as of early 2026, sourced from the cited TaxCloud and
salestaxcolorado.com summaries below; verify against each city's official portal before
relying on these numbers in production.

| City | Combined rate | Notable home-rule deviation from state base |
|---|---|---|
| Denver | 9.15% | City portion 5.15%; Denver taxes prepared food at extra rate, taxes some services |
| Aurora | 8.0% | City portion 3.75% (varies by district); food-for-home-consumption taxable locally |
| Boulder | 9.045% | City portion ~3.86%; groceries taxable locally |
| Colorado Springs | 8.2% | City portion ~3.07%; groceries taxable locally |
| Fort Collins | 7.55% | City portion ~3.85%; groceries taxable locally |
| Lakewood | 7.5% | Self-collecting home-rule |
| Thornton | 8.75% | Self-collecting home-rule |
| Arvada | 8.48% | Self-collecting home-rule |
| Pueblo | 7.5% | Self-collecting home-rule |
| Greeley | 6.46% | Self-collecting home-rule |
| Westminster | (not surveyed in this pass) | Self-collecting home-rule |
| Centennial | (not surveyed in this pass) | Self-collecting home-rule |

(About 60 additional home-rule cities exist beyond the top 12; the full roster lives in
DR 1002. The exact count varies — CDOR cites "approximately 70" and at least one outside
roster says 68 — because cities periodically opt in and out of state-collected status.)

### The specific architectural problem

The current `StateModule` Protocol assumes one taxability matrix and one rate stack per
state. Encoding "Denver taxes groceries at 4% but the state exempts them" requires either:

- Per-jurisdiction taxability overrides, OR
- Multiple `StateModule`-like instances per state (one per home-rule city), OR
- A new `SubJurisdiction` carrier with its own taxability matrix and rate.

None of these exist in the v0.6 schema. The orchestrator brief is explicit: **stop and
ask before any schema change.** This decision picks the no-schema-change option for v0.7.

## Options considered

### Option A — State-only encoding (CHOSEN)

**What:** Ship `colorado.py` with the 2.9% statewide rate, statewide taxability matrix
(groceries non-taxable, prescription drugs exempt, clothing taxable, digital goods
taxable, prepared food taxable). Document the home-rule limitation prominently in:

- The module docstring (verified by a test that asserts the warning string is present).
- `specs/research/references.md` (extensive notes section).
- `MAINTAINERS.md` (call out CO is the canonical "needs sub-jurisdiction support" state).
- The PR description.

The integration test promotes CO to tier-1 (replaces it in the tier-0 list with NM).

**Pros:**
- No schema change. Ships in v0.7 alongside the other Batch-B states.
- The state portion is **factually correct** for any address in Colorado — nothing the
  module returns is wrong; it's just incomplete (missing the home-rule city portion).
- Sets the precedent for the "honest deferral" pattern that SC and VA already follow
  for their local taxes.
- Reversible — when sub-jurisdiction support lands, the existing state row becomes the
  base layer of a richer stack.

**Cons:**
- A consumer calculating tax for an address inside Denver will get **2.9%** when the
  correct combined rate is **9.15%**. That's a 6.25-percentage-point under-collection
  for the largest CO market.
- The taxability matrix is misleading for groceries: Denver, Boulder, Colorado Springs,
  Fort Collins (and many others) **do** tax groceries at the local level, so a grocery
  purchase that the engine reports as 0% tax may actually owe ~3-4% to a home-rule city.
- API consumers will need extensive documentation + a runtime warning to avoid
  mis-relying on the engine for CO.

**Mitigation:** the module's `general` taxability rule's `notes` field carries an explicit
"home-rule cities not modeled" warning; the v0.7 release notes call out CO's status; a
future API docs page lists Colorado as a "state-portion-only coverage" state.

### Option B — Schema extension (REJECTED for v0.7; REVISIT for v1.0)

**What:** Extend the `StateModule` Protocol (or add a sibling `SubJurisdiction` Protocol)
to support per-municipality tax regimes with their own taxability matrix and rate stack.
The engine would query both the state module and any matching sub-jurisdiction module
when resolving tax for an address.

**Why rejected for v0.7:**
- Schema changes are **explicitly out of scope** for the per-state agent's brief
  (orchestrator-only files, see `multi-agent-coordination.md`).
- Cross-cutting work — would block the entire Batch B fanout while the schema stabilizes.
- Affects loader, engine, models, migrations, and every existing state's tests.
- The right time to take this on is when LA (parishes) and AL (independent locals) come
  online — both face structurally similar problems; doing it once for all three is
  cheaper than doing it three times.

**Recommendation:** revisit as **Decision 05** when CO + LA + AL all need it. Do that as
its own phase (Phase 8 candidate) with a dedicated spec.

### Option C — Per-city stub modules (REJECTED for v0.7)

**What:** Ship CO state + 5-7 stub modules (`colorado_denver.py`, `colorado_boulder.py`,
etc.) that each implement the `StateModule` Protocol with `state_abbrev = "CO"` plus a
sub-jurisdiction discriminator.

**Why rejected:**
- Requires the orchestrator's prior approval per the brief.
- Couldn't avoid touching the registry — the registry currently keys on `state_abbrev`,
  so 5-7 modules with `state_abbrev = "CO"` would either collide or need a registry
  schema change (the very thing Option A is designed to avoid).
- Even if the registry were extended, the engine doesn't yet have the "match
  sub-jurisdiction by ZIP+4" wiring; the stubs would be unreachable code.
- Half-shipping 5-7 stubs and deferring the other ~60 home-rule cities is the worst of
  both worlds — wrong numbers in many places, plus the appearance of correctness in a
  few showcase cities.

**Recommendation:** if Option B is chosen later, the right move is to ship sub-jurisdictions
**all at once** (full DR 1002 ingestion) rather than piecemeal stubs.

## What v0.7 ships (for the record)

- `src/opensalestax/states/colorado.py` — `StateModule` implementation:
  - `state_abbrev = "CO"`, `state_name = "Colorado"`, `sst_member = False`,
    `has_sales_tax = True`, `tier = 1`, `self_seeded = True`.
  - **Statewide rate:** `Decimal("2.900")`, effective `dt.date(2001, 1, 1)`.
  - **Taxability matrix:**
    - `general` — TAXABLE (notes cite §39-26-104).
    - `clothing` — TAXABLE (notes cite that CO has no clothing exemption).
    - `groceries` — NON-TAXABLE (notes cite §39-26-707(1)(e) and warn about home-rule
      cities that **do** tax groceries locally).
    - `prescription_drugs` — exempt (notes cite §39-26-717).
    - `prepared_food` — TAXABLE.
    - `digital_goods` — TAXABLE per HB21-1312 (notes cite §39-26-102(15)(b.5),
      effective 2021-07-01).
  - `holidays_for(year)` — returns empty iter (CO has no state-level holidays).
  - **Module docstring** — prominent home-rule warning that maintainers, API consumers,
    and downstream integrators must understand BEFORE relying on the module.

- `tests/unit/test_state_colorado.py` — 13 tests:
  - Metadata, Protocol satisfaction, registry presence.
  - Parametrized 6-category taxability test.
  - `parse_rates` returns single 2.9% row effective 2001-01-01.
  - `parse_rates` ignores `source_file` argument.
  - `parse_boundaries` returns empty.
  - `holidays_for` returns empty for any year (no state-level holidays).
  - `special_cases` returns empty.
  - **Two home-rule-warning tests** — one asserts the docstring contains "home-rule"
    and "self-administer" / "self-collect" warning text; one asserts the `general`
    taxability rule's `notes` field warns about home-rule cities.
  - Groceries-warns-about-local-taxes test (mirrors SC's test pattern).

- `src/opensalestax/states/__init__.py` — one alphabetically-sorted import line for
  `colorado`.
- `tests/integration/test_api.py`:
  - Add `"CO"` to `test_phase_3_non_sst_states_are_tier_1`'s parametrized abbrev list.
  - Replace `"CO"` with `"NM"` in `test_states_marks_unsupported_states_tier_0`'s list
    (NM uses the Gross Receipts Tax model and remains tier 0; AL, MO, MS still tier 0).
- `specs/research/references.md` — append `## CO — Colorado` section per the template
  in §4 of that file.
- `MAINTAINERS.md` — add a CO row to the tier-1 table (vacant maintainer; flag CO as
  the priority candidate for the v1.0+ sub-jurisdiction work).

## Honesty bar for the PR description

The PR opening this state must be unambiguous:

- Title: `feat(states): add Colorado tier-1 module (state-portion only)`
- Body must say, in plain English near the top:
  > "This module returns Colorado's **state-level** 2.9% rate and state taxability
  > matrix. It does **NOT** model the ~70 home-rule self-collecting cities (Denver,
  > Boulder, Colorado Springs, Fort Collins, Lakewood, etc.). API consumers calling
  > `/v1/calculate` for an address inside a home-rule city will receive an
  > **under-collection** of tax — the city portion is missing entirely, and the
  > taxability matrix may be wrong (notably, Denver and most other home-rule cities
  > tax groceries at the local level even though the state exempts them). See
  > `specs/decisions/04-colorado-home-rule.md` for the full rationale."

This honesty is not optional — it's how the project preserves trust while shipping
incrementally.

## When this decision changes

Re-open this decision when **either**:

1. The orchestrator opens a phase to land Option B (`SubJurisdiction` schema +
   loader), OR
2. CO, LA, and AL all need the same primitive — that's the natural moment to design
   the abstraction once.

Until then, leave Colorado as state-portion-only with the loud caveat.

## Sources consulted (all 2026-05-03)

- [C.R.S. § 39-26-106 (state rate)](https://law.justia.com/codes/colorado/title-39/specific-taxes/sales-and-use-tax/article-26/part-1/section-39-26-106/)
- [C.R.S. § 39-26-707 (food exemption)](https://colorado.public.law/statutes/crs_39-26-707)
- [C.R.S. § 39-26-717 (drugs and medical)](https://law.justia.com/codes/colorado/title-39/specific-taxes/sales-and-use-tax/article-26/part-7/section-39-26-717/)
- [C.R.S. § 39-26-102(15)(b.5) (digital goods)](https://www.stateandlocaltax.com/digital-economy/colorado-defines-digital-goods-as-taxable-tangible-personal-property-regardless-of-the-means-of-delivery/) — HB21-1312, effective 2021-07-01
- [CDOR DR 1002 publication landing page](https://tax.colorado.gov/DR1002)
- [CDOR home-rule city overview](https://tax.colorado.gov/local-government-sales-tax)
- [salestaxcolorado.com home-rule jurisdictions list](https://www.salestaxcolorado.com/2022/10/06/which-towns-cities-in-colorado-are-self-collecting-home-rule-jurisdictions/)
- [TaxCloud Colorado guide (combined rate cross-check)](https://taxcloud.com/sales-tax/colorado/) — used only as a cross-reference, not as a data source
- [Colorado Municipal League HB-1162 position paper](https://www.cml.org/docs/default-source/uploadedfiles/legislative/position-papers/2021-position-papers/hb-1162-position-paper.pdf?sfvrsn=10477b4a_0) — confirms HB21-1162 addressed destination sourcing (not digital goods); the orchestrator brief's mention of "1162 affected sourcing" is correct, while digital goods are governed by HB21-1312

Per `specs/research/references.md` §1.1, Sovos is **not** an authoritative source and was
not used to derive any data point in this decision; it is referenced only because
`specs/research/state-coverage.md` already calls Colorado "the hardest US state" and
Sovos's CO row is one of the entries with a known copy-paste defect.
