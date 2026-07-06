# HI Maui County GET surcharge — under-collection corrected (2026-07-06)

**Status:** FIXED in repo (commit pending). Prod HI reload PENDING (chipped).

## Summary

The engine under-collected the **Maui County 0.5% GET surcharge** on
**every Maui-County transaction from 2024-01-01 onward**. `hi_data.py`
recorded Maui County at `0.000%` (combined 4.0%) with a comment
asserting "Maui Bill No. 30 (2023) authorized but did not enact a 0.5%
surcharge … verified against the official DOTAX surcharge schedule on
2026-05-04." That assertion was wrong: the Maui surcharge has been in
effect since **2024-01-01**.

## Authoritative confirmation

- **Hawaii DOTAX county-surcharge schedule**
  (https://tax.hawaii.gov/geninfo/countysurcharge/):
  > "The county surcharge at the rate of 0.5% is effective from
  > January 1, 2024 to December 31, 2030." (Maui County)

  Combined Maui rate = state 4.0% + 0.5% surcharge = **4.5%**.
- **Maui County Council** — public notice "General excise tax
  surcharge in effect for Maui County." Enacted by **County Ordinance
  5511**, signed by Mayor Richard T. Bissen, Jr. on **2023-07-19**,
  effective **2024-01-01**.
- The surcharge applies only to activities taxed at the 4.0% rate
  (not the 0.5% wholesale rate or the 0.15% insurance-commission rate).

This was the open item flagged in the handoff (iter-158/159), which
took a conservative "leave at 0.0% pending authoritative cross-check
against HI DOTAX Tax Facts 31-1" stance. The 2026-07-06 daily audit
performed that cross-check; the surcharge is confirmed enacted and
continuously in effect since 2024-01-01, so the deferral is resolved.

## Root cause of the earlier error

The 2026-05-04 module build appears to have conflated "authorized"
(the state enabling legislation permitting counties to levy the
surcharge) with "not yet enacted," and recorded Maui at 0%. In fact
Maui County exercised that authority via Ordinance 5511 well before
the module was written. There was no period in 2024–2026 when Maui was
at 0%; the DOTAX schedule shows a continuous 2024-01-01 → 2030-12-31
surcharge.

## Changes made (repo)

- `src/opensalestax/states/hi_data.py` — `HI_COUNTY_RATE_PCT["Maui County"]`
  `0.000` → `0.500`; `HI_COUNTY_SURCHARGE_EFFECTIVE["Maui County"]`
  `None` → `2024-01-01`; docstring table + notes corrected.
- `src/opensalestax/states/hawaii.py` — docstring ("three of four" →
  "all four" counties) + prepared_food/general TaxabilityRule notes.
- `src/opensalestax/core/coverage.py` — **removed HI from
  `STATE_COVERAGE_WARNINGS`.** The HI warning existed solely because
  of the Maui gap ("Maui rate is provisional"); with all four
  inhabited counties now correctly modeled, HI no longer understates
  the rate, and a warning would be misleading.
- `src/opensalestax/api/v1/{schemas,calculate,rates}.py` — removed the
  now-stale "HI Maui dispute" example from the coverage_warning docs.
- Tests: `tests/unit/test_state_hawaii.py` (Maui rate 0.0→0.5, effective
  date pin, `test_hawaii_combined_rate_maui_is_4_5` rename),
  `tests/unit/test_core_coverage.py` (HI removed from warning set),
  `tests/integration/test_sst_dor_validation.py` (Kahului 96732 pin
  4.000→4.500).

## Prod follow-up (PENDING — chipped)

The **live engine still returns 4.000% for Maui** (96732 Kahului) until
prod is redeployed and HI data is reloaded. Until then the Kahului pin
fails under `-m liveapi`. Deploy sequence:

```bash
ssh opensalestax-01 "cd /home/ejosterberg/open-sales-tax && \
  git pull --ff-only origin main && \
  docker compose build api && \
  docker compose up -d --force-recreate api && \
  docker exec open-sales-tax-api-1 python -m opensalestax data load -s HI -v <current-HI-version>"
```

HI is self-seeded (non-SST), so the reload re-parses `hi_data.py`; no
upstream file is needed.

## Cross-check for other jurisdictions

While here, confirmed Honolulu (0.5% since 2007), Kauai (0.5% since
2019), and Hawaii County (0.5% since 2020) all match the DOTAX
schedule — no change. Kalawao County correctly stays at 0% (no county
taxing authority). All other HI pins (Honolulu 96813, Hilo 96720,
Lihue 96766, Pearl City, Kaneohe, Waipahu, Kailua-Kona) match the
engine at 4.500%.
