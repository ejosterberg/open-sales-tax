# State audit — VT — 2026-11-01 (full-sweep)

## TL;DR
- **VT: REFRESH_PENDING.** Prod is still two quarters behind (`VTR2026Q2FEB20` / `VTB2026Q2FEB20`); the current upstream file `VTR2026Q4AUG20` / `VTB2026Q4AUG20` carries **9 new 1% Local Option Sales Taxes** (8 effective 2026-07-01, Peru 2026-10-01) that the engine is not yet enforcing. The ≥ 11 under-collections documented in the 2026-10-28 audit are **still live on prod** as of 2026-11-01. The chip ("Refresh VT SST to 2026 Q4") remains open; **no new code change is possible on the agent side** until Eric reloads the SST file.

## Source
- Vermont Department of Taxes "Local Option Tax" (`tax.vermont.gov/business/local-option-tax`) — list of 38 active LOST municipalities, including the 9 that enacted on 2026-07-01 / 2026-10-01.
- SST rate index 2026-11-01 shows `VTR2026Q4AUG20.zip`; boundary index shows `VTB2026Q4AUG20.zip`. Prod cache holds the older `VTR2026Q2FEB20.zip` / `VTB2026Q2FEB20.zip`.

## Prod state (read-only)
- `data_versions` for VT: SST `VT-SST-2026Q2FEB20` (2026-05-06) + ZCTA (2026-05-11).
- Cached under `/var/lib/opensalestax/data/`: `VTR2026Q2FEB20.zip`, `VTB2026Q2FEB20.zip`. **Stale: Q4 is published, prod is on Q2.**

## Probes (prod `/v1/calculate`, bare ZIP5, $100 general tangible, 2026-11-01)
| Town (ZIP) | Expected (VT DoT) | Actual | Delta | Status |
|---|---|---|---|---|
| Fair Haven 05743 | 7.00 | 6.00 | **−1.00** | still under-collecting |
| Morristown 05661 | 7.00 | 6.00 | **−1.00** | still under-collecting |
| Pomfret 05053 | 7.00 | 6.00 | **−1.00** | still under-collecting |
| Vergennes 05491 | 7.00 | 6.00 | **−1.00** | still under-collecting |
| Waitsfield 05673 | 7.00 | 6.00 | **−1.00** | still under-collecting |
| Burlington 05401 | 7.00 | 7.00 | 0.00 | correct |
| Montpelier 05602 | 7.00 | 7.00 | 0.00 | correct |
| Bristol 05443 | 7.00 | 7.00 | 0.00 | correct total; friendly-name shows "Middlebury" (ZIP-span heuristic artefact — tracked, not changed here) |
| Rutland City 05701 | 7.00 | 7.00 | 0.00 | correct (long-standing LOST) |
| Swanton 05488 | 7.00 | 7.00 | 0.00 | correct total; authority `VT-city-61750` placeholder — same heuristic artefact |
| Peru 05152 | 7.00 | 7.00 | 0.00 | correct total; authority `VT-city-85075` placeholder — same heuristic artefact |
| Bennington 05201 (no LOST) | 6.00 | 6.00 | 0.00 | correct |

Five of the nine new-LOST towns are still under-collecting 1.00pp on bare ZIP5 lookup. Three others (Bristol, Swanton, Peru) incidentally return the right combined 7.00% because a *neighbouring* LOST town's code sits on the same ZIP — the authority name in the response is wrong, and the right total is a coincidence.

## Recommended action
- **REFRESH NEEDED on prod:** load `VTR2026Q4AUG20` + `VTB2026Q4AUG20` (reuse the existing data-version label `VT-SST-2026Q4AUG20` or similar — the loader purges by exact label, so renaming matters). Chip from 2026-10-28 (`"Refresh UT + VT SST to 2026 Q4"`) is still open.
- **After the refresh,** add the 9 new SST codes to `vt_names.py` once each is verified by probe (per that file's rule). This is a follow-on commit, not part of this audit.
- **No code change this run** — the fix is upstream data, chipped already. Ogden/UT pin + prior-audit chip are the only in-repo artefacts.

## Pin / grid state
- `tests/integration/test_sst_dor_validation.py` VT block has 7 pins:
  Burlington 05401 7.00, Montpelier 05602 7.00, Essex Junction 05452 7.00, Middlebury 05753 7.00, Barre City 05641 7.00, St. Albans City 05478 7.00, Bennington 05201 6.00.
  All 7 pass today — none of them exercise the 9 new-LOST towns, so a pre-refresh regression guard would be worth adding. **Deferred** to not conflict with other region work; the under-collections are already catalogued above.
