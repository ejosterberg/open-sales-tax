# WA state-tax audit — 2026-11-01 (full-sweep Pacific)

**Auditor:** region-agent (Pacific sweep)
**Branch:** `audit-sweep-pac-20261101`
**Status:** REFRESH_PENDING (Q3 2026 still unapplied; Q4 publication status unverified)

## What was checked

- Prod `data_versions` for WA: `WA-SST-2026Q2FEB26` fetched 2026-05-15.
  **Still one quarter behind the known-upstream Q3 (`WAR2026Q3MAY27`).**
- SST state-tax-files index https://www.streamlinedsalestax.org/state-tax-files
  returned HTTP 404 to the web-fetch; could not confirm whether a
  `WAR2026Q4<MMMDD>` has published or whether Q3 is still the current head.
- WA is SST → no code fix is possible for a rate change; the fix is a
  file refresh.
- `wa_names.py` and the 7 DOR_GRID pins bumped on 2026-08-25 (Tacoma, etc.)
  — unchanged this run; all 7 continue to fail under `-m liveapi` by
  design until the Q3+ refresh lands.

## Live defects still outstanding (no new fixes landed this run)

Six under-collections, live and wrong for **~124 days** (eff. 2026-07-01):

| ZIP | City | Prod | Correct |
|---|---|---:|---:|
| 98402 | Tacoma | 10.400 | **10.500** |
| 98225 | Bellingham | 9.100 | **9.200** |
| 98003 | Federal Way | 10.300 | **10.400** |
| 98501 | Olympia | 9.800 | **10.000** |
| 98499 | Lakewood | 10.100 | **10.300** |
| 98901 | Yakima | 8.500 | **8.600** |

Fix is a `data load -s WA -v <latest-Q3-or-Q4>` after redeploy. If Q4
2026 has published, apply Q4 and skip Q3 (handoff precedent for other
states). Q4 has no tier-1 exposure other than Mattawa (not pinned).

## Files touched

None. Audit report only.

## Live engine status

No code change this run. 6 live-wrong WA rates remain pending Q3/Q4 refresh.

## Follow-ups

- Re-verify SST file index when reachable; identify whether a
  `WAR2026Q4<MMMDD>` / `WAB2026Q4<MMMDD>` has published.
- When refreshing, remember that a ZIP-only query to the WA DOR
  address-rate API returns `code="5"` (ZIP-centroid county/PTBA
  fallback) — use a full street address at two addresses per city,
  as recorded in the 2026-08-25 audit.

## Commits

- `data(WA): full-sweep 2026-11-01 audit — Q3 refresh still unapplied; 6 live-wrong rates`
