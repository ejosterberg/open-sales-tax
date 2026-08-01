# Multi-county ZIP county selection uses an arbitrary FIPS-first tiebreak

**Found:** 2026-08-01 (daily state audit, day 1 — AK + AL)
**Status:** ✅ **FIXED IN REPO 2026-08-01** — prod reload still pending
(see "Resolution" at the bottom)
**Severity:** Medium-high. **617 ZIPs across 7 states** get a county rate
chosen by a tiebreak that has no relationship to which county actually
contains the ZIP. Some picks are right by luck; the rule itself is
arbitrary, and at least one confirmed case **over-collects by 2.00pp**.

## Summary

Every self-seeded (non-SST) state module binds **at most one county per
ZIP**. When a ZIP straddles multiple counties and the ZIP has no seeded
city to anchor it, the loader takes **the first county in FIPS-sorted
order**. FIPS order is alphabetical-by-county-name at assignment time —
it says nothing about population, land area, or where the ZIP's
addresses actually are.

The code is explicit about it. `src/opensalestax/states/alabama.py:520`:

```python
# No city anchor for this ZIP -- take the first AL county.
chosen_county = al_county_name
break
```

`ZIP_COUNTY` already records the full multi-county truth
(`"35040": frozenset({("AL", "021"), ("AL", "117")})`) — the loader
discards all but one, by a rule that is effectively a coin flip.

## Confirmed wrong case (the one that motivated this finding)

**Calera, AL — ZIP 35040.**

| | |
|---|---|
| `ZIP_COUNTY["35040"]` | `{AL-021 Chilton, AL-117 Shelby}` |
| FIPS-first pick | **021 → Chilton County, 3.000%** |
| Actual county | **Shelby County, 1.000%** (verified: Avalara Calera page — "Calera is located in Shelby County"; Calera is the ZIP's principal city) |
| Live engine `GET /v1/rates?zip5=35040` | `7.000%` = Alabama 4.0 + **Chilton County 3.0** |
| Correct county component | **1.000%** |
| **Error** | **county component over-collects by 2.00pp** |

The engine also misses Calera's 5% city tax (a separate, documented
Alabama home-rule coverage gap — ALDOR-published combined rate is
10.000%). Those two errors point in opposite directions and must not be
treated as cancelling: the county component is independently wrong, and
would still be wrong after the city is seeded.

Two more AL ZIPs surfaced the same way in the same audit, both
rate-neutral by coincidence (both candidate counties happen to levy
2.000%), so they mislabel the jurisdiction without changing the rate:

| ZIP | Principal city | FIPS-first pick | Actual county |
|---|---|---|---|
| 35563 | Guin | Fayette County (057) | **Marion County** (093) |
| 35564 | Hackleburg | Franklin County (059) | **Marion County** (093) |

## Blast radius

Measured by walking `ZIP_COUNTY` against each module's own
`parse_rates()` / `parse_boundaries()` output (script preserved below).
"Arbitrary" = the ZIP straddles ≥2 counties that the module rates, and
**no seeded city anchored it**, so the FIPS-first rule alone decided.
"Rate-differing" = those candidate counties do **not** all levy the same
rate, so the choice changes the answer.

| State | Rate-differing | Arbitrary multi-county ZIPs |
|---|---:|---:|
| AL | **172** | 227 |
| NY | **112** | 318 |
| FL | **96** | 137 |
| SC | **93** | 154 |
| CA | **89** | 125 |
| AZ | **28** | 30 |
| PA | **27** | 354 |
| TX | 0 | 491 |
| VA | 0 | 283 |
| MS | 0 | 226 |
| NM | 0 | 37 |
| HI | 0 | 0 |
| **TOTAL** | **617** | **2382** |

TX/VA/MS/NM/HI are unaffected today only because their counties levy a
uniform rate (or the state models no county tier) — they are still
running the same arbitrary rule and would start producing wrong answers
the moment any county's rate diverges. The rule is latent everywhere.

Worst spreads observed (candidate rates that differ most, so the
tiebreak matters most):

| ZIP | Chosen | Candidates |
|---|---|---|
| 35016 (Arab, AL) | Blount 3.000% | Blount 3.0 / **Cullman 4.5** / Marshall 1.0 / Morgan 1.0 |
| 29945 (SC) | Beaufort 0.000% | Beaufort 0.0 / Colleton 2.0 / Hampton 1.0 / **Jasper 3.0** |
| 11001 (Floral Park, NY) | Nassau 4.250% | Nassau 4.25 / Queens 0.0 |
| 90265 (Malibu, CA) | Los Angeles 2.500% | LA 2.5 / Ventura 0.0 |
| 34141 (FL) | Collier 0.000% | Collier 0.0 / Miami-Dade 1.0 / **Monroe 1.5** |

## Why this is a real bug and not "ZIPs are inherently imprecise"

A ZIP that straddles a county line has no single correct answer for
*every* address in it — that much is inherent, and the API documents
ZIP-level approximation. But that is an argument for picking the
**dominant** county, not an arbitrary one. Today's rule:

- is not documented to consumers as "arbitrary" — the response names a
  specific county authority, which reads as an assertion of fact;
- is unstable in the wrong way: it is *stable* across runs but tracks
  FIPS numbering, so a rate change in an unrelated county silently
  changes who over/under-collects;
- already has a correct precedent in this codebase. The **cross-state**
  ZIP dedup (iter-165..168) solved the identical problem by summing
  Census `AREALAND_PART` per state and taking the area majority — see
  `_canonical_state_for_zip` and `CLAUDE.md`'s "Cross-state ZIP dedup"
  note. The same Census ZCTA relationship data carries county parts.

## Recommended fix

1. Extend the ZCTA-derived dominance rule from state → **county**.
   Load the Census ZCTA-to-county relationship file's per-county
   `AREALAND_PART` (ideally `POPULATION_PART`, which is the better proxy
   for where taxable transactions occur) and pick the majority county.
2. Replace the `# take the first <XX> county` branch in all 12 modules
   (`alabama`, `arizona`, `california`, `florida`, `hawaii`,
   `mississippi`, `new_mexico`, `new_york`, `pennsylvania`,
   `south_carolina`, `texas`, `virginia`) with a single shared helper so
   the rule lives in one place and cannot drift per state.
3. Add a regression test asserting the dominant-county rule for a fixed
   set of known-straddling ZIPs (35040 Calera→Shelby, 35563 Guin→Marion,
   35564 Hackleburg→Marion are ready-made fixtures).
4. Consider surfacing multi-county ambiguity in the response — either a
   `coverage_warning` for straddling ZIPs, or returning the ZIP+4 path as
   the precise answer. **Do not** paper over the individual ZIPs by
   hand-pinning them; that hides the rule instead of fixing it.

Per the root-cause discipline in the global CLAUDE.md: hand-editing
`ZIP_COUNTY` or adding city anchors for the three AL ZIPs found today
would make the symptom disappear while leaving 617 ZIPs on the same
arbitrary rule. Fix the selection rule.

## Reproduction

```bash
# Live confirmation of the Calera case:
curl -s -H 'User-Agent: Mozilla/5.0' \
  'https://api.opensalestax.org/v1/rates?zip5=35040'
# -> 7.000% = Alabama 4.0 + Chilton County 3.0   (Calera is in Shelby, 1.0)
```

The blast-radius table was produced by importing each registered module,
calling `parse_rates()` / `parse_boundaries()`, and comparing the bound
county against all `ZIP_COUNTY` candidates for ZIPs with no city-anchor
boundary row. Requires Python 3.11+ (the repo's Poetry venv).

---

## Resolution (2026-08-01, same day)

Fixed as recommended — the selection rule was replaced, not the
individual ZIPs.

**New shared helper:** `src/opensalestax/data/county_choice.py`
(`choose_county_name`). Three tiers, in order:

1. A hand-curated **city anchor** wins — it is a human-verified
   assertion and outranks geometry.
2. Otherwise the **Census land-area-majority county**, from the new
   `ZIP_COUNTY_DOMINANT` map.
3. Only if Census records nothing usable among the *rated* candidates,
   the historical lowest-FIPS fallback, so the function stays total.

**New data + generator:** `src/opensalestax/data/zip_county_dominant.py`
(33,931 `(ZIP, state)` pairs) generated by
`scripts/regen_zip_county_dominant.py` from the same Census ZCTA→county
relationship file (`AREALAND_PART`, column 17) that the cross-state
dedup already uses. `zip_county.py` was deliberately left untouched so
the diff stays reviewable.

**All 12 modules converted** — `alabama`, `arizona`, `california`,
`florida`, `hawaii`, `mississippi`, `new_mexico`, `new_york`,
`pennsylvania`, `south_carolina`, `texas`, `virginia`. Two needed care:

- **Virginia** keeps its Historic Triangle tier, a deliberate
  rate-preserving override that still outranks geometry; only its final
  arbitrary tier changed.
- **Hawaii** has no city anchors and zero measured multi-county ZIPs
  (its counties are islands), but was converted anyway so the arbitrary
  rule is not left latent there.

### Measured impact

**1,257 ZIPs re-bound to a different county; 305 of those change the
rate.**

| State | Re-bound | Rate changed |
|---|---:|---:|
| TX | 257 | 0 |
| PA | 186 | 16 |
| NY | 172 | 59 |
| VA | 146 | 0 |
| MS | 129 | 0 |
| AL | 118 | 86 |
| SC | 82 | 42 |
| FL | 69 | 47 |
| CA | 64 | 41 |
| NM | 19 | 0 |
| AZ | 15 | 14 |
| HI | 0 | 0 |

(The 617 figure above measures *exposure* — how many ZIPs have
rate-differing candidates — and is a property of the data, so it does
not move when the rule changes. 305 is the count of answers that
actually changed.)

Largest corrections, each verified as a real-world county fix:

| ZIP | Was | Now | Δ |
|---|---|---|---|
| NY 10803 (Pelham) | Bronx 0.000% | **Westchester 4.000%** | +4.000 |
| AL 35621/35622 (Falkville) | Cullman 4.500% | **Morgan 1.000%** | −3.500 |
| SC 29927 (Hardeeville) | Beaufort 0.000% | **Jasper 3.000%** | +3.000 |
| CA 95552 (Mad River) | Humboldt 2.250% | **Trinity 0.000%** | −2.250 |
| AL 35040 (Calera) | Chilton 3.000% | **Shelby 1.000%** | −2.000 |
| CA 90623 (La Palma) | Los Angeles 2.500% | **Orange 0.500%** | −2.000 |
| AZ 86434 (Peach Springs) | Coconino 1.300% | **Mohave 0.000%** | −1.300 |
| FL 32081 (Ponte Vedra) | Duval 1.500% | **St. Johns 0.500%** | −1.000 |
| PA 15003 (Ambridge) | Allegheny 1.000% | **Beaver 0.000%** | −1.000 |

FL 32081 was independently confirmed against Avalara ("Saint Johns
County … 6.5% = state 6.0 + county 0.5"), matching the corrected
output exactly.

### Tests

`tests/unit/test_county_choice.py` (19 cases) pins the nine confirmed
corrections, four ZIPs the old rule got right (guarding against
over-correction), anchor precedence, the unrated-county and
nothing-rated edges, and an end-to-end check that the AL module
actually calls the helper. Full suite: 1573 passed.

### Still to do

The live engine keeps returning the old counties until each affected
state is reloaded on prod — that reload is **not** part of this change
and is tracked separately.
