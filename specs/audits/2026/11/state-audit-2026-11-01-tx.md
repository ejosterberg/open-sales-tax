# Daily state sales tax audit — 2026-11-01 (full-sweep, TX)

Part of the multi-agent full-sweep audit run on 2026-11-01, South-Central region
(AR, LA, MS, OK, TX).

## TL;DR

- **No live rate error identified at the dollar level**, but **three
  2026-10-01 TX county changes complicate the local-cap stacking** in
  ways the module should eventually model honestly:
  - **Fayette County 0 → 0.500%** (adopted, eff 2026-10-01).
    `TX_COUNTY_RATE_PCT["Fayette County"]` is still **0.000%**.
    Modeled Fayette cities (**La Grange** 78945, **Schulenburg** 78956)
    carry `city_rate = 2.000%` to produce 8.25% combined; after the
    county adoption, TX Comptroller's own city.php page shows these
    cities now break out as **county 0.5% + city 1.5%** (combined
    still **8.25%**, at the §321.101(f) local cap). **Dollar total
    unchanged**; only the breakdown drifts.
  - **Navarro County 0 → 0.500%** (adopted, eff 2026-10-01).
    `TX_COUNTY_RATE_PCT["Navarro County"]` is still **0.000%**.
    **No modeled city** currently sits in Navarro County, so no
    engine row changes.
  - **McLennan County 0.500 → 0** (abolished, eff 2026-10-01).
    `TX_COUNTY_RATE_PCT["McLennan County"]` is already **0.000%** —
    the module always encoded Waco as `city_rate = 2.000%` (combined
    into city for arithmetic ease, per the Waco `# state 6.25 +
    McLennan 0 + city 2.0` docstring). The abolition brings the
    comptroller's own breakdown into alignment with our model —
    **net zero drift**.
- **No live-rate change is owed on 2026-10-01.** The three county
  moves above are rate-neutral at the dollar level for every ZIP in
  `TX_CITIES` because the engine clamps combined local at TX's 2.0%
  cap by construction.
- **Statewide rate confirmed 6.250%** per Tex. Tax Code §151.051 and
  the TX Comptroller's quarterly updates landing page
  (retrieved 2026-11-01).
- The handoff's two carried items remain open and NOT touched here:
  - **24 TX DOR_GRID rows cite an aggregator** (SalesTaxHandbook /
    Avalara); flagged in the 2026-09-28 audit for re-citation to
    primary TX Comptroller sources. Not done this run.
  - **2 contradictory DOR_GRID pins** on the same TX ZIP+4 (from the
    790-row sweep in `specs/findings/dor-grid-contradictory-
    duplicate-pins-2026-09.md`). Not touched; needs primary-source
    reconciliation.

## Primary sources

- TX Comptroller *Quarterly Updates to Rates and City Annexed Areas*
  (`https://comptroller.texas.gov/taxes/sales/quarterly-updates/`,
  retrieved 2026-11-01):
  - `/2026-oct.php` — 2026-10-01 changes: new adoptions include
    Fayette County 0.5%, Navarro County 0.5%, Beckville, Ellinger,
    Frost, Northlake (Denton), ESD districts; abolitions include
    McLennan County 0.5%, Bellmead, Naples, Morris Co., Orchard
    (Fort Bend), Roscoe (Nolan), Shoreacres (Harris; merging into La
    Porte).
  - `/jul-2026.php` — 2026-07-01 changes: Weston (Collin) 1.5%,
    Taft (San Patricio) abolished, several SPDs. None affect
    modeled `TX_CITIES` entries.
- TX Comptroller city.php (retrieved 2026-11-01, offset 100000)
  cross-checks the modeled dollar totals for Waco (8.25%), La Grange
  (8.25%), Schulenburg (8.25%).

## Modeled-city impact scan (2026-10-01 changes)

- **Fayette County adoption** → affects La Grange 78945, Schulenburg
  78956 (both modeled). Dollar total unchanged (city rate absorbs
  cap). Breakdown drift only.
- **Navarro County adoption** → no modeled city.
- **McLennan County abolition** → affects Waco 76701 (modeled).
  Dollar total unchanged (we already encoded Waco as county 0 +
  city 2.0). Breakdown drift reduced.
- **Northlake, Beckville, Ellinger, Frost, Weston, Taft, Bellmead,
  Naples, Orchard, Roscoe, Shoreacres**: none in `TX_CITIES`. No
  engine change needed.
- **Morris County abolition** (0.5 → 0): `TX_COUNTY_RATE_PCT["Morris
  County"]` is **0.000%** — already consistent (no modeled city in
  Morris anyway).

## Pin edits this run

**None.** No live-rate drift was found at the pinned ZIPs; the three
county moves rearrange breakdowns but preserve the combined local
cap. Updating the Fayette/Navarro county entries to 0.500% without
simultaneously reducing La Grange / Schulenburg city rates to 1.500%
would push combined local above the §321.101(f) 2.0% cap and
introduce a new over-collection — more harm than good. Chipped as
"TX county/city stacking refactor" in follow-ups rather than fixing
blind.

## Status

**UNCHANGED** at the dollar level. Breakdown drift noted and chipped.

## Follow-ups chipped

- **Refactor TX county/city stacking** for Fayette (La Grange,
  Schulenburg), McLennan (Waco), Navarro: bring county entries into
  line with TX Comptroller's own breakdown while simultaneously
  reducing city entries to maintain the 2.0% local cap. This is a
  non-trivial change — needs a test fixture that proves the engine
  honors §321.101(f) and a decision on whether the cap is enforced
  by data or by the engine. Not blocking.
- **Re-cite the 24 aggregator-sourced TX DOR_GRID pins** to primary
  TX Comptroller sources (quarterly-updates PDF rates, or city.php
  values). Carried from 2026-09-28.
- **Reconcile 2 contradictory TX DOR_GRID pins** per
  `specs/findings/dor-grid-contradictory-duplicate-pins-2026-09.md`.
  Carried.
- TX Comptroller does not publish an "effective-dated" city.php — a
  future ratchet should pin a quarterly snapshot of city.php to the
  release and diff successive snapshots. (TX Comptroller publishes
  `city_rates.xlsx` under city.php — periodic snapshot is the
  cleanest approach.)
