# Full-sweep state audit — FL — 2026-11-01

## TL;DR

- **FL is non-SST, self-seeded** (prod version `FL-SST-2026Q2APR15`,
  fetched 2026-05-11). **Three live over-collections** persist on
  prod, all fixed in repo and all awaiting a `data load -s FL`:
  Palm Beach (33401, 33432), Collier (34102), Okeechobee (34972).
  Confirmed by live probe this run.
- **Zero new drift this cycle.** DR-15DSS CY2026 (R. 11/25) is still
  the authoritative FL surtax chart; **DR-15DSS CY2027 is NOT YET
  POSTED** — `dr15dss_27.pdf` returns 404 as of 2026-11-01 14:50 CT.
- **Brevard + Charlotte expire 2026-12-31.** DR-15DSS CY2026 confirms
  both: Brevard (.5%+.5%) Dec 31 2026 end date, Charlotte 1% Apr 1
  1995–Dec 31 2026. If neither renews on the CY2027 chart, Palm Bay
  (`32905`, Brevard) and Punta Gorda (Charlotte) drop to the state 6%
  base effective 2027-01-01. **This becomes drift on the day the
  CY2027 chart posts** (normally November).
  - The dedicated day-5 November run (handoff item) still owes the
    CY2027 chart check as soon as it posts; chipped.
- **Source-URL trap re-confirmed.** The unsuffixed
  `.../current/dr15dss.pdf` **still serves CY2025 (R. 11/24)** —
  Brevard, Charlotte, Palm Beach, Martin and Collier are all wrong
  there. Future audits must use the year-suffixed `dr15dss_26.pdf` (or
  the eventual `dr15dss_27.pdf` when posted). The warning in
  `fl_data.py`'s docstring stays accurate.
- **No commit from this audit on FL.** All three repo-side fixes
  (`32a61f6` from 2026-07-05 for Palm Beach / Collier, the Okeechobee
  revert from the 2026-09-21 daily audit) are already in main. Fixture
  only re-exercises the known reload chip.

## Prod data version

```
FL | sst              | FL-SST-2026Q2APR15 | 2026-05-11
FL | zcta-census-2020 | FL-ZCTA-2020       | 2026-05-11
```

Repo HEAD = fixtures include the Palm Beach 0.5%, Collier None,
Okeechobee 1% corrections. Prod has none of them.

## Live probes (bare ZIP, `/v1/rates`)

| ZIP | City (county) | Engine | DR-15DSS CY2026 expected | Delta |
|---|---|---|---|---|
| 33401 | West Palm Beach (Palm Beach) | **7.000** | 6.500 | **+0.500** (over) |
| 33432 | Boca Raton (Palm Beach)      | not probed      | 6.500 | **+0.500** (over, same cause) |
| 34102 | Naples (Collier)             | **7.000** | 6.000 | **+1.000** (over) |
| 34972 | Okeechobee                   | **7.500** | 7.000 | **+0.500** (over) |
| 33010 | Hialeah (Miami-Dade)         | not probed      | 7.000 | 0.00 (expected) |

All three over-collections are the same reload-pending issue; one
`data load -s FL` lands all three.

## CY2026 DR-15DSS re-verification (fetched this run)

Downloaded `dr15dss_26.pdf` (R. 11/25) and extracted the rows for every
county previously flagged:

| County | DR-15DSS row | Repo fixture | Match? |
|---|---|---|---|
| Palm Beach | **.5%** Jan 1 2026 — Dec 31 2035 | 0.500 | ✓ |
| Collier | **None** | 0.000 | ✓ |
| Okeechobee | **1%** Oct 1 1995 — None | 1.000 | ✓ |
| Brevard | **1%** (.5+.5) — both Dec 31 2026 | 1.000 | ✓ (will drift 2027-01-01) |
| Charlotte | **1%** Apr 1 1995 — Dec 31 2026 | 1.000 | ✓ (will drift 2027-01-01) |
| Jackson | 1.5% | — | ✓ (not in FL_CITIES) |
| Martin | **.5%** Jan 1 2025 — Dec 31 2034 | — | ✓ (not in FL_CITIES) |

## CY2027 DR-15DSS availability

Checked `https://floridarevenue.com/Forms_library/current/dr15dss_27.pdf`
at 2026-11-01 14:50 CT. **Server returned HTTP 404 Not Found.** The
CY2027 chart has not yet posted. Historically it posts in November, so
the day-5 November run (next scheduled 2026-11-05 under the daily
rotation) is still the right place to check.

## Status

- **REFRESH / RELOAD PENDING** (unchanged chip from 2026-09-21).
- **No new code change this audit.** All three fixes already in repo.
- **Open watch items**:
  1. CY2027 DR-15DSS when it posts (Brevard / Charlotte renewal).
  2. `dr15dss.pdf` unsuffixed URL still serves CY2025 — leave the
     docstring warning in place.
  3. 32 FL pins all pass with current repo code; the `DOR_GRID`
     ad-hoc offline check (chipped since 2026-09-05) is still the
     project-wide top follow-up.

## Reload command (for Eric when deploy unblocks)

```bash
ssh opensalestax-01 'cd /home/ejosterberg/open-sales-tax && \
  git pull --ff-only origin main && \
  docker compose build api && \
  docker compose up -d --force-recreate api && \
  docker exec open-sales-tax-api-1 python -m opensalestax data load \
    -s FL -v FL-SST-2026Q2APR15'
```

Reuse the existing label (loader purges by exact label match).
