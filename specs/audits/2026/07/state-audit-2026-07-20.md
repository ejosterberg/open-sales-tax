# Daily state sales tax audit — 2026-07-20 (day 20: PA + PR)

## TL;DR
- 2 jurisdictions audited (both non-SST, both self-seeded). **0 combined-rate
  changes found, 0 requiring code/test updates.** Both engines match their
  authoritative rates exactly across every tier-1 city.
- **PA:** fully clean. State 6% / Allegheny (Pittsburgh) 7% / Philadelphia 8%,
  all 65 other counties 6% — unchanged for 2026, engine matches all 14 seeded
  cities.
- **PR:** combined IVU rate fully clean (uniform 11.5% at every address,
  unchanged since 2015). One **non-drift accuracy/documentation gap** surfaced:
  the engine models `prepared_food` at the full 11.5% and does not represent
  Puerto Rico's **merchant-certification-gated reduced 7% IVU on prepared foods**
  (Act 257-2018 / DA 19-03, eff. 2019-10-01). Documented + chipped for human
  review; NOT auto-changed (it needs an engine feature, and the default-case
  11.5% the engine returns is defensible). See
  `specs/findings/pr-prepared-food-reduced-7pct-2026-07.md`.

## PA (Pennsylvania) — non-SST, self-seeded (`pa_data.py`)
- **Source:** PA DOR rate schedule
  (https://www.pa.gov/agencies/revenue/resources/tax-rates); 72 P.S. §7202(a)/(b).
  Cross-checked vs Avalara / SalesTaxHandbook 2026 PA rate pages.
- **Last loaded on prod:** self-seeded from `pa_data.py` (no SST file; PA is not
  an SST member). Module last touched at build (2026-05-04); no changes needed.
- **Latest available:** 6% state; Allegheny County +1% (RAD levy, 1994);
  Philadelphia City/County +2% (raised 1%→2% eff. 2009-10-08). **No 2026 change.**
- **Drift summary:** none. Every seeded city matches the live engine and the DOR
  structure.
- **Recommended action:** none.
- **Details (live engine @ api.opensalestax.org/v1/calculate, 2026-07-20):**

  | City | County | Expected (DOR) | Actual (engine) | Delta |
  |---|---|---|---|---|
  | Philadelphia (19102) | Philadelphia | 8.000 | 8.000 | 0 |
  | Pittsburgh (15222) | Allegheny | 7.000 | 7.000 | 0 |
  | Allentown (18101) | Lehigh | 6.000 | 6.000 | 0 |
  | Erie (16501) | Erie | 6.000 | 6.000 | 0 |
  | Reading (19601) | Berks | 6.000 | 6.000 | 0 |
  | Scranton (18503) | Lackawanna | 6.000 | 6.000 | 0 |
  | Lancaster (17602) | Lancaster | 6.000 | 6.000 | 0 |
  | Harrisburg (17101) | Dauphin | 6.000 | 6.000 | 0 |
  | York (17401) | York | 6.000 | 6.000 | 0 |
  | Bethlehem (18015) | Northampton | 6.000 | 6.000 | 0 |
  | State College (16801) | Centre | 6.000 | 6.000 | 0 |
  | Wilkes-Barre (18701) | Luzerne | 6.000 | 6.000 | 0 |
  | Chester (19013) | Delaware | 6.000 | 6.000 | 0 |
  | Norristown (19401) | Montgomery | 6.000 | 6.000 | 0 |

- **Note on coverage (not drift):** PA authorizes local sales tax in only two
  places (Allegheny 1%, Philadelphia 2%). The module docstring already flags a
  future ratchet to add Allegheny-County *suburban* ZIPs beyond Pittsburgh proper
  (Monroeville, Bethel Park, McKeesport, etc.) so they pick up the +1%. That's a
  coverage-expansion item, not a rate change — left as-is.

## PR (Puerto Rico) — non-SST US territory, self-seeded (`puerto_rico.py`)
- **Source:** Departamento de Hacienda de Puerto Rico (https://hacienda.pr.gov/);
  13 L.P.R.A. §§32021 (state 10.5%) + 32024 (municipal 1.0%). Cross-checked vs
  Avalara / Kintsugi / DAVO 2026 PR rate pages.
- **Last loaded on prod:** self-seeded from `puerto_rico.py` (no SST file; PR is a
  US territory, not an SST member). Two-row encoding (10.5% state + 1.0% municipal
  SUT) → 11.5% combined.
- **Latest available:** 11.5% combined, uniform across all 78 municipios, in
  effect since 2015-07-01 (Act No. 72 of 2015). **No 2026 change.**
- **Drift summary:** none on the combined rate.
- **Recommended action:** none for the combined rate. Low-priority accuracy gap
  chipped separately (see below).
- **Details (live engine, 2026-07-20):**

  | Municipio | ZIP | Expected (Hacienda) | Actual (engine) | Delta |
  |---|---|---|---|---|
  | San Juan | 00901 | 11.500 | 11.500 | 0 |
  | Ponce | 00731 | 11.500 | 11.500 | 0 |
  | Bayamón | 00956 | 11.500 | 11.500 | 0 |
  | Carolina | 00979 | 11.500 | 11.500 | 0 |
  | Mayagüez | 00680 | 11.500 | 11.500 | 0 |
  | Caguas | 00725 | 11.500 | 11.500 | 0 |

  Each returns two jurisdictions (Puerto Rico 10.500 + Puerto Rico Municipal SUT
  1.000), exactly matching the v0.32 two-row encoding.

### Non-drift finding: prepared-food reduced 7% rate not modeled
Puerto Rico grants a **reduced 7% IVU on prepared foods** (restaurant/food-truck
prepared meals, pastry, candy, carbonated beverages) sold by **certified**
merchants — the 4.5% state surcharge is waived, dropping 11.5% → 7%. Enacted by
**Act 257-2018** amending §4210.01 of the PR Internal Revenue Code of 2011,
implemented by **Administrative Determination DA 19-03** (2019-08-02), effective
**2019-10-01**. It is **certification-gated**: only merchants holding the SC 2995
"Authorized Business – Reduced SUT Rate on Prepared Foods" certificate (current
IVU filings, IVU terminal at every POS) may charge it; alcohol is excluded.

The `puerto_rico.py` module models `prepared_food` as **taxable at the full
11.5%** and its docstring does not mention the 7% reduced rate at all. Because the
reduced rate is merchant-certification-gated, returning the ordinary 11.5% for a
generic (uncertified) transaction is defensible as the *default* — but the model
is incomplete for the common certified-restaurant case, and the docstring is
silent on the mechanism. This is **not rate drift** and was **not auto-changed**
(it needs an engine feature to represent a category-level, merchant-gated reduced
rate). Written up + chipped for Eric's review:
`specs/findings/pr-prepared-food-reduced-7pct-2026-07.md`.

## Actions taken this run
- Report-only. **No code or test changes** (no combined-rate drift in either
  jurisdiction).
- 1 background chip: model/document the PR prepared-food reduced 7% rate
  (low priority, human review).
- Neither jurisdiction is SST → no quarterly-file refresh applies.

## Sources
- PA DOR tax rates: https://www.pa.gov/agencies/revenue/resources/tax-rates
- PA rates cross-check: https://www.avalara.com/taxrates/en/state-rates/pennsylvania.html
- PR Hacienda: https://hacienda.pr.gov/
- PR rate cross-check: https://www.avalara.com/taxrates/en/state-rates/puerto-rico.html
- PR prepared-food 7% (DA 19-03 / Act 257-2018):
  https://www.rsm.global/puertorico/insights/tax-alerts/prepared-foods-now-subject-reduced-tax-and-use-rate-7
  and https://hacienda.pr.gov/certificado-de-tasa-reducida-de-7-del-ivu-en-alimentos-preparados-0
