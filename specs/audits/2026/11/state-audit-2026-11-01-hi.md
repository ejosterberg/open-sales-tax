# HI state-tax audit — 2026-11-01 (full-sweep Pacific)

**Auditor:** region-agent (Pacific sweep)
**Branch:** `audit-sweep-pac-20261101`
**Status:** REFRESH_PENDING (Maui fix still unapplied on prod)

## What was checked

- Prod `data_versions` for HI: `HI-SST-V0.32-COUNTIES` fetched **2026-05-05**.
  Predates the 2026-07-06 Maui fix (`HI-SST-V0.32-COUNTIES` label reused in repo).
- `src/opensalestax/states/hi_data.py` — unchanged this run.
- Hawaii DOTAX source: https://tax.hawaii.gov/geninfo/countysurcharge/ (updated
  Jan 9, 2024) — county surcharges unchanged: Honolulu 0.5% (2007-2030),
  Kauai 0.5% (2019-2030), Hawaii 0.5% (2020-2030), **Maui 0.5% (2024-2030)**,
  Kalawao 0% (not listed; always 0). No 2026 or 2027 changes announced.
- GET general rate page https://tax.hawaii.gov/get/ (updated Aug 27 2026) —
  4.5% general rate (4% + 0.5% county surcharge for counties that levy it);
  0.5% wholesale; 0.15% insurance commissions. No change.

## Live defects still outstanding (no new fixes landed this run)

### Maui County `96732` Kahului returns 4.000%, should be 4.500%

**0.5pp under-collection on every Maui transaction since 2024-01-01**. Fixed
in repo on 2026-07-06; prod HI DataVersion is `HI-SST-V0.32-COUNTIES`
fetched 2026-05-05 — predates the fix. Fix is a plain
`data load -s HI -v HI-SST-V0.32-COUNTIES` (reuse label) after a redeploy
or hot-load of the states module. **Cheapest outstanding fix on the board.**

## Files touched

None. Audit report only.

## Live engine status

No code change this run. HI 96732 remains 0.5pp under-collecting pending
prod reload. All other HI pins (7 of 8) pass.

## Commits

- `data(HI): full-sweep 2026-11-01 audit — Maui 96732 reload still pending`
