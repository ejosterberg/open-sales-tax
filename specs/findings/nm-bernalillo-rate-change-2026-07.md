# NM Town of Bernalillo — July 1 2026 GRT rate change (ambiguous, needs human review)

**Status:** OPEN — flagged by the daily state-tax audit 2026-07-17 (day 17,
NM+NV). **No engine change was made.** The correct new rate must be confirmed
against the authoritative NM TRD July-1-2026 GRT schedule before touching the
module.

## What triggered this

NM updates Gross Receipts Tax (GRT) rates twice a year (Jan 1 and Jul 1). The
engine's `nm_data.py` is sourced from the **Jan 1, 2026** TRD schedule. The
**July 1, 2026** schedule is now in effect (audit ran 2026-07-17).

The July-1-2026 change set (per usgeocoder + Bloomberg Tax) is small:

- **Cities:** Los Ranchos de Albuquerque, **Bernalillo**, Elephant Butte
- **Counties:** Colfax, Los Alamos (Los Alamos County +0.625% → county
  combined 7.0625% → 7.6875%)

Of these, the engine models **only the Town of Bernalillo** (ZIP 87004,
Sandoval County, module key `"Bernalillo"`). The others are not modeled
(coverage-expansion candidates, tracked separately — see "Not-modeled" below).

## The ambiguity (why this is not an auto-commit)

Three sources give three different current Bernalillo combined rates, and even
the location code is inconsistent:

| Source | Combined rate | City portion | Location code | Period |
|--------|--------------:|-------------:|---------------|--------|
| Engine / `nm_data.py` (current) | **7.4375%** | 2.5625% | `29-119` | Jan 1 2026 (per module comment) |
| salestaxstates / search hit | 6.9375% | — | `29-120` | Jul 1 2025 – Jun 30 2026 |
| Avalara (Bernalillo city page) | 7.1875% | 2.3125% | — | "minimum combined 2026" |

Complications to resolve during review:
1. **Location code 29-119 vs 29-120.** The module comment cites `29-119`; a
   search hit cites the Town of Bernalillo as `29-120`. NM assigns distinct
   location codes to city-limits vs county-remainder areas that share a ZIP —
   picking the wrong code yields the wrong rate. (Also note the classic NM
   foot-gun: the *Town of Bernalillo* is in **Sandoval County**, not
   Bernalillo County.)
2. **Avalara "minimum combined"** is often the lowest overlay for a
   multi-code ZIP, not necessarily the town-proper rate — treat as a
   lower bound, not the answer.
3. The module's 7.4375% was itself set in iter-175 (2026-05) from
   SalesTaxHandbook and flagged as a "-0.5% rate cut"; it may already have
   been slightly off before the July-1-2026 change compounded it.

## How to resolve (for the human/next session)

1. Pull the **authoritative NM TRD GRT Rate Schedule effective
   July 1 2026 – Dec 31 2026** (the official PDF/CSV, not a third-party
   calculator). Entry point:
   https://www.tax.newmexico.gov/all-nm-taxes/current-historic-tax-rates-overview/gross-receipts-tax-rates/
   (the schedule is also mirrored in county PDFs, e.g. Sandoval County's
   published GRT schedule).
2. Find the **Town of Bernalillo** row (confirm the correct location code
   for city-limits). Record the combined rate and its city portion.
3. Update `src/opensalestax/states/nm_data.py` `"Bernalillo"` entry:
   set the `Decimal(...)` city-portion so `4.875 + portion == published
   combined`, and update the inline comment (loc code + combined rate +
   "iter-NNN: July 1 2026 refresh from 7.4375%").
4. If a tier-1/tier-2 test pin exists for 87004, bump it; otherwise consider
   adding one to `tests/integration/test_sst_dor_validation.py`.
5. Full quality gate + SonarQube + CI-green before pushing (per the
   mandatory pre-push gate).

## Not-modeled July-1-2026 changes (coverage-expansion candidates, NOT drift)

These changed on Jul 1 2026 but the engine does not currently model them, so
they are not returning a *wrong* rate for a modeled city — they're simply
absent. Candidates for a future NM expansion ratchet:

- **Los Ranchos de Albuquerque** (Bernalillo County village; ZIP overlaps ABQ
  87107/87113 — would need sub-ZIP precision, low priority).
- **Elephant Butte** (Sierra County; distinct from the modeled *Truth or
  Consequences* 87901, which is a separate municipality and unaffected).
- **Los Alamos County** (+0.625% → 7.6875%; White Rock / Los Alamos townsite,
  ZIPs 87544/87547 — not modeled).
- **Colfax County** cities (Raton 87740, Springer, Angel Fire — not modeled).

## Impact assessment

- **Low immediate impact.** Only one modeled ZIP (87004) is affected, and the
  three candidate rates differ by ≤0.5%. Every other modeled NM city matches
  the engine and is unaffected by the July-1-2026 change set.
- Because this is a source-currency issue (not a deploy lag), the engine and
  repo agree; fixing the module + a prod redeploy is all that's needed once
  the authoritative rate is confirmed.
