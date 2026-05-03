# Research — Sovos state-by-state summary

> Per-state nexus, marketplace, and filing-frequency reference compiled
> from Sovos's public "State-by-State Guide to Sales Tax." Used here as
> a **cross-reference for sanity-checking**, not as an ingestible data
> source.

## Source + provenance

- **Origin URL:** https://sovos.com/content-library/sut/state-by-state-guide-to-sales-tax/
- **Format on origin:** JS-rendered interactive map; underlying data not
  exposed as static HTML or JSON.
- **Captured by:** Eric Osterberg, manually transcribed from the
  rendered page.
- **Captured on:** 2026-05-02.
- **Raw file:** `sovos-state-summary.tsv` in this directory (TSV with
  multi-line cells; preserved as-fetched).
- **Coverage:** 50 states + DC. **Puerto Rico is not included** — the
  project's `state-coverage.md` lists PR as Tier B; another source
  (e.g., Hacienda) will be needed for it.

## Usage policy — read before using

**This data must NOT be ingested into OpenSalesTax as a runtime data
source.** Per [`constitution.md`](../constitution.md) §3, acceptable
data sources are limited to SST quarterly files, state DOR public
publications, US Census, and OpenStreetMap. Sovos is explicitly
listed as a **non-acceptable** source — it's a paid commercial
service whose content is proprietary.

What this file IS for:

- **Sanity-checking** state base rates and economic-nexus thresholds
  during Phase 1 + Phase 2 implementation. If our SST parser yields
  Minnesota = 7.875%, this doc says 6.875% — investigate the
  discrepancy.
- **Identifying state-specific quirks** (HI GET, NM GRT, AZ TPT, AK
  ARSSTC commission, NJ Jersey Gardens, NY MTA surcharge, PA
  Allegheny/Philadelphia, CO home-rule, LA parishes) that the
  per-state modules will need to handle.
- **Test-fixture ideas** — the nexus thresholds + filing
  frequencies are useful for designing eventual `nexus_rules` and
  filing-frequency reference tables.

What this file is NOT for:

- Direct ingestion by any state-module parser.
- Bundling into the Docker image or distributing as
  OpenSalesTax data.
- Publishing in API responses.

## Data-quality defects in the source

The raw transcription has visible defects from Sovos's own page.
**Fix or work around these before relying on any specific cell.**

| # | Location | Defect |
|---|---|---|
| 1 | Header for PA | Spelled "Pennsylvani" (missing trailing 'a') |
| 2 | AL marketplace cell | Says "must collect **Wyoming** sales tax" — Wyoming text pasted into Alabama row |
| 3 | CT filing-threshold cell | Says "Quarterly when sales tax liability is less between $15 and $600 per month" — verbatim Colorado language, not Connecticut's |
| 4 | DE filing-frequency cell | Says "Monthly when sales tax liability is greater than $600 per month" — contradicts DE having no sales tax |
| 5 | ME sales-tax-holiday cell | "Tax-free three-day weekend every February… Energy Star Product…" — that's Maryland's Shop Maryland Energy weekend, not Maine's |
| 6 | HI, MO, MS, SD, TN rows | Multi-line cells leak across the next state's header, so naive TSV parsing assigns data to the wrong state. Read with awareness of this. |
| 7 | Several filing-frequency cells | Mix of "tax due per month," "annual tax due," and "monthly liability" wording — not normalized; some thresholds appear inconsistent within their own row (e.g., KY shows two overlapping "Monthly" tiers) |

## Quick-reference table

State base rate, local-jurisdiction independence, economic-nexus
threshold, and SST membership. Pulled from the raw TSV with the
defects above corrected against general knowledge where possible.
**Verify against the official state DOR before treating any cell as
authoritative.**

| State | Base rate | Indep. local nexus | Economic nexus threshold | SST member |
|---|---:|:---:|---|:---:|
| AK | none | Yes | $100k via ARSSTC (no txn count as of 2025-01-01) | No |
| AL | 4.000% | Yes | $250k | No |
| AR | 6.500% | No | $100k OR 200 txn | Yes |
| AZ | 5.600% | No (Indian res. independent) | $100k | No |
| CA | 7.250% | No | $500k | No |
| CO | 2.900% | Yes | $100k | No |
| CT | 6.350% | Yes (Mashantucket Pequot 1%) | $100k AND 200 txn (12-mo ending 9/30) | No |
| DC | 6.000% | n/a | $100k OR 200 txn | No |
| DE | none | n/a | n/a | No |
| FL | 6.000% | No (1% in Panama City + PCB) | $100k | No |
| GA | 4.000% | No | $100k OR 200 txn | Yes |
| HI | 4.000% (GET) | No | $100k OR 200 txn | No |
| IA | 6.000% | No | $100k | Yes |
| ID | 6.000% | Yes | $100k | No |
| IL | 6.250% | No | $100k (eff. 2026-01-01) | No |
| IN | 7.000% | No | $100k | Yes |
| KS | 6.500% | No | $100k | Yes |
| KY | 6.000% | No | $100k OR 200 txn | Yes |
| LA | 5.000% | Yes | $100k OR 200 txn | No |
| MA | 6.250% | No | $100k | No |
| MD | 6.000% | No | $100k OR 200 txn | No |
| ME | 5.500% | No | $100k | No |
| MI | 6.000% | No | $100k OR 200 txn | Yes |
| MN | 6.875% | No | $100k OR 200 txn (12-mo) | Yes |
| MO | 4.225% | No | $100k (12-mo) | No |
| MS | 7.000% | No | $250k (12-mo) | No |
| MT | none | n/a | n/a | No |
| NC | 4.750% | No | $100k | Yes |
| ND | 5.000% | No | $100k | Yes |
| NE | 5.500% | No | $100k OR 200 txn | Yes |
| NH | none | n/a | n/a | No |
| NJ | 6.625% | Yes (Jersey Gardens District) | $100k OR 200 txn | Yes |
| NM | 4.875% (GRT) | No | $100k | No |
| NV | 6.850% | No | $100k OR 200 txn | Yes |
| NY | 4.000% | No | $500k AND >100 txn (4 prior quarters) | No |
| OH | 5.750% | No | $100k OR 200 txn | Yes |
| OK | 4.500% | No | $100k seller / $10k marketplace | Yes |
| OR | none | n/a | none enacted | No |
| PA | 6.000% | No | $100k | No |
| RI | 7.000% | No | $100k OR 200 txn | Yes |
| SC | 6.000% | No | $100k | No |
| SD | 4.200% | No | $100k | Yes |
| TN | 7.000% | No | $100k (12-mo) | Yes (associate) |
| TX | 6.250% | No | $500k (12-mo) | No |
| UT | 4.850% | No (Navajo Nation independent) | $100k | Yes |
| VA | 4.300% | Yes | $100k OR 200 txn | No |
| VT | 6.000% | No | $100k OR 200 txn (12-mo) | Yes |
| WA | 6.500% | No | $100k | Yes |
| WI | 5.000% | No | $100k | Yes |
| WV | 6.000% | No | $100k OR 200 txn | Yes |
| WY | 4.000% | No | $100k | Yes |

**Counts:** 5 no-tax states (AK, DE, MT, NH, OR), 24 SST members
(23 full + TN associate) — matches `state-coverage.md`. PR not
covered by Sovos.

## State-specific quirks worth flagging up-front

Pulled from the longer-form cells in the raw TSV. These are
already on the radar via `state-coverage.md`, but Sovos's
treatment confirms them:

- **AK** — no state tax, but the [Alaska Remote Seller Sales Tax
  Commission](https://arsstc.org) administers a unified collection
  scheme for participating localities at a $100k threshold (200-txn
  count was removed 2025-01-01).
- **AL** — local jurisdictions have **independent** nexus; rates
  change monthly. State publishes; locals self-administer.
- **AZ** — Transaction Privilege Tax, not a true sales tax.
  Indian reservations have independent nexus.
- **CA** — district taxes layer on top of the 7.25% base; nexus
  threshold is $500k (higher than most).
- **CO** — independent local nexus; the home-rule city problem
  flagged in `state-coverage.md`.
- **CT** — only one local jurisdiction (Mashantucket Pequot Tribal
  Nation, 1%).
- **HI** — GET (Gross Excise Tax), not sales tax. Counties may add
  a surcharge up to 0.5% (Honolulu, Kauai, Hawaii County have it;
  Maui added it 2024-01-01). Pass-through max 4.7120%.
- **LA** — independent parish-level nexus; each parish
  self-administers.
- **NJ** — Jersey Gardens District has independent nexus (Urban
  Enterprise Zone reduced rate).
- **NM** — Gross Receipts Tax, not sales tax. Navajo Nation has
  separate filing.
- **NV** — Good Life Districts can change the state rate to 2.75%.
- **NY** — MTA surcharge (0.375%) in NYC + 7 counties; ~57
  counties + ~18 cities impose local tax.
- **OK** — marketplace nexus threshold ($10k) is dramatically
  lower than seller threshold ($100k) — easy to misread.
- **PA** — Allegheny County and City of Philadelphia have
  surtaxes; otherwise statewide single rate.
- **TX** — origin-based sourcing for in-state sellers (per
  `state-coverage.md`); $500k nexus.
- **UT** — Navajo Nation has independent nexus on the Utah
  portion.

## Possible follow-ups (not committing to these)

If a cleaner, machine-readable cross-reference becomes useful:

1. **Sales Tax Institute** publishes a similar state-by-state
   table at https://www.salestaxinstitute.com/resources/rates as
   static HTML — easier to scrape, similar coverage.
2. **TaxJar's free state guides** at
   https://www.taxjar.com/sales-tax/<state> are also static and
   often more current. Same usage caveat: reference, not
   ingestion.
3. **Each state's DOR economic-nexus FAQ page** is the
   authoritative source for that state's threshold; build a
   per-state link list in `data-sources.md` over time.

These would replace the Sovos doc as the cross-reference if/when
Sovos's content drifts or this snapshot becomes stale.
