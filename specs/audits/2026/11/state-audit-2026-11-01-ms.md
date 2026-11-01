# Daily state sales tax audit — 2026-11-01 (full-sweep, MS)

Part of the multi-agent full-sweep audit run on 2026-11-01, South-Central region
(AR, LA, MS, OK, TX).

## TL;DR

- **MS fully clean. No rate change.** The Mississippi general sales tax rate
  is **7.000%** per Miss. Code Ann. §27-65-17 and the current MSDOR Sales &
  Use Tax page (retrieved 2026-11-01).
- Prod carries `MS-SST-V0.31-STATEWIDE` (self-seeded), fetched 2026-05-04.
  Mississippi is self-seeded flat 7% with hand-curated city/county overlays
  (Jackson 1% Special Sales Tax, Tupelo 0.25%); no SST file exists to drift
  against.
- All **10 MS DOR_GRID pins** are consistent with the module.

## Primary source

- MSDOR Sales & Use Tax page
  (`https://www.dor.ms.gov/business/sales-use-tax/sales-tax-rates`,
  retrieved 2026-11-01). Confirms **7%** general rate; no 2026 statewide
  rate change announced. Reduced rates for groceries (5%) and the
  Ackerman "special tourism and parks tax" are category-specific or
  jurisdiction-specific and do not change the general-retail headline.
- 2026 Second Amendment Sales Tax Holiday (late August 2026) is a
  temporary exemption, not a rate change.

## State module

- `src/opensalestax/states/mississippi.py` — unchanged.
- `src/opensalestax/states/ms_data.py` — unchanged (Jackson 1% Special
  Sales Tax, Tupelo 0.25% Water Procurement Facility Tax). Statewide 7%
  via the state authority is the correct fallback for all other
  jurisdictions (per §27-65-241: no county may impose a general-retail
  surcharge).

## Pins

All 10 `MS` rows in `tests/integration/test_sst_dor_validation.py` are
internally consistent with `mississippi.py` + `ms_data.py` (Jackson 8.000%,
Tupelo 7.250%, Hattiesburg 7.000%, Gulfport 7.000%, etc.).

## Status

**UNCHANGED.** No fix needed. No reload owed.

## Follow-ups chipped

- None state-specific. (The project-wide "hotel/tourism per-category
  taxability" ratchet remains the only MS modeling gap; it is noted in
  `mississippi.py`'s own docstring.)
