# Full-sweep state audit — WV — 2026-11-01

## TL;DR

- **WV is SST.** Prod is on **`WVR2026Q1AUG14` / `WVB2026Q1SEP02`**
  (fetched 2026-05-15) — **two quarters stale.** Latest SST publication
  is **`WVR2026Q3FEB25.csv` / `WVB2026Q3APR29.csv`** (no Q4 WV file
  published).
- **No tier-1 drift.** All three major-city pins (Charleston 25301,
  Morgantown 26505, Huntington 25701) return 7.000% exact — WV's state
  6% + municipal 1% stacks cleanly, and these three cities have been at
  1% for over 5 years.
- **WV State Tax Dept "Municipalities Imposing Sales And Use Taxes"
  PDF (issued 10/22/2026) adds 6 new municipalities effective
  2027-01-01** — Danville, Farmington, Gilbert, Kenova, Keyser,
  Wellsburg — all at the standard 1% rate. Three municipalities were
  added effective 2026-07-01 (Granville, Ronceverte, Welch) that the
  prod Q1 file does not know about. All of these are **boundary-level**
  additions (new ZIP → authority bindings) — the state 6% + municipal
  1% math itself does not change.
- **The 2027-01-01 WV additions make the Q3 refresh time-critical.**
  Chipped the batched SST refresh with WV included.
- **88 of 98 placeholder authority names labelled; 10 remain** (per the
  2026-08-25 handoff). This full-sweep audit did not attempt the long
  tail — the right fix is the FIPS-cousub approach documented in the
  handoff for WI, applied to WV's remaining placeholders.
- **No commit from this audit on WV.** No new code change; one owed
  `data load -s WV` closes both the Q3 refresh and the Q4 boundary
  update, and the January 2027 additions will land in a Q4 file if WV
  publishes one in time.

## Prod data version

```
WV | sst              | WV-SST-2026Q1AUG14 | 2026-05-15
WV | zcta-census-2020 | WV-ZCTA-2020       | 2026-05-11
```

**Two quarters stale.** The 2026-07-26 and 2026-08-25 audits both
chipped the Q3 refresh; it has not been applied.

## SST file index (2026-11-01)

```
WVR2026Q3FEB25.csv   (latest rate)
WVB2026Q3APR29.csv   (latest boundary)
```

No Q4 WV file is published yet.

## WV State Tax Dept municipality list (issued 10/22/2026)

Pulled from `tax.wv.gov/Documents/SUT/MunicipalitiesImposingSalesAndUseTaxes.pdf`:

| Group | Count | Examples |
|---|---|---|
| 2026-07-01 additions | 3 | Granville, Ronceverte, Welch |
| 2027-01-01 additions | 6 | Danville, Farmington, Gilbert, Kenova, Keyser, Wellsburg |

All at the standard 1% municipal rate; combined 7% state + municipal.

The 2026-07-01 batch lands when WV Q3 is loaded on prod; the
2027-01-01 batch needs the WV Q4 file if WV publishes one before
2027-01-01, otherwise an interim muni-only fix is owed. Chipped.

## Live engine probes (bare ZIP, `/v1/rates`)

| ZIP | City (county) | Engine | WV Tax expected | Delta |
|---|---|---|---|---|
| 25301 | Charleston (Kanawha) | 7.000 | 7.000 | 0.00 ✓ |
| 26505 | Morgantown (Monongalia) | 7.000 | 7.000 | 0.00 ✓ |
| 25701 | Huntington (Cabell) | 7.000 | 7.000 | 0.00 ✓ |

All tier-1 cities match.

## Status

- **REFRESH / RELOAD PENDING** — one owed `data load -s WV` closes the
  Q3 refresh. The 2027-01-01 additions become drift on 2027-01-01 if
  not loaded by then.
- **Placeholder-name long tail (10 remaining)**: tracked as a separate
  friendly-name ratchet, out of scope for the full-sweep audit.
- **No code change** this audit.

## Reload command (for Eric when deploy unblocks)

```bash
ssh opensalestax-01 'cd /home/ejosterberg/open-sales-tax && \
  git pull --ff-only origin main && \
  docker compose build api && \
  docker compose up -d --force-recreate api && \
  docker exec open-sales-tax-api-1 python -m opensalestax data load \
    -s WV -v WV-SST-2026Q1AUG14'
```

Reuse the existing label.
