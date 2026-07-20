# PR prepared-food reduced 7% IVU not modeled (accuracy/doc gap, not drift)

**Found:** 2026-07-20 daily audit (day 20: PA + PR).
**Status:** Open — chipped for human review. NOT auto-changed. **Not rate drift.**
**Severity:** Low (default-case behavior is defensible; affects an unmodeled
sub-category, not the general combined rate).

## Summary

Puerto Rico's general IVU is 11.5% (10.5% state + 1.0% municipal), and the
OpenSalesTax engine returns that correctly at every PR address. Separately, PR
grants a **reduced 7% IVU rate on prepared foods** sold by **certified**
merchants. The `puerto_rico.py` module models the `prepared_food` category at the
full **11.5%** and its docstring does not mention the 7% reduced rate. This is an
accuracy/documentation gap for the certified-restaurant case, not a drift in the
general rate.

## The reduced rate (primary sources)

- **Statute:** Act 257-2018 ("Puerto Rico Tax Reform of 2018") amending
  **§4210.01** of the Puerto Rico Internal Revenue Code of 2011. It exempts
  prepared foods, carbonated beverages, pastry products, and candy sold by
  qualifying restaurants from the **4.5% state SUT surcharge**, leaving a
  **reduced combined rate of 7%** (vs the ordinary 11.5%).
- **Implementing guidance:** Departamento de Hacienda **Administrative
  Determination DA 19-03** (2019-08-02).
- **Effective:** 2019-10-01.
- **Scope:** "prepared foods" served hot or with eating utensils, by a
  "restaurant" (broadly defined, includes food trucks). **Alcoholic beverages are
  excluded** (stay at 11.5%).
- **Certification-gated:** only merchants holding certificate **SC 2995**
  ("Authorized Business – Reduced SUT Rate on Prepared Foods") may charge 7%.
  Eligibility: current on all IVU filings, no outstanding tax debt, and an IVU
  fiscal terminal installed at every point of sale. Certificate issued through
  SURI.

## Why it was NOT auto-changed

1. **It is not rate drift.** The general/combined IVU rate is 11.5% and the engine
   is exactly correct for it. This is a category-level reduced rate, not a change
   to the headline rate.
2. **The default is defensible.** Because the 7% rate is merchant-certification-
   gated (only certified sellers may charge it, and OST has no notion of the
   seller's certification status), returning the ordinary 11.5% for a generic
   `prepared_food` line is a reasonable conservative default.
3. **It needs an engine feature, not a one-line data edit.** Representing a
   category-level, merchant-gated reduced rate cleanly is a modeling decision
   (e.g. a reduced-rate override on the `prepared_food` taxability rule, possibly
   gated by a request flag indicating the seller is certified). That belongs in
   human-reviewed design, not an autonomous audit commit.

## Recommended options (for Eric / a future session)

- **Minimum (docs):** update the `puerto_rico.py` `prepared_food` docstring to
  document the 7% reduced rate, its certification gate (SC 2995 / DA 19-03), the
  alcohol exclusion, and the rationale for defaulting to 11.5%. Zero behavior
  change; closes the "module is silent on a real rule" gap.
- **Fuller (model):** add an optional reduced-rate representation for
  `prepared_food` (e.g. a `reduced_rate_pct = 7.0` on the taxability rule, applied
  when the caller signals a certified seller). Requires an API-surface decision on
  how a caller expresses seller certification, plus tests. Track as its own phase
  if pursued.

## Verification pointers

- Engine today: `POST /v1/calculate {"address":{"zip5":"00901"},
  "line_items":[{"amount":100,"category":"prepared_food"}]}` → 11.5% (full rate).
- Sources:
  - RSM PR alert: https://www.rsm.global/puertorico/insights/tax-alerts/prepared-foods-now-subject-reduced-tax-and-use-rate-7
  - Hacienda certificate page: https://hacienda.pr.gov/certificado-de-tasa-reducida-de-7-del-ivu-en-alimentos-preparados-0
  - Hacienda DA 19-03: https://hacienda.pr.gov/publicaciones/determinacion-administrativa-num-19-03
