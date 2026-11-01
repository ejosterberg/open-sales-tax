# Full-sweep state audit — AL — 2026-11-01

## TL;DR

- **AL is a non-SST, self-seeded state** (prod version
  `AL-SST-V0.31-STATEWIDE-COUNTY`, fetched 2026-05-10). The one real,
  modelled rate change this season — **Autauga County 2.0% → 2.5% eff
  2026-09-01** (Act 2026-362, ALDOR notice `Autauga-County_20260824.pdf`,
  `taxrates.csv` locality 7001 `RC` row active 20260901) — is already
  committed in repo (`f5390fd`) but **has not been reloaded on prod**.
  Prattville 36066 still returns 9.500% on the live engine; the ALDOR +
  Avalara answer is 10.000%. **0.5pp live under-collection, 61 days
  stale.**
- **No new rate drift on any of the 24 pinned AL cities.** All 24 pins
  match the live engine (combined 9.0–10.0%). The Autauga Prattville
  pin at `tests/integration/test_sst_dor_validation.py` line 3474 is
  already recorded (bumped 9.500 → 10.000 by the 2026-10-01 daily audit)
  and continues to fail under `-m liveapi` by design.
- **ALDOR local-tax-notices page checked 2026-11-01**: four rate-change
  notices with 2026-10-01 effective dates (Semmes, Huntsville, Madison,
  Moody) plus four 2026-11-01 non-rate items (Winston County new tax,
  Cleveland / Opelika / Tallapoosa County admin changes).
  - **Huntsville notice `Huntsville_20260921.pdf` is lodgings only**
    (general lodgings 9.0% → 10.0%, ordinance 26-484); not general
    sales tax, out of v1 scope.
  - **Madison, Moody and Winston County notices not yet fetched** —
    low expected impact (Madison lodgings is the pattern for this
    round; Winston / Cleveland / Opelika / Tallapoosa are admin
    changes). None of them is on an AL_CITIES seed except Madison;
    the Madison general-retail rate (city 4.5% + Madison Co Sp 1%
    folded, iter-74) was not touched.
  - **Semmes** was already in the handoff backlog as a 2026-10-01
    change that is NOT seeded in `AL_CITIES` (coverage-expansion
    candidate under the home-rule gap, not drift).
- **Deploy backlog unchanged** (reload is Eric's step):
  1. Autauga County 2.0 → 2.5 (repo `f5390fd`, this project)
  2. The 2026-08-01 `e99237f` fixes (multi-county tiebreak,
     AK/AL/AZ data, Calera Chilton → Shelby)
  3. 2026-10-01 ALDOR coverage-gap candidates (Dadeville, Pike Road,
     Semmes) — unseeded under the ~670-city home-rule gap
- **No commit from this audit** on AL. Nothing new to add.

## Prod data version

```
AL | sst              | AL-SST-V0.31-STATEWIDE-COUNTY | 2026-05-10
AL | zcta-census-2020 | AL-ZCTA-2020                  | 2026-05-11
```

Prod code deploy: `091d9ba` (per handoff 2026-10-01); the Autauga and
multi-county-tiebreak fixes landed later and have never been reloaded.

## Live probes (bare ZIP, `/v1/rates`)

| ZIP | City (county) | Engine | ALDOR expected | Delta |
|---|---|---|---|---|
| 36066 | Prattville (Autauga) | **9.500** | **10.000** | **−0.500** |
| 35203 | Birmingham (Jefferson) | 10.000 | 10.000 | 0.00 (BSD +1% not modeled) |
| 35801 | Huntsville (Madison) | 9.000 | 9.000 | 0.00 |
| 36602 | Mobile (Mobile) | 10.000 | 10.000 | 0.00 |
| 36104 | Montgomery (Montgomery) | 10.000 | 10.000 | 0.00 |

The Prattville under-collection is the full extent of modelled-city
drift. All 24 pinned AL cities pass; the Prattville pin is already in
`DOR_GRID` at line 3474 and will xpass after the reload.

## Status

- **REFRESH / RELOAD PENDING** — one real rate change (Autauga) in
  repo but not on prod. ~ 2 months of 0.5pp over-collection on every
  Autauga County / Prattville transaction averted only by whoever
  reloads AL on `opensalestax-01`.
- **No new drift** this cycle.
- **Home-rule coverage gap**: still 30 of ~700 cities seeded; chipped
  for a future ratchet (ALDOR `taxrates.csv` makes wholesale city
  seeding tractable).

## Reload command (for Eric when deploy unblocks)

```bash
ssh opensalestax-01 'cd /home/ejosterberg/open-sales-tax && \
  git pull --ff-only origin main && \
  docker compose build api && \
  docker compose up -d --force-recreate api && \
  docker exec open-sales-tax-api-1 python -m opensalestax data load \
    -s AL -v AL-SST-V0.31-STATEWIDE-COUNTY'
```

Reuse the **existing** label; the loader purges by exact label match and
a new label would double-stack the May rows.
