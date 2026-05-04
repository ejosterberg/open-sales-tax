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
| Alabama | AL | _vacant — see issue tracker_ | _v0.13 (Phase 6 Batch C tier-0 -> tier-1; non-SST; 4.0% per Ala. Code § 40-23-2(1); **state portion only** -- ~700+ self-administering home-rule cities under § 11-51-200 et seq. and 67 counties deferred to the SubJurisdiction Protocol abstraction (see [`specs/decisions/04-colorado-home-rule.md`](specs/decisions/04-colorado-home-rule.md) and [`specs/decisions/05-louisiana-parishes.md`](specs/decisions/05-louisiana-parishes.md)); reduced 2.0% state grocery rate via rate_modifier per HB 386 of 2024 (phase-down history: 4.0% -> 3.0% on 2023-09-01 per HB 479 of 2023 -> 2.0% on 2025-09-01); two annual STATE holidays (Severe Weather Preparedness Feb 27 - Mar 1, 2026 under § 40-23-210 et seq.; Back-to-School July 17-19, 2026 under § 40-23-211) with local-opt-in caveat documented in every HolidayWindow notes; alongside CO and LA, one of the three canonical priority candidates for the v1.0+ SubJurisdiction Protocol work)_ |
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
| Maine | ME | _vacant — see issue tracker_ | _Phase 8 (non-SST tier-0 -> tier-1; 5.5% per Me. Rev. Stat. tit. 36 § 1811(1) effective 2013-10-01 (PL 2013, c. 368, Pt. M; permanent under PL 2015, c. 267, Pt. OOOO); state-only -- ME levies no general local sales tax (joins IN/KY/MI/RI no-local-tax club); statutory higher rates 8% prepared food / 9% lodging / 10% short-term auto rental / 14% cannabis NOT modeled in v1 pending category-aware-rate engine extension; no enacted sales-tax holiday)_ |
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
| Rhode Island | RI | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1 promotion; statewide 7.0% only -- RI levies no general local sales tax (combined rate equals state rate everywhere; mirrors IN/KY/MI). Clothing exempt up to $250 per article per R.I. Gen. Laws § 44-18-30(27) with the excess above $250 taxable at 7%; the v0.10 engine does not yet enforce per-item thresholds, so the module encodes is_taxable=False to match the dominant case (everyday clothing under $250) -- under-collects on the excess-above-$250 portion of high-end items pending the v0.6 threshold-rules feature. No state sales-tax holiday.)_ |
| South Carolina | SC | _vacant — see issue tracker_ | _v0.6_ |
| South Dakota | SD | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1; 4.2% per SDCL § 10-45-2 with **statutory sunset 2027-06-30** per HB 1137 of 2023 (reverts to 4.5% absent extension); groceries fully taxed; **Wayfair plaintiff state**)_ |
| Tennessee | TN | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1; SST associate member; 7.0% per Tenn. Code Ann. § 67-6-202; reduced 4.0% grocery rate via rate_modifier (§ 67-6-228); back-to-school holiday Jul 24-26, 2026 with 4 scopes)_ |
| Utah | UT | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1; rate composition 4.85% = 4.7% state + 0.10% statewide-uniform local + 0.05% mass transit per Utah Code § 59-12-103; reduced 1.75% grocery state rate via rate_modifier; **Navajo Nation deferred regime** under federal Indian-law preemption)_ |
| Vermont | VT | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1; 6.0% per Vt. Stat. Ann. tit. 32 § 9771; clothing EXEMPT year-round per § 9741(45) -- joins PA/MA/MN/NJ/RI broad-exemption club; Local Option Sales Tax 1% in ~17 towns deferred to per-municipality data)_ |
| Virginia | VA | _vacant — see issue tracker_ | _v0.6_ |
| Washington | WA | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1; 6.5% per RCW § 82.08.020; combined rates up to ~10.35% (King County); broad digital-services tax base per RCW § 82.04.050(6) + § 82.04.192; **B&O gross-receipts tax under RCW chapter 82.04 is a separate seller-side tax and out of scope**)_ |
| West Virginia | WV | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1; 6.0% per W. Va. Code § 11-15-3; **groceries fully exempt since 2013** after a 7-year phase-out (6%→5%→4%→3%→2%→1%→0%); August holiday Aug 7-10, 2026 with 5 scope-specific windows)_ |
| Wisconsin | WI | _vacant — see issue tracker_ | _Phase 1 ship_ |
| Wyoming | WY | _vacant — see issue tracker_ | _v0.11 (SST tier-2 -> tier-1; **final SST promotion completing Phase 7**; 4.0% per Wyo. Stat. § 39-15-104; digital goods NOT taxable -- joins MI/NV/OK; no holidays ever)_ |

### Tier 2 states (rate-only via SST data)

**Phase 7 complete in v0.11.0 — every SST member is now tier 1.**

The 22 SST members were promoted across:
- v0.1 ship (MN, WI)
- v0.8 (AR, GA, IA, IN)
- v0.9 (KS, KY, MI, NE, NV)
- v0.10 (NJ, NC, ND, OH, OK)
- v0.11 (RI, SD, TN, UT, VT, WA, WV, WY) — final batch

No SST states remain in tier-2.

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
