# Daily state sales tax audit — 2026-07-04 (day 4: CT + DC)

## TL;DR
- 2 jurisdictions audited (both non-SST, self-seeded, state-only).
- **0 rate changes found; 0 requiring code/test updates.**
- One near-miss avoided: several third-party tax aggregators list DC's
  *current* general rate as **6.5%**. That is **incorrect** — the DC
  *Sales Tax Increase Delay Amendment Act of 2025* postponed the
  originally-planned Oct-1-2025 step to 6.5%, so DC **remains 6.0%
  through Sept 30 2026** and jumps directly to **7.0% on Oct 1 2026**.
  The module already encodes this correctly. **Do not "fix" DC to
  6.5%** in a future audit — that would introduce a real bug.

## CT (Connecticut)
- **Source:** CT DRS — portal.ct.gov/drs; Conn. Gen. Stat. § 12-408.
- **Type:** Non-SST, self-seeded, state-only (no county/municipal sales
  tax anywhere in CT).
- **Last loaded on prod / modeled:** flat **6.350%** statewide, effective
  2011-07-01 (P.A. 11-6). No upstream SST file (self-seeded).
- **Latest available:** 6.35% statewide — unchanged. Confirmed against
  multiple 2026 references (Avalara, Stripe, TaxCloud, SalesTaxHandbook)
  and DRS statute; all agree 6.35% is the sole rate, no locals.
- **Drift summary:** None.
- **Recommended action:** None.
- **Details:**

  | City | Expected (DRS) | Actual (engine, live) | Delta |
  |---|---|---|---|
  | Hartford (06103-1234) | 6.350 | 6.35000 | 0.000 |
  | New Haven (06510-0001) | 6.350 | 6.35000 | 0.000 |
  | Stamford (06901-0001) | 6.350 | 6.35000 | 0.000 |
  | Bridgeport (06604-0001) | 6.350 | 6.35000 | 0.000 |

- **Notes:** CT's category-specific rates (7.75% luxury, 7.35% meals,
  15% hotel, 9.35% short-term vehicle rental, 1% computer/data services,
  2.99% vessels) remain **documented deferrals**, not drift — they await
  the rate-modifier / threshold-rule engine feature. The annual Sales
  Tax Free Week (2026: Aug 16–22) is encoded in `holidays_for`.

## DC (District of Columbia)
- **Source:** DC OTR — "Notice of Oct. 1, 2025 Tax Changes"
  (https://otr.cfo.dc.gov/release/notice-oct-1-2025-tax-changes);
  DC Code § 47-2002.
- **Type:** Non-SST, self-seeded, single-jurisdiction (no sub-District
  locals).
- **Last loaded on prod / modeled:** **6.000%** through 2026-09-30, then
  **7.000%** effective 2026-10-01 (two effective-dated rows).
- **Latest available:** Matches. OTR primary notice confirms the general
  rate **remains 6.0% through Sept 30 2026**, rising to **7.0% on Oct 1
  2026**. The *Sales Tax Increase Delay Amendment Act of 2025*
  superseded the earlier two-step (6→6.5→7) plan, cancelling the
  Oct-1-2025 step to 6.5%.
- **Drift summary:** None. Live engine returns 6.000% today (correct for
  the 6.0% period through 2026-09-30).
- **Recommended action:** None now. **Watch item:** on/after 2026-10-01
  the live engine should flip to 7.000% automatically via the encoded
  effective-dated row — the next DC audit after Oct 1 2026 should
  confirm the flip actually happened in production data.
- **Details:**

  | City | Expected (OTR) | Actual (engine, live) | Delta |
  |---|---|---|---|
  | Washington (20001-0001) | 6.000 | 6.00000 | 0.000 |

- **Conflicting-source note (important for future audits):** As of this
  audit, `sales.tax`, `taxcloud.com`, `trykintsugi.com`, and
  `vatupdate.com` variously state DC's *current* rate is **6.5%**. This
  is **stale/incorrect** — they report the pre-Delay-Act plan. The
  authoritative OTR notice and the Delay Amendment Act of 2025 both
  confirm 6.0% is current through 2026-09-30. If a future audit sees
  "6.5%" on an aggregator and the engine shows 6.0%, the engine is
  **right** — verify against otr.cfo.dc.gov before touching the module.
  DC's special-category rates (10% restaurant/on-premises alcohol,
  10.25% off-premises alcohol / rental vehicles, 15.95% hotel, 18%
  parking, 8% soft drinks, 7.5% commercial bingo) remain documented
  deferrals pending the category-specific-rate engine feature.

## Audit method
- Read both state modules (`connecticut.py`, `district_of_columbia.py`),
  the canonical city pins in `tests/integration/test_sst_dor_validation.py`,
  and recent git history (no CT/DC-specific commits since iter-198/235).
- Queried the live engine at `https://api.opensalestax.org/v1/calculate`
  (browser UA to clear Cloudflare) for each tier-1 city.
- Cross-checked against DOR primary sources (CT DRS statute; DC OTR
  Oct-1-2025 notice) and multiple 2026 third-party references.
- No SST file check applies — both jurisdictions are non-SST /
  self-seeded (no `XXR…zip` / `XXB…zip` upstream files).
