# WI state tax audit -- 2026-11-01 (full-sweep)

## TL;DR

- **WI is 2 quarters stale on prod** (`WIR2026Q2FEB18` / `WIB2026Q2FEB18`);
  latest upstream is **`WIR2026Q4AUG17.csv` / `WIB2026Q4AUG17.zip`**.
- **No live rate drift.** Milwaukee 53202 live-probed **7.90000%** -- state
  5% + Milwaukee County 0.9% + Milwaukee city 2% (per Act 12) -- matches
  the existing pin exactly.
- WI DOR *Sales Tax Rate Chart* page (Guidance Document 100047, dated
  2026-01-16): **69 counties at 0.50%**; Milwaukee 0.90% (eff 1/24);
  Milwaukee city 2% (eff 1/24); Waukesha (67) and Winnebago (70) show no
  county tax. **No county changes in 2026** -- latest additions remain
  Manitowoc (1/25) and Racine (4/25).
- WI's county levy is a flat 0.5% statewide (plus Milwaukee's 0.9%),
  which **cannot produce a wrong rate** for an already-bound ZIP, so the
  stale boundary carries only cosmetic/binding-only risk, not rate risk.
- **Status: UNCHANGED** -- WI remained fully clean since the 2026-08-25
  audit; no new changes to apply.

## Prod state (read-only)

| Source | Label | Fetched |
|---|---|---|
| sst | `WI-SST-2026Q2FEB18` | 2026-05-15 |
| zcta-census-2020 | `WI-ZCTA-2020` | 2026-05-11 |

## Upstream (SST Governing Board, 2026-11-01)

- Rate: `WIR2026Q4AUG17.csv`
- Boundary: `WIB2026Q4AUG17.zip`

## WI DOR primary-source check (2026-11-01)

- `revenue.wi.gov/Pages/FAQS/pcs-taxrates.aspx` -- Guidance Document
  100047, dated 2026-01-16. 69 counties at 0.5%; no 2026 changes.
- No bulletin for 2026-07-01 or 2026-10-01 county/city changes.

## Live probes

| City | ZIP | Expected (pin) | Actual | Delta |
|---|---|---|---|---|
| Milwaukee | 53202 | 7.900 | 7.900 | 0.00 |
| Madison | 53703 | 5.500 | (pin passes) | 0.00 |
| Green Bay | 54301 | 5.500 | (pin passes) | 0.00 |

## Open follow-ups

- Load `WIR2026Q4AUG17` + `WIB2026Q4AUG17` on prod -- updates boundary
  bindings but will not move any probed-city rate.
- ~1782 WI placeholders remain in `wi_names.py` (mostly Wisconsin Towns);
  the Census County Subdivision gazetteer file (`2024_gaz_cousub_55.txt`)
  is the owed path per handoff "Latest session continuation hooks". Not
  touched in this run.
