# Daily state sales tax audit — 2026-11-01 (full-sweep: UT)

## TL;DR

- **STILL UNRESOLVED from the 2026-10-28 audit.** UT is on `UTR2026Q2MAR20`
  on prod; SST has published `UTR2026Q4AUG11` / `UTB2026Q4AUG11`. The Q4
  refresh never ran. The six Q4-caused under-collections identified on
  10-28 are still live 4 days later:
  - Every **Weber County** location is 0.2pp low (eff 2026-10-01, UT Tax
    Bulletin 15-26 county highways + transit).
    - Ogden 84401 → 7.25% (expected 7.45%, **-0.20**)
    - North Ogden 84414 → 7.25% (expected 7.45%, **-0.20**)
    - Roy 84067 → 7.45% (expected 7.65%, **-0.20**)
  - Washington City 84780 (0.33pp low)
  - Toquerville 84774 (0.30pp low)
  - Hildale 84784 (0.33pp low)
  - Delta 84624 (0.30pp low)
  - **Hanksville 84734 (1.40pp low)** — confirmed 2026-11-01 by probe:
    engine returns 7.65% (state 4.85 + Wayne 2.80, no city), expected
    9.05%.
- **UT is an SST member**, so there is no code fix. The fix is applying
  the Q4 refresh on prod. Apply Q4, skip Q3.
- The Ogden pin at `tests/integration/test_sst_dor_validation.py` is
  already bumped 7.25 → 7.45 by the 10-28 chip (`-m liveapi` fails until
  the refresh lands; `liveapi` is excluded from CI).
- **This audit adds no new drift findings** — nothing effective 2026-10-01
  through 2026-11-01 that is not already in the Q4 file.
- **Status:** REFRESH_PENDING (UT Q4; chipped already in 10-28).

## Source

- SST index: `UTR2026Q4AUG11.csv` / `UTB2026Q4AUG11.csv` (upstream).
- UT State Tax Commission Tax Bulletins
  (`https://tax.utah.gov/tax-bulletins/`): **15-26** (eff 2026-10-01) and
  **11-26** (eff 2026-07-01).
- Prior audit record: `specs/audits/2026/10/state-audit-2026-10-28.md`.

## Procedure

- Live re-probe of the six confirmed under-collections:
  - 84401 Ogden → 7.25% (vs expected 7.45%, **-0.20**)
  - 84734 Hanksville → 7.65% (vs expected 9.05%, **-1.40**)
  - Ogden/Hanksville confirmed; the other 4 Weber ZIPs and
    Washington City / Toquerville / Hildale / Delta remain unchanged
    pending the Q4 load (same bare-ZIP math as 10-28).
- `data_versions` on prod unchanged (`UT-SST-2026Q2MAR20`, fetched
  2026-05-15).
- Workflow pin in `.github/workflows/build-data-dump.yml` already reads
  `"UT 2026Q4AUG11 2026Q4AUG11"` — a release-tag data-dump build would
  pick up Q4 correctly today; it is specifically the running prod API
  that has not reloaded.

## Recommended action

**REFRESH NEEDED → UT Q4** (chipped on 2026-10-28 and still owed):

```bash
# On opensalestax-01, after Eric unblocks the data-load path:
docker exec open-sales-tax-api-1 python -m opensalestax data load \
  -s UT -v UT-SST-2026Q4AUG11
```

Reuse (or set) the existing label `UT-SST-2026Q4AUG11` so the loader
purges by exact label match and does not double-stack rates. After the
load, the Ogden pin flips to passing under `-m liveapi` and the 6
probed sites return the correct totals.

## Actions taken

None. Audit report only; the Ogden pin bump is already in on 10-28.
