# Full-sweep state audit — NC — 2026-11-01

## TL;DR

- **NC is SST**. Prod is on the ~ 2-year-stale `NCR2024Q3APR26.csv` with
  boundary `NCB2026Q2FEB18`, fetched 2026-05-04. Latest SST publication
  is **`NCR2026Q3APR23.csv` / `NCB2026Q4AUG19.zip`** — no Q4 rate file;
  only a Q4 boundary. NCDOR's own "Current Sales and Use Tax Rates"
  page re-verified today as **"Effective July 1, 2026"** with no newer
  edition published.
- **One live under-collection, 123 days unapplied: Charlotte 28202
  returns 7.250%, should be 8.250%** (Mecklenburg additional 1% eff
  2026-07-01, voter-approved 2025-11-04). Confirmed live this run.
  Pin at line 220 (`28202 → 8.250`) continues to fail under `-m liveapi`
  by design.
- **No other NC county moved in 2026.** NCDOR's rate page confirms
  Mecklenburg is the only county change in 2025-26. Raleigh, Wake,
  Guilford, Durham, Forsyth, Cumberland, Buncombe, New Hanover all
  still 7.00–7.25% matching the engine.
- **iter-221 NC district-name fix is in repo but not deployed.**
  `nc_names.py` is still accurate: NCDOR lists exactly four active
  99XXX Public Transportation Tax codes (99063 Durham, 99119
  Mecklenburg, 99135 Orange, 99183 Wake); 99055 is NOT listed by NCDOR
  and remains removed. No change needed this audit.
- **No commit from this audit on NC.** No new code change; the single
  owed `data load -s NC` lands both the Mecklenburg correction and the
  iter-221 friendly-name reload.

## Prod data version

```
NC | sst              | NC-SST-2024Q3APR26 | 2026-05-04
NC | zcta-census-2020 | NC-ZCTA-2020       | 2026-05-11
```

**~ 2 years stale** on rates (prod `NCR2024Q3APR26`; upstream
`NCR2026Q3APR23`). NC is the stalest SST state after what remains of
the long tail.

## SST file index (2026-11-01)

```
NCR2026Q3APR23.csv   (latest rate; no Q4 rate file published)
NCB2026Q4AUG19.zip   (latest boundary)
```

NCDOR has not published a Q4 2026 rate chart. The Q4 boundary file was
published on schedule (Aug 19).

## NCDOR rate chart re-verification (2026-11-01)

NCDOR page `/taxes-forms/sales-and-use-tax/sales-and-use-tax-rates-other-information`
confirmed to still show **"Current Tax Rates (Effective July 1, 2026)"**
with Mecklenburg as the single 2026 county change.

## Live engine probes (bare ZIP, `/v1/rates`)

| ZIP | City (county) | Engine | NCDOR expected | Delta |
|---|---|---|---|---|
| 28202 | **Charlotte (Mecklenburg)** | **7.250** | **8.250** | **−1.000** |
| 27601 | Raleigh (Wake) | 7.250 | 7.250 | 0.00 ✓ |

Mecklenburg's additional 1% was enabled by the 2025-11-04 referendum
and took effect 2026-07-01 (NCDOR Important Notice 2026-06-24). The
engine still returns the pre-change value — a reload is required.

## Status

- **REFRESH / RELOAD PENDING** (unchanged chip from 2026-07-14).
- **No new code change** this audit.
- **iter-221 district-name correction** still waiting for the same
  reload.
- **1 live wrong rate**, 1 engine over-collection count unchanged.

## Reload command (for Eric when deploy unblocks)

```bash
ssh opensalestax-01 'cd /home/ejosterberg/open-sales-tax && \
  git pull --ff-only origin main && \
  docker compose build api && \
  docker compose up -d --force-recreate api && \
  docker exec open-sales-tax-api-1 python -m opensalestax data load \
    -s NC -v NC-SST-2024Q3APR26'
```

Reuse the existing label. After reload, the Charlotte `28202 → 8.250`
pin xpasses and the iter-221 district-name xfails should also xpass.
