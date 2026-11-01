# Daily state sales tax audit — 2026-11-01 (full-sweep: ID)

## TL;DR

- **ID state rate 6.00% returned exactly** on Boise 83702 and Coeur
  d'Alene 83814 (both state-only) and on Ketchum 83340 (state 6 + resort
  3 = 9.00%, as modelled).
- **Fully clean at the pinned cities.** No per-rate drift against the
  Idaho State Tax Commission as of 2026-11-01 — no local-option rate
  changes have been announced since the 2026-08-15 clean audit.
- **Known coverage gap unchanged** — 11 of 23 ISTC local-option cities
  (Bellevue, Bonners Ferry, Hailey, Harrison, Irwin, Kellogg, Mackay,
  Ponderay, Swan Valley, Tetonia, Victor) remain deferred because the
  ISTC does not publish a consolidated rate table and each city levies
  under its own ordinance (rate, scope, base, cadence all differ).
- **No code or data change this run.**
- **Status:** UNCHANGED.

## Source

- ID State Tax Commission "Sales and Use Tax Rate Changes"
  (`https://tax.idaho.gov/taxes/sales-use/local-sales-tax/`) — the ISTC
  directs filers to contact each city for its exact ordinance.
- Prior clean audit: `specs/audits/2026/08/state-audit-2026-08-15.md`.

## Procedure

- Live probes (`POST /v1/calculate`, bare ZIP5, $100):
  - `83702` Boise → 6.00% ✓ (state only).
  - `83814` Coeur d'Alene → 6.00% ✓ (state only; CDA is not a
    local-option city).
  - `83340` Ketchum → 9.00% ✓ (state 6 + resort 3).
- `id_data.py` module unchanged since the 2026-08-15 clean run.

## Known gaps (standing)

- 11 ISTC local-option cities not modelled (listed above). Each would
  require a per-city primary-source lookup; no consolidated rate table
  from ISTC. Noted in handoff as a coverage-expansion candidate.

## Actions taken

None. Audit report only.
