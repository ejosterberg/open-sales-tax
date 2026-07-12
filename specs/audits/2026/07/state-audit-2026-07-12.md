# Daily state sales tax audit — 2026-07-12 (day 12: MI + MN)

## TL;DR
- 2 states audited (both SST members). **0 rate changes on any tier-1 city.**
- **MI:** fully current — nothing to do. Flat 6% statewide, no local tax; prod
  SST file (`MIR2023Q1DEC22`) is the latest SST publishes (MI's rate is
  constitutionally fixed and its file hasn't changed since 2023).
- **MN:** tier-1 clean (Minneapolis 9.025%, St. Paul 9.875% both match DOR), but
  prod is **one quarter behind** (Q2 vs available Q3 2026). One in-scope general
  local tax change this quarter — **Meeker County 0.5% Transit Sales & Use Tax,
  eff. 2026-07-01** — surfaces only after the Q3 load. **Chipped** a refresh.
  Also surfaced a rural-Meeker cross-county attribution quirk (finding written;
  expected to self-resolve on the Q3 reload).
- **0 code changes.** Documentation only (this report + 1 finding + handoff
  follow-ups).

## MI (Michigan) — SST member

- Source: SST Governing Board state-files index
  (`streamlinedsalestax.org/ratesandboundry/{Rates,Boundary}/`); MCL §205.52(1)
  (flat 6% statewide, constitutionally capped, no general local tax).
- Last loaded on prod: `MIR2023Q1DEC22.csv` / `MIB2023Q1DEC15.csv`
- Latest available: `MIR2023Q1DEC22.csv` / `MIB2023Q1DEC15.csv` — **identical**.
  MI's SST file is not re-issued quarterly because the rate never changes.
- Drift summary: **None.** Every MI address is exactly 6.000%.
- Recommended action: **None** — MI is fully current.
- Details:
  | City | ZIP | Expected (DOR) | Actual (engine) | Delta |
  |------|-----|----------------|-----------------|-------|
  | Detroit | 48226 | 6.000% | 6.000% | 0 |
  | Detroit | 48201 | 6.000% | 6.000% | 0 |
  | Grand Rapids | 49503 | 6.000% | 6.000% | 0 |
  | Warren | 48088 | 6.000% | 6.000% | 0 |

## MN (Minnesota) — SST member

- Source: SST Governing Board index; [MN DOR local-sales-tax
  guides](https://www.revenue.state.mn.us/local-sales-tax-information) (Q3 2026
  Local + Twin Cities rate guides, eff. 7/1/2026–9/30/2026); cross-checked vs
  SalesTaxHandbook / Avalara.
- Last loaded on prod: `MNR2026Q2FEB18.zip` / `MNB2026Q2FEB18.zip` (Q2 2026)
- Latest available: **`MNR2026Q3MAY20.zip` / `MNB2026Q3MAY20.zip`** (Q3 2026,
  posted 2026-05-20, eff. 2026-07-01) → **prod is one quarter behind.**
- Drift summary: **No tier-1 rate drift.** Minneapolis, St. Paul, Rochester, and
  Duluth all match published DOR rates on the live engine. The only in-scope
  change this quarter is a **new general local tax** that isn't on prod yet.
- Recommended action: **REFRESH NEEDED — chipped** "Refresh MN SST quarterly to
  MNR2026Q3MAY20 / MNB2026Q3MAY20." Do it in the same pass as the pending
  iter-220/221 MN/IA/NC district-name reload (handoff open item #1) so the new
  Meeker authority and the corrected friendly names land together. Not
  auto-pulled (SST files are Eric-reviewed per the task rules).
- Details (tier-1 + tier-2 cross-check):
  | City | ZIP | Expected (DOR) | Actual (engine) | Delta |
  |------|-----|----------------|-----------------|-------|
  | Minneapolis | 55401 | 9.025% | 9.025% | 0 |
  | St. Paul | 55101 | 9.875% | 9.875% | 0 |
  | Rochester | 55901 | 8.125% | 8.125% | 0 |
  | Duluth | 55802 | 8.875% | 8.875% | 0 |

### MN Q3 2026 local-tax changes (eff. 2026-07-01)

| Change | In v1 scope? | Handling |
|--------|--------------|----------|
| **Meeker County** 0.5% Transit Sales & Use Tax | **Yes** (general local sales/use tax, Minn. Stat. 297A.993) | Surfaces after Q3 load; friendly name already in `mn_names.py` (code 80054). Covered by the refresh chip. |
| Chisago Lakes Area 3% Lodging Tax | No | Lodging-only excise; not a general retail sales tax. Out of v1 scope. |
| Fairmont 3% Lodging Tax | No | Lodging-only. Out of scope. |
| Waseca 3% Lodging Tax | No | Lodging-only. Out of scope. |

### MN secondary observations (not rate drift)

- **Rural Meeker County cross-county attribution.** Litchfield (55355), Dassel
  (55325), and Grove City (55329) resolve to neighboring counties (McLeod /
  Stearns) with a stale `Anoka County Transportation` label on 55329 — Meeker
  County is absent from their stacks because it had no county tax before
  2026-07-01. Full write-up + root-cause hypothesis + post-reload re-verification
  steps in
  [`specs/findings/mn-meeker-county-zip-attribution-2026-07.md`](../../findings/mn-meeker-county-zip-attribution-2026-07.md).
  **Expected to self-resolve on the Q3 reload** (Meeker's transit authority binds
  + iter-220 names apply). Chipped for post-reload verification; do **not** ship
  an engine change until re-verified.
- **Placeholder city friendly-name gaps** (cosmetic, low priority): Rochester's
  city authority shows as `MN-city-54880` and Duluth's as `MN-city-17000`. Rates
  are correct; only the display name is unresolved. Candidate for a future
  `mn_names.py` friendly-name sweep (weekly-improvement territory), not this
  audit.

## Actions taken

1. Report written (this file).
2. Finding written: `specs/findings/mn-meeker-county-zip-attribution-2026-07.md`.
3. Chip: "Refresh MN SST quarterly to MNR2026Q3MAY20 / MNB2026Q3MAY20"
   (combine with pending iter-220 MN/IA/NC name reload).
4. Chip: "Verify MN Meeker County ZIP attribution after Q3 reload".
5. `handoff.md` open-follow-ups updated.
6. No code changes — MI current, MN rates correct; only data-currency + a
   documentation trail.
