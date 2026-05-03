# Research — State Coverage Plan

> Per-state notes: SST membership status, data availability, difficulty,
> recommended order. Compiled 2026-05-02 from direct fetches of SST
> source pages.

## Roll-up

| Bucket | Count | Difficulty | When |
|---|---|---|---|
| **SST full members** (free CSV/ZIP data, conformance tested) | 23 | Easy | Phases 1-2 |
| **SST associate members** | 1 (TN) | Easy | Phase 2 |
| **Non-SST sales-tax states with public DOR data** | ~22 | Medium-Hard (per-state effort) | Phase 3+ |
| **Non-SST states with no general sales tax** | 5 (AK, DE, MT, NH, OR) | Trivial (return zero) | Phase 1 |
| **Total US states + DC + PR** | 52 | n/a | Long-term |

## Group 1 — SST Full Members (23 states)

These are the easy wins. All 23 publish quarterly rate + boundary
files via SST in machine-readable format under public licenses.

| State | Abbrev | Joined SST | Notes for our module |
|---|---|---|---|
| Arkansas | AR | 2008 | CSV format (rates + boundary) |
| Georgia | GA | 2011 | CSV format |
| Indiana | IN | 2008 | CSV format |
| Iowa | IA | 2008 | ZIP archive — investigate format |
| Kansas | KS | 2008 | ZIP archive |
| Kentucky | KY | 2008 | CSV format |
| Michigan | MI | 2008 | CSV format |
| **Minnesota** | **MN** | 2008 | ZIP archive. **Phase 1 priority** — Eric's home state, integration target for SC Books, already partially seeded in SC Books's `inc/mn-metro-taxes.php` |
| Nebraska | NE | 2009 | ZIP archive |
| Nevada | NV | 2008 | ZIP archive |
| New Jersey | NJ | 2008 | Boundary CSV; rates ZIP |
| North Carolina | NC | 2008 | CSV format |
| North Dakota | ND | 2008 | ZIP archive |
| Ohio | OH | 2008 | CSV format |
| Oklahoma | OK | 2008 | ZIP archive |
| Rhode Island | RI | 2008 | CSV format (both rates + boundary) |
| South Dakota | SD | 2008 | ZIP archive |
| Utah | UT | 2008 | ZIP archive |
| Vermont | VT | 2008 | ZIP archive |
| Washington | WA | 2008 | ZIP archive — high-rate state, complex local taxes |
| West Virginia | WV | 2008 | CSV format |
| **Wisconsin** | **WI** | 2009 | CSV format. **Phase 1 priority** — pairs with MN to test contrast (clothing taxable in WI vs not in MN) |
| Wyoming | WY | 2008 | CSV format |

### Phase-1 picks: Minnesota + Wisconsin

**Why MN:** Eric's home state, his businesses operate here, SC Books
integration target. MN already has partial seed data in
`../CRL-NewAccounting/inc/mn-metro-taxes.php`. Validates the design
against a real-world consumer.

**Why WI as the second:** geographically adjacent (Eric likely has
cross-border customers), but tax rules differ in instructive ways:
- WI: clothing is **taxable**
- MN: clothing is **non-taxable**
- WI: groceries are **non-taxable** (mostly aligned)
- MN: groceries are **non-taxable**

This pair lets us validate that the per-state-module pattern
correctly handles divergent taxability rules with a common engine.

### Phase-2 expansion: remaining 22 SST states

Bring all 24 SST states online with the same module pattern. Should
be relatively mechanical once the MN + WI parsers exist as reference.

## Group 2 — SST Associate Member (1 state)

| State | Abbrev | Status |
|---|---|---|
| Tennessee | TN | Associate member; data published, conformance partial |

Bring online in Phase 2 alongside the rest of the SST batch.

## Group 3 — Non-SST sales-tax states (22 states + DC + PR)

These are the hard ones. Each requires a per-state effort to find,
parse, and maintain rate data. Primary candidates for community
contributors.

### Tier A: high-impact, high-effort

These states have huge populations + complex tax rules. Solving them
well is high value but hard.

| State | Abbrev | Why hard | Why important |
|---|---|---|---|
| **California** | CA | District taxes (~hundreds), home-rule cities, special-purpose taxing districts | Largest US economy |
| **Texas** | TX | Origin-based sourcing for in-state sellers; many local jurisdictions | 2nd largest |
| **New York** | NY | Many local jurisdictions, MTA surcharge, complex taxability | 3rd largest |
| **Florida** | FL | DR-15DSS discretionary surtax per county | 4th largest, tourism complications |
| **Pennsylvania** | PA | Allegheny + Philadelphia surtaxes; lots of edge cases | Major economy |
| **Illinois** | IL | Home-rule cities; ROT (Retailer Occupation Tax) vs UT distinction | Major economy |

Each of these is a meaningful project on its own. Phase 3 should
attempt CA first (highest impact + most-needed by SC Books-style
small business users).

### Tier B: medium-impact, medium-effort

| State | Abbrev | Notes |
|---|---|---|
| Alabama | AL | Self-administered cities; AL DOR publishes rates; tricky |
| Arizona | AZ | Transaction Privilege Tax (different from sales tax conceptually) |
| **Colorado** | CO | **The hardest US state.** ~70 home-rule cities self-administer. Each has its own rates + rules + filing. State publishes only state + state-collected portion |
| Connecticut | CT | Statewide single rate; easy. Some local additions |
| District of Columbia | DC | Single jurisdiction; trivial |
| Hawaii | HI | General Excise Tax (GET) — different model; gross-receipts tax not technically sales tax |
| Idaho | ID | State + a few local resort taxes |
| Louisiana | LA | Heavily decentralized; parish-level (each parish self-administers) |
| Maine | ME | Statewide single rate; easy |
| Maryland | MD | Statewide single rate; easy |
| Massachusetts | MA | Statewide single rate; easy |
| Mississippi | MS | Some local; statewide majority |
| Missouri | MO | Many local jurisdictions; pretty manageable |
| New Mexico | NM | Gross Receipts Tax (different model — like HI) |
| Puerto Rico | PR | Sales-and-use tax; bilingual data |
| South Carolina | SC | Statewide + local options; tractable |
| Virginia | VA | Statewide + regional; tractable |

### Tier C: trivial — no general sales tax

These states have no general statewide sales tax; OpenSalesTax
returns 0% with a note.

| State | Abbrev | Notes |
|---|---|---|
| Alaska | AK | No statewide; ~110 boroughs/cities have local sales tax. Phase-1 ships state-level zero; per-locality is later |
| Delaware | DE | None |
| Montana | MT | None statewide; some resort taxes (Whitefish, etc.) |
| New Hampshire | NH | None |
| Oregon | OR | None |

These can be supported in **Phase 1** as a near-no-op state module
(returns zero with a note about local taxes for AK and MT).

## Recommended state rollout order

| Phase | State(s) | Why |
|---|---|---|
| 1 | MN, WI, AK, DE, MT, NH, OR | MN/WI for the contrast; the 5 no-tax states for completeness with minimal work |
| 2 | All remaining SST states (22 more): AR, GA, IA, IN, KS, KY, MI, NE, NV, NJ, NC, ND, OH, OK, RI, SD, TN, UT, VT, WA, WV, WY | Mechanical expansion using MN/WI parser pattern |
| 3 | CA | Highest-impact non-SST state |
| 4 | TX, NY, FL | Other big economies |
| 5 | All remaining tractable non-SST states (~17 states) | Community-contributor wave |
| 6 | Hard states: CO, AL, LA | Recruit dedicated state maintainers |
| 7 | Specialty: HI, NM (gross receipts), AK localities | Edge cases |

This roadmap covers all 50 states + DC + PR by Phase 7. Realistic
timeline: 12-18 months from Phase 1 launch if the contributor
recruitment lands.

## Per-state module checklist (constitutional minimum)

Every state module must ship with:

- [ ] State data parser (consumes upstream rate + boundary files)
- [ ] Schema-compliant rate / jurisdiction tables populated
- [ ] Taxability matrix entries (which categories are taxable)
- [ ] At least 10 known-good test cases (real addresses + expected rates)
- [ ] Documentation of state-specific quirks (1-page MD per state)
- [ ] Update procedure (CLI command + cron-ready)
- [ ] Maintainer listed in MAINTAINERS.md

**No tests = not officially supported.** This is constitutional.

## State maintainer recruitment ideas

- **State CPA society partnerships** — each state has a Society of
  CPAs with members who'd benefit from + contribute to this.
- **State DOR engagement** — some DORs would love to publish a
  reference implementation; could provide expertise.
- **Tax-tech Reddit / HN** — established community of tax-software
  developers who might volunteer.
- **OSS-friendly accounting firms** — a few firms publish OSS tools
  (e.g., Bench's open-source contributions).
- **Conference talks** — Dynamic Languages / OSCON / RailsConf-style
  events with a tax-tech angle.

Eric to drive this once Phase 1 ships and there's something concrete
to point at.

## Living document

Update this file every time:
- A state module ships → mark as ✅ in the table above.
- A state's data format changes → note in that state's row.
- A state maintainer signs up → add to MAINTAINERS.md and reference here.
- A state's tax rules change in a way that affects our parser → log in
  the state's `state-X-changelog.md`.
