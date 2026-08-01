# Daily state sales tax audit — 2026-08-01 (day 1: AK + AL)

## TL;DR

- 2 jurisdictions audited. **0 rate-pin drift** — all 18 pinned AK rows
  and all 24 pinned AL rows match the live engine exactly.
- **3 new findings, none of them rate-file staleness**, all found by
  going past the pinned cities into the authoritative source tables:
  1. **Systematic engine bug — multi-county ZIPs pick a county by an
     arbitrary FIPS-first tiebreak.** **617 ZIPs across 7 states** get a
     county rate chosen by a rule unrelated to which county the ZIP is
     actually in. Confirmed wrong at Calera AL 35040, which
     **over-collects the county component by 2.00pp**.
  2. **AK ZIP 99928 (Ward Cove) over-collects by 3.00pp** — the engine
     applies Ketchikan *city* 5.5% to a ZIP outside city limits and
     drops the 2.5% borough tax it does owe. Six more AK ZIPs return
     0.000% against published ARSSTC rates.
  3. **Six Alabama cities changed rates on 2026-07-01 / 2026-08-01** —
     two of them (**Rogersville, Bay Minette**) effective **today**.
     None are modelled by the engine, so this is coverage, not drift.
- **Both prior findings are engine/loader defects, not data staleness** —
  no SST refresh would fix either. Written up in `specs/findings/` and
  chipped; **no auto-commit**, per the "conservative on automated
  commits" constraint.
- AK + AL were also covered yesterday on the day-31 buffer run. That run
  checked 10 and 10 tier-1 cities and found both clean; today went
  deeper (full ARSSTC sheet diff, full ALDOR notice archive) and that is
  where all three findings came from.
- Prod healthy: both containers `Up 5 days (healthy)`, public API
  responding. The 2026-07-26 outage has not recurred.

---

## AK (Alaska) — non-SST (no state tax) — ⚠️ 1 over-collect, 6 zero-rate ZIPs

- **Source:** ARSSTC "Sales Tax Rate Sheet with Zip Codes **7-1-2026**"
  (`arsstc.org/wp-content/uploads/2026/07/`), downloaded and diffed
  row-by-row rather than spot-checked.
- **Last loaded on prod:** self-seeded module (`ak_data.py`); Alaska is
  not an SST state and has no quarterly file.
- **Latest available:** 7-1-2026 is the newest ARSSTC publication —
  **there is no 8-1-2026 sheet, so nothing took effect in Alaska today.**
- **Drift summary:** no drift in the pinned set; the full-sheet diff
  surfaced 7 ZIPs outside it that are wrong.
- **Recommended action:** engine/boundary fix, chipped. No data refresh
  would help — the rates are right, the ZIP→authority bindings are not.

### Pinned rows — all 18 match

| City (ZIP) | Expected (ARSSTC) | Actual (engine) | Delta |
|---|---|---|---|
| Homer (99603) | 7.850% | 7.850% | 0.000 |
| Juneau (99801) | 5.000% | 5.000% | 0.000 |
| Ketchikan (99901) | 8.000% | 8.000% | 0.000 |
| Sitka (99835) | 6.000% | 6.000% | 0.000 |
| Wasilla (99654) | 2.500% | 2.500% | 0.000 |
| Kodiak (99615) | 7.000% | 7.000% | 0.000 |
| Seward (99664) | 7.000% | 7.000% | 0.000 |
| Bethel (99559) | 6.000% | 6.000% | 0.000 |
| Nome (99762) | 6.000% | 6.000% | 0.000 |
| Seldovia (99663) | 9.500% | 9.500% | 0.000 |
| North Pole (99705) | 5.500% | 5.500% | 0.000 |
| Petersburg (99833) | 6.000% | 6.000% | 0.000 |
| Wrangell (99929) | 7.000% | 7.000% | 0.000 |
| Soldotna (99669) | 6.000% | 6.000% | 0.000 |
| Kenai (99611) | 6.000% | 6.000% | 0.000 |
| Anchor Point / Ninilchik / Sterling (99556/99639/99672) | 3.000% | 3.000% | 0.000 |

### Full-sheet diff — 84 ARSSTC ZIPs

**73 exact match · 4 defensibly between the inside/outside bracket ·
1 over-collect · 6 under-collect.**

| ZIP | ARSSTC city | Inside | Outside | Engine | Verdict |
|---|---|---:|---:|---:|---|
| **99928** | **Ward Cove** | — | **2.5** | **5.500** | **OVER-collects 3.00pp** |
| 99903 | Ketchikan | 8.0 | 2.5 | 0.000 | under ≥2.50pp |
| 99918 | Ketchikan | 8.0 | 2.5 | 0.000 | under ≥2.50pp |
| 99950 | Ketchikan | 8.0 | 2.5 | 0.000 | under ≥2.50pp |
| 99824 | Juneau (Douglas) | — | 5.0 | 0.000 | under 5.00pp |
| 99836 | (Sitka area) | 6.0 | — | 0.000 | under 6.00pp |
| 99850 | Excursion Inlet | 4.5 | — | 0.000 | under 4.50pp |
| 99637 | Bethel | 6.0 | 0.0 | 2.000 | between (Toksook Bay) — OK |
| 99645 | Palmer | 4.0 | 0.0 | 3.000 | between — OK |
| 99827 | Excursion Inlet | 4.5 | 7.0 | 5.500 | between (Haines) — OK |
| 99919 | Ketchikan | 8.0 | 2.5 | 6.000 | between (Thorne Bay) — OK |

**99928 Ward Cove is the priority.** Ward Cove is unincorporated in
Ketchikan Gateway Borough — ARSSTC assigns it no city filing code at
all. The engine nonetheless applies the City of Ketchikan's 5.5% tax
*and* drops the 2.5% borough tax it genuinely owes, so both components
are wrong. The correctly-modelled neighbour 99901 returns borough 2.5 +
city 5.5 = 8.0%, which is right.

Full write-up, including why the six 0.000% ZIPs look like missing
boundary rows rather than wrong rates:
`specs/findings/ak-ward-cove-overcollect-and-zero-rate-zips-2026-08.md`.

---

## AL (Alabama) — non-SST — ✅ no pin drift; 6 unmodelled city changes

- **Source:** ALDOR Local Tax Notices archive
  (`revenue.alabama.gov/sales-use/local-tax-notices/`), cross-checked
  against Avalara per-city pages.
- **Last loaded on prod:** self-seeded module (`al_data.py`), built
  2026-05-04; 30 cities + all 67 counties.
- **Drift summary:** **none** in the 24 pinned rows.
- **Recommended action:** none for the rates; see the county-binding bug
  below, which is a separate engine defect.

### Pinned rows — all 24 match

Auburn 36830 9.000 · Birmingham 35203 10.000 · Decatur 35601 9.000 ·
Dothan 36301/36303 9.000 · Epes 35460 8.000 · Florence 35630 9.500 ·
Gadsden 35901 10.000 · Holly Pond 35083 8.500 · Hoover 35226 9.500 ·
Huntsville 35801 9.000 · Knoxville 35469 7.000 · Madison
35756/35757/35758 9.000 · Mobile 36602 10.000 · Montgomery 36104
10.000 · Paint Rock 35764 6.000 · Prattville 36066 9.500 · Selma 36701
10.000 · Tuscaloosa 35401 10.000 · Vredenburgh 36481 7.500 ·
Tuscumbia 35674 5.500 — every one delta 0.000.

One labelling nuance, not an error: ZIP **35216** is pinned as "Hoover"
but the engine returns `Vestavia Hills 4.0 + Jefferson 2.0`. The
combined 10.000% is correct and matches the pin; only the city label
differs, and 35216 does straddle both cities.

### Six ALDOR rate changes — none modelled by the engine

| City | Effective | Modelled? | Engine returns |
|---|---|---|---|
| **Rogersville** | **2026-08-01 (today)** | no | 5.000% (state 4 + Lauderdale 1) |
| **Bay Minette** | **2026-08-01 (today)** | no | 7.000% (state 4 + Baldwin 3) |
| Calera | 2026-07-01 | no | 7.000% — **and the county is wrong, see below** |
| Priceville | 2026-07-01 | no | 35603 resolves to Decatur (shared ZIP) |
| Hackleburg | 2026-07-01 | no | 6.000% |
| Guin | 2026-06-01 | no | 6.000% |

None of the six appear in `AL_CITIES`, so **no engine rate changed and
none is drift** — they are instances of the documented Alabama home-rule
coverage gap (30 of ~700 municipalities seeded). Rogersville's increase
is +1% (its first in 25 years, per WAFF 2026-06-10); the exact new rates
for the others are in the individual ALDOR notice PDFs and should be
read from there before any seeding work.

**Standing doc-accuracy item, re-confirmed today:** Alabama's
`coverage_warning` still says city overlays are not modelled, while 30
cities *are*. Consumers can't tell which. Carried forward from the
2026-07-31 audit; still worth rewording.

---

## Cross-cutting finding — arbitrary county selection on multi-county ZIPs

Chasing why Calera (35040) returned Chilton County uncovered a
**systematic engine defect affecting 7 states, not just Alabama.**

Self-seeded state modules bind at most one county per ZIP. For a ZIP
straddling several counties with no seeded city to anchor it, the loader
takes **the first county in FIPS-sorted order** —
`alabama.py:520`: `# No city anchor for this ZIP -- take the first AL county.`
FIPS order encodes nothing about population or land area.

`ZIP_COUNTY` already stores the full truth
(`"35040": {("AL","021" Chilton), ("AL","117" Shelby)}`); the loader
throws all but one away on a coin flip.

**Confirmed wrong:** Calera AL 35040 → engine binds **Chilton 3.000%**;
Calera is in **Shelby County, 1.000%** (Avalara: "Calera is located in
Shelby County"). The county component **over-collects by 2.00pp**.
Guin 35563 (→ Fayette, actually Marion) and Hackleburg 35564 (→
Franklin, actually Marion) mislabel identically but happen to be
rate-neutral.

**Blast radius** — ZIPs where no city anchor existed, so the tiebreak
alone decided, *and* the candidate counties levy different rates:

| State | Rate-differing | Arbitrary multi-county ZIPs |
|---|---:|---:|
| AL | 172 | 227 |
| NY | 112 | 318 |
| FL | 96 | 137 |
| SC | 93 | 154 |
| CA | 89 | 125 |
| AZ | 28 | 30 |
| PA | 27 | 354 |
| TX / VA / MS / NM / HI | 0 | 1037 |
| **TOTAL** | **617** | **2382** |

TX/VA/MS/NM/HI escape only because their counties currently levy uniform
rates — they run the same rule and would start returning wrong answers
the moment any county diverges. The defect is latent in all 12 modules.

The fix already has a precedent in this codebase: the cross-state ZIP
dedup (iter-165..168) picks the **area-majority** state from Census
`AREALAND_PART`. The same ZCTA relationship data carries county parts,
so the rule should be extended state → county and hoisted into one
shared helper. Hand-pinning the three AL ZIPs would hide 617 others.

Full write-up:
`specs/findings/multi-county-zip-fips-first-tiebreak-2026-08.md`.

---

## Actions taken

| Action | Detail |
|---|---|
| Report | this file |
| Finding | `specs/findings/multi-county-zip-fips-first-tiebreak-2026-08.md` |
| Finding | `specs/findings/ak-ward-cove-overcollect-and-zero-rate-zips-2026-08.md` |
| Chips | 2 — one per finding |
| Commits | **0 rate/pin commits.** Every pin matches; both findings are engine defects needing review, not mechanical bumps. |
| SST refresh | none needed — neither AK nor AL is an SST state |

## Operational note

`open-sales-tax-api-1` and `open-sales-tax-postgres-1` both
`Up 5 days (healthy)`; `api.opensalestax.org` served every probe in this
run. The ~2-day outage found on 2026-07-26 has not recurred, but the
compose services **still carry no `restart:` policy** — that chip
remains open and unapplied.

## Carried forward, still unapplied

The seven-state Q3 SST refresh backlog (AR, ND, NE, SD, TN, WV, WY) is
untouched since the 2026-07-31 audit flagged it as a process problem.
Neither of today's states is affected, but the backlog keeps growing.
