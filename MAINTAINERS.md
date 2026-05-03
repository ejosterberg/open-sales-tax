# OpenSalesTax Maintainers

This file lists the people responsible for OpenSalesTax. Per
[`specs/constitution.md`][const] §14, maintainers review PRs, set
direction, and take final responsibility for code that ships under
their area.

[const]: specs/constitution.md

## Project maintainer

- **Eric Osterberg** ([@ejosterberg](https://github.com/ejosterberg))
  — initial maintainer. Owns project direction, license decisions,
  and tie-breaks until 3+ active maintainers exist.

## Per-state maintainers

The architectural keystone is the per-state contributor model: each
US state has a designated maintainer responsible for that state's
data, taxability matrix, edge cases, and quarterly data refreshes.

A state without a maintainer can still ship as **tier 2 (rate-only)**
based on official SST data — but **tier 1 (fully maintained)** status
requires a named maintainer.

### Tier 1 states (fully maintained)

| State | Abbrev | Maintainer | Since |
|---|---|---|---|
| Arkansas | AR | _vacant — see issue tracker_ | _v0.8 (SST tier-2 → tier-1 promotion)_ |
| Colorado | CO | _vacant — see issue tracker_ | _v0.7 (state portion only; home-rule cities deferred — see [`specs/decisions/04-colorado-home-rule.md`](specs/decisions/04-colorado-home-rule.md))_ |
| Connecticut | CT | _vacant — see issue tracker_ | _v0.6_ |
| District of Columbia | DC | _vacant — see issue tracker_ | _v0.6_ |
| Georgia | GA | _vacant — see issue tracker_ | _v0.8 (promoted from tier 2; state-only grocery exemption per O.C.G.A. § 48-8-3(57) -- locals still tax groceries)_ |
| Idaho | ID | _vacant — see issue tracker_ | _v0.7_ |
| Indiana | IN | _vacant — see issue tracker_ | _v0.8 (SST tier-2 -> tier-1 promotion; state-only -- IN levies no local sales tax)_ |
| Iowa | IA | _vacant — see issue tracker_ | _v0.8 (SST tier-2 -> tier-1 promotion)_ |
| Kansas | KS | _vacant — see issue tracker_ | _v0.9 (SST tier-2 -> tier-1; state grocery rate phased to 0% effective 2025-01-01 per K.S.A. 79-3603(p))_ |
| Kentucky | KY | _vacant — see issue tracker_ | _v0.9 (SST tier-2 -> tier-1; state-only -- KY levies no local sales tax)_ |
| Louisiana | LA | _vacant — see issue tracker_ | _v0.7 (state portion only; ~64 parishes deferred — see [`specs/decisions/05-louisiana-parishes.md`](specs/decisions/05-louisiana-parishes.md))_ |
| Michigan | MI | _vacant — see issue tracker_ | _v0.9 (SST tier-2 -> tier-1 promotion; state-only -- MI levies no general local sales tax; notable peer-state difference: digital goods NOT taxable per Treasury RAB 2023-22)_ |
| Minnesota | MN | _vacant — see issue tracker_ | _Phase 1 ship_ |
| Mississippi | MS | _vacant — see issue tracker_ | _v0.7_ |
| Missouri | MO | _vacant — see issue tracker_ | _v0.7_ |
| Nebraska | NE | _vacant — see issue tracker_ | _v0.9 (SST tier-2 -> tier-1 promotion; LB 1317 of 2024 Good Life District 2.75% reduced state rate flows through SST quarterly file)_ |
| North Dakota | ND | _vacant — see issue tracker_ | _v0.10 (SST tier-2 -> tier-1; 5.0% per N.D.C.C. § 57-39.2-02.1; no state sales-tax holiday)_ |
| Nevada | NV | _vacant — see issue tracker_ | _v0.9 (SST tier-2 -> tier-1 promotion; statewide minimum 6.85% only -- per-county add-ons (Clark ~1.525%, Washoe ~1.415%) deferred. Nevada National Guard Sales Tax Holiday under NRS 372.7282 is buyer-eligibility-restricted and NOT modeled in v1 -- engine does not currently model buyer eligibility.)_ |
| New Jersey | NJ | _vacant — see issue tracker_ | _v0.10 (SST tier-2 -> tier-1 promotion; statewide 6.625% only -- NJ levies no general local sales tax. Urban Enterprise Zones (N.J.S.A. 52:27H-80, ~32 municipalities, half rate 3.3125%) and Salem County (N.J.S.A. 54:32B-8.45, half rate 3.3125%) are seller-eligibility-restricted reduced rates and NOT modeled in v1. Atlantic City Luxury Tax (N.J.S.A. 40:48-8.15, 3% on hotels/restaurants/alcohol/amusements) is a separate non-sales-tax layer and out of scope. Clothing is BROADLY EXEMPT year-round per N.J.S.A. 54:32B-8.4.)_ |
| North Carolina | NC | _vacant — see issue tracker_ | _v0.10 (SST tier-2 -> tier-1 promotion; unusual state-exempt-but-2%-local food county tax under N.C.G.S. section 105-468.1 encoded via rate_modifier=Decimal("2.000"); back-to-school holiday repealed effective 2014 by S.L. 2013-316)_ |
| Ohio | OH | _vacant — see issue tracker_ | _v0.10 (SST tier-2 -> tier-1 promotion; 2026 reverts to traditional 3-day back-to-school holiday under ORC 5739.02(B)(55) after HB 186 of 136th GA (signed 2025-12-19) cancelled the expanded 14-day section 5739.41 holiday for 2026)_ |
| Oklahoma | OK | _vacant — see issue tracker_ | _v0.10 (SST tier-2 -> tier-1 promotion; HB 1955 of 2024 eliminated state-portion grocery tax effective 2024-08-29 -- locals still apply; August clothing/footwear $100 holiday under 68 O.S. 1357.10; digital goods NOT taxable per OAC 710:65-19-156)_ |
| South Carolina | SC | _vacant — see issue tracker_ | _v0.6_ |
| Virginia | VA | _vacant — see issue tracker_ | _v0.6_ |
| Wisconsin | WI | _vacant — see issue tracker_ | _Phase 1 ship_ |

### Tier 2 states (rate-only via SST data)

The 8 other Streamlined Sales Tax member states ship as tier 2 —
official SST data drives rates and boundaries, default taxability
matrix applies (everything taxable except groceries).
(AR, GA, IA, IN promoted in v0.8; KS, KY, MI, NE, NV in v0.9; NC, ND, NJ, OH, OK in v0.10 -- see the table above.)

If you'd like to upgrade your state to tier 1, please open an issue.

States: RI, SD, TN, UT, VT, WA, WV, WY.

### No-tax states

Generic zero-rate module covers AK, DE, MT, NH, OR.

## Becoming a maintainer

**Per-state maintainer:** demonstrate familiarity with that state's
sales-tax rules and the OpenSalesTax codebase by submitting a series
of useful PRs for that state. Open an issue requesting maintainership;
existing maintainers approve by consensus.

**Project maintainer:** invited by the project maintainer after
sustained contribution across multiple areas. The project maintainer
list grows organically; there's no formal application.

## Decision-making

Per constitution §14: consensus-seeking among maintainers; Eric
breaks ties until 3+ active maintainers exist. State-specific
decisions defer to the state maintainer.

## Recognition

OpenSalesTax substitutes recognition for legal enforcement of
contribute-back behavior (constitution §2). Maintainers are listed
publicly here, in release notes, and on the project website.
Contributors who upstream meaningful changes to per-state modules
get credit in `CHANGELOG.md` and the relevant state's documentation.

## Code of conduct enforcement

Maintainers are responsible for enforcing the
[Code of Conduct (Contributor Covenant 2.1)][cc]. Report violations
privately to the project maintainer.

[cc]: https://www.contributor-covenant.org/version/2/1/code_of_conduct/
