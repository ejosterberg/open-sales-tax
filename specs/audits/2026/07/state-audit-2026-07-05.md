# Daily state sales tax audit — 2026-07-05 (day 5: DE + FL)

## TL;DR
- 2 jurisdictions audited (DE, FL). **2 rate changes found in FL, both
  requiring code + test updates** (Collier and Palm Beach counties).
  DE is a no-sales-tax state — nothing to audit.
- Root cause: both FL values were stale data-entry errors carried from
  the 2026-05-04 module build; the authoritative **CY2026 DR-15DSS
  (R. 11/25)** contradicts them. Prod has been over-collecting for
  Collier (+1.0%) and Palm Beach (+0.5%) since the FL module shipped.
- Fixed in-repo (mechanical rate corrections + 3 test-pin bumps + unit
  test lock-in). Prod data-reload chip filed so the live engine picks
  up the corrected `fl_data.py`.

## DE (Delaware)
- Source: Delaware has **no state or local sales tax** (Del. Code Title
  30). Delaware levies a gross-receipts tax on sellers instead, which is
  not a transaction sales tax and out of scope for this engine.
- Engine state: no `de_*` module exists (correct — nothing to model).
- Drift summary: **None possible.** Any DE address correctly resolves to
  0% sales tax.
- Recommended action: none. (This is the expected steady state for DE;
  it will report "no drift" on every rotation.)

## FL (Florida)
- Source: **FL DOR Form DR-15DSS, "Discretionary Sales Surtax
  Information for Calendar Year 2026" (R. 11/25)** —
  https://floridarevenue.com/Forms_library/current/dr15dss_26.pdf
  (the `/current/dr15dss.pdf` link still serves the CY2025 R.11/24 table;
  the CY2026 table lives at the `_26` suffix).
  Secondary confirmation: Avalara + SalesTaxHandbook per-county pages.
- Engine data: `src/opensalestax/states/fl_data.py`
  (`FL_COUNTY_SURTAX_PCT`, hardcoded — FL is non-SST, no cached quarterly
  file). Module docstring claimed CY2026 sourcing "verified 2026-05-04".
- Drift summary: **2 counties drifted** — Collier (engine 1.0% → should
  be 0%/None) and Palm Beach (engine 1.0% → should be 0.5% eff Jan 1
  2026). The other 12 tier-1 counties matched the CY2026 DR-15DSS
  exactly.
- Recommended action: **corrected in this commit**; prod data reload
  chipped (see below).

### Live-engine probe (all 20 FL tier-1 pins, before fix)
All 20 returned exactly their pinned value — the engine was internally
consistent but two of the pins themselves were stale. Cross-check
against CY2026 DR-15DSS surfaced the two drifts:

| City | ZIP | County | Engine (pre-fix) | CY2026 DR-15DSS | Corrected |
|---|---|---|---|---|---|
| Naples | 34102 | Collier | 7.000 | **6.000** (None) | ✅ 6.000 |
| West Palm Beach | 33401 | Palm Beach | 7.000 | **6.500** (0.5%) | ✅ 6.500 |
| Boca Raton | 33432 | Palm Beach | 7.000 | **6.500** (0.5%) | ✅ 6.500 |
| Miami | 33130 | Miami-Dade | 7.000 | 7.000 (1.0%) | no change |
| Hialeah | 33010 | Miami-Dade | 7.000 | 7.000 (1.0%) | no change |
| Palm Bay | 32905 | Brevard | 7.000 | 7.000 (1.0%)¹ | no change |
| Orlando | 32801 | Orange | 6.500 | 6.500 (0.5%) | no change |
| Tampa | 33602 | Hillsborough | 7.500 | 7.500 (1.5%) | no change |
| Jacksonville | 32202 | Duval | 7.500 | 7.500 (1.5%) | no change |
| St. Petersburg | 33701 | Pinellas | 7.000 | 7.000 (1.0%) | no change |
| Clearwater | 33755 | Pinellas | 7.000 | 7.000 (1.0%) | no change |
| Fort Lauderdale | 33301 | Broward | 7.000 | 7.000 (1.0%) | no change |
| Hollywood | 33020 | Broward | 7.000 | 7.000 (1.0%) | no change |
| Tallahassee | 32301 | Leon | 7.500 | 7.500 (1.5%) | no change |
| Gainesville | 32601 | Alachua | 7.500 | 7.500 (1.5%) | no change |
| Lakeland | 33801 | Polk | 7.000 | 7.000 (1.0%) | no change |
| Cape Coral | 33904 | Lee | 6.500 | 6.500 (0.5%) | no change |
| Miami Beach | 33139 | Miami-Dade | 7.000 | 7.000 (1.0%) | no change |
| Key West | 33040 | Monroe | 7.500 | 7.500 (1.5%) | no change |

¹ Brevard's two 0.5% components both carry a **Dec 31 2026** expiration —
still 1.0% now, but flag for the CY2027 reissue. Same for Charlotte (1%,
exp. Dec 31 2026), which is not a tier-1 pin.

### Details of the two corrections

**Collier County — 1.000% → 0.000%.**
The engine had `"Collier County": Decimal("1.000")` mislabeled "School
Capital Outlay". Collier's actual 1% surtax was a *Local Government
Infrastructure* surtax (effective Jan 1 2019, 7-year term with a $490M
collection cap). It reached its cap and **terminated early**; the
DR-15DSS has listed Collier as "None" for both CY2025 and CY2026.
SalesTaxHandbook confirms "Collier County Has No County-Level Sales
Tax" and Naples = 6%. All Collier ZIPs (Naples, Marco Island, Immokalee)
now correctly resolve to **6.0%**.

**Palm Beach County — 1.000% → 0.500%.**
The engine had `"Palm Beach County": Decimal("1.000")` ("1% Infrastructure").
That 1% infrastructure surtax ran ~2016–2025 and **ended**; a new **0.5%**
surtax took effect **Jan 1 2026** (runs through Dec 31 2035) per the
CY2026 DR-15DSS. Avalara confirms Palm Beach 2026 combined = 6.5%. All
Palm Beach ZIPs (West Palm Beach, Boca Raton, Boynton Beach, Delray
Beach, Jupiter, Palm Beach Gardens, etc.) now correctly resolve to
**6.5%**.

### Changes made in this run
- `src/opensalestax/states/fl_data.py`: Collier 1.000 → 0.000; Palm Beach
  1.000 → 0.500; docstring re-verification note + notable-situations list
  updated.
- `tests/integration/test_sst_dor_validation.py`: Naples 34102 pin
  7.000 → 6.000; West Palm Beach 33401 pin 7.000 → 6.500; Boca Raton
  33432 pin 7.000 → 6.500.
- `tests/unit/test_state_florida.py`: added Collier (0.000) + Palm Beach
  (0.500) to the well-known-county parametrized lock-in test.

### Follow-up (chipped)
- **Prod data reload for FL.** The corrected `fl_data.py` must be
  hot-deployed and the FL loader re-run on `opensalestax-01` so
  `tax_authorities` reflects Collier 0% / Palm Beach 0.5%. Until then the
  *live* engine keeps returning the old (over-collecting) rates even
  though the repo + CI are correct. Chip filed.
