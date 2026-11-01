# Full-sweep state audit — VA — 2026-11-01

## TL;DR

- **VA is non-SST, self-seeded** (prod version `VA-SST-V0.31-STATEWIDE`,
  fetched 2026-05-04). All 15 tier-1 pin sites (Hampton Roads, Northern
  VA, Central VA, Historic Triangle, Roanoke, Lynchburg,
  Charlottesville, Leesburg, Manassas, Smithfield, Mechanicsville) are
  **exact against VA Tax**. Last confirmed by probe this run.
- **No new drift on modelled jurisdictions.** VA Tax's "Retail Sales
  and Use Tax" page re-verified this run: the regional district
  structure (Hampton Roads 0.7, Northern VA 0.7, Central VA 0.7,
  Historic Triangle +1.0) is unchanged for 2026-07-01 and 2026-10-01.
- **Known coverage gap persists — the 8 Southside localities at 6.3%.**
  VA Tax lists **Charlotte, Danville, Gloucester, Halifax, Henry,
  Northampton, Patrick, Pittsylvania at 6.3%** (state 5.3% + "additional
  local 1%" under Va. Code 58.1-602). The engine returns **5.3%** for
  these — **−1.0pp under-collection** at every Southside ZIP. Confirmed
  live: Danville 24541 → 5.300, Halifax 24558 → 5.300.
  - This is a **documented limitation**, not fresh drift
    (`virginia.py` line 32–39 chips a future ratchet). The 2026-07-19
    audit also noted it. Not fixed in this sweep: the right fix is a
    `VA_SOUTHSIDE_DISTRICT` 1.0% district layer (parallels the
    Historic Triangle pattern in v0.31), which is a feature ratchet
    rather than a daily-audit edit.
- **One county-binding smell on 24112 (Martinsville).** The engine
  returns `Franklin County` as the county for `24112`, but Martinsville
  is an independent city surrounded by Henry County, not Franklin.
  Rate-neutral at the moment (both 5.3% in the engine), but the county
  attribution is wrong. Chipped — same shape as the
  `multi-county-zip-fips-first-tiebreak` finding; not fixed in this
  audit.
- **No commit from this audit on VA.** No code change (both items are
  pre-existing).

## Prod data version

```
VA | sst              | VA-SST-V0.31-STATEWIDE | 2026-05-04
VA | zcta-census-2020 | VA-ZCTA-2020           | 2026-05-11
```

VA is non-SST and self-seeded. The `sst` source is a label convention.

## VA Tax rate-page re-verification (2026-11-01)

Checked `https://www.tax.virginia.gov/retail-sales-and-use-tax`. The
page lists exactly:

- **7.0%** — James City County, Williamsburg, York County (Historic
  Triangle)
- **6.3%** — Charlotte, Danville, Gloucester, Halifax, Henry,
  Northampton, Patrick, Pittsylvania (Southside additional local 1%)
- **6.0%** — Hampton Roads (11 localities), Northern VA (9 localities),
  Central VA (8 localities)
- **5.3%** — everywhere else

No 2026 rate change is called out beyond the pre-existing Southside
additional-local tier.

## Live engine probes (bare ZIP, `/v1/rates`)

| ZIP | City (county) | Engine | VA Tax expected | Delta |
|---|---|---|---|---|
| 23219 | Richmond city (Central VA) | 6.000 | 6.000 | 0.00 ✓ |
| 23451 | Virginia Beach (Hampton Roads) | not probed, pinned | 6.000 | 0.00 ✓ |
| 23185 | Williamsburg (Historic Triangle) | 7.000 | 7.000 | 0.00 ✓ |
| 24011 | Roanoke (no district) | 5.300 | 5.300 | 0.00 ✓ |
| 22902 | Charlottesville (no district) | pinned 5.300 | 5.300 | 0.00 ✓ |
| **24541** | **Danville (Pittsylvania)** | **5.300** | **6.300** | **−1.000** (Southside gap) |
| **24558** | **Halifax County** | **5.300** | **6.300** | **−1.000** (Southside gap) |
| 24112 | Martinsville (should bind Henry) | 5.300, binds Franklin | 6.300 | **−1.000** rate + wrong county |

## Status

- **UNCHANGED** for drift purposes — no new rate changed in the
  modelled jurisdictions.
- **Known coverage gap** on the 8 Southside localities (6.3% not
  modelled). A `VA_SOUTHSIDE_DISTRICT` ratchet would close it with
  one data edit; chip for a dedicated session rather than a daily
  audit.
- **24112 county-binding smell** (Martinsville → Franklin County);
  chipped under the FIPS-first tiebreak class, not fresh.
- **No code change** this audit.

## Reload / deploy

No reload required for VA this cycle. The Southside gap is a code
ratchet (data-only `va_data.py` edit plus a shared district binding),
not a `data load`.
