# Daily state sales tax audit — 2026-07-17 (day 17: NM + NV)

## TL;DR
- 2 jurisdictions audited. **1 rate change relevant to existing coverage**
  (NM Town of Bernalillo, July 1 2026 GRT change) — **flagged for human
  review, not auto-committed**, because the correct new rate is ambiguous
  across three sources. **0 trivial fixes committed.**
- **NV is fully current** — prod's SST files are the latest SST publishes,
  and both tier-1 cities match the live engine.
- NM's other 28 modeled cities are unaffected by the July-1-2026 change set
  and all match the live engine.

## NM (New Mexico) — non-SST, self-seeded module `nm_data.py`
- Source: NM TRD Gross Receipts Tax rate schedule.
  - Overview: https://www.tax.newmexico.gov/all-nm-taxes/current-historic-tax-rates-overview/gross-receipts-tax-rates/
  - July-1-2026 change summary (secondary): https://blog.usgeocoder.com/2026-new-mexico-sales-tax-rate-changes/
  - Bloomberg Tax (July-1-2026 GRT code/rate update, secondary)
- Last loaded on prod: engine data matches repo `nm_data.py`, which is
  sourced from the **NM TRD GRT schedule effective Jan 1, 2026** (built
  2026-05-04, re-verified iter-172..175).
- Latest available: **NM TRD GRT schedule effective July 1, 2026 –
  Dec 31, 2026** is now in effect (today is 2026-07-17). NM updates GRT
  rates twice a year (Jan 1 and Jul 1); the module is one half-year behind.
- Drift summary: The July-1-2026 change set is small and touches only
  **one modeled jurisdiction — the Town of Bernalillo (Sandoval County,
  ZIP 87004)**. The other July-1-2026 changes (Los Ranchos de Albuquerque,
  Elephant Butte, Los Alamos County, Colfax County) are **not modeled** by
  the engine, so they are coverage-expansion candidates, not drift in
  existing coverage. All 28 other modeled NM cities are unaffected and
  match the engine exactly.
- Recommended action: **Investigate + human-review the Bernalillo rate**
  (finding written, chipped). Do NOT auto-commit — three sources disagree
  on the current rate (see finding). The engine's non-Bernalillo NM
  coverage is correct as of the audit.
- Details (live engine vs module, all internally consistent — engine
  matches repo; "July-1-2026?" column flags jurisdictions in the change set):

  | City | ZIP | Engine rate_pct | In Jul-1-2026 change set? |
  |------|-----|-----------------|---------------------------|
  | Albuquerque | 87102 | 7.62500 | no |
  | Santa Fe | 87501 | 8.18750 | no |
  | Las Cruces | 88001 | 8.39000 | no |
  | Rio Rancho | 87124 | 7.87500 | no |
  | Roswell | 88201 | 8.27080 | no |
  | Farmington | 87401 | 8.18750 | no |
  | Hobbs | 88240 | 6.56250 | no |
  | Carlsbad | 88220 | 7.39580 | no |
  | Clovis | 88101 | 7.93750 | no |
  | Alamogordo | 88310 | 8.18750 | no |
  | Gallup | 87301 | 8.56250 | no |
  | Los Lunas | 87031 | 8.42500 | no |
  | Sunland Park | 88063 | 8.19000 | no |
  | Las Vegas NM | 87701 | 8.14580 | no |
  | Deming | 88030 | 8.25000 | no |
  | Lovington | 88260 | 7.00000 | no |
  | Portales | 88130 | 8.55000 | no |
  | Artesia | 88210 | 7.64580 | no |
  | **Bernalillo (Town)** | **87004** | **7.43750** | **YES — see finding** |

## NV (Nevada) — SST full member
- Source: SST Governing Board state rate/boundary files
  (https://www.streamlinedsalestax.org/ratesandboundry/Rates/); NV DOR
  https://tax.nv.gov/tax-types/sales-tax-use-tax/
- Last loaded on prod: **`NVR2025Q4NOV05` / `NVB2025Q4NOV05`** (Q4 2025,
  posted 2025-11-05).
- Latest available: **`NVR2025Q4NOV05`** — confirmed as the most recent NV
  file SST currently publishes (SST rates directory listing + independent
  web search both show Q4-2025-Nov-05 as newest; no Q3-2026 NV file exists
  because NV county rates have not changed). **Prod is current.**
- Drift summary: **None.** Both tier-1 cities match exactly.
- Recommended action: **No action.** File currency is up to date and rates
  match. Nevada's county-option rates are stable; the Q4-2025 file remains
  the authoritative current publication.
- Details:

  | City | ZIP | Expected (NV DOR combined) | Actual (engine) | Delta |
  |------|-----|----------------------------|-----------------|-------|
  | Las Vegas (Clark Co) | 89101 | 8.375% | 8.37500 | 0 |
  | Reno (Washoe Co) | 89501 | 8.265% | 8.26500 | 0 |
  | Henderson (Clark Co) | 89015 | 8.375% | 8.37500 | 0 |
  | Carson City | 89701 | 7.60% | 7.60000 | 0 |
  | Elko (Elko Co) | 89801 | 7.10% | 7.10000 | 0 |
  | Fallon (Churchill Co) | 89406 | 7.60% | 7.60000 | 0 |

## Actions taken
1. Finding written: `specs/findings/nm-bernalillo-rate-change-2026-07.md`
2. Chip spawned for Eric to apply the authoritative July-1-2026 Bernalillo
   rate after confirming it against the official TRD schedule.
3. No code/rate commits (Bernalillo rate ambiguous; every other modeled
   value is correct).
4. `specs/handoff.md` open-follow-ups updated.

## Notes / methodology
- The live engine was cross-checked with a browser User-Agent (the audit
  gotcha: Cloudflare 403s a bare python-urllib UA). Request shape:
  `POST /v1/calculate {"address":{"zip5":...},"line_items":[{"amount":"100.00"}]}`,
  reading `lines[0].rate_pct`.
- Engine internal consistency confirmed: prod's returned rates equal the
  repo's `nm_data.py` values, so any NM drift is a stale-source issue, not
  a deploy lag.
