# Daily state sales tax audit — 2026-07-10 (day 10: LA + MA)

## TL;DR
- 2 states audited (both non-SST, both flat self-seeded statewide rates).
- **0 rate changes found. 0 requiring code/test updates.** Both states
  are fully current and match the live engine exactly.
- LA's documented parish-deferral (state-only 5%) is unchanged and
  out of scope for v1 — noted below, not a drift finding.

## LA (Louisiana)
- Source: LDR FAQ "What is the state sales tax rate?"
  (https://revenue.louisiana.gov/tax-education-and-faqs/faqs/sales-tax-reform/what-is-the-state-sales-tax-rate/)
- Model: non-SST, **self-seeded state-only 5.000%**. Parish/municipal/
  special-district rates are **not modeled** in v1 by design — see
  `specs/decisions/05-louisiana-parishes.md`. LA fires a
  `coverage_warning` on every response (state-only understates the
  true combined rate).
- Last loaded on prod: statewide 5.000% row (`v0.7-statewide`,
  effective 2025-01-01 → 2029-12-31 per Act 11 / HB 10, 2024 3rd
  Extraordinary Session).
- Latest available: **5.000%** — LDR confirms the 5% rate is in effect
  "Until 12/31/2029" (steps down to 4.75% on 2030-01-01 absent further
  legislation). No change for 2026.
- Drift summary: **None.** Engine 5.000% == LDR headline 5.000%.
- Recommended action: **None.** File is a self-seeded constant, not an
  SST quarterly file — nothing to refresh. Flag for CY2029: the
  `effective_to=2029-12-31` self-expiry + the 4.75% successor row will
  need to be added as 2030 approaches (already documented in the
  module docstring).
- Details:

  | City | Expected (DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | New Orleans 70112 (state-only) | 5.000% | 5.000% | 0.000% |

  Note: New Orleans's *true combined* rate is ~9.45% (state 5% +
  Orleans Parish local ~4.45%). The engine's 5.000% is the documented
  state-only answer, surfaced with a `coverage_warning`; this is
  intentional v1 scope, **not** a rate change. LA per-parish rollup
  remains the single most impactful open state-buildout contribution
  (64 parish commissions) — tracked in the module docstring /
  MAINTAINERS, not re-chipped here.

## MA (Massachusetts)
- Source: mass.gov/dor (M.G.L. c. 64H); cross-checked vs
  SalesTaxHandbook Boston page.
- Model: non-SST, **self-seeded flat statewide 6.250%**, effective
  2009-08-01. Massachusetts has **no local sales tax** (municipalities
  may levy a separate 0.75% meals tax, administered separately — not a
  general sales tax and out of scope for the rate engine).
- Last loaded on prod: statewide 6.250% row.
- Latest available: **6.250%** — unchanged since 2009-08-01. No 2026
  legislative change. SalesTaxHandbook confirms Boston combined =
  6.25% (state only; county/city/special = N/A).
- Drift summary: **None.** Engine 6.250% == MA DOR 6.250% across all
  tier-1 cities.
- Recommended action: **None.** Flat constant, current.
- Details:

  | City | Expected (DOR) | Actual (engine) | Delta |
  |---|---|---|---|
  | Boston 02108 | 6.250% | 6.250% | 0.000% |
  | Boston 02110 | 6.250% | 6.250% | 0.000% |
  | Worcester 01608 | 6.250% | 6.250% | 0.000% |
  | Springfield 01103 | 6.250% | 6.250% | 0.000% |

## Method notes
- Live engine probed at `https://api.opensalestax.org/v1/calculate`
  with a browser User-Agent (Cloudflare 403s bare python-urllib) and
  the canonical `{"address":{"zip5","zip4"},"line_items":[{"amount"}]}`
  payload.
- Both states are self-seeded flat-rate modules (no SST quarterly file
  to compare against), so this audit reduces to (1) confirm the
  statewide constant against the DOR headline rate and (2) confirm the
  live engine returns that constant for the pinned tier-1 cities. Both
  checks passed clean.
- No commits, no chips, no findings, no handoff open-follow-ups added
  (per the task's "update handoff only if drift was found").
