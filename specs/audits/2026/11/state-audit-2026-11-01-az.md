# Daily state sales tax audit — 2026-11-01 (full-sweep: AZ)

## TL;DR

- **The 2026-09-05 deploy + reload has fully landed on prod.** 14/14
  AZ probes exact at that run; this audit re-ran the key defect probes
  and all still match. **Status: UNCHANGED post-09-05 deploy.**
- **Still owed from the 2026-09-05 audit (coverage gaps, not drift):**
  - **Tusayan** (86023): combined city rate 2% → 4% effective
    2026-10-01 (ord. 2026-02). **Not modelled.** 86023 still returns
    6.90% (state 5.6 + Coconino 1.3, no city), unchanged by this run
    because the city isn't in `AZ_CITIES`. Would be 10.90% if modelled.
    Candidate for a coverage ratchet.
  - **San Tan Valley** (ord. 2026-06, eff 2026-10-01). 85143 binds to
    Queen Creek (2.25% city) via `AZ_CITIES` and returns 8.55%. STV is
    an unincorporated CDP in Pinal County and does not have its own
    general-retail city rate — the ordinance referenced in the earlier
    handoff is a Pinal **community district**-flavoured levy that does
    not map to AZ_CITIES' per-city structure. **Treat as unresolved and
    needs Eric's modeling decision** (same shape as Sun City / Vail —
    see the 2026-09-05 report).
  - **Tombstone, Willcox** (Cochise County) still cite **Avalara** in
    `az_data.py` comments (lines around the "iter-193" block). Not
    touched in this sweep — handoff lists this as part of the ~130
    aggregator-sourced-rate hits across AL/AZ/CA, with AZ "cleaned"
    at the pinned-city level and the comment lineage flagged for a
    primary-source pass.
- **Verified live on 2026-11-01:**
  - Kingman 86401 → 8.60% ✓ (post-2026-09-01 Kingman ord. 2003 applied)
  - Huachuca City 85616 → 9.50% ✓ (Cochise 1.0 + city 2.9)
  - Florence 85132 → 10.20% ✓ (Pinal 1.1 + Florence 3.5)
  - Sierra Vista 85635 → 8.55% ✓
  - Tusayan 86023 → 6.90% (coverage gap, see above)
  - San Tan Valley 85143 → 8.55% (coverage decision pending)
- **Source:** AZ DOR "All Business Classifications Tax Rate Table"
  CSV, business code 017 RETAIL. Latest file index at
  `https://azdor.gov/transaction-privilege-tax/tax-rate-tables`.
  Current table in `az_data.py` is the May 2026 CSV with ordinance
  patches to 2026-09-01.

## Source

- AZ DOR TPT_RATETABLE_ALL_* monthly CSVs (business code 017 "Retail
  Sales").
- Model City Tax Code ordinance page
  (`modelcitytaxcode.az.gov/`) — ordinance 2003 (Kingman), 2026-02
  (Tusayan), 2026-06 (San Tan Valley / Florence 780-26 / Huachuca
  City 2026-06).
- Prior deploy record: `specs/audits/2026/09/state-audit-2026-09-05.md`,
  Proxmox snapshot `predeploy20260905`.

## Procedure

- Live probes against `api.opensalestax.org` (6 cities above, all pass
  or are known coverage gaps).
- `az_data.py` reviewed: Kingman, Florence, Huachuca City, Cochise
  County 1.0% all present with primary-source citations. Tombstone +
  Willcox still comment-cite Avalara (noted; not fixed here).
- Prod `data_versions`: `AZ-SST-V0.55.4` fetched 2026-09-06 after the
  deploy; `AZ-ZCTA-2020` fetched 2026-05-11. No further load owed.
- Model City Tax Code ordinance page spot-checked for any ordinance
  posted since 2026-09-05 with effective date ≤ 2026-11-01 that would
  change a **modelled** city rate: **none identified** in this run.
  Tusayan and San Tan Valley effective dates (2026-10-01) are now
  past, but both are coverage gaps, not drift.

## Status: UNCHANGED

Nothing in `src/opensalestax/states/az_data.py` needed editing. The
09-05 deploy continues to carry the correct answers for every modelled
city.

## Actions taken

None. Audit report only.
